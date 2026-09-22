"""UBS-58 / FR-HLT-001: heartbeat emitter and wire format."""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.heartbeat import (
    HeartbeatEmitter,
    HttpHeartbeatSink,
    LoggingHeartbeatSink,
    heartbeat_json,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_shared.models.health import AgentHeartbeat

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self, start: datetime = T0) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class Collect:
    def __init__(self) -> None:
        self.items: list[AgentHeartbeat] = []

    def __call__(self, hb: AgentHeartbeat) -> None:
        self.items.append(hb)


def _reporter(clock: FakeClock) -> HealthReporter:
    config = HeartbeatConfig(
        agent_id="magic-agent-sg-01",
        instance_ids=("magic-prod-01",),
        agent_version="0.1.0+test",
        interval_seconds=10.0,
    )
    return HealthReporter({}, heartbeat=config, clock=clock)


# --- payload -------------------------------------------------------------------


def test_heartbeat_payload_matches_spec_004_section_6() -> None:
    clock = FakeClock()
    reporter = _reporter(clock)
    clock.advance(42)

    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))

    assert wire["schemaVersion"] == 1
    assert wire["agentId"] == "magic-agent-sg-01"
    assert wire["instanceIds"] == ["magic-prod-01"]
    assert wire["sentAtUtc"].startswith("2026-09-20T04:00:42")
    assert wire["agentVersion"] == "0.1.0+test"
    assert wire["uptimeSeconds"] == 42.0
    assert wire["status"] == "healthy"
    assert wire["statusReasons"] == []
    assert wire["files"] == []
    # FR-HLT-004: signals with no producer on this branch are null, never 0
    for gap in (
        "readLagMs",
        "parseErrorCountLast5Min",
        "callbackFailuresLast5Min",
        "publishQueueDepth",
        "droppedEventsLast5Min",
    ):
        assert wire[gap] is None, gap
    # a backend can rehydrate what we send
    AgentHeartbeat.model_validate_json(heartbeat_json(reporter.build_heartbeat()))


def test_heartbeat_carries_file_state_and_lag(tmp_path: Path) -> None:
    log = tmp_path / "Fix.log"
    log.write_text("35=D|11=ORD-1|\n", newline="\n")
    monitor = LogMonitor(log, offset_tracker=OffsetTracker(tmp_path / "o.json"))
    reporter = HealthReporter({"Fix.log": monitor})
    list(monitor.poll_lines())

    hb = reporter.build_heartbeat()
    assert hb.files[0].state == "reading"
    assert hb.files[0].offset == 15
    assert hb.read_lag_ms is not None and hb.read_lag_ms >= 0
    monitor.close()


# --- emitter ---------------------------------------------------------------------


def test_tick_sends_once_and_counts() -> None:
    sink = Collect()
    emitter = HeartbeatEmitter(_reporter(FakeClock()), sink)
    emitter.tick()
    assert len(sink.items) == 1
    assert emitter.sent_count == 1 and emitter.failed_count == 0
    assert emitter.last_sent_at == T0


def test_interval_defaults_from_reporter_config() -> None:
    emitter = HeartbeatEmitter(_reporter(FakeClock()), Collect())
    assert emitter.interval_seconds == 10.0
    assert (
        HeartbeatEmitter(_reporter(FakeClock()), Collect(), 2.5).interval_seconds == 2.5
    )
    with pytest.raises(ValueError):
        HeartbeatEmitter(_reporter(FakeClock()), Collect(), 0)


def test_sink_failure_is_counted_not_raised(caplog: pytest.LogCaptureFixture) -> None:
    def boom(_: AgentHeartbeat) -> None:
        raise ConnectionError("backend down")

    emitter = HeartbeatEmitter(_reporter(FakeClock()), boom)
    with caplog.at_level(logging.WARNING):
        emitter.tick()
        emitter.tick()
    assert emitter.failed_count == 2 and emitter.sent_count == 0
    assert "heartbeat sink failed" in caplog.text


def test_run_emits_on_interval_with_no_log_activity() -> None:
    """AC: an idle agent still heartbeats; N ticks in ~N intervals."""
    sink = Collect()
    emitter = HeartbeatEmitter(_reporter(FakeClock()), sink, interval_seconds=0.05)

    async def scenario() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(emitter.run(stop))
        await asyncio.sleep(0.32)
        stop.set()
        await asyncio.wait_for(task, timeout=1)

    asyncio.run(scenario())
    # first tick immediate + ~6 intervals; wide bounds for Windows' ~16ms timer
    assert 4 <= len(sink.items) <= 9
    assert all(hb.agent_id == "magic-agent-sg-01" for hb in sink.items)


def test_run_keeps_going_after_sink_failure() -> None:
    calls = 0

    def flaky(_: AgentHeartbeat) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("first one fails")

    emitter = HeartbeatEmitter(_reporter(FakeClock()), flaky, interval_seconds=0.01)

    async def scenario() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(emitter.run(stop))
        await asyncio.sleep(0.05)
        stop.set()
        await asyncio.wait_for(task, timeout=1)

    asyncio.run(scenario())
    assert emitter.failed_count == 1
    assert emitter.sent_count >= 2


# --- sinks -----------------------------------------------------------------------


def test_logging_sink_writes_wire_json(caplog: pytest.LogCaptureFixture) -> None:
    hb = _reporter(FakeClock()).build_heartbeat()
    with caplog.at_level(logging.INFO):
        LoggingHeartbeatSink()(hb)
    assert '"agentId":"magic-agent-sg-01"' in caplog.text


def test_http_sink_posts_json_and_raises_on_4xx() -> None:
    from http import HTTPStatus
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from threading import Thread

    received: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            received.append(json.loads(body))
            code = HTTPStatus.ACCEPTED if self.path == "/ok" else HTTPStatus.BAD_REQUEST
            self.send_response(code)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *_: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    hb = _reporter(FakeClock()).build_heartbeat()
    try:
        HttpHeartbeatSink(f"{base}/ok")(hb)
        assert received[-1]["agentId"] == "magic-agent-sg-01"
        assert "sentAtUtc" in received[-1]
        with pytest.raises(RuntimeError, match="400"):
            HttpHeartbeatSink(f"{base}/bad")(hb)
    finally:
        server.shutdown()
        server.server_close()


# --- review fixes ----------------------------------------------------------------


def test_naive_sent_at_is_rejected_and_aware_is_normalised_to_utc() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="timezone-aware"):
        AgentHeartbeat.model_validate_json(
            '{"agentId":"a","instanceIds":["i"],"sentAtUtc":"2026-09-20T04:00:00",'
            '"agentVersion":"0","uptimeSeconds":1,"status":"healthy"}'
        )
    sg = datetime(2026, 9, 20, 12, 0, tzinfo=timezone(timedelta(hours=8)))
    hb = AgentHeartbeat(
        agent_id="a",
        instance_ids=["i"],
        sent_at_utc=sg,
        agent_version="0",
        uptime_seconds=1,
        status="healthy",
    )
    assert hb.sent_at_utc == datetime(2026, 9, 20, 4, 0, tzinfo=UTC)
    assert hb.sent_at_utc.tzinfo == UTC


def test_slow_sink_does_not_block_the_event_loop() -> None:
    """A sink stuck in blocking I/O must not starve other coroutines."""
    import time

    def slow(_: AgentHeartbeat) -> None:
        time.sleep(0.3)

    emitter = HeartbeatEmitter(_reporter(FakeClock()), slow, interval_seconds=10)
    beats = 0

    async def other() -> None:
        nonlocal beats
        for _ in range(10):
            await asyncio.sleep(0.02)
            beats += 1

    async def scenario() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(emitter.run(stop))
        await other()
        stop.set()
        await asyncio.wait_for(task, timeout=2)

    asyncio.run(scenario())
    assert beats == 10
    assert emitter.sent_count >= 1
