"""Shared agent-to-backend ingestion contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, model_validator

from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.snapshot import Snapshot


class TelemetryEvent(CamelModel):
    """One derived operational event."""

    schema_version: Literal[1]
    event_id: UUID
    agent_id: str = Field(min_length=1)
    application: str = Field(min_length=1)
    instance_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    timestamp_utc: datetime
    time_source: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    dimensions: dict[str, str] = Field(default_factory=dict)
    fields: dict[str, Any] = Field(default_factory=dict)


class HeartbeatFile(CamelModel):
    """Per-file health reported by an agent heartbeat."""

    path: str = Field(min_length=1)
    instance_id: str = Field(min_length=1)
    offset: int = Field(ge=0)
    read_lag_ms: float | None = Field(default=None, ge=0)
    last_line_at_utc: datetime | None = None
    rotations_detected: int = Field(ge=0)
    state: str = Field(min_length=1)


class ResourceUsage(CamelModel):
    rss_mb: float = Field(ge=0)
    cpu_percent: float = Field(ge=0)
    active_tasks: int = Field(ge=0)


class Heartbeat(CamelModel):
    """The standalone and batch heartbeat payload."""

    schema_version: Literal[1]
    agent_id: str = Field(min_length=1)
    instance_ids: list[str] = Field(min_length=1)
    sent_at_utc: datetime
    agent_version: str = Field(min_length=1)
    uptime_seconds: int = Field(ge=0)
    status: Literal["healthy", "degraded", "unhealthy"]
    files: list[HeartbeatFile] = Field(default_factory=list)
    parse_error_count_last5_min: int = Field(ge=0)
    callback_failures_last5_min: int = Field(ge=0)
    publish_queue_depth: int = Field(ge=0)
    publish_buffer_bytes: int = Field(ge=0)
    dropped_events_last5_min: int = Field(ge=0)
    active_alert_count: int = Field(ge=0)
    resource_usage: ResourceUsage


class TelemetryBatch(CamelModel):
    """Primary ingestion request."""

    schema_version: Literal[1]
    batch_id: UUID
    batch_seq: int = Field(ge=0)
    agent_id: str = Field(min_length=1)
    application: str = Field(min_length=1)
    sent_at_utc: datetime
    snapshots: list[Snapshot] = Field(default_factory=list)
    events: list[TelemetryEvent] = Field(default_factory=list)
    alerts: list[AlertEvent] = Field(default_factory=list)
    heartbeat: Heartbeat | None = None

    @model_validator(mode="after")
    def identities_match_batch(self) -> TelemetryBatch:
        """Reject accidental cross-agent batches before they enter the queue."""
        for snapshot in self.snapshots:
            if snapshot.agent_id != self.agent_id:
                raise ValueError("item agentId must match batch agentId")
            if snapshot.application != self.application:
                raise ValueError("item application must match batch application")
        for event in self.events:
            if event.agent_id != self.agent_id:
                raise ValueError("item agentId must match batch agentId")
            if event.application != self.application:
                raise ValueError("item application must match batch application")
        for alert in self.alerts:
            if alert.agent_id != self.agent_id:
                raise ValueError("item agentId must match batch agentId")
            if alert.application != self.application:
                raise ValueError("item application must match batch application")
        if self.heartbeat is not None and self.heartbeat.agent_id != self.agent_id:
            raise ValueError("heartbeat agentId must match batch agentId")
        return self


class EventsRequest(CamelModel):
    """Convenience endpoint request for events."""

    events: list[TelemetryEvent] = Field(min_length=1)
