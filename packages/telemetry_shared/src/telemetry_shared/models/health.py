"""Agent heartbeat wire format (spec 004 §6, FR-HLT-001..004).

`None` on any signal field means "no producer for this signal yet", which the
backend must not read as zero (FR-HLT-004). Which producers exist today is
tracked in docs/plan/ubs58-notes.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from telemetry_shared.models._base import CamelModel

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
