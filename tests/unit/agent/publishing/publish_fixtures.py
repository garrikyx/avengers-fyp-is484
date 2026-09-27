"""Shared test support for the publishing package: builds `Snapshot`,
`TelemetryEvent` and `AlertEvent` fixtures directly, mirroring
`tests/unit/agent/callbacks/callback_fixtures.py`'s own approach of
keeping individual tests terse.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import TelemetryEvent
from telemetry_shared.models.snapshot import Snapshot

AGENT_ID = "magic-agent-sg-01"
APPLICATION = "Magic"
INSTANCE_ID = "magic-prod-01"


def make_snapshot(
    *,
    agent_id: str = AGENT_ID,
    application: str = APPLICATION,
    bucket_start_utc: datetime | None = None,
) -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id=agent_id,
        application=application,
        instance_id=INSTANCE_ID,
        bucket_start_utc=bucket_start_utc or datetime.now(UTC),
        bucket_seconds=10,
    )


def make_event(
    *, agent_id: str = AGENT_ID, application: str = APPLICATION
) -> TelemetryEvent:
    return TelemetryEvent(
        schema_version=1,
        event_id=uuid4(),
        agent_id=agent_id,
        application=application,
        instance_id=INSTANCE_ID,
        event_type="agent.started",
        timestamp_utc=datetime.now(UTC),
        time_source="agent",
        severity="info",
    )


def make_alert(
    *,
    alert_id: str = "alert-1024",
    agent_id: str = AGENT_ID,
    application: str = APPLICATION,
) -> AlertEvent:
    now = datetime.now(UTC)
    return AlertEvent(
        alert_id=alert_id,
        rule_name="HighRejectRate",
        severity="critical",
        status="firing",
        application=application,
        instance_id=INSTANCE_ID,
        agent_id=agent_id,
        matched_condition="rejectRate > 0.05 for 5 minutes",
        observed_value=0.064,
        threshold=0.05,
        first_observed_utc=now,
        last_observed_utc=now,
        notification_count=1,
    )
