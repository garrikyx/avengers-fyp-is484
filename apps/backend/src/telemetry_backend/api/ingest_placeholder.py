"""PLACEHOLDER heartbeat ingest (UBS-69). UBS-66 owns ingestion and replaces this.

Spec 007 s2.3's narrow `POST /telemetry/heartbeat` exists so the health read
side (UBS-69) has data before the batch path (UBS-66/85/86/87) lands. What
is deliberately missing: auth and agentId/identity check (FR-ING-002), size
and rate limits (FR-ING-008), the ingest queue (FR-ING-009), the
first-contact *event* (FR-ING-010 - only the boolean is returned). When the
ingestion router exists it should call `registry.record_heartbeat()` exactly
as this does and this file should be deleted.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.health import AgentHeartbeat

from telemetry_backend.deps import AppDeps, get_deps

router = APIRouter(prefix="/telemetry", tags=["ingest (placeholder)"])


class HeartbeatAccepted(CamelModel):
    accepted: bool = True
    first_contact: bool


@router.post(
    "/heartbeat",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=HeartbeatAccepted,
    response_model_by_alias=True,
)
def post_heartbeat(
    heartbeat: AgentHeartbeat, deps: AppDeps = Depends(get_deps)
) -> HeartbeatAccepted:
    # FastAPI validates the body against the shared model: schema drift is a
    # 422 with a field-level error list (FR-ING-003's shape, not its 400 code).
    first = deps.registry.record_heartbeat(heartbeat, received_at=deps.clock())
    return HeartbeatAccepted(first_contact=first)
