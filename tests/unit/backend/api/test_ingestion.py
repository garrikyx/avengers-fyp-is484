"""Unit tests for the ingestion API contract and queue hand-off."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
from telemetry_backend.main import BatchAccepted, create_app
from telemetry_backend.services.ingestion import IngestionService
from telemetry_shared.models.ingestion import EventsRequest, TelemetryBatch

NOW = datetime(2026, 9, 19, 9, 0, 0, tzinfo=UTC).isoformat()
Endpoint = Callable[..., Awaitable[BatchAccepted | JSONResponse]]


def _event() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "eventId": str(uuid4()),
        "agentId": "magic-agent-sg-01",
        "application": "Magic",
        "instanceId": "magic-prod-01",
        "eventType": "agent.started",
        "timestampUtc": NOW,
        "timeSource": "agent",
        "severity": "info",
        "dimensions": {},
        "fields": {},
    }


def _batch() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "batchId": str(uuid4()),
        "batchSeq": 1,
        "agentId": "magic-agent-sg-01",
        "application": "Magic",
        "sentAtUtc": NOW,
        "events": [_event()],
        "snapshots": [],
        "alerts": [],
    }


def _request(app: FastAPI) -> Request:
    request = Request({"type": "http", "app": app, "headers": []})
    request.state.request_id = "request-id-test"
    return request


def _endpoint(app: FastAPI, path: str) -> Endpoint:
    route = next(
        (
            candidate
            for candidate in app.routes
            if isinstance(candidate, APIRoute) and candidate.path == path
        ),
        None,
    )
    assert route is not None
    return cast(Endpoint, route.endpoint)


def test_batch_contract_accepts_a_valid_payload_and_enqueues_it() -> None:
    service = IngestionService()
    app = create_app(service)
    payload = TelemetryBatch.model_validate(_batch())
    endpoint = _endpoint(app, "/telemetry/batch")
    response = asyncio.run(endpoint(_request(app), payload))

    assert isinstance(response, BatchAccepted)
    assert response.status == "accepted"
    assert response.batch_id
    assert response.received_at_utc
    assert response.accepted.events == 1
    assert response.rejected == []
    assert service.accepted_payloads_total == 1
    assert service.queue_depth == 1


def test_malformed_payload_returns_400_with_the_failing_field_and_is_counted() -> None:
    service = IngestionService()
    app = create_app(service)
    handler = app.exception_handlers[RequestValidationError]
    validation_error = RequestValidationError(
        [
            {
                "type": "missing",
                "loc": ("body", "agentId"),
                "msg": "Field required",
                "input": _batch(),
            }
        ]
    )
    response = asyncio.run(
        cast(Awaitable[Response], handler(_request(app), validation_error))
    )

    assert response.status_code == 400
    body = json.loads(bytes(response.body))["error"]
    assert body["code"] == "invalid_field"
    assert any(detail["field"] == "agentId" for detail in body["details"])
    assert service.rejected_payloads_total == 1


def test_events_endpoint_returns_the_accepted_single_event_id() -> None:
    event = _event()
    app = create_app()
    endpoint = _endpoint(app, "/telemetry/events")
    response = asyncio.run(
        endpoint(_request(app), EventsRequest.model_validate({"events": [event]}))
    )

    assert isinstance(response, BatchAccepted)
    assert response.event_id == event["eventId"]
    assert response.received_at_utc
    assert response.accepted.events == 1
