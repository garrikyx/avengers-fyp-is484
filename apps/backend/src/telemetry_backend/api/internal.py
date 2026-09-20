"""Operator probes (UBS-96; FR-HLT-010, FR-HLT-012; spec 007 s5.3).

Mounted only on the *internal* app, so these are reachable on
`backend.internalListen` (loopback / cluster-internal) and never on the
public listener. `/metrics` is unauthenticated by design on that listener.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from telemetry_backend.deps import AppDeps, get_deps

router = APIRouter(tags=["internal"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness only: the process is up and serving. No dependency checks,
    so a broken store or a silent fleet never makes the orchestrator restart
    a backend that is otherwise fine."""
    return {"status": "ok"}


@router.get("/readyz")
def readyz(response: Response, deps: AppDeps = Depends(get_deps)) -> dict[str, object]:
    """Readiness incl. warm-up (FR-QRY-005). 503 while `warming` so load
    balancers keep traffic off an empty store; the body says how far along
    the warm-up is so a human can tell "just started" from "never got data"."""
    warmup = deps.warmup.status(deps.clock())
    if warmup.state != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": warmup.state,
        "warmupWindowSeconds": warmup.warmup_window_seconds,
        "sinceFirstIngestSeconds": warmup.since_first_ingest_seconds,
    }


@router.get("/metrics")
def metrics(deps: AppDeps = Depends(get_deps)) -> Response:
    body, content_type = deps.self_metrics.exposition(deps.warmup)
    return Response(content=body, media_type=content_type)
