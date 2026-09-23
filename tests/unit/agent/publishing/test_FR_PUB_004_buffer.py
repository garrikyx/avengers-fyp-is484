"""FR-PUB-004: the byte-and-age-bounded `PublishBuffer` (UBS-104's
replacement for UBS-103's item-count-only placeholder).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from telemetry_agent.publishing.buffer import PendingItem, PublishBuffer

_NOW = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)


def _item(tag: str, *, size: int = 10, age_seconds: float = 0) -> PendingItem:
    """A distinguishable pending item -- `payload` carries `tag` so tests
    can assert order/identity without depending on model equality."""
    return PendingItem(
        "event", tag, _NOW - timedelta(seconds=age_seconds), size  # type: ignore[arg-type]
    )


def _tags(items: list[PendingItem]) -> list[str]:
    return [item.payload for item in items]  # type: ignore[misc]


def test_append_and_take_preserve_fifo_order() -> None:
    buf = PublishBuffer(max_bytes=1000, max_age_seconds=900)
    buf.append(_item("a"))
    buf.append(_item("b"))
    buf.append(_item("c"))

    taken = buf.take(2)

    assert _tags(taken) == ["a", "b"]
    assert buf.depth() == 1


def test_take_returns_fewer_than_requested_when_buffer_short() -> None:
    buf = PublishBuffer(max_bytes=1000, max_age_seconds=900)
    buf.append(_item("a"))

    taken = buf.take(5)

    assert _tags(taken) == ["a"]
    assert buf.depth() == 0


def test_total_bytes_tracks_append_and_take() -> None:
    buf = PublishBuffer(max_bytes=1000, max_age_seconds=900)
    buf.append(_item("a", size=30))
    buf.append(_item("b", size=20))
    assert buf.total_bytes() == 50

    buf.take(1)
    assert buf.total_bytes() == 20


def test_byte_overflow_drops_oldest_and_counts() -> None:
    dropped = 0

    def on_drop() -> None:
        nonlocal dropped
        dropped += 1

    buf = PublishBuffer(max_bytes=25, max_age_seconds=900, on_drop=on_drop)
    buf.append(_item("a", size=10))
    buf.append(_item("b", size=10))
    buf.append(_item("c", size=10))  # total would be 30 > 25 -> "a" dropped

    assert buf.depth() == 2
    assert buf.total_bytes() == 20
    assert dropped == 1
    assert _tags(buf.take(2)) == ["b", "c"]


def test_an_item_larger_than_the_whole_cap_is_not_self_evicted() -> None:
    """A single oversized item stays (over cap) rather than evicting
    itself into an infinite loop -- the next append evicts it normally
    once something else exists to make room for."""
    dropped = 0

    def on_drop() -> None:
        nonlocal dropped
        dropped += 1

    buf = PublishBuffer(max_bytes=10, max_age_seconds=900, on_drop=on_drop)
    buf.append(_item("huge", size=1000))

    assert buf.depth() == 1
    assert dropped == 0

    buf.append(_item("b", size=5))  # now over cap with 2 items -> "huge" evicted

    assert dropped == 1
    assert _tags(buf.take(2)) == ["b"]


def test_expire_drops_only_items_older_than_max_age() -> None:
    dropped = 0

    def on_drop() -> None:
        nonlocal dropped
        dropped += 1

    buf = PublishBuffer(max_bytes=1000, max_age_seconds=60, on_drop=on_drop)
    buf.append(_item("stale", age_seconds=120))  # already 2 minutes old
    buf.append(_item("fresh", age_seconds=5))

    evicted_count = buf.expire(_NOW)

    assert evicted_count == 1
    assert dropped == 1
    assert _tags(buf.take(5)) == ["fresh"]


def test_expire_only_checks_the_head_stops_at_first_fresh_item() -> None:
    buf = PublishBuffer(max_bytes=1000, max_age_seconds=60)
    buf.append(_item("fresh_but_first", age_seconds=5))
    buf.append(_item("stale_but_second", age_seconds=120))

    buf.expire(_NOW)

    # "stale_but_second" is never reached because insertion order means
    # anything behind a fresh head is at least as fresh.
    assert buf.depth() == 2


def test_requeue_front_restores_original_order() -> None:
    buf = PublishBuffer(max_bytes=1000, max_age_seconds=900)
    buf.append(_item("a"))
    buf.append(_item("b"))
    buf.append(_item("c"))
    taken = buf.take(2)  # ["a", "b"]

    buf.requeue_front(taken)

    assert _tags(buf.take(3)) == ["a", "b", "c"]
    assert buf.total_bytes() == 0


def test_requeue_front_over_capacity_evicts_the_requeued_oldest_items() -> None:
    """Drop-oldest still holds after a requeue: the items just put back are
    the oldest data the buffer holds (they've been pending the longest),
    so if the buffer is now over capacity they are the ones evicted --
    not whatever arrived while they were in flight.
    """
    dropped = 0

    def on_drop() -> None:
        nonlocal dropped
        dropped += 1

    buf = PublishBuffer(max_bytes=20, max_age_seconds=900, on_drop=on_drop)
    buf.append(_item("a", size=10))
    buf.append(_item("b", size=10))
    taken = buf.take(2)  # buffer now empty; "a", "b" are in flight
    buf.append(_item("c", size=10))
    buf.append(_item("d", size=10))  # buffer now full: ["c", "d"]

    buf.requeue_front(taken)  # would be 40 bytes -> over cap

    assert buf.total_bytes() == 20
    assert dropped == 2
    assert _tags(buf.take(2)) == ["c", "d"]


def test_oldest_age_seconds() -> None:
    buf = PublishBuffer(max_bytes=1000, max_age_seconds=900)
    assert buf.oldest_age_seconds(_NOW) is None

    buf.append(_item("a", age_seconds=30))

    assert buf.oldest_age_seconds(_NOW) == 30


def test_max_bytes_must_be_positive() -> None:
    with pytest.raises(ValueError):
        PublishBuffer(max_bytes=0, max_age_seconds=900)


def test_max_age_seconds_must_be_positive() -> None:
    with pytest.raises(ValueError):
        PublishBuffer(max_bytes=1000, max_age_seconds=0)
