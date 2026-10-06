"""FR-QRY-016/017: alert store retention and merge semantics."""

from __future__ import annotations

import threading
from datetime import timedelta

from telemetry_backend.config import AlertStoreConfig
from telemetry_backend.services.alert_store import AlertStore

from tests.unit.backend.services.alert_fixtures import (
    BASE_TIME,
    INSTANCE_ID,
    make_alert_event,
    make_resolved_event,
)


def test_FR_QRY_016_active_alert_is_retained_and_resolved_moves_to_history() -> None:
    store = AlertStore()
    store.merge(make_alert_event(alert_id="alert-a"))
    active = store.list_alerts(status="active")
    assert len(active.alerts) == 1
    assert active.alerts[0].alert_id == "alert-a"

    store.merge(make_resolved_event(alert_id="alert-a"))
    assert store.list_alerts(status="active").counts.active == 0
    resolved = store.list_alerts(status="resolved")
    assert len(resolved.alerts) == 1
    assert resolved.alerts[0].status == "resolved"


def test_FR_QRY_016_resolved_history_is_capped_per_instance() -> None:
    store = AlertStore(AlertStoreConfig(recent_alert_limit=2))
    for index in range(3):
        alert_id = f"alert-{index}"
        store.merge(make_alert_event(alert_id=alert_id))
        store.merge(make_resolved_event(alert_id=alert_id))

    resolved = store.list_alerts(status="resolved", limit=10)
    assert len(resolved.alerts) == 2
    assert {alert.alert_id for alert in resolved.alerts} == {"alert-1", "alert-2"}


def test_FR_QRY_016_reingest_updates_existing_alert_without_duplicating() -> None:
    store = AlertStore()
    store.merge(make_alert_event(alert_id="alert-a", severity="warning"))
    updated = make_alert_event(
        alert_id="alert-a",
        severity="critical",
        last_observed_utc=BASE_TIME + timedelta(minutes=1),
        notification_count=2,
    )
    store.merge(updated)

    listed = store.list_alerts(status="active")
    assert len(listed.alerts) == 1
    assert listed.alerts[0].severity == "critical"
    assert listed.alerts[0].notification_count == 2


def test_FR_QRY_017_unknown_resolved_alert_is_stored_as_synthetic() -> None:
    store = AlertStore()
    store.merge(make_resolved_event(alert_id="unknown-after-restart"))

    detail = store.get_alert("unknown-after-restart")
    assert detail is not None
    assert detail.alert.synthetic is True
    assert detail.alert.status == "resolved"


def test_FR_QRY_016_transition_history_is_bounded_to_fifty() -> None:
    store = AlertStore(AlertStoreConfig(max_transitions=50))
    for index in range(55):
        store.merge(
            make_alert_event(
                alert_id="alert-history",
                last_observed_utc=BASE_TIME + timedelta(seconds=index),
                notification_count=index + 1,
            )
        )

    detail = store.get_alert("alert-history")
    assert detail is not None
    assert len(detail.transitions) == 50
    assert detail.transitions[0].notification_count == 6


def test_FR_QRY_016_concurrent_merge_on_same_instance_is_safe() -> None:
    store = AlertStore()

    def merge_many(prefix: str) -> None:
        for index in range(20):
            store.merge(make_alert_event(alert_id=f"{prefix}-{index}"))

    threads = [
        threading.Thread(target=merge_many, args=("a",)),
        threading.Thread(target=merge_many, args=("b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    listed = store.list_alerts(status="active", instance_id=INSTANCE_ID, limit=500)
    assert len(listed.alerts) == 40
