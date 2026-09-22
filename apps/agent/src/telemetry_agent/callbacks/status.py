"""UBS-34: per-alert-occurrence callback delivery status, timestamped at
each transition.

Distinct from `self_metrics.CounterRegistry`, which only tracks aggregate
counts across all alerts — this answers "what is the current delivery
state of alert X right now", not just "how many callbacks failed overall
since startup".
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


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
    """One alert's current delivery state. `attempt_count` and
    `last_error` are carried forward from the previous record on each
    `record()` call unless the new transition itself sets them
    (`DeliveryTracker.record`) — so `status_of()` always reflects "how many
    attempts so far" and "why it last failed", not just the latest
    transition in isolation.
    """

    status: DeliveryStatus
    updated_at: datetime
    attempt_count: int = 0
    last_error: str | None = None


class DeliveryTracker:
    """Keyed by `alert_id`. A lock guards concurrent updates from multiple
    dispatcher worker tasks delivering different alerts at once.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, DeliveryRecord] = {}

    def record(
        self,
        alert_id: str,
        status: DeliveryStatus,
        *,
        now: datetime,
        error: str | None = None,
    ) -> None:
        """Append a timestamped transition. Only `SENT` increments
        `attempt_count` — it's the transition that fires exactly once per
        actual HTTP attempt. `RETRYING` describes the outcome of the `SENT`
        already counted (the attempt failed, waiting to try again), so it
        must not double-count the same attempt; `PENDING` isn't an attempt
        at all, and the terminal states (`DELIVERED`/`FAILED`) describe an
        outcome, not a new one.
        """
        with self._lock:
            previous = self._records.get(alert_id)
            attempt_count = previous.attempt_count if previous is not None else 0
            if status is DeliveryStatus.SENT:
                attempt_count += 1
            last_error = (
                error if error is not None
                else (previous.last_error if previous is not None else None)
            )
            self._records[alert_id] = DeliveryRecord(
                status=status,
                updated_at=now,
                attempt_count=attempt_count,
                last_error=last_error,
            )

    def status_of(self, alert_id: str) -> DeliveryRecord | None:
        with self._lock:
            return self._records.get(alert_id)

    def snapshot(self) -> dict[str, DeliveryRecord]:
        with self._lock:
            return dict(self._records)
