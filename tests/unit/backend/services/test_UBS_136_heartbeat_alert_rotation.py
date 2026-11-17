"""UBS-136: backend heartbeat alerts rotate alertId per outage (FR-QRY-018)."""

from __future__ import annotations

from datetime import timedelta

from telemetry_backend.config import AlertingConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.heartbeat_monitor import HeartbeatMonitor

from tests.unit.backend.services.test_FR_QRY_018_heartbeat_missing import (
    AGENT_ID,
    BASE,
    _heartbeat,
)


def test_UBS_136_second_outage_of_same_agent_opens_new_firing_alert() -> None:
    store = AlertStore()
    clock = {"now": BASE}

    registry = AgentRegistry(
        missing_threshold_seconds=60,
        clock=lambda: clock["now"],
    )
    monitor = HeartbeatMonitor(
        registry=registry,
        alert_store=store,
        config=AlertingConfig(missing_heartbeat_threshold_seconds=60),
        now_fn=lambda: clock["now"],
    )

    registry.record_heartbeat(_heartbeat(sent_at=BASE), received_at=BASE)

    clock["now"] = BASE + timedelta(seconds=90)
    monitor.evaluate_once()
    first = store.list_alerts(status="active", rule_name="AgentHeartbeatMissing")
    assert first.counts.active == 1
    alert_id_1 = first.alerts[0].alert_id

    fresh = BASE + timedelta(seconds=80)
    registry.record_heartbeat(_heartbeat(sent_at=fresh), received_at=fresh)
    clock["now"] = fresh
    monitor.on_heartbeat(AGENT_ID)

    resolved = store.list_alerts(status="resolved", rule_name="AgentHeartbeatMissing")
    assert len(resolved.alerts) == 1
    assert resolved.alerts[0].alert_id == alert_id_1
    active_after_resolve = store.list_alerts(
        status="active", rule_name="AgentHeartbeatMissing"
    )
    assert active_after_resolve.counts.active == 0

    clock["now"] = fresh + timedelta(seconds=120)
    monitor.evaluate_once()

    second = store.list_alerts(status="active", rule_name="AgentHeartbeatMissing")
    assert second.counts.active == 1
    alert_id_2 = second.alerts[0].alert_id
    assert alert_id_2 != alert_id_1

    still_resolved = store.get_alert(alert_id_1)
    assert still_resolved is not None
    assert still_resolved.alert.status == "resolved"
