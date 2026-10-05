"""UBS-94: alert query API list + detail endpoints."""

from __future__ import annotations

import time
from datetime import timedelta

from starlette.testclient import TestClient
from telemetry_backend.config import AlertStoreConfig
from telemetry_backend.main import create_app
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.ingestion import IngestionService

from tests.unit.backend.services.alert_fixtures import (
    BASE_TIME,
    INSTANCE_ID,
    make_alert_event,
    make_resolved_event,
)


def _app_with_store(store: AlertStore):
    service = IngestionService(alert_store=store)
    return create_app(service=service, enable_heartbeat_monitor=False)


def test_UBS_94_list_filters_by_status_instance_and_since() -> None:
    store = AlertStore()
    store.merge(make_alert_event(alert_id="active-1"))
    store.merge(
        make_resolved_event(
            alert_id="resolved-1",
            last_observed_utc=BASE_TIME + timedelta(minutes=10),
        )
    )
    app = _app_with_store(store)

    with TestClient(app) as client:
        active = client.get("/telemetry/alerts?status=active")
        assert active.status_code == 200
        body = active.json()
        assert len(body["alerts"]) == 1
        assert body["alerts"][0]["alertId"] == "active-1"

        filtered = client.get(
            "/telemetry/alerts",
            params={
                "status": "resolved",
                "instanceId": INSTANCE_ID,
                "since": (BASE_TIME + timedelta(minutes=5)).isoformat(),
            },
        )
        assert filtered.status_code == 200
        assert len(filtered.json()["alerts"]) == 1


def test_UBS_94_list_reports_truncation_when_limit_is_exceeded() -> None:
    store = AlertStore()
    for index in range(5):
        store.merge(make_alert_event(alert_id=f"alert-{index}"))
    app = _app_with_store(store)

    with TestClient(app) as client:
        response = client.get("/telemetry/alerts?limit=2")
        assert response.status_code == 200
        body = response.json()
        assert len(body["alerts"]) == 2
        assert body["truncated"] is True


def test_UBS_94_detail_returns_transition_history_and_unknown_is_404() -> None:
    store = AlertStore(AlertStoreConfig(max_transitions=50))
    store.merge(make_alert_event(alert_id="detail-me"))
    store.merge(
        make_alert_event(
            alert_id="detail-me",
            severity="warning",
            last_observed_utc=BASE_TIME + timedelta(minutes=1),
        )
    )
    app = _app_with_store(store)

    with TestClient(app) as client:
        detail = client.get("/telemetry/alerts/detail-me")
        assert detail.status_code == 200
        body = detail.json()
        assert body["alert"]["alertId"] == "detail-me"
        assert len(body["transitions"]) == 2

        missing = client.get("/telemetry/alerts/evicted-or-unknown")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "not_found"


def test_UBS_94_unknown_query_parameter_returns_invalid_field() -> None:
    app = _app_with_store(AlertStore())

    with TestClient(app) as client:
        response = client.get("/telemetry/alerts?typo=yes")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_field"


def test_UBS_94_batch_ingestion_makes_alerts_queryable() -> None:
    store = AlertStore()
    service = IngestionService(alert_store=store)
    app = create_app(service=service, enable_heartbeat_monitor=False)

    with TestClient(app) as client:
        alert = make_alert_event(alert_id="from-batch")
        batch = {
            "schemaVersion": 1,
            "batchId": "01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60",
            "batchSeq": 1,
            "agentId": alert.agent_id,
            "application": alert.application,
            "sentAtUtc": BASE_TIME.isoformat(),
            "snapshots": [],
            "events": [],
            "alerts": [alert.model_dump(mode="json", by_alias=True)],
        }
        posted = client.post("/telemetry/batch", json=batch)
        assert posted.status_code == 202
        deadline = time.monotonic() + 2.0
        while service.queue_depth and time.monotonic() < deadline:
            time.sleep(0.01)
        listed = client.get("/telemetry/alerts?ruleName=HighRejectRate")
        assert listed.status_code == 200
        assert any(
            item["alertId"] == "from-batch" for item in listed.json()["alerts"]
        )
