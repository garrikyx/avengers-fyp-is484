from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from telemetry_agent.publishing.buffer import PendingItem, PublishBuffer

_NOW = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)


def _item(tag: str, *, offset: int = 0) -> PendingItem:
    """A distinguishable pending item — `payload` carries `tag` so tests
    can assert order/identity without depending on model equality.
    """
    return PendingItem("event", tag, _NOW + timedelta(seconds=offset))  # type: ignore[arg-type]


def _tags(items: list[PendingItem]) -> list[str]:
    return [item.payload for item in items]  # type: ignore[misc]


def test_append_and_take_preserve_fifo_order() -> None:
    buf = PublishBuffer(max_items=10)
    buf.append(_item("a"))
    buf.append(_item("b"))
    buf.append(_item("c"))

    taken = buf.take(2)

    assert _tags(taken) == ["a", "b"]
    assert buf.depth() == 1


def test_take_returns_fewer_than_requested_when_buffer_short() -> None:
    buf = PublishBuffer(max_items=10)
    buf.append(_item("a"))

    taken = buf.take(5)

    assert _tags(taken) == ["a"]
    assert buf.depth() == 0


def test_overflow_drops_oldest_and_counts() -> None:
    dropped = 0

    def on_drop() -> None:
        nonlocal dropped
        dropped += 1

    buf = PublishBuffer(max_items=2, on_drop=on_drop)
    buf.append(_item("a"))
    buf.append(_item("b"))
    buf.append(_item("c"))  # over cap -> "a" dropped

    assert buf.depth() == 2
    assert dropped == 1
    assert _tags(buf.take(2)) == ["b", "c"]


def test_requeue_front_restores_original_order() -> None:
    buf = PublishBuffer(max_items=10)
    buf.append(_item("a"))
    buf.append(_item("b"))
    buf.append(_item("c"))
    taken = buf.take(2)  # ["a", "b"]

    buf.requeue_front(taken)

    assert _tags(buf.take(3)) == ["a", "b", "c"]


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

    buf = PublishBuffer(max_items=2, on_drop=on_drop)
    buf.append(_item("a"))
    buf.append(_item("b"))
    taken = buf.take(2)  # buffer now empty; "a", "b" are in flight
    buf.append(_item("c"))
    buf.append(_item("d"))  # buffer now full: ["c", "d"]

    buf.requeue_front(taken)  # would be ["a", "b", "c", "d"] -> over cap

    assert buf.depth() == 2
    assert dropped == 2
    assert _tags(buf.take(2)) == ["c", "d"]


def test_max_items_must_be_positive() -> None:
    with pytest.raises(ValueError):
        PublishBuffer(max_items=0)
