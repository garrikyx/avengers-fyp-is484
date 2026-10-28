"""Callback delivery wire mapping (FR-CBK-009)."""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_agent.callbacks.delivery_wire import enrich_alert_delivery
from telemetry_agent.callbacks.status import DeliveryStatus, DeliveryTracker

from tests.unit.backend.services.alert_fixtures import make_alert_event


def test_enrich_alert_delivery_maps_tracker_state() -> None:
    tracker = DeliveryTracker()
    alert = make_alert_event(alert_id="a-1")
    now = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    tracker.record(alert.alert_id, DeliveryStatus.SENT, now=now)
    tracker.record(alert.alert_id, DeliveryStatus.DELIVERED, now=now)

    enriched = enrich_alert_delivery(alert, tracker, correlation_id="cb-99")
    assert enriched.callback_delivery is not None
    assert enriched.callback_delivery.status == "delivered"
    assert enriched.callback_delivery.correlation_id == "cb-99"
