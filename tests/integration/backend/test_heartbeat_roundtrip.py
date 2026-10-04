"""Agent Health Reporter (UBS-58/59/60) -> Ingestion (UBS-66) -> health read
side (UBS-69), through the real app and the real wire contract.

This is the one test that exercises the whole chain the way production will:
the agent's `HealthReporter` builds a heartbeat, `health/wire.py` flattens it
to the ingestion contract, it is POSTed to the merged `POST
/telemetry/heartbeat` route, recorded in the Agent Registry, and read back
from `GET /telemetry/health/agents/{agentId}`. No sockets - `TestClient`
drives the same ASGI app `uvicorn` serves.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.heartbeat import heartbeat_json
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_backend.config import BackendHealthConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app

T0 = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def test_agent_heartbeat_reaches_the_health_endpoint(tmp_path: Path) -> None:
    backend_clock = FakeClock()
    deps = AppDeps(
        config=BackendHealthConfig(missing_heartbeat_threshold_seconds=60),
        clock=backend_clock,
    )
    client = TestClient(create_app(deps=deps))

    # --- agent side, wired as the demo wires it
    log = tmp_path / "Fix.log"
    log.write_text("35=D|11=ORD-1|\n", newline="\n")
    monitor = LogMonitor(log, offset_tracker=OffsetTracker(tmp_path / "o.json"))
    reporter = HealthReporter(
        {"Fix.log": monitor},
        heartbeat=HeartbeatConfig(
            agent_id="magic-agent-sg-01", instance_ids=("magic-prod-01",)
        ),
    )
    reporter.set_queue_depth_provider(lambda: 4)
    reporter.record_parse_error()
    list(monitor.poll_lines())

    heartbeat = reporter.build_heartbeat()
    assert heartbeat.status == "unhealthy"  # 1/1 parse errors

    # --- the wire: exactly what HttpHeartbeatSink sends
    resp = client.post(
        "/telemetry/heartbeat",
        content=heartbeat_json(heartbeat, "ingestion"),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 202, resp.text

    # --- read side
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    assert body["status"] == "unhealthy"
    assert body["reportedStatus"] == "unhealthy"
    assert body["parseErrorCountLast5Min"] == 1
    assert body["publishQueueDepth"] == 4
    assert body["files"][0]["path"] == str(log)
    assert body["files"][0]["state"] == "reading"
    assert body["files"][0]["instanceId"] == "magic-prod-01"
    assert body["logReadLagMs"] is not None

    listing = client.get("/telemetry/health/agents").json()
    assert listing["counts"]["unhealthy"] == 1

    # --- the agent goes quiet; only the backend can notice
    backend_clock.advance(61)
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    assert body["status"] == "missing"
    assert body["reportedStatus"] == "unhealthy"  # its last word is kept
    monitor.close()


def test_heartbeat_embedded_in_a_batch_is_registered_too(tmp_path: Path) -> None:
    """Agents publish a heartbeat inside the 10s batch (FR-PUB-001), not only
    through the standalone endpoint."""
    deps = AppDeps(clock=FakeClock())
    client = TestClient(create_app(deps=deps))
    reporter = HealthReporter(
        {}, heartbeat=HeartbeatConfig(agent_id="batched-agent", instance_ids=("i-1",))
    )
    import json

    heartbeat = json.loads(heartbeat_json(reporter.build_heartbeat(), "ingestion"))

    resp = client.post(
        "/telemetry/batch",
        json={
            "schemaVersion": 1,
            "batchId": "0192f3a1-1c2d-7f00-8a1b-9f2c3d4e5f60",
            "batchSeq": 1,
            "agentId": "batched-agent",
            "application": "Magic",
            "sentAtUtc": "2026-09-22T04:00:00Z",
            "snapshots": [],
            "events": [],
            "alerts": [],
            "heartbeat": heartbeat,
        },
    )
    assert resp.status_code == 202, resp.text
    assert client.get("/telemetry/health/agents/batched-agent").status_code == 200


def test_unknown_agent_is_404() -> None:
    client = TestClient(create_app(deps=AppDeps(clock=FakeClock())))
    resp = client.get("/telemetry/health/agents/never-seen")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "not_found"
