"""FastAPI app factories (spec 006 s1, FR-HLT-012).

Two apps in one process: the *public* app carries the telemetry API
(ingest, query, health) and the *internal* app carries only the operator
probes (`/healthz`, `/readyz`, `/metrics`), so those can be bound to a
loopback/cluster-internal listener and never share a socket with the public
API. Both apps share one `AppDeps`.

Other tickets add routers here: UBS-66 mounts ingestion on the public app
(and deletes `ingest_placeholder`).
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from telemetry_backend.api import health, ingest_placeholder, internal
from telemetry_backend.deps import AppDeps


def _latency_middleware(deps: AppDeps) -> Callable[..., Awaitable[Response]]:
    """Observe server-side latency per *route template* (bounded label set;
    never the raw path, which would carry agent IDs). Unmatched paths (404s)
    are labelled `unmatched` so they cannot grow cardinality."""

    async def middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = time.perf_counter()
        try:
            return await call_next(request)
        finally:
            route = request.scope.get("route")
            template = getattr(route, "path", None) or "unmatched"
            deps.self_metrics.query_latency.labels(route=template).observe(
                time.perf_counter() - started
            )

    return middleware


def create_public_app(deps: AppDeps | None = None) -> FastAPI:
    deps = deps or AppDeps()
    app = FastAPI(title="Magic Telemetry Backend", version="0.1.0")
    app.state.deps = deps
    app.middleware("http")(_latency_middleware(deps))
    app.include_router(health.router)
    app.include_router(ingest_placeholder.router)
    return app


def create_internal_app(deps: AppDeps | None = None) -> FastAPI:
    deps = deps or AppDeps()
    app = FastAPI(title="Magic Telemetry Backend (internal)", version="0.1.0")
    app.state.deps = deps
    app.include_router(internal.router)
    return app
