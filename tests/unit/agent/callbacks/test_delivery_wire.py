"""Callback delivery wire mapping (FR-CBK-009)."""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_agent.callbacks.delivery_wire import enrich_alert_delivery
from telemetry_agent.callbacks.status import (
    DeliveryStatus,
    DeliveryTracker,
    notification_key,
)

from tests.unit.backend.services.alert_fixtures import make_alert_event

_NOW = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)


def test_enrich_alert_delivery_maps_tracker_state() -> None:
    tracker = DeliveryTracker()
    alert = make_alert_event(alert_id="a-1")
    key = notification_key(alert)
    tracker.record(alert.alert_id, DeliveryStatus.SENT, now=_NOW, notification=key)
    tracker.record(alert.alert_id, DeliveryStatus.DELIVERED, now=_NOW, notification=key)

    enriched = enrich_alert_delivery(alert, tracker, correlation_id="cb-99")
    assert enriched.callback_delivery is not None
    assert enriched.callback_delivery.status == "delivered"
    assert enriched.callback_delivery.correlation_id == "cb-99"


def test_enrich_alert_delivery_reports_the_alerts_own_notification() -> None:
    """Firing and resolved share an `alertId`; each must report its own
    delivery, not whichever notification was updated last."""
    tracker = DeliveryTracker()
    firing = make_alert_event(alert_id="a-1", status="firing")
    resolved = make_alert_event(alert_id="a-1", status="resolved")
    tracker.record(
        "a-1",
        DeliveryStatus.DELIVERED,
        now=_NOW,
        notification=notification_key(firing),
    )
    tracker.record(
        "a-1",
        DeliveryStatus.PENDING,
        now=_NOW,
        notification=notification_key(resolved),
    )

    assert enrich_alert_delivery(firing, tracker).callback_delivery.status == (  # type: ignore[union-attr]
        "delivered"
    )
    assert enrich_alert_delivery(resolved, tracker).callback_delivery.status == (  # type: ignore[union-attr]
        "pending"
    )


def test_enrich_alert_delivery_takes_the_correlation_id_from_the_record() -> None:
    tracker = DeliveryTracker()
    alert = make_alert_event(alert_id="a-1")
    tracker.record(
        "a-1",
        DeliveryStatus.SENT,
        now=_NOW,
        notification=notification_key(alert),
        delivery_id="delivery-7",
    )

    enriched = enrich_alert_delivery(alert, tracker)

    assert enriched.callback_delivery.correlation_id == "delivery-7"  # type: ignore[union-attr]


def test_enrich_alert_delivery_leaves_an_untracked_alert_alone() -> None:
    alert = make_alert_event(alert_id="a-1")

    assert enrich_alert_delivery(alert, DeliveryTracker()) is alert
