"""Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).

Missing-heartbeat detection is here, backend-side, at read time: an agent
that stopped sending cannot say so itself. `status` is `missing` past
`missingHeartbeatThreshold`, otherwise the agent's own last verdict.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from telemetry_shared.models.health import (
    AgentHealthDetail,
    AgentHealthList,
    AgentHealthSummary,
    HealthCounts,
)

from telemetry_backend.deps import AppDeps, get_deps
from telemetry_backend.services.agent_registry import AgentRecord, AgentRegistry

router = APIRouter(prefix="/telemetry/health", tags=["health"])


def _summary(
    registry: AgentRegistry, record: AgentRecord, at: datetime
) -> AgentHealthSummary:
    return AgentHealthSummary(
        agent_id=record.agent_id,
        status=registry.status_of(record, at),
        instance_ids=record.instance_ids,
        last_heartbeat_utc=record.last_heartbeat_utc,
        heartbeat_age_ms=registry.heartbeat_age_ms(record, at),
        agent_version=record.agent_version,
    )


@router.get("/agents", response_model=AgentHealthList, response_model_by_alias=True)
def list_agents(deps: AppDeps = Depends(get_deps)) -> AgentHealthList:
    now = deps.clock()
    summaries = [_summary(deps.registry, r, now) for r in deps.registry.all()]
    tally = {"healthy": 0, "degraded": 0, "unhealthy": 0, "missing": 0}
    for s in summaries:
        tally[s.status] += 1
    return AgentHealthList(agents=summaries, counts=HealthCounts(**tally))


@router.get(
    "/agents/{agent_id}",
    response_model=AgentHealthDetail,
    response_model_by_alias=True,
)
def get_agent(agent_id: str, deps: AppDeps = Depends(get_deps)) -> AgentHealthDetail:
    record = deps.registry.get(agent_id)
    if record is None:
        raise HTTPException(
            status_code=404, detail={"code": "not_found", "agentId": agent_id}
        )
    now = deps.clock()
    hb = record.heartbeat
    # FR-HLT-011: `files[].path` is passed through as the agent reported it and
    # is the only path-like data here; nothing on the backend opens it.
    return AgentHealthDetail(
        agent_id=record.agent_id,
        status=deps.registry.status_of(record, now),
        instance_ids=record.instance_ids,
        last_heartbeat_utc=record.last_heartbeat_utc,
        heartbeat_age_ms=deps.registry.heartbeat_age_ms(record, now),
        first_seen_utc=record.first_seen_at,
        agent_version=hb.agent_version,
        uptime_seconds=hb.uptime_seconds,
        reported_status=hb.status,
        status_reasons=list(hb.status_reasons),
        log_read_lag_ms=hb.read_lag_ms,
        parse_error_count_last5_min=hb.parse_error_count_last5_min,
        callback_failures_last5_min=hb.callback_failures_last5_min,
        publish_queue_depth=hb.publish_queue_depth,
        dropped_events_last5_min=hb.dropped_events_last5_min,
        active_alert_count=hb.active_alert_count,
        files=list(hb.files),
        resource_usage=hb.resource_usage,
    )
