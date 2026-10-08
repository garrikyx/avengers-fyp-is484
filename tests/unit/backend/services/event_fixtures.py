"""Shared TelemetryEvent fixtures for backend event-store tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from telemetry_shared.models.ingestion import TelemetryEvent

BASE_TIME = datetime(2026, 9, 19, 9, 0, 0, tzinfo=UTC)
INSTANCE_ID = "magic-prod-01"
AGENT_ID = "magic-agent-sg-01"
APPLICATION = "Magic"


def make_telemetry_event(
    *,
    event_id: str | UUID | None = None,
    event_type: str = "agent.started",
    timestamp_utc: datetime | None = None,
    severity: str = "info",
    instance_id: str = INSTANCE_ID,
    dimensions: dict[str, str] | None = None,
    fields: dict[str, object] | None = None,
) -> TelemetryEvent:
    return TelemetryEvent(
        schema_version=1,
        event_id=UUID(str(event_id)) if event_id is not None else uuid4(),
        agent_id=AGENT_ID,
        application=APPLICATION,
        instance_id=instance_id,
        event_type=event_type,
        timestamp_utc=timestamp_utc or BASE_TIME,
        time_source="agent",
        severity=severity,
        dimensions=dimensions or {},
        fields=fields or {},
    )
