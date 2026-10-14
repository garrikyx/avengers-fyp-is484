"""Agent Health Reporter (UBS-58/59/60) -> Backend Publisher -> Ingestion
(UBS-66) -> health read side (UBS-69), through the real app and the real wire
contract.

This exercises the chain the way production does: the agent's
`HealthReporter` builds a heartbeat, the Backend Publisher asks for it through
`health/publishing.heartbeat_provider`, carries it in the `heartbeat` slot of
a `TelemetryBatch` to `POST /telemetry/batch`, the backend records it in the
Agent Registry, and it is read back from `GET /telemetry/health/agents/{id}`.
No sockets - `httpx.ASGITransport` and `TestClient` drive the same ASGI app
`uvicorn` serves.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.publishing import (
    connect_reporter_to_publisher,
    drop_hook,
    heartbeat_provider,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink
from telemetry_backend.config import BackendHealthConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app

T0 = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)
ENDPOINT = "https://backend.example/telemetry/batch"


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def _publisher(
    app: object, reporter: HealthReporter, agent_id: str
) -> BackendPublisher:
    publisher = BackendPublisher(
        HttpsPublishSink(
            ENDPOINT, "test-token", transport=httpx.ASGITransport(app=app)
        ),
        parse_publish_config({"endpoint": ENDPOINT}),
        agent_id=agent_id,
        application="Magic",
        heartbeat_provider=heartbeat_provider(reporter),
        on_drop=drop_hook(reporter),
    )
    connect_reporter_to_publisher(reporter, publisher)
    return publisher


def test_agent_heartbeat_reaches_the_health_endpoint(tmp_path: Path) -> None:
    backend_clock = FakeClock()
    deps = AppDeps(
        config=BackendHealthConfig(missing_heartbeat_threshold_seconds=60),
        clock=backend_clock,
    )
    app = create_app(deps=deps)
    client = TestClient(app)

    # --- agent side: reporter wired to the publisher, as production wires it
    log = tmp_path / "Fix.log"
    log.write_text("35=D|11=ORD-1|\n", newline="\n")
    monitor = LogMonitor(log, offset_tracker=OffsetTracker(tmp_path / "o.json"))
    reporter = HealthReporter(
        {"Fix.log": monitor},
        heartbeat=HeartbeatConfig(
            agent_id="magic-agent-sg-01", instance_ids=("magic-prod-01",)
        ),
    )
    publisher = _publisher(app, reporter, "magic-agent-sg-01")
    reporter.record_parse_error()
    list(monitor.poll_lines())
    assert reporter.build_heartbeat().status == "unhealthy"  # 1/1 parse errors

    # --- the wire: the publisher carries the heartbeat in a batch
    assert asyncio.run(publisher.publish_once()) is PublishAction.COMMIT

    # --- read side
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    assert body["status"] == "unhealthy"
    assert body["reportedStatus"] == "unhealthy"
    assert body["parseErrorCountLast5Min"] == 1
    assert body["publishQueueDepth"] == 0  # read from the publisher (UBS-60)
    assert body["droppedEventsLast5Min"] == 0  # producer wired, nothing dropped
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


def test_heartbeat_provider_output_is_accepted_in_a_batch() -> None:
    """The backend contract for the batch's heartbeat slot, without the
    publisher: what `heartbeat_provider` returns is a valid batch heartbeat."""
    deps = AppDeps(clock=FakeClock())
    client = TestClient(create_app(deps=deps))
    reporter = HealthReporter(
        {}, heartbeat=HeartbeatConfig(agent_id="batched-agent", instance_ids=("i-1",))
    )
    heartbeat = heartbeat_provider(reporter)().model_dump(mode="json", by_alias=True)

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
