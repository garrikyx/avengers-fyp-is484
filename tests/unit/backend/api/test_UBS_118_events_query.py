"""UBS-118: event query API and ingestion round-trip."""

from __future__ import annotations

import time
from uuid import uuid4

from starlette.testclient import TestClient
from telemetry_backend.main import create_app
from telemetry_backend.services.event_store import EventStore
from telemetry_backend.services.ingestion import IngestionService

from tests.unit.backend.services.event_fixtures import (
    AGENT_ID,
    APPLICATION,
    BASE_TIME,
    INSTANCE_ID,
    make_telemetry_event,
)


def _app_with_store(store: EventStore):
    service = IngestionService(event_store=store, heartbeat_monitor=None)
    return create_app(service=service, enable_heartbeat_monitor=False)


def _event_payload() -> dict[str, object]:
    event = make_telemetry_event(event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60")
    return event.model_dump(mode="json", by_alias=True)


def test_UBS_118_events_endpoint_round_trip() -> None:
    store = EventStore()
    service = IngestionService(event_store=store, heartbeat_monitor=None)
    app = create_app(service=service, enable_heartbeat_monitor=False)

    with TestClient(app) as client:
        posted = client.post("/telemetry/events", json={"events": [_event_payload()]})
        assert posted.status_code == 202
        deadline = time.monotonic() + 2.0
        while service.queue_depth and time.monotonic() < deadline:
            time.sleep(0.01)

        listed = client.get("/telemetry/events?eventType=agent.started")
        assert listed.status_code == 200
        body = listed.json()
        assert len(body["events"]) == 1
        assert body["events"][0]["eventId"] == "01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60"

        detail = client.get(
            "/telemetry/events/01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60"
        )
        assert detail.status_code == 200
        assert detail.json()["eventType"] == "agent.started"


def test_UBS_118_batch_ingestion_makes_events_queryable() -> None:
    store = EventStore()
    service = IngestionService(event_store=store, heartbeat_monitor=None)
    app = create_app(service=service, enable_heartbeat_monitor=False)

    with TestClient(app) as client:
        batch = {
            "schemaVersion": 1,
            "batchId": str(uuid4()),
            "batchSeq": 1,
            "agentId": AGENT_ID,
            "application": APPLICATION,
            "sentAtUtc": BASE_TIME.isoformat(),
            "snapshots": [],
            "events": [_event_payload()],
            "alerts": [],
        }
        posted = client.post("/telemetry/batch", json=batch)
        assert posted.status_code == 202
        deadline = time.monotonic() + 2.0
        while service.queue_depth and time.monotonic() < deadline:
            time.sleep(0.01)

        listed = client.get(f"/telemetry/events?instanceId={INSTANCE_ID}")
        assert listed.status_code == 200
        assert any(
            item["eventId"] == "01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60"
            for item in listed.json()["events"]
        )


def test_UBS_118_unknown_query_param_returns_400() -> None:
    app = _app_with_store(EventStore())

    with TestClient(app) as client:
        response = client.get("/telemetry/events?bogus=1")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_field"


def test_UBS_118_missing_event_returns_404() -> None:
    app = _app_with_store(EventStore())

    with TestClient(app) as client:
        response = client.get(
            "/telemetry/events/01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60"
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"
