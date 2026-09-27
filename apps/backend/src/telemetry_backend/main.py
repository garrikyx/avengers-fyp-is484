"""FastAPI entry point for the Telemetry Backend (spec 006 §1, §7).

Serves the ingestion contract (`/telemetry/batch`, `/telemetry/events`,
`/telemetry/heartbeat`), the two probe endpoints `/healthz` and `/readyz`
(`FR-HLT-010`, `FR-QRY-005`) and the agent-liveness read side under
`/telemetry/health` (UBS-69, `FR-ING-010`). The query, alert and NL routes
depend on components this app doesn't build yet and are out of scope here.

    uv run telemetry-backend [--config config/backend.yaml]
    uv run uvicorn telemetry_backend.main:app
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field
from starlette.middleware.base import RequestResponseEndpoint
from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.ingestion import EventsRequest, Heartbeat, TelemetryBatch

from telemetry_backend.api import health as health_api
from telemetry_backend.config import (
    BackendConfigError,
    StreamProcessorConfig,
    load_backend_health_config,
)
from telemetry_backend.deps import AppDeps
from telemetry_backend.services.ingestion import AcceptedIngestion, IngestionService
from telemetry_backend.services.stream_processor import StreamProcessor

logger = logging.getLogger(__name__)


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
    deps: AppDeps | None = None,
) -> FastAPI:
    """Build an application, allowing tests and deployment to supply a service."""
    # One StreamProcessor, shared by ingestion and `/readyz`. `is_ready()`
    # needs the store to have data, so probing a separate instance that
    # ingestion never feeds would report `warming` forever. Its warmup
    # clock starts once, here - for the module-level `app = create_app()`
    # below that is import time, matching FR-QRY-005's "since this replica
    # started".
    if service is not None:
        if processor is not None and processor is not service.stream_processor:
            raise ValueError(
                "processor must be the service's own stream_processor, or "
                "omitted; /readyz has to probe the store ingestion writes to"
            )
        ingestion = service
    else:
        ingestion = IngestionService(
            stream_processor=processor or StreamProcessor(StreamProcessorConfig())
        )
    stream = ingestion.stream_processor
    # UBS-69: the Agent Registry and the health read side. Shared via
    # app.state so routers reach the same instance (see deps.py).
    app_deps = deps or AppDeps()

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
    app.state.processor = stream
    app.state.deps = app_deps
    app.include_router(health_api.router)

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
        since this replica started *and* ingestion has merged data into the
        store, so an orchestrator doesn't route traffic to a replica whose
        just-restarted, empty store would misreport as caught-up-and-idle.
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
        # A heartbeat embedded in a batch counts the same as a standalone one.
        if batch.heartbeat is not None:
            app_deps.registry.record_heartbeat(batch.heartbeat)
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
        # FR-ING-010: record every agent's last heartbeat, version and
        # connectivity state in the Agent Registry as telemetry arrives.
        # `record_heartbeat` returns True on first contact - the unknown-agent
        # event that hangs off it is UBS-87.
        # No explicit received_at: the registry stamps it from the same clock
        # it judges staleness with, so a test (or a replica) can inject one.
        app_deps.registry.record_heartbeat(heartbeat)
        return BatchAccepted(
            status="accepted",
            received_at_utc=_received_at_utc(),
            accepted=_counts(),
        )

    return app


app = create_app()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magic Telemetry Backend")
    parser.add_argument("--config", type=Path, default=Path("config/backend.yaml"))
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="validate the config file and exit (spec 011 install runbook)",
    )
    parser.add_argument("--log-level", default="info")
    return parser


def main() -> None:
    """`uv run telemetry-backend [--config config/backend.yaml]`.

    A missing config file means defaults (spec 010), so this runs with no
    file at all. `store.warmupWindow` from the file feeds the one shared
    StreamProcessor, so `/readyz` honours it.
    """
    args = _build_parser().parse_args()
    logging.basicConfig(
        level=args.log_level.upper(), format="%(levelname)s %(name)s %(message)s"
    )
    try:
        config = load_backend_health_config(args.config)
    except BackendConfigError as exc:
        raise SystemExit(f"config error: {exc}") from exc
    if args.check_config:
        print(f"config ok: {config}")
        return
    processor = StreamProcessor(
        StreamProcessorConfig(
            warmup_window_seconds=int(config.warmup_window_seconds)
        )
    )
    host, port = config.listen_host_port
    logger.info("public API on http://%s:%d", host, port)
    try:
        uvicorn.run(
            create_app(processor=processor, deps=AppDeps(config=config)),
            host=host,
            port=port,
            log_level=args.log_level,
        )
    except KeyboardInterrupt:
        pass
