"""UBS-104: publish buffer bytes and dropped-event rate in the heartbeat.

Mirrors `test_queue_depth.py` (UBS-60)'s style for the provider-based
`publishBufferBytes` gauge, and `test_parse_errors.py` (UBS-59)'s style
for the rolling-window `droppedEventsLast5Min` counter.
"""

import json
from datetime import UTC, datetime, timedelta

from telemetry_agent.health.heartbeat import heartbeat_json
from telemetry_agent.health.reporter import HealthReporter

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


# --- publishBufferBytes: provider-based gauge, same shape as queue depth -----------


def test_buffer_bytes_is_none_without_a_provider() -> None:
    reporter = HealthReporter({}, clock=lambda: T0)
    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))
    assert wire["publishBufferBytes"] is None


def test_buffer_bytes_provider_can_be_registered_and_removed() -> None:
    reporter = HealthReporter({}, clock=lambda: T0)
    reporter.set_buffer_bytes_provider(lambda: 4096)
    assert reporter.snapshot().publish_buffer_bytes == 4096
    reporter.set_buffer_bytes_provider(None)
    assert reporter.snapshot().publish_buffer_bytes is None


def test_buffer_bytes_is_read_fresh_on_every_snapshot() -> None:
    state = {"bytes": 100}
    reporter = HealthReporter(
        {}, clock=lambda: T0, buffer_bytes_provider=lambda: state["bytes"]
    )
    assert reporter.snapshot().publish_buffer_bytes == 100
    state["bytes"] = 9000
    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))
    assert wire["publishBufferBytes"] == 9000


# --- droppedEventsLast5Min: rolling window, None until first record() -------------


def test_dropped_events_is_none_until_the_first_record() -> None:
    reporter = HealthReporter({}, clock=lambda: T0)
    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))
    assert wire["droppedEventsLast5Min"] is None


def test_recording_zero_marks_the_signal_seen_without_counting_anything() -> None:
    """A supervisor wiring the Publisher in calls this once at startup so a
    healthy Publisher (zero drops ever) reports a genuine `0`, not `None`
    forever -- `None` should mean "nothing is measuring this", not "nothing
    bad has happened yet"."""
    reporter = HealthReporter({}, clock=lambda: T0)
    reporter.record_dropped_events(0)
    assert reporter.snapshot().dropped_events == 0


def test_dropped_events_accumulate_within_the_window() -> None:
    clock = FakeClock()
    reporter = HealthReporter({}, clock=clock)
    reporter.record_dropped_events(3, clock.now)
    clock.advance(10)
    reporter.record_dropped_events(2, clock.now)

    assert reporter.snapshot(clock.now).dropped_events == 5


def test_dropped_events_roll_off_after_the_window() -> None:
    clock = FakeClock()
    reporter = HealthReporter({}, clock=clock)  # default 5-minute window
    reporter.record_dropped_events(7, clock.now)
    clock.advance(301)  # just past 5 minutes

    assert reporter.snapshot(clock.now).dropped_events == 0


def test_dropped_events_reach_the_wire() -> None:
    clock = FakeClock()
    reporter = HealthReporter({}, clock=clock)
    reporter.record_dropped_events(4, clock.now)

    wire = json.loads(heartbeat_json(reporter.build_heartbeat(now=clock.now)))

    assert wire["droppedEventsLast5Min"] == 4
