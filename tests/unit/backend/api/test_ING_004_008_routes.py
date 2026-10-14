"""UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from telemetry_backend.config import BackendHealthConfig, IngestGuardConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app, create_internal_app
from telemetry_backend.services.ingest_guard import Accept
from telemetry_backend.services.ingestion import AcceptedIngestion, IngestionService

T0 = datetime(2026, 9, 29, 4, 0, 0, tzinfo=UTC)
AGENT = "magic-agent-sg-01"


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def deps(limit: int = 30) -> AppDeps:
    return AppDeps(
        config=BackendHealthConfig(
            ingest=IngestGuardConfig(max_batches_per_minute_per_agent=limit)
        ),
        clock=FakeClock(),
    )


def batch(batch_id: str | None = None, agent: str = AGENT) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "batchId": batch_id or str(uuid4()),
        "batchSeq": 1,
        "agentId": agent,
        "application": "Magic",
        "sentAtUtc": T0.isoformat(),
        "snapshots": [],
        "events": [],
        "alerts": [],
    }


def metrics(d: AppDeps) -> str:
    return TestClient(create_internal_app(d)).get("/metrics").text


def test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() -> None:
    service = IngestionService()
    d = deps()
    client = TestClient(create_app(service, deps=d))
    body = batch()

    first = client.post("/telemetry/batch", json=body)
    second = client.post("/telemetry/batch", json=body)

    assert first.status_code == 202
    assert first.json()["duplicate"] is False
    assert second.status_code == 202
    assert second.json()["duplicate"] is True
    assert second.json()["batchId"] == body["batchId"]
    assert second.json()["accepted"] == {"snapshots": 0, "events": 0, "alerts": 0}
    assert service.queue_depth == 1
    text = metrics(d)
    assert "telemetry_backend_ingest_dedupe_hits_total 1.0" in text
    assert "telemetry_backend_ingest_batches_total 1.0" in text


def test_batches_past_the_per_agent_limit_get_429_with_retry_after() -> None:
    d = deps(limit=2)
    client = TestClient(create_app(deps=d))
    assert client.post("/telemetry/batch", json=batch()).status_code == 202
    assert client.post("/telemetry/batch", json=batch()).status_code == 202

    refused = client.post("/telemetry/batch", json=batch())
    assert refused.status_code == 429
    assert refused.headers["Retry-After"] == "60"
    assert refused.json()["error"]["code"] == "rate_limited"
    # Another agent is unaffected.
    other = client.post("/telemetry/batch", json=batch(agent="magic-agent-sg-02"))
    assert other.status_code == 202
    assert "telemetry_backend_ingest_rate_limited_total 1.0" in metrics(d)


def test_a_batch_refused_with_queue_full_is_accepted_on_retry() -> None:
    service = IngestionService(queue_size=1)
    service.enqueue(AcceptedIngestion())  # fill the only slot
    d = deps()
    client = TestClient(create_app(service, deps=d))
    body = batch()

    assert client.post("/telemetry/batch", json=body).status_code == 503
    # Not remembered: the agent's retry must not be swallowed as a duplicate.
    assert d.ingest_guard.check(AGENT, str(body["batchId"])) == Accept()
    assert "telemetry_backend_ingest_dedupe_hits_total 0.0" in metrics(d)
