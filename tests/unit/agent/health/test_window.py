"""UBS-59: bounded sliding-window counter."""

from datetime import UTC, datetime, timedelta

import pytest
from telemetry_agent.health.window import SlidingWindowCounter

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


def at(seconds: float) -> datetime:
    return T0 + timedelta(seconds=seconds)


def test_counts_events_inside_window() -> None:
    w = SlidingWindowCounter(window_seconds=300)
    for s in (0, 1, 2, 150, 299):
        w.record(at(s))
    assert w.count(at(299)) == 5


def test_decays_as_window_slides() -> None:
    w = SlidingWindowCounter(window_seconds=300)
    w.record(at(0), n=3)
    w.record(at(100))
    assert w.count(at(299)) == 4
    assert w.count(at(300)) == 1  # the t=0 bucket has just left the window
    assert w.count(at(399)) == 1
    assert w.count(at(400)) == 0


def test_idle_window_reads_zero_not_none() -> None:
    w = SlidingWindowCounter(window_seconds=60)
    assert w.count(at(0)) == 0
    w.record(at(0))
    assert w.count(at(5000)) == 0


def test_memory_is_bounded_regardless_of_event_rate() -> None:
    w = SlidingWindowCounter(window_seconds=300, bucket_seconds=1)
    for i in range(100_000):  # 100k events across 1000s
        w.record(at(i / 100))
    assert len(w) <= w.capacity == 300
    assert w.count(at(999.99)) == 30_000  # last 300s x 100/s


def test_late_event_still_inside_window_is_counted() -> None:
    w = SlidingWindowCounter(window_seconds=300)
    w.record(at(200))
    w.record(at(150))  # arrives late, still within the window
    assert w.count(at(200)) == 2


def test_event_older_than_window_is_dropped() -> None:
    w = SlidingWindowCounter(window_seconds=60)
    w.record(at(100))
    w.record(at(0))  # 100s stale against a 60s window
    assert w.count(at(100)) == 1
    assert len(w) == 1


def test_uses_injected_clock_when_now_omitted() -> None:
    now = at(0)
    w = SlidingWindowCounter(window_seconds=10, clock=lambda: now)
    w.record()
    assert w.count() == 1
    now = at(11)
    assert w.count() == 0


@pytest.mark.parametrize(("window", "bucket"), [(0, 1), (10, 0), (10, 20), (-5, 1)])
def test_rejects_bad_geometry(window: float, bucket: float) -> None:
    with pytest.raises(ValueError):
        SlidingWindowCounter(window_seconds=window, bucket_seconds=bucket)
