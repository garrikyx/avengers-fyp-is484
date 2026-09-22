"""FastAPI entry point for the Telemetry Backend.

Carries the ingestion contract (UBS-66) plus the operator liveness/readiness
probes (`FR-HLT-010`, `FR-QRY-005`). `/metrics` is deliberately absent: spec
007 §5.3 keeps it on the internal listener only (`FR-HLT-012`), and it lands
with UBS-96 alongside the richer agent-liveness endpoints of UBS-69.

`uv run uvicorn telemetry_backend.main:app`
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field
from starlette.middleware.base import RequestResponseEndpoint
from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.ingestion import EventsRequest, Heartbeat, TelemetryBatch

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.ingestion import AcceptedIngestion, IngestionService
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
) -> FastAPI:
    """Build an application, allowing tests and deployment to supply a service."""
    ingestion = service or IngestionService()
    # Built once per app, not per request: `/readyz`'s warmupWindow clock
    # starts when this replica starts, matching FR-QRY-005's "since this
    # replica started" rather than restarting on every probe.
    readiness = processor or StreamProcessor(StreamProcessorConfig())

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        worker = asyncio.create_task(ingestion.run(), name="telemetry-ingestion")
        try:
            yield
        finally:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="Telemetry Backend", lifespan=lifespan)
    app.state.ingestion = ingestion

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

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        """FR-HLT-010: liveness only - process up, no dependency checks. A
        probe that checked dependencies would have an orchestrator restart a
        backend that is serving fine while something upstream is down."""
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz(response: Response) -> dict[str, str]:
        """FR-QRY-005: `warming` (503) until `warmupWindow` has elapsed since
        this replica started *and* data has actually arrived, so an
        orchestrator does not route queries at a just-restarted, empty store
        whose emptiness would read as caught-up-and-idle."""
        if readiness.is_ready(now=_received_at_utc()):
            return {"status": "ready"}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "warming"}

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

    return app


app = create_app()
