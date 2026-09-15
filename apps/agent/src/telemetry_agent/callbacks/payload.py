"""FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)."""

from __future__ import annotations

from datetime import datetime

from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.alerts import AlertEvent

_SCHEMA_VERSION = 1


class CallbackAlertPayload(CamelModel):
    """Matches spec 005 §3.3 exactly.

    `summary` and `runbook_url` aren't produced anywhere upstream yet
    (`AlertEvent` has no `summary` field) — `from_alert_event` synthesizes
    a stopgap rather than inventing spec-quality copy; this needs a real
    product/spec decision later, not a finished design.
    """

    schema_version: int = _SCHEMA_VERSION
    alert_id: str
    status: str
    severity: str
    application: str
    instance_id: str
    agent_id: str
    rule_name: str
    summary: str
    matched_condition: str
    observed_value: float | None
    threshold: float
    first_observed_utc: datetime
    timestamp_utc: datetime
    notification_count: int
    metric_context: dict[str, float | int | str]
    runbook_url: str | None = None


def from_alert_event(
    alert: AlertEvent, *, now: datetime, runbook_url: str | None = None
) -> CallbackAlertPayload:
    return CallbackAlertPayload(
        alert_id=alert.alert_id,
        status=alert.status,
        severity=alert.severity,
        application=alert.application,
        instance_id=alert.instance_id,
        agent_id=alert.agent_id,
        rule_name=alert.rule_name,
        summary=f"{alert.rule_name} matched: {alert.matched_condition}",
        matched_condition=alert.matched_condition,
        observed_value=alert.observed_value,
        threshold=alert.threshold,
        first_observed_utc=alert.first_observed_utc,
        timestamp_utc=now,
        notification_count=alert.notification_count,
        metric_context=alert.metric_context,
        runbook_url=runbook_url,
    )
