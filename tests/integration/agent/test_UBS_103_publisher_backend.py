"""UBS-103 integration test: the Backend Publisher against the *real*
Telemetry Backend FastAPI app (`telemetry_backend.main.create_app()`), via
`httpx.ASGITransport` -- no real socket, but the exact same
`HttpsPublishSink` -> `httpx.AsyncClient` -> FastAPI request/response path
production uses. Covers what the live backend actually implements today
(202 happy path, 503 when its queue is full); 401/403/413/429 are covered
against a scripted fake sink in
`tests/unit/agent/publishing/test_UBS_103_response_contract.py` since the
real backend doesn't enforce auth/size/rate limits yet.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import httpx
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink
from telemetry_backend.main import create_app
from telemetry_backend.services.ingestion import AcceptedIngestion, IngestionService
from telemetry_shared.models.snapshot import Snapshot

_AGENT_ID = "magic-agent-sg-01"
_APPLICATION = "Magic"
_ENDPOINT = "https://backend.example/telemetry/batch"
_NOW = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)


def _snapshot() -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
        instance_id="magic-prod-01",
        bucket_start_utc=_NOW,
        bucket_seconds=10,
    )


def _publisher(app: object, transport: httpx.ASGITransport) -> BackendPublisher:
    sink = HttpsPublishSink(_ENDPOINT, "test-token", transport=transport)
    config = parse_publish_config({"endpoint": _ENDPOINT})
    return BackendPublisher(sink, config, agent_id=_AGENT_ID, application=_APPLICATION)


def test_happy_path_against_the_real_backend_app() -> None:
    app = create_app()
    publisher = _publisher(app, httpx.ASGITransport(app=app))
    publisher.enqueue_snapshot(_snapshot())

    action = asyncio.run(publisher.publish_once(now=_NOW))

    assert action is PublishAction.COMMIT
    assert publisher.queue_depth() == 0
    # The backend genuinely accepted it into its own ingestion queue.
    assert app.state.ingestion.queue_depth == 1


def test_503_when_the_backend_queue_is_full() -> None:
    service = IngestionService(queue_size=1)
    service.enqueue(AcceptedIngestion())  # fills the only slot
    app = create_app(service=service)
    publisher = _publisher(app, httpx.ASGITransport(app=app))
    publisher.enqueue_snapshot(_snapshot())

    action = asyncio.run(publisher.publish_once(now=_NOW))

    assert action is PublishAction.BACKOFF
    assert publisher.queue_depth() == 1  # item stayed buffered, not lost
