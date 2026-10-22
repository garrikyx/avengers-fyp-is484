"""UBS-117: monitor and terminal callback producers preserve existing behaviour."""

import asyncio
import json

import pytest
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker

from tests.unit.agent.callbacks.callback_fixtures import make_alert_event
from tests.unit.agent.publishing.test_UBS_117_events import sent, stack


def test_monitor_events_and_stall_recovery_without_losing_lines(tmp_path):
    clock = [0.0]
    emitter, publisher, sink = stack()
    path = tmp_path / "PRIVATE_PATH.log"
    path.write_text("first line\n")
    monitor = LogMonitor(
        path,
        OffsetTracker(tmp_path / "offsets.json"),
        monotonic=lambda: clock[0],
        log_stall_threshold=5,
        on_event=lambda kind: emitter.log_lifecycle(kind, 0),
    )
    try:
        assert [line.text for line in monitor.poll_lines()] == ["first line"]
        clock[0] = 5
        assert list(monitor.poll_lines()) == []
        clock[0] = 10
        assert list(monitor.poll_lines()) == []  # only one event per idle episode
        path.rename(tmp_path / "PRIVATE_PATH.log.1")
        path.write_text("second line\n")
        assert [line.text for line in monitor.poll_lines()] == ["second line"]
        path.write_text("x\n")
        assert [line.text for line in monitor.poll_lines()] == ["x"]
        clock[0] = 15
        list(monitor.poll_lines())
        events = sent(publisher, sink)
        assert [e["eventType"] for e in events] == [
            "log.stalled",
            "log.rotated",
            "log.truncated",
            "log.stalled",
        ]
        assert all(e["fields"] == {"sourceIndex": 0} for e in events)
        assert "PRIVATE_PATH" not in json.dumps(events)
    finally:
        monitor.close()


def test_event_hook_failure_does_not_interrupt_monitor(tmp_path):
    path = tmp_path / "app.log"
    path.write_text("long first line\n")

    def fail(_):
        raise RuntimeError("event hook unavailable")

    monitor = LogMonitor(path, OffsetTracker(tmp_path / "offsets.json"), on_event=fail)
    try:
        list(monitor.poll_lines())
        path.write_text("short\n")
        assert [line.text for line in monitor.poll_lines()] == ["short"]
    finally:
        monitor.close()


@pytest.mark.parametrize(
    "content",
    [
        "{",
        "null",
        "[1]",
        '{"key": 3}',
        '[{"fileStateOS": {"device": 1, "inode": 2}, "offset": "bad"}]',
    ],
)
def test_corrupt_registry_is_reported_without_crashing(tmp_path, content):
    path = tmp_path / "offsets.json"
    path.write_text(content)
    tracker = OffsetTracker(path)
    assert tracker.state_reset_reason == "corrupt"
    assert tracker.get_offset(1, 2) == 0


def test_valid_registry_does_not_report_reset(tmp_path):
    path = tmp_path / "offsets.json"
    tracker = OffsetTracker(path)
    assert tracker.state_reset_reason == "missing"
    tracker.commit_offset("app.log", 1, 2, 42)
    tracker.save()
    loaded = OffsetTracker(path)
    assert loaded.state_reset_reason is None
    assert loaded.get_offset(1, 2) == 42


class CallbackSink:
    def __init__(self, statuses):
        self.statuses = iter(statuses)

    async def send(self, **kwargs):
        return CallbackResult(status_code=next(self.statuses), latency_ms=0)


@pytest.mark.parametrize(
    ("statuses", "max_bytes", "reason", "attempts"),
    [
        ([400], 65536, "permanent_http_failure", 1),
        ([503, 503], 65536, "retries_exhausted", 2),
        ([None, None], 65536, "retries_exhausted", 2),
        ([], 1, "payload_too_large", 0),
        ([503, 200], 65536, None, 0),
        ([200], 65536, None, 0),
    ],
)
def test_callback_only_terminal_failures_emit(statuses, max_bytes, reason, attempts):
    emitter, publisher, sink = stack()
    cfg = parse_callbacks_config(
        {
            "endpoint": "https://callback.invalid",
            "maxAttempts": 2,
            "maxBytes": max_bytes,
            "retry": {"base": "0s", "jitter": 0},
        }
    )
    dispatcher = CallbackDispatcher(
        CallbackSink(statuses), cfg, b"secret", on_failure=emitter.callback_failed
    )
    asyncio.run(dispatcher._deliver(make_alert_event()))
    events = sent(publisher, sink) if publisher.queue_depth() else []
    if reason is None:
        assert events == []
    else:
        assert len(events) == 1
        assert events[0]["eventType"] == "callback.failed"
        assert events[0]["fields"]["reason"] == reason
        assert events[0]["fields"]["attempts"] == attempts
        assert "secret" not in json.dumps(events)


def test_callback_event_failure_does_not_break_terminal_delivery_tracking():
    def fail(*args):
        raise RuntimeError("event sink unavailable")

    dispatcher = CallbackDispatcher(
        CallbackSink([400]),
        parse_callbacks_config({"endpoint": "https://callback.invalid"}),
        b"secret",
        on_failure=fail,
    )
    asyncio.run(dispatcher._deliver(make_alert_event()))
    assert dispatcher.counters.snapshot()["callback_failures"] == 1
    assert dispatcher.counters.snapshot()["callback_event_errors"] == 1
