"""Backend HTTP entrypoint (spec 006 §1, §7).

Only `/healthz` and `/readyz` exist so far (`FR-HLT-010`, `FR-QRY-005`) — the
ingestion, query, alert and NL routes each depend on components this app
doesn't build yet (Ingestion Service, Query Engine, Alert Store) and are
deliberately out of scope here. `uv run uvicorn telemetry_backend.main:app`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, Response

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.stream_processor import StreamProcessor

app = FastAPI(title="telemetry-backend")

# Process-lifetime singleton: `/readyz` reports against the same instance
# every request, so its `warmupWindow` clock starts once, at import time —
# not per-request — matching "since this replica started" (FR-QRY-005).
_processor = StreamProcessor(StreamProcessorConfig())


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """FR-HLT-010: liveness only — process up, no dependency checks."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz(response: Response) -> dict[str, str]:
    """FR-QRY-005: `warming` (HTTP 503) until `warmupWindow` has elapsed
    since this replica started, so an orchestrator doesn't route traffic to
    a replica whose just-restarted, empty store would misreport as
    caught-up-and-idle.
    """
    if _processor.is_ready(now=datetime.now(UTC)):
        return {"status": "ready"}
    response.status_code = 503
    return {"status": "warming"}
