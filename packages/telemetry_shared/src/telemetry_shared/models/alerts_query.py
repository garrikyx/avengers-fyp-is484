"""Alert query response models (spec 007 §4, `FR-QRY-016`)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from telemetry_shared.models._base import CamelModel


class AlertDelivery(CamelModel):
    """Callback delivery status surfaced in alert query results."""

    status: str
    attempts: int = Field(ge=0, default=0)
    last_attempt_utc: datetime | None = None
    correlation_id: str | None = None


class AlertRecord(CamelModel):
    """One alert as returned by `GET /telemetry/alerts`."""

    alert_id: str
    source: Literal["agent", "backend"]
    synthetic: bool = False
    agent_id: str
    application: str
    instance_id: str
    rule_name: str
    severity: str
    status: str
    matched_condition: str
    observed_value: float | None
    threshold: float
    first_observed_utc: datetime
    last_observed_utc: datetime
    resolved_at_utc: datetime | None = None
    notification_count: int = Field(ge=0)
    delivery: AlertDelivery
    group_by: dict[str, str] = Field(default_factory=dict)
    metric_context: dict[str, float | int | str] = Field(default_factory=dict)
    runbook_url: str | None = None


class AlertTransition(CamelModel):
    """One state transition in an alert's history."""

    status: str
    severity: str
    observed_value: float | None
    threshold: float
    timestamp_utc: datetime
    notification_count: int = Field(ge=0)
    matched_condition: str


class AlertCounts(CamelModel):
    active: int = Field(ge=0)
    critical: int = Field(ge=0)
    warning: int = Field(ge=0)


class AlertsListResponse(CamelModel):
    alerts: list[AlertRecord]
    counts: AlertCounts
    truncated: bool = False


class AlertDetailResponse(CamelModel):
    alert: AlertRecord
    transitions: list[AlertTransition]
