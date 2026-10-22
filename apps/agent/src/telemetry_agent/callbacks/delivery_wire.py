"""Map callback delivery tracker state to backend wire models (FR-CBK-009)."""

from __future__ import annotations

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.alerts_query import AlertDelivery

from telemetry_agent.callbacks.status import (
    DeliveryRecord,
    DeliveryStatus,
    DeliveryTracker,
)

_API_STATUS: dict[DeliveryStatus, str] = {
    DeliveryStatus.PENDING: "pending",
    DeliveryStatus.SENT: "retrying",
    DeliveryStatus.RETRYING: "retrying",
    DeliveryStatus.DELIVERED: "delivered",
    DeliveryStatus.FAILED: "failed",
}


def alert_delivery_from_record(
    record: DeliveryRecord,
    *,
    correlation_id: str | None = None,
) -> AlertDelivery:
    return AlertDelivery(
        status=_API_STATUS.get(record.status, "unknown"),
        attempts=record.attempt_count,
        last_attempt_utc=record.updated_at,
        correlation_id=correlation_id,
    )


def enrich_alert_delivery(
    alert: AlertEvent,
    tracker: DeliveryTracker,
    *,
    correlation_id: str | None = None,
) -> AlertEvent:
    record = tracker.status_of(alert.alert_id)
    if record is None:
        return alert
    delivery = alert_delivery_from_record(record, correlation_id=correlation_id)
    return alert.model_copy(update={"callback_delivery": delivery})
