"""UBS-135: read access checkpoint, question rate limit and query audit."""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from telemetry_backend.api.access import read_access
from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app
from telemetry_backend.services.ingestion import IngestionService
from telemetry_backend.services.question_limiter import QuestionLimiter
from telemetry_backend.services.stream_processor import StreamProcessor

from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot

QUESTION = "Why are orders rejecting in the last 30 minutes?"
# Agent-authenticated write paths (FR-ING-002); not part of the read surface.
INGESTION_PATHS = {"/telemetry/batch", "/telemetry/events", "/telemetry/heartbeat"}


def _nl_client(per_minute: int = 20) -> TestClient:
    processor = StreamProcessor(StreamProcessorConfig())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 50, "orders_rejected": 5}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    nl_config = NlConfig(
        enabled=True,
        llm=LlmConfig(provider="mock"),
        per_user_rate_limit_per_minute=per_minute,
    )
    app = create_app(
        service=IngestionService(stream_processor=processor),
        deps=AppDeps(nl_config=nl_config),
    )
    return TestClient(app)


def test_FR_NLQ_018_every_read_route_goes_through_read_access() -> None:
    app = create_app(deps=AppDeps())
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/telemetry"):
            continue
        if route.methods & {"POST", "PUT", "PATCH", "DELETE"}:
            reads = {"/telemetry/query/metrics", "/telemetry/nl/query"}
            assert route.path in reads | INGESTION_PATHS, route.path
            if route.path in INGESTION_PATHS:
                continue
        calls = [dep.call for dep in route.dependant.dependencies]
        assert read_access in calls, route.path


def test_FR_NLQ_021_default_limit_is_20_per_minute() -> None:
    assert AppDeps().question_limiter._per_minute == 20


def test_FR_NLQ_021_question_over_limit_is_429_with_retry_after() -> None:
    client = _nl_client(per_minute=2)
    for _ in range(2):
        assert client.post(
            "/telemetry/nl/query", json={"question": QUESTION}
        ).is_success
    refused = client.post("/telemetry/nl/query", json={"question": QUESTION})
    assert refused.status_code == 429
    assert refused.json()["error"]["code"] == "rate_limited"
    assert int(refused.headers["Retry-After"]) >= 1


def test_FR_NLQ_021_window_slides() -> None:
    now = [NOW]
    limiter = QuestionLimiter(1, clock=lambda: now[0])
    assert limiter.acquire("a") is None
    assert limiter.acquire("a") == 60
    assert limiter.acquire("b") is None
    now[0] += timedelta(seconds=60)
    assert limiter.acquire("a") is None


def test_FR_NLQ_019_audit_logs_interpreted_query_not_question(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _nl_client()
    with caplog.at_level(logging.INFO, logger="telemetry_backend.audit"):
        response = client.post(
            "/telemetry/nl/query",
            json={"question": QUESTION},
            headers={"X-Request-Id": "req-135"},
        )
    assert response.status_code == 200
    [line] = [r.getMessage() for r in caplog.records if r.name.endswith("audit")]
    assert "request_id=req-135" in line
    assert "actor=unauthenticated" in line
    assert "rejection_summary" in line
    assert QUESTION not in line


def test_FR_NLQ_018_copilot_plugin_exposes_only_read_operations() -> None:
    from deployment.copilot.export_openapi import plugin_openapi

    spec = plugin_openapi("https://example.invalid")
    ops = {op["operationId"] for ops in spec["paths"].values() for op in ops.values()}
    assert "ingest_batch_telemetry_batch_post" not in ops
    assert len(ops) == 6
    plugin = json.loads(Path("deployment/copilot/ai-plugin.json").read_text())
    assert {f["name"] for f in plugin["functions"]} == ops
    assert set(plugin["runtimes"][0]["run_for_functions"]) == ops
