"""Alert store callback delivery merge (UBS-102, FR-CBK-009)."""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_shared.models.alerts_query import AlertDelivery
from telemetry_backend.services.alert_store import AlertStore

from tests.unit.backend.services.alert_fixtures import make_alert_event


def test_merge_updates_delivery_without_extra_transition() -> None:
    store = AlertStore()
    event = make_alert_event(alert_id="alert-delivery")
    store.merge(event)

    delivery = AlertDelivery(
        status="delivered",
        attempts=1,
        last_attempt_utc=datetime(2026, 6, 12, 4, 1, 0, tzinfo=UTC),
        correlation_id="cb-1",
    )
    update = make_alert_event(alert_id="alert-delivery").model_copy(
        update={"callback_delivery": delivery}
    )
    store.merge(update)

    listed = store.list_alerts(status="active")
    assert listed.alerts[0].delivery.status == "delivered"
    assert listed.alerts[0].delivery.attempts == 1
    detail = store.get_alert("alert-delivery")
    assert detail is not None
    assert len(detail.transitions) == 1
