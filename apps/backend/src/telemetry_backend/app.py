"""FastAPI app factories (spec 006 s1, FR-HLT-012).

Two apps in one process: the *public* app carries the telemetry API
(ingest, query, health) and the *internal* app carries only the operator
probes (`/healthz`, `/readyz`, `/metrics`), so those can be bound to a
loopback/cluster-internal listener and never share a socket with the public
API. Both apps share one `AppDeps`.

Other tickets add routers here: UBS-66 mounts ingestion on the public app
(and deletes `ingest_placeholder`), UBS-96 mounts `api/internal.py` on the
internal app.
"""

from __future__ import annotations

from fastapi import FastAPI

from telemetry_backend.api import health, ingest_placeholder
from telemetry_backend.deps import AppDeps


def create_public_app(deps: AppDeps | None = None) -> FastAPI:
    deps = deps or AppDeps()
    app = FastAPI(title="Magic Telemetry Backend", version="0.1.0")
    app.state.deps = deps
    app.include_router(health.router)
    app.include_router(ingest_placeholder.router)
    return app


def create_internal_app(deps: AppDeps | None = None) -> FastAPI:
    deps = deps or AppDeps()
    app = FastAPI(title="Magic Telemetry Backend (internal)", version="0.1.0")
    app.state.deps = deps
    return app
