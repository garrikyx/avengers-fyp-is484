"""FastAPI entry point for the Telemetry Backend (spec 006 §1, §7).

Serves ingestion (`/telemetry/batch`, `/telemetry/events`,
`/telemetry/heartbeat`), alert queries (`/telemetry/alerts`), agent health
(`/telemetry/health`), and probe endpoints `/healthz` and `/readyz`
(`FR-HLT-010`, `FR-QRY-005`).

    uv run telemetry-backend [--config config/backend.yaml]
    uv run uvicorn telemetry_backend.main:app
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field, ValidationError
from starlette.middleware.base import RequestResponseEndpoint
from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.alerts_query import AlertDetailResponse, AlertsListResponse
from telemetry_shared.models.ingestion import EventsRequest, Heartbeat, TelemetryBatch

from telemetry_backend.api import health as health_api
from telemetry_backend.api import internal as internal_api
from telemetry_backend.config import (
    BackendConfigError,
    StreamProcessorConfig,
    load_backend_health_config,
)
from telemetry_backend.deps import AppDeps
from telemetry_backend.services.ingest_guard import Duplicate, RateLimited
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


def _notify_heartbeat(
    ingestion: IngestionService, agent_id: str
) -> None:
    if ingestion.heartbeat_monitor is not None:
        ingestion.heartbeat_monitor.on_heartbeat(agent_id)


def create_app(
    service: IngestionService | None = None,
    processor: StreamProcessor | None = None,
    deps: AppDeps | None = None,
    *,
    enable_heartbeat_monitor: bool = True,
) -> FastAPI:
    """Build an application, allowing tests and deployment to supply a service."""
    app_deps = deps or AppDeps()
    if service is not None:
        if processor is not None and processor is not service.stream_processor:
            raise ValueError(
                "processor must be the service's own stream_processor, or "
                "omitted; /readyz has to probe the store ingestion writes to"
            )
        ingestion = service
    else:
        monitor = app_deps.heartbeat_monitor if enable_heartbeat_monitor else None
        ingestion = IngestionService(
            stream_processor=processor
            or StreamProcessor(
                StreamProcessorConfig(
                    warmup_window_seconds=int(app_deps.config.warmup_window_seconds)
                )
            ),
            alert_store=app_deps.alert_store,
            heartbeat_monitor=monitor,
        )
    stream = ingestion.stream_processor
    store = ingestion.alert_store
    app_deps.ingestion = ingestion
    self_metrics = app_deps.self_metrics
    monitor = ingestion.heartbeat_monitor

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        worker = asyncio.create_task(ingestion.run(), name="telemetry-ingestion")
        heartbeat_task: asyncio.Task[None] | None = None
        if monitor is not None:
            heartbeat_task = asyncio.create_task(
                monitor.run(), name="telemetry-heartbeat-monitor"
            )
        try:
            yield
        finally:
            worker.cancel()
            tasks: list[asyncio.Task[None]] = [worker]
            if heartbeat_task is not None:
                # monitor.run() is `while True`; awaiting it uncancelled hung
                # shutdown forever (every `with TestClient(app)` exit, and a
                # real SIGTERM).
                heartbeat_task.cancel()
                tasks.append(heartbeat_task)
            for task in tasks:
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    app = FastAPI(title="Telemetry Backend", lifespan=lifespan)
    app.state.ingestion = ingestion
    app.state.processor = stream
    app.state.deps = app_deps
    app.state.alert_store = store
    app.include_router(health_api.router)

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
    async def query_latency(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """UBS-96: server-side latency per *route template* (bounded label
        set; never the raw path, which would carry agent IDs). Unmatched
        paths (404s) are labelled `unmatched` so they cannot grow
        cardinality."""
        started = time.perf_counter()
        try:
            return await call_next(request)
        finally:
            route = request.scope.get("route")
            template = getattr(route, "path", None) or "unmatched"
            self_metrics.query_latency.labels(route=template).observe(
                time.perf_counter() - started
            )

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
        ingestion.release_cardinality_reservation(item)
        return _error_response(
            request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="queue_full",
            message="Ingestion queue is full; retry the batch later.",
            details=[],
        )

    def validate_or_reject(
        request: Request, item: AcceptedIngestion
    ) -> JSONResponse | None:
        issues = ingestion.validate_and_reserve(item)
        if not issues:
            return None
        ingestion.record_rejection()
        issue_codes = {issue.code for issue in issues}
        code = issue_codes.pop() if len(issue_codes) == 1 else "invalid_field"
        return _error_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code=code,
            message="Request payload failed ingestion policy validation.",
            details=[
                ErrorDetail(field=issue.field, issue=issue.issue) for issue in issues
            ],
        )

    @app.post(
        "/telemetry/batch",
        response_model=BatchAccepted,
        status_code=status.HTTP_202_ACCEPTED,
        responses={
            400: {"model": ErrorEnvelope},
            429: {"model": ErrorEnvelope},
            503: {"model": ErrorEnvelope},
        },
    )
    async def ingest_batch(
        request: Request, batch: TelemetryBatch
    ) -> BatchAccepted | JSONResponse:
        batch_id = str(batch.batch_id)
        verdict = app_deps.ingest_guard.check(batch.agent_id, batch_id)
        if isinstance(verdict, Duplicate):
            self_metrics.dedupe_hits.inc()
            return BatchAccepted(
                status="accepted",
                batch_id=batch_id,
                received_at_utc=_received_at_utc(),
                duplicate=True,
                accepted=_counts(),
            )
        if isinstance(verdict, RateLimited):
            self_metrics.rate_limited.inc()
            limited = _error_response(
                request,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                code="rate_limited",
                message="Per-agent batch rate exceeded; honour Retry-After.",
                details=[],
            )
            limited.headers["Retry-After"] = str(verdict.retry_after_seconds)
            return limited
        item = AcceptedIngestion(
            snapshots=tuple(batch.snapshots),
            events=tuple(batch.events),
            alerts=tuple(batch.alerts),
            heartbeat=batch.heartbeat,
        )
        invalid = validate_or_reject(request, item)
        if invalid is not None:
            return invalid
        full = enqueue_or_full(request, item)
        if full is not None:
            return full
        app_deps.ingest_guard.commit(batch.agent_id, batch_id)
        self_metrics.ingest_batches.inc()
        if batch.heartbeat is not None:
            app_deps.registry.record_heartbeat(batch.heartbeat)
            self_metrics.heartbeats_received.inc()
            _notify_heartbeat(ingestion, batch.heartbeat.agent_id)
        return BatchAccepted(
            status="accepted",
            batch_id=batch_id,
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
        item = AcceptedIngestion(events=tuple(payload.events))
        invalid = validate_or_reject(request, item)
        if invalid is not None:
            return invalid
        full = enqueue_or_full(request, item)
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
        app_deps.registry.record_heartbeat(heartbeat)
        self_metrics.heartbeats_received.inc()
        _notify_heartbeat(ingestion, heartbeat.agent_id)
        return BatchAccepted(
            status="accepted",
            received_at_utc=_received_at_utc(),
            accepted=_counts(),
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


def create_internal_app(deps: AppDeps) -> FastAPI:
    """UBS-96, FR-HLT-012: `/healthz`, `/readyz` and `/metrics` for the
    internal listener. Pass the `AppDeps` of an app built by `create_app`,
    so the probes read the ingestion service and store that app writes to.
    """
    if deps.ingestion is None:
        raise ValueError("build the public app with create_app(deps=deps) first")
    internal = FastAPI(title="Telemetry Backend (internal)")
    internal.state.deps = deps
    internal.include_router(internal_api.router)
    return internal


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


async def _serve(deps: AppDeps, log_level: str) -> None:
    """Two uvicorn servers, one process, one `AppDeps` (FR-HLT-012)."""
    public = create_app(deps=deps)
    internal = create_internal_app(deps)
    public_host, public_port = deps.config.listen_host_port
    internal_host, internal_port = deps.config.internal_listen_host_port
    servers = [
        uvicorn.Server(
            uvicorn.Config(
                public, host=public_host, port=public_port, log_level=log_level
            )
        ),
        uvicorn.Server(
            uvicorn.Config(
                internal, host=internal_host, port=internal_port, log_level=log_level
            )
        ),
    ]
    logger.info(
        "public API on http://%s:%d, internal probes on http://%s:%d",
        public_host,
        public_port,
        internal_host,
        internal_port,
    )
    await asyncio.gather(*(server.serve() for server in servers))


def main() -> None:
    """`uv run telemetry-backend [--config config/backend.yaml]`.

    A missing config file means defaults (spec 010), so this runs with no
    file at all. `store.warmupWindow` from the file feeds the one shared
    StreamProcessor (see `create_app`), so both `/readyz`s honour it.
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
    try:
        asyncio.run(_serve(AppDeps(config=config), args.log_level))
    except KeyboardInterrupt:
        pass
