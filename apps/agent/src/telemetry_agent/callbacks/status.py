"""UBS-34: per-notification callback delivery status, timestamped at each
transition.

Distinct from `self_metrics.CounterRegistry`, which only tracks aggregate
counts across all alerts — this answers "what is the current delivery
state of alert X right now", not just "how many callbacks failed overall
since startup".

An alert is notified more than once: firing, resolved, and each re-notify
are separate callbacks that share an `alert_id`. Each is tracked on its own
(`notification_key`), so a firing callback still retrying never shares
attempts or status with the resolved one sent while it waited.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from telemetry_shared.models.alerts import AlertEvent

# Notifications kept per alert. A long-firing alert re-notifies for as long
# as it fires; only the recent ones can still be in flight, so older records
# are dropped rather than growing without bound.
MAX_NOTIFICATIONS_PER_ALERT = 8


def notification_key(alert: AlertEvent) -> str:
    """Identity of one callback notification — the same triple the
    dispatcher's `X-Telemetry-Idempotency-Key` carries (`FR-CBK-003`)."""
    return f"{alert.alert_id}:{alert.status}:{alert.notification_count}"


class DeliveryStatus(StrEnum):
    """UBS-34 AC: every dispatched callback has exactly one of these five
    states at any time."""

    PENDING = "pending"
    SENT = "sent"
    RETRYING = "retrying"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DeliveryRecord:
    """One notification's current delivery state. `attempt_count`,
    `last_error` and `correlation_id` are carried forward from the previous
    record on each `record()` call unless the new transition itself sets
    them (`DeliveryTracker.record`) — so `status_of()` always reflects "how
    many attempts so far" and "why it last failed", not just the latest
    transition in isolation. `correlation_id` is the
    `X-Telemetry-Delivery-Id` of the latest attempt.
    """

    status: DeliveryStatus
    updated_at: datetime
    attempt_count: int = 0
    last_error: str | None = None
    correlation_id: str | None = None


class DeliveryTracker:
    """Keyed by `alert_id`, then by notification. A lock guards concurrent
    updates from multiple dispatcher worker tasks delivering different
    notifications at once.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # alert_id -> notification -> record. Each inner dict is ordered by
        # last update, so its last item is the alert's latest notification.
        self._records: dict[str, dict[str, DeliveryRecord]] = {}

    def record(
        self,
        alert_id: str,
        status: DeliveryStatus,
        *,
        now: datetime,
        error: str | None = None,
        notification: str = "",
        delivery_id: str | None = None,
    ) -> None:
        """Append a timestamped transition to one notification. Only `SENT`
        increments `attempt_count` — it's the transition that fires exactly
        once per actual HTTP attempt. `RETRYING` describes the outcome of the
        `SENT` already counted (the attempt failed, waiting to try again), so
        it must not double-count the same attempt; the terminal states
        (`DELIVERED`/`FAILED`) describe an outcome, not a new one.

        `PENDING` starts a new delivery run, so it begins the count, error
        and delivery id afresh.
        """
        with self._lock:
            notifications = self._records.setdefault(alert_id, {})
            previous = notifications.pop(notification, None)
            if status is DeliveryStatus.PENDING:
                previous = None
            attempt_count = previous.attempt_count if previous is not None else 0
            if status is DeliveryStatus.SENT:
                attempt_count += 1
            last_error = (
                error
                if error is not None
                else (previous.last_error if previous is not None else None)
            )
            correlation_id = (
                delivery_id
                if delivery_id is not None
                else (previous.correlation_id if previous is not None else None)
            )
            notifications[notification] = DeliveryRecord(
                status=status,
                updated_at=now,
                attempt_count=attempt_count,
                last_error=last_error,
                correlation_id=correlation_id,
            )
            while len(notifications) > MAX_NOTIFICATIONS_PER_ALERT:
                del notifications[next(iter(notifications))]

    def status_of(
        self, alert_id: str, notification: str | None = None
    ) -> DeliveryRecord | None:
        """One notification's record, or — without `notification` — the
        alert's most recently updated one."""
        with self._lock:
            notifications = self._records.get(alert_id)
            if not notifications:
                return None
            if notification is None:
                return next(reversed(notifications.values()))
            return notifications.get(notification)

    def snapshot(self) -> dict[str, DeliveryRecord]:
        """The latest notification's record for each alert."""
        with self._lock:
            return {
                alert_id: next(reversed(notifications.values()))
                for alert_id, notifications in self._records.items()
                if notifications
            }
