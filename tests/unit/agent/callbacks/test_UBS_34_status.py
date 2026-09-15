"""UBS-34: per-alert delivery status tracking tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from telemetry_agent.callbacks.status import DeliveryStatus, DeliveryTracker


def test_UBS_34_unknown_alert_has_no_status() -> None:
    tracker = DeliveryTracker()
    assert tracker.status_of("never-seen") is None


def test_UBS_34_enqueue_records_pending() -> None:
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.PENDING, now=now)

    record = tracker.status_of("alert-1")
    assert record is not None
    assert record.status is DeliveryStatus.PENDING
    assert record.updated_at == now
    assert record.attempt_count == 0


def test_UBS_34_immediate_success_sequence() -> None:
    """pending -> sent -> delivered, one attempt."""
    tracker = DeliveryTracker()
    t0 = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.PENDING, now=t0)
    tracker.record("alert-1", DeliveryStatus.SENT, now=t0 + timedelta(milliseconds=1))
    tracker.record(
        "alert-1", DeliveryStatus.DELIVERED, now=t0 + timedelta(milliseconds=10)
    )

    record = tracker.status_of("alert-1")
    assert record is not None
    assert record.status is DeliveryStatus.DELIVERED
    assert record.attempt_count == 1
    assert record.last_error is None


def test_UBS_34_retried_then_delivered_sequence() -> None:
    """pending -> sent (fails) -> retrying -> sent -> delivered: exactly
    two attempts, not three — RETRYING must not double-count the SENT
    that produced it."""
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.PENDING, now=now)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.RETRYING, now=now, error="http_500")
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.DELIVERED, now=now)

    record = tracker.status_of("alert-1")
    assert record is not None
    assert record.status is DeliveryStatus.DELIVERED
    assert record.attempt_count == 2


def test_UBS_34_retried_then_failed_sequence() -> None:
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.PENDING, now=now)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.RETRYING, now=now, error="http_500")
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.FAILED, now=now, error="http_500")

    record = tracker.status_of("alert-1")
    assert record is not None
    assert record.status is DeliveryStatus.FAILED
    assert record.attempt_count == 2
    assert record.last_error == "http_500"


def test_UBS_34_last_error_persists_across_terminal_transition() -> None:
    """FAILED itself carries no new error, but should keep the reason from
    the RETRYING transition that preceded it — losing it would defeat the
    point of a queryable failure reason."""
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.RETRYING, now=now, error="http_503")
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.FAILED, now=now)  # no error passed here

    record = tracker.status_of("alert-1")
    assert record is not None
    assert record.last_error == "http_503"


def test_UBS_34_each_transition_is_timestamped() -> None:
    tracker = DeliveryTracker()
    t1 = datetime.now(UTC)
    t2 = t1 + timedelta(seconds=1)
    tracker.record("alert-1", DeliveryStatus.PENDING, now=t1)
    assert tracker.status_of("alert-1").updated_at == t1  # type: ignore[union-attr]

    tracker.record("alert-1", DeliveryStatus.SENT, now=t2)
    assert tracker.status_of("alert-1").updated_at == t2  # type: ignore[union-attr]


def test_UBS_34_snapshot_reflects_latest_state_per_alert() -> None:
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.DELIVERED, now=now)
    tracker.record("alert-2", DeliveryStatus.FAILED, now=now, error="http_400")

    snapshot = tracker.snapshot()
    assert set(snapshot.keys()) == {"alert-1", "alert-2"}
    assert snapshot["alert-1"].status is DeliveryStatus.DELIVERED
    assert snapshot["alert-2"].status is DeliveryStatus.FAILED


def test_UBS_34_tracking_one_alert_does_not_affect_another() -> None:
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-2", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.DELIVERED, now=now)

    assert tracker.status_of("alert-1").status is DeliveryStatus.DELIVERED  # type: ignore[union-attr]
    assert tracker.status_of("alert-2").status is DeliveryStatus.SENT  # type: ignore[union-attr]
