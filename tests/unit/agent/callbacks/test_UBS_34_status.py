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


def test_UBS_34_a_new_notification_of_the_same_alert_starts_afresh() -> None:
    """Firing and resolved are two notifications of one `alert_id`. The
    resolved one took a single attempt; it must not report the firing
    notification's attempts or error on top of its own."""
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.PENDING, now=now)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.RETRYING, now=now, error="http_500")
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.DELIVERED, now=now)

    tracker.record("alert-1", DeliveryStatus.PENDING, now=now)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now)
    tracker.record("alert-1", DeliveryStatus.DELIVERED, now=now)

    record = tracker.status_of("alert-1")
    assert record is not None
    assert record.attempt_count == 1
    assert record.last_error is None


def test_UBS_34_notifications_of_one_alert_in_flight_together_stay_apart() -> None:
    """A slow firing callback can still be retrying when the resolved one is
    sent. Each notification keeps its own status and attempt count."""
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    firing, resolved = "alert-1:firing:1", "alert-1:resolved:1"
    tracker.record("alert-1", DeliveryStatus.PENDING, now=now, notification=firing)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now, notification=firing)
    tracker.record("alert-1", DeliveryStatus.RETRYING, now=now, notification=firing)
    tracker.record("alert-1", DeliveryStatus.PENDING, now=now, notification=resolved)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now, notification=resolved)
    tracker.record("alert-1", DeliveryStatus.DELIVERED, now=now, notification=resolved)
    tracker.record("alert-1", DeliveryStatus.SENT, now=now, notification=firing)
    tracker.record("alert-1", DeliveryStatus.DELIVERED, now=now, notification=firing)

    first = tracker.status_of("alert-1", notification=firing)
    second = tracker.status_of("alert-1", notification=resolved)
    assert first is not None and second is not None
    assert (first.status, first.attempt_count) == (DeliveryStatus.DELIVERED, 2)
    assert (second.status, second.attempt_count) == (DeliveryStatus.DELIVERED, 1)


def test_UBS_34_status_of_without_a_notification_is_the_latest_update() -> None:
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record("alert-1", DeliveryStatus.DELIVERED, now=now, notification="n1")
    tracker.record("alert-1", DeliveryStatus.FAILED, now=now, notification="n2")
    tracker.record("alert-1", DeliveryStatus.SENT, now=now, notification="n1")

    latest = tracker.status_of("alert-1")
    assert latest is not None
    assert latest.status is DeliveryStatus.SENT
    assert tracker.snapshot()["alert-1"] == latest


def test_UBS_34_unknown_notification_has_no_status() -> None:
    tracker = DeliveryTracker()
    tracker.record("alert-1", DeliveryStatus.SENT, now=datetime.now(UTC))

    assert tracker.status_of("alert-1", notification="other") is None


def test_UBS_34_a_long_firing_alert_keeps_only_recent_notifications() -> None:
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    for n in range(100):
        tracker.record(
            "alert-1", DeliveryStatus.DELIVERED, now=now, notification=f"n{n}"
        )

    assert tracker.status_of("alert-1", notification="n0") is None
    assert tracker.status_of("alert-1", notification="n99") is not None


def test_UBS_34_the_delivery_id_is_carried_per_notification() -> None:
    tracker = DeliveryTracker()
    now = datetime.now(UTC)
    tracker.record(
        "a", DeliveryStatus.SENT, now=now, notification="n1", delivery_id="d1"
    )
    tracker.record("a", DeliveryStatus.DELIVERED, now=now, notification="n1")
    tracker.record(
        "a", DeliveryStatus.SENT, now=now, notification="n2", delivery_id="d2"
    )

    assert tracker.status_of("a", notification="n1").correlation_id == "d1"  # type: ignore[union-attr]
    assert tracker.status_of("a", notification="n2").correlation_id == "d2"  # type: ignore[union-attr]
