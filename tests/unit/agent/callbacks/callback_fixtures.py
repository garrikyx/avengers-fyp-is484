"""Shared test support for the callbacks package: builds `AlertEvent`
fixtures directly, mirroring `tests/unit/agent/rules/rule_fixtures.py`'s
own approach of keeping individual tests terse.
"""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_shared.models.alerts import AlertEvent


def make_alert_event(
    *,
    alert_id: str = "alert-1024",
    rule_name: str = "HighRejectRate",
    severity: str = "critical",
    status: str = "firing",
    observed_value: float | None = 0.064,
    threshold: float = 0.05,
    notification_count: int = 1,
    metric_context: dict[str, float | int | str] | None = None,
) -> AlertEvent:
    now = datetime.now(UTC)
    return AlertEvent(
        alert_id=alert_id,
        rule_name=rule_name,
        severity=severity,
        status=status,
        application="Magic",
        instance_id="magic-prod-01",
        agent_id="magic-agent-sg-01",
        matched_condition="rejectRate > 0.05 for 5 minutes",
        observed_value=observed_value,
        threshold=threshold,
        first_observed_utc=now,
        last_observed_utc=now,
        metric_context=metric_context or {},
        notification_count=notification_count,
    )
