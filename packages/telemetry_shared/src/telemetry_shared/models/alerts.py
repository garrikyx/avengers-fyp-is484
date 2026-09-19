"""Shared contract: one Rule Engine alert (spec 005 §2, `FR-RUL-015`).

Consumed by the (future) Callback Dispatcher and Backend Publisher — both
agent-internal today, but this is a telemetry_shared Pydantic model per
FR-ING-022 since it is the cross-component contract, matching the callback
payload shape (spec 005 §3.3) and the backend's alert query response
(spec 007 §4.1).

Wire format is camelCase; Python attributes stay snake_case via
`alias_generator`, same pattern as `telemetry_shared.models.metrics`.
"""

from __future__ import annotations

from datetime import datetime

from telemetry_shared.models._base import CamelModel


class AlertEvent(CamelModel):
    """One alert transition or re-notification (`FR-RUL-015`).

    `severity` reflects the currently matched tier (`FR-RUL-022`) — for a
    multi-tier rule this can change while `status` stays `"firing"`.
    `metric_context` is capped at 10 entries by the caller (`FR-RUL-016`),
    built only from allowlisted snapshot counters, never raw log/FIX text.
    """

    alert_id: str
    rule_name: str
    severity: str
    status: str
    application: str
    instance_id: str
    agent_id: str
    matched_condition: str
    observed_value: float | None
    threshold: float
    first_observed_utc: datetime
    last_observed_utc: datetime
    resolved_at_utc: datetime | None = None
    group_by: dict[str, str] = {}
    metric_context: dict[str, float | int | str] = {}
    notification_count: int
