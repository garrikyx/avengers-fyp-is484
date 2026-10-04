"""Operator probes (UBS-96; FR-HLT-010, FR-HLT-012; spec 007 s5.3).

Mounted on the *internal* app, which `main()` binds to
`backend.internalListen` (loopback / cluster-internal). `/metrics` lives
only here and is unauthenticated by design on that listener. `/healthz` and
`/readyz` are also still served by the public app, which existing probes
and demos point at.
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
    """Readiness incl. warm-up (FR-QRY-005), from the same
    `StreamProcessor.is_ready()` the public `/readyz` uses. The extra fields
    let a human tell "just started" (`hasData` true, window not yet
    elapsed) from "never got data" (`hasData` false)."""
    processor = deps.ingestion.stream_processor if deps.ingestion else None
    ready = processor is not None and processor.is_ready(now=deps.clock())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ready" if ready else "warming",
        "warmupWindowSeconds": deps.config.warmup_window_seconds,
        "hasData": processor is not None and processor.store.has_data,
    }


@router.get("/metrics")
def metrics(deps: AppDeps = Depends(get_deps)) -> Response:
    body, content_type = deps.self_metrics.exposition()
    return Response(content=body, media_type=content_type)
