"""Unit tests for the ingestion API contract and queue hand-off."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.main import BatchAccepted, create_app
from telemetry_backend.services.ingestion import IngestionService
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.ingestion import EventsRequest, TelemetryBatch
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

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


def test_unknown_event_dimension_is_rejected_before_enqueue() -> None:
    service = IngestionService()
    app = create_app(service)
    batch = _batch()
    event = cast(dict[str, object], cast(list[object], batch["events"])[0])
    event["dimensions"] = {"account": "sensitive-value"}

    response = asyncio.run(
        _endpoint(app, "/telemetry/batch")(
            _request(app), TelemetryBatch.model_validate(batch)
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "unknown_dimension"
    assert body["error"]["details"] == [
        {
            "field": "events.0.dimensions.account",
            "issue": "dimension key is not allowlisted",
        }
    ]
    assert "sensitive-value" not in bytes(response.body).decode()
    assert service.queue_depth == 0
    assert service.rejected_payloads_total == 1


def test_unknown_event_field_is_rejected_on_events_endpoint() -> None:
    service = IngestionService()
    app = create_app(service)
    event = _event()
    event["fields"] = {"price": "sensitive-value"}

    response = asyncio.run(
        _endpoint(app, "/telemetry/events")(
            _request(app), EventsRequest.model_validate({"events": [event]})
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "invalid_field"
    assert body["error"]["details"][0]["field"] == "events.0.fields.price"
    assert "sensitive-value" not in bytes(response.body).decode()
    assert service.queue_depth == 0


def test_allowlisted_event_dimension_and_field_are_accepted() -> None:
    event = _event()
    event["dimensions"] = {"session": "MAGIC->EXCH1", "symbol": "ABC"}
    event["fields"] = {"msgType": "8", "clOrdIdHash": "0123456789abcdef"}
    service = IngestionService()
    app = create_app(service)

    response = asyncio.run(
        _endpoint(app, "/telemetry/events")(
            _request(app), EventsRequest.model_validate({"events": [event]})
        )
    )

    assert isinstance(response, BatchAccepted)
    assert response.status == "accepted"
    assert service.queue_depth == 1


def test_unknown_snapshot_dimension_is_rejected_before_enqueue() -> None:
    snapshot = Snapshot(
        schema_version=1,
        agent_id="magic-agent-sg-01",
        application="Magic",
        instance_id="magic-prod-01",
        bucket_start_utc=datetime.fromisoformat(NOW),
        bucket_seconds=10,
        series=[
            SeriesEntry(
                dimensions={"account": "sensitive-value"},
                counters={"orders_submitted": Decimal(1)},
            )
        ],
    )
    batch = _batch()
    batch["events"] = []
    batch["snapshots"] = [snapshot]
    service = IngestionService()
    app = create_app(service)

    response = asyncio.run(
        _endpoint(app, "/telemetry/batch")(
            _request(app), TelemetryBatch.model_validate(batch)
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "unknown_dimension"
    assert body["error"]["details"][0]["field"].endswith("dimensions.account")
    assert service.queue_depth == 0


def test_series_over_max_per_bucket_are_rejected_at_ingest() -> None:
    processor = StreamProcessor(StreamProcessorConfig(max_series_per_bucket=2))
    service = IngestionService(stream_processor=processor)
    app = create_app(service)
    snapshot = Snapshot(
        schema_version=1,
        agent_id="magic-agent-sg-01",
        application="Magic",
        instance_id="magic-prod-01",
        bucket_start_utc=datetime.fromisoformat(NOW),
        bucket_seconds=10,
        series=[
            SeriesEntry(
                dimensions={"symbol": symbol},
                counters={"orders_submitted": Decimal(1)},
            )
            for symbol in ("AAA", "BBB", "CCC")
        ],
    )
    batch = _batch()
    batch["events"] = []
    batch["snapshots"] = [snapshot]

    response = asyncio.run(
        _endpoint(app, "/telemetry/batch")(
            _request(app), TelemetryBatch.model_validate(batch)
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "cardinality_exceeded"
    assert body["error"]["details"] == [
        {
            "field": "snapshots.0.series",
            "issue": (
                "bucket would contain 3 distinct series; maxSeriesPerBucket is 2"
            ),
        }
    ]
    assert service.queue_depth == 0
    assert processor.store.dropped_series_over_cap_total == 0


def test_series_at_max_per_bucket_are_accepted() -> None:
    processor = StreamProcessor(StreamProcessorConfig(max_series_per_bucket=2))
    service = IngestionService(stream_processor=processor)
    app = create_app(service)
    snapshot = Snapshot(
        schema_version=1,
        agent_id="magic-agent-sg-01",
        application="Magic",
        instance_id="magic-prod-01",
        bucket_start_utc=datetime.fromisoformat(NOW),
        bucket_seconds=10,
        series=[
            SeriesEntry(
                dimensions={"symbol": symbol},
                counters={"orders_submitted": Decimal(1)},
            )
            for symbol in ("AAA", "BBB")
        ],
    )
    batch = _batch()
    batch["events"] = []
    batch["snapshots"] = [snapshot]

    response = asyncio.run(
        _endpoint(app, "/telemetry/batch")(
            _request(app), TelemetryBatch.model_validate(batch)
        )
    )

    assert isinstance(response, BatchAccepted)
    assert response.status == "accepted"
    assert service.queue_depth == 1


def test_cardinality_uses_canonical_bucket_across_requests() -> None:
    processor = StreamProcessor(StreamProcessorConfig(max_series_per_bucket=2))
    service = IngestionService(stream_processor=processor)
    app = create_app(service)
    now = datetime.now(UTC)
    canonical_start = now - timedelta(
        seconds=now.second % 10,
        microseconds=now.microsecond,
    )

    def batch_at(start: str, symbols: tuple[str, ...]) -> TelemetryBatch:
        snapshot = Snapshot(
            schema_version=1,
            agent_id="magic-agent-sg-01",
            application="Magic",
            instance_id="magic-prod-01",
            bucket_start_utc=datetime.fromisoformat(start),
            bucket_seconds=10,
            series=[
                SeriesEntry(
                    dimensions={"symbol": symbol},
                    counters={"orders_submitted": Decimal(1)},
                )
                for symbol in symbols
            ],
        )
        batch = _batch()
        batch["events"] = []
        batch["snapshots"] = [snapshot]
        return TelemetryBatch.model_validate(batch)

    first = asyncio.run(
        _endpoint(app, "/telemetry/batch")(
            _request(app),
            batch_at(
                (canonical_start + timedelta(seconds=1)).isoformat(),
                ("AAA", "BBB"),
            ),
        )
    )
    second = asyncio.run(
        _endpoint(app, "/telemetry/batch")(
            _request(app),
            batch_at((canonical_start + timedelta(seconds=8)).isoformat(), ("CCC",)),
        )
    )

    assert isinstance(first, BatchAccepted)
    assert isinstance(second, JSONResponse)
    assert second.status_code == 400
    assert json.loads(bytes(second.body))["error"]["code"] == "cardinality_exceeded"
    assert service.queue_depth == 1
