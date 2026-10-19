"""HTTP routes for NL query."""

from __future__ import annotations

from fastapi.testclient import TestClient
from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app
from telemetry_backend.nl.factory import build_nl_service
from telemetry_backend.services.ingestion import IngestionService
from telemetry_backend.services.stream_processor import StreamProcessor

from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot


def test_nl_query_disabled_returns_503() -> None:
    app = create_app(deps=AppDeps(nl_config=NlConfig(enabled=False)))
    client = TestClient(app)
    response = client.post(
        "/telemetry/nl/query",
        json={"question": "Why are orders rejecting?"},
    )
    assert response.status_code == 503


def test_nl_query_enabled_returns_answer() -> None:
    processor = StreamProcessor(StreamProcessorConfig())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 50, "orders_rejected": 5}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    ingestion = IngestionService(stream_processor=processor)
    nl_config = NlConfig(enabled=True, llm=LlmConfig(provider="mock"))
    deps = AppDeps(nl_config=nl_config)
    app = create_app(service=ingestion, deps=deps)
    engine = app.state.query_engine
    prebuilt = build_nl_service(
        nl_config,
        query_engine=engine,
        alert_store=deps.alert_store,
        stream_config=processor._config,
    )
    deps = AppDeps(nl_config=nl_config, nl_service=prebuilt)
    app = create_app(service=ingestion, deps=deps)
    client = TestClient(app)
    response = client.post(
        "/telemetry/nl/query",
        json={
            "question": "Why are orders rejecting in the last 30 minutes?",
            "context": {"defaultApplication": "Magic"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "answer"
    assert body["intent"] == "rejection_summary"
    assert "interpretedQuery" in body
