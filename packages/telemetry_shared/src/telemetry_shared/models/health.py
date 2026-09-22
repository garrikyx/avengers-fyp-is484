"""Agent heartbeat wire format (spec 004 §6, FR-HLT-001..004).

`None` on any signal field means "no producer for this signal yet", which the
backend must not read as zero (FR-HLT-004). Which producers exist today is
tracked in docs/plan/ubs58-60-notes.md.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import field_validator

from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.ingestion import ResourceUsage as IngestionResourceUsage

AgentStatus = Literal["healthy", "degraded", "unhealthy"]
FileReadState = Literal["reading", "waiting", "error"]


class FileReadHealth(CamelModel):
    """Per-file read health (UBS-30). See docs/plan/ubs30-notes.md."""

    path: str
    offset: int
    instance_id: str | None = None
    size: int | None = None
    last_line_at_utc: datetime | None = None
    read_lag_ms: float | None = None
    rotations_detected: int = 0
    state: FileReadState = "waiting"


class ResourceUsage(CamelModel):
    rss_mb: float | None = None
    cpu_percent: float | None = None
    active_tasks: int | None = None


class AgentHeartbeat(CamelModel):
    schema_version: int = 1
    agent_id: str
    instance_ids: list[str]
    sent_at_utc: datetime
    agent_version: str
    uptime_seconds: float
    status: AgentStatus
    # FR-HLT-003: every condition that contributed to a non-healthy status.
    status_reasons: list[str] = []
    files: list[FileReadHealth] = []
    read_lag_ms: float | None = None
    parse_error_count_last5_min: int | None = None
    callback_failures_last5_min: int | None = None
    publish_queue_depth: int | None = None
    publish_buffer_bytes: int | None = None
    dropped_events_last5_min: int | None = None
    active_alert_count: int | None = None
    resource_usage: ResourceUsage | None = None

    @field_validator("sent_at_utc")
    @classmethod
    def _aware_utc(cls, value: datetime) -> datetime:
        # The backend orders heartbeats by this field; a naive value would
        # be incomparable with aware ones. Reject at the contract boundary.
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("sentAtUtc must be timezone-aware")
        return value.astimezone(UTC)


# --- Backend health read side (UBS-69; spec 007 §5.1 / §5.2) ------------------------
#
# `missing` is the backend's own verdict when no heartbeat has arrived within
# `missingHeartbeatThreshold`; the other three are whatever the agent last
# reported. The agent cannot report its own death, so only the backend can
# decide this one.

RegistryStatus = Literal["healthy", "degraded", "unhealthy", "missing"]


class AgentHealthSummary(CamelModel):
    agent_id: str
    status: RegistryStatus
    instance_ids: list[str]
    last_heartbeat_utc: datetime
    heartbeat_age_ms: int
    agent_version: str


class HealthCounts(CamelModel):
    healthy: int = 0
    degraded: int = 0
    unhealthy: int = 0
    missing: int = 0


class AgentHealthList(CamelModel):
    agents: list[AgentHealthSummary]
    counts: HealthCounts


class AgentHealthFile(CamelModel):
    """`files[]` as the API returns it (spec 007 §5.2). FR-HLT-011: these
    paths are configured values echoed back, never interpolated into any
    filesystem operation on the backend."""

    path: str
    instance_id: str
    read_lag_ms: float | None = None
    last_line_at_utc: datetime | None = None
    rotations_detected: int = 0
    state: str


class AgentHealthDetail(CamelModel):
    """spec 007 §5.2: the last heartbeat re-keyed for the API, plus the
    backend's own view (`status`, `heartbeatAgeMs`, `firstSeenUtc`).

    `logReadLagMs` is the worst-case across `files[]` - the ingestion
    heartbeat contract reports lag per file rather than as a single gauge.
    There is no `statusReasons` here because that contract has no such field;
    see docs/plan/ubs69-96-notes.md.
    """

    agent_id: str
    status: RegistryStatus
    instance_ids: list[str]
    last_heartbeat_utc: datetime
    heartbeat_age_ms: int
    first_seen_utc: datetime
    agent_version: str
    uptime_seconds: int
    reported_status: AgentStatus
    log_read_lag_ms: float | None
    parse_error_count_last5_min: int
    callback_failures_last5_min: int
    publish_queue_depth: int
    publish_buffer_bytes: int
    dropped_events_last5_min: int
    active_alert_count: int
    files: list[AgentHealthFile]
    resource_usage: IngestionResourceUsage
