"""UBS-68: HTTP contract for POST /telemetry/query/metrics."""

from __future__ import annotations

from datetime import timedelta

from starlette.testclient import TestClient
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.main import create_app
from telemetry_backend.services.ingestion import IngestionService
from telemetry_backend.services.stream_processor import StreamProcessor

from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot


def _client_with_data() -> TestClient:
    processor = StreamProcessor(StreamProcessorConfig())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 42, "orders_rejected": 2}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    service = IngestionService(stream_processor=processor)
    app = create_app(service=service, enable_heartbeat_monitor=False)
    return TestClient(app)


def test_UBS_68_http_query_returns_totals() -> None:
    with _client_with_data() as client:
        response = client.post(
            "/telemetry/query/metrics",
            json={
                "timeRange": {
                    "fromUtc": BASE_TIME.isoformat(),
                    "toUtc": (BASE_TIME + timedelta(minutes=5)).isoformat(),
                },
                "filters": {"instanceId": "magic-prod-01"},
                "metrics": ["orders", "rejections"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["totals"]["orders"] == 42
    assert body["totals"]["rejections"] == 2
    assert "dataCompleteness" in body
    assert "queryId" in body


def test_UBS_68_unknown_field_returns_400() -> None:
    with _client_with_data() as client:
        response = client.post(
            "/telemetry/query/metrics",
            json={
                "timeRange": {"last": "30m"},
                "metrics": ["orders"],
                "typoField": True,
            },
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_field"
