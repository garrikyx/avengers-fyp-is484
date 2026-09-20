"""Agent Health Reporter (UBS-58/59/60) -> backend health read side (UBS-69).

Builds a real heartbeat with the agent's `HealthReporter`, posts it through
the FastAPI app with the agent's own `HttpHeartbeatSink`-equivalent encoding,
and reads it back from `/telemetry/health/agents/{agentId}`. No sockets; the
point is that the two sides agree on the shared `AgentHeartbeat` contract
(FR-ING-022) and that staleness is decided on the backend.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.heartbeat import HeartbeatEmitter, heartbeat_json
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_backend.app import create_public_app
from telemetry_backend.config import BackendHealthConfig
from telemetry_backend.deps import AppDeps

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def test_agent_heartbeat_round_trips_into_health_endpoint(tmp_path: Path) -> None:
    # --- backend
    backend_clock = FakeClock()
    deps = AppDeps(
        config=BackendHealthConfig(missing_heartbeat_threshold_seconds=60),
        clock=backend_clock,
    )
    client = TestClient(create_public_app(deps))

    # --- agent, wired exactly like the demo: emitter -> sink -> POST
    log = tmp_path / "Fix.log"
    log.write_text("35=D|11=ORD-1|\n", newline="\n")
    monitor = LogMonitor(log, offset_tracker=OffsetTracker(tmp_path / "o.json"))
    agent_clock = FakeClock()
    reporter = HealthReporter(
        {"Fix.log": monitor},
        heartbeat=HeartbeatConfig(agent_id="magic-agent-sg-01", instance_ids=("p1",)),
        clock=agent_clock,
    )
    reporter.set_queue_depth_provider(lambda: 2)
    reporter.record_parse_error()

    def http_sink(hb: object) -> None:
        resp = client.post(
            "/telemetry/heartbeat",
            content=heartbeat_json(hb),  # type: ignore[arg-type]
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 202, resp.text

    emitter = HeartbeatEmitter(reporter, http_sink)
    list(monitor.poll_lines())
    emitter.tick()
    assert emitter.sent_count == 1

    # --- read side
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    assert body["status"] == "unhealthy"  # 1/1 parse errors -> agent said unhealthy
    assert body["reportedStatus"] == "unhealthy"
    assert body["parseErrorCountLast5Min"] == 1
    assert body["publishQueueDepth"] == 2
    assert body["files"][0]["path"] == str(log)
    assert body["files"][0]["state"] == "reading"
    assert body["logReadLagMs"] is not None

    listing = client.get("/telemetry/health/agents").json()
    assert listing["counts"]["unhealthy"] == 1

    # --- the agent goes quiet; only the backend clock decides it is missing
    backend_clock.advance(61)
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    assert body["status"] == "missing"
    assert body["reportedStatus"] == "unhealthy"
    monitor.close()
