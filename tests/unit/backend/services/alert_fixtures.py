"""Shared alert fixtures for backend store and API tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from telemetry_shared.models.alerts import AlertEvent

INSTANCE_ID = "magic-prod-01"
AGENT_ID = "magic-agent-sg-01"
APPLICATION = "Magic"
BASE_TIME = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)


def make_alert_event(
    *,
    alert_id: str = "alert-1024",
    status: str = "firing",
    severity: str = "critical",
    rule_name: str = "HighRejectRate",
    instance_id: str = INSTANCE_ID,
    last_observed_utc: datetime | None = None,
    first_observed_utc: datetime | None = None,
    resolved_at_utc: datetime | None = None,
    notification_count: int = 1,
) -> AlertEvent:
    first = first_observed_utc or BASE_TIME
    last = last_observed_utc or first
    return AlertEvent(
        alert_id=alert_id,
        rule_name=rule_name,
        severity=severity,
        status=status,
        application=APPLICATION,
        instance_id=instance_id,
        agent_id=AGENT_ID,
        matched_condition="rejectRate > 0.05 for 5 minutes",
        observed_value=0.064,
        threshold=0.05,
        first_observed_utc=first,
        last_observed_utc=last,
        resolved_at_utc=resolved_at_utc,
        notification_count=notification_count,
    )


def make_resolved_event(
    *,
    alert_id: str = "alert-1024",
    last_observed_utc: datetime | None = None,
) -> AlertEvent:
    resolved_at = last_observed_utc or BASE_TIME + timedelta(minutes=5)
    return make_alert_event(
        alert_id=alert_id,
        status="resolved",
        last_observed_utc=resolved_at,
        resolved_at_utc=resolved_at,
    )
