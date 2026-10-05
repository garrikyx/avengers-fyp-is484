"""FastAPI entry point for the Telemetry Backend (spec 006 §1, §7).

Serves ingestion (`/telemetry/batch`, `/telemetry/events`,
`/telemetry/heartbeat`), metrics queries (`POST /telemetry/query/metrics`),
alert queries (`/telemetry/alerts`), and probe endpoints `/healthz` and
`/readyz` (`FR-HLT-010`, `FR-QRY-005`).

    uv run uvicorn telemetry_backend.main:app
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field, ValidationError
from starlette.middleware.base import RequestResponseEndpoint
from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.alerts_query import AlertDetailResponse, AlertsListResponse
from telemetry_shared.models.ingestion import EventsRequest, Heartbeat, TelemetryBatch
from telemetry_shared.models.metrics_query import (
    MetricsQueryRequest,
    MetricsQueryResponse,
)

from telemetry_backend.config import QueryConfig, StreamProcessorConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.heartbeat_monitor import HeartbeatMonitor
from telemetry_backend.services.ingestion import AcceptedIngestion, IngestionService
from telemetry_backend.services.query_engine import (
    QueryEngine,
    QueryTimeoutError,
    QueryValidationError,
)
from telemetry_backend.services.replica_fanout import (
    REPLICA_QUERY_HEADER,
    HttpxFanoutClient,
)
from telemetry_backend.services.stream_processor import StreamProcessor


class ItemCounts(CamelModel):
    snapshots: int = Field(ge=0)
    events: int = Field(ge=0)
    alerts: int = Field(ge=0)


class RejectedItem(CamelModel):
    kind: str
    index: int = Field(ge=0)
    code: str
    detail: str


class BatchAccepted(CamelModel):
    status: str
    batch_id: str | None = None
    event_id: str | None = None
    received_at_utc: datetime
    duplicate: bool = False
    accepted: ItemCounts
    rejected: list[RejectedItem] = Field(default_factory=list)


class ErrorDetail(CamelModel):
    field: str
    issue: str


class ErrorBody(CamelModel):
    code: str
    message: str
    details: list[ErrorDetail]
    request_id: str


class ErrorEnvelope(CamelModel):
    error: ErrorBody


class AlertsQueryParams(CamelModel):
    """Strict query model for `GET /telemetry/alerts` (`FR-QRY-032`)."""

    status: Literal["active", "resolved", "all"] = "active"
    application: str | None = None
    instance_id: str | None = Field(default=None, validation_alias="instanceId")
    rule_name: str | None = Field(default=None, validation_alias="ruleName")
    severity: str | None = None
    since: datetime | None = None
    limit: int = Field(default=100, ge=1, le=500)


_ALERTS_QUERY_KEYS = frozenset(
    {"status", "application", "instanceId", "ruleName", "severity", "since", "limit"}
)


def _received_at_utc() -> datetime:
    return datetime.now(UTC)


def _counts(*, snapshots: int = 0, events: int = 0, alerts: int = 0) -> ItemCounts:
    return ItemCounts(snapshots=snapshots, events=events, alerts=alerts)


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail],
) -> JSONResponse:
    """Build a consistent error response."""
    body = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=details,
            request_id=request.state.request_id,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", by_alias=True),
    )


def create_app(
    service: IngestionService | None = None,
    processor: StreamProcessor | None = None,
    alert_store: AlertStore | None = None,
    agent_registry: AgentRegistry | None = None,
    heartbeat_monitor: HeartbeatMonitor | None = None,
    query_engine: QueryEngine | None = None,
    query_config: QueryConfig | None = None,
    *,
    enable_heartbeat_monitor: bool = True,
) -> FastAPI:
    """Build an application, allowing tests and deployment to supply a service."""
    qconfig = query_config or QueryConfig()
    if service is not None:
        ingestion = service
        stream = ingestion.stream_processor
        store = ingestion.alert_store
        monitor = ingestion.heartbeat_monitor
        registry = ingestion.agent_registry
    else:
        stream = processor or StreamProcessor(StreamProcessorConfig())
        store = alert_store or AlertStore()
        registry = agent_registry or AgentRegistry()
        monitor = heartbeat_monitor
        if monitor is None and enable_heartbeat_monitor:
            monitor = HeartbeatMonitor(registry=registry, alert_store=store)
        ingestion = IngestionService(
            stream_processor=stream,
            alert_store=store,
            agent_registry=registry,
            heartbeat_monitor=monitor,
        )

    engine = query_engine or QueryEngine(
        stream.store,
        stream_processor=stream,
        agent_registry=registry,
        query_config=qconfig,
    )
    fanout_client: HttpxFanoutClient | None = None
    if qconfig.query_mode == "fanout" and qconfig.replica_registry:
        fanout_client = HttpxFanoutClient()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        worker = asyncio.create_task(ingestion.run(), name="telemetry-ingestion")
        heartbeat_task: asyncio.Task[None] | None = None
        if monitor is not None and enable_heartbeat_monitor:
            heartbeat_task = asyncio.create_task(
                monitor.run(), name="telemetry-heartbeat-monitor"
            )
        try:
            yield
        finally:
            worker.cancel()
            tasks: list[asyncio.Task[None]] = [worker]
            if heartbeat_task is not None:
                tasks.append(heartbeat_task)
            for task in tasks:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if fanout_client is not None:
                await fanout_client.aclose()

    app = FastAPI(title="Telemetry Backend", lifespan=lifespan)
    app.state.ingestion = ingestion
    app.state.processor = stream
    app.state.alert_store = store
    app.state.query_engine = engine
    app.state.fanout_client = fanout_client

    # The probe endpoints return bare dicts rather than this module's
    # CamelModel envelopes on purpose: an orchestrator's liveness/readiness
    # check shouldn't have to parse a telemetry-shaped response.
    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """FR-HLT-010: liveness only — process up, no dependency checks."""
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz(response: Response) -> dict[str, str]:
        """FR-QRY-005: `warming` (HTTP 503) until `warmupWindow` has elapsed
        since this replica started, so an orchestrator doesn't route traffic
        to a replica whose just-restarted, empty store would misreport as
        caught-up-and-idle.
        """
        if stream.is_ready(now=datetime.now(UTC)):
            return {"status": "ready"}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "warming"}

    @app.middleware("http")
    async def request_id(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.request_id = request.headers.get("X-Request-Id", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_payload(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        ingestion.record_rejection()
        details = [
            ErrorDetail(
                field=".".join(str(part) for part in error["loc"] if part != "body"),
                issue=error["msg"],
            )
            for error in exc.errors()
        ]
        return _error_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_field",
            message="Request payload validation failed.",
            details=details,
        )

    def enqueue_or_full(
        request: Request, item: AcceptedIngestion
    ) -> JSONResponse | None:
        if ingestion.enqueue(item):
            return None
        return _error_response(
            request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="queue_full",
            message="Ingestion queue is full; retry the batch later.",
            details=[],
        )

    @app.post(
        "/telemetry/batch",
        response_model=BatchAccepted,
        status_code=status.HTTP_202_ACCEPTED,
        responses={400: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
    )
    async def ingest_batch(
        request: Request, batch: TelemetryBatch
    ) -> BatchAccepted | JSONResponse:
        full = enqueue_or_full(
            request,
            AcceptedIngestion(
                snapshots=tuple(batch.snapshots),
                events=tuple(batch.events),
                alerts=tuple(batch.alerts),
                heartbeat=batch.heartbeat,
            ),
        )
        if full is not None:
            return full
        return BatchAccepted(
            status="accepted",
            batch_id=str(batch.batch_id),
            received_at_utc=_received_at_utc(),
            accepted=_counts(
                snapshots=len(batch.snapshots),
                events=len(batch.events),
                alerts=len(batch.alerts),
            ),
        )

    @app.post(
        "/telemetry/events",
        response_model=BatchAccepted,
        status_code=status.HTTP_202_ACCEPTED,
        responses={400: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
    )
    async def ingest_events(
        request: Request, payload: EventsRequest
    ) -> BatchAccepted | JSONResponse:
        full = enqueue_or_full(request, AcceptedIngestion(events=tuple(payload.events)))
        if full is not None:
            return full
        return BatchAccepted(
            status="accepted",
            event_id=str(payload.events[0].event_id)
            if len(payload.events) == 1
            else None,
            received_at_utc=_received_at_utc(),
            accepted=_counts(events=len(payload.events)),
        )

    @app.post(
        "/telemetry/heartbeat",
        response_model=BatchAccepted,
        status_code=status.HTTP_202_ACCEPTED,
        responses={400: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
    )
    async def ingest_heartbeat(
        request: Request, heartbeat: Heartbeat
    ) -> BatchAccepted | JSONResponse:
        full = enqueue_or_full(request, AcceptedIngestion(heartbeat=heartbeat))
        if full is not None:
            return full
        return BatchAccepted(
            status="accepted",
            received_at_utc=_received_at_utc(),
            accepted=_counts(),
        )

    @app.post(
        "/telemetry/query/metrics",
        response_model=MetricsQueryResponse,
        responses={
            400: {"model": ErrorEnvelope},
            504: {"model": ErrorEnvelope},
        },
    )
    async def query_metrics(
        request: Request, body: MetricsQueryRequest
    ) -> MetricsQueryResponse | JSONResponse:
        skip_fanout = request.headers.get(REPLICA_QUERY_HEADER) == "1"
        try:
            return await engine.query(
                body,
                skip_fanout=skip_fanout,
                fanout_client=fanout_client,
            )
        except QueryValidationError as exc:
            return _error_response(
                request,
                status_code=status.HTTP_400_BAD_REQUEST,
                code=exc.code,
                message=exc.message,
                details=[ErrorDetail(field=exc.field, issue=exc.issue)],
            )
        except QueryTimeoutError:
            return _error_response(
                request,
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                code="query_timeout",
                message="Query exceeded the server-side deadline.",
                details=[],
            )

    @app.get(
        "/telemetry/alerts",
        response_model=AlertsListResponse,
        responses={400: {"model": ErrorEnvelope}},
    )
    async def list_alerts(
        request: Request,
    ) -> AlertsListResponse | JSONResponse:
        unknown = set(request.query_params.keys()) - _ALERTS_QUERY_KEYS
        if unknown:
            return _error_response(
                request,
                status_code=status.HTTP_400_BAD_REQUEST,
                code="invalid_field",
                message="Unknown query parameter.",
                details=[
                    ErrorDetail(field=name, issue="Unknown query parameter.")
                    for name in sorted(unknown)
                ],
            )
        try:
            params = AlertsQueryParams.model_validate(dict(request.query_params))
        except ValidationError as exc:
            details = [
                ErrorDetail(
                    field=".".join(str(part) for part in error["loc"]),
                    issue=error["msg"],
                )
                for error in exc.errors()
            ]
            return _error_response(
                request,
                status_code=status.HTTP_400_BAD_REQUEST,
                code="invalid_field",
                message="Query parameter validation failed.",
                details=details,
            )
        return store.list_alerts(
            status=params.status,
            application=params.application,
            instance_id=params.instance_id,
            rule_name=params.rule_name,
            severity=params.severity,
            since=params.since,
            limit=params.limit,
        )

    @app.get(
        "/telemetry/alerts/{alert_id}",
        response_model=AlertDetailResponse,
        responses={404: {"model": ErrorEnvelope}},
    )
    async def get_alert(
        request: Request, alert_id: str
    ) -> AlertDetailResponse | JSONResponse:
        detail = store.get_alert(alert_id)
        if detail is None:
            return _error_response(
                request,
                status_code=status.HTTP_404_NOT_FOUND,
                code="not_found",
                message="Alert not found.",
                details=[],
            )
        return detail

    return app


app = create_app()
