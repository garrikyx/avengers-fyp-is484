"""FR-QRY-018: backend-owned AgentHeartbeatMissing rule."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from telemetry_backend.config import AlertingConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.heartbeat_monitor import HeartbeatMonitor
from telemetry_shared.models.ingestion import Heartbeat, ResourceUsage

AGENT_ID = "magic-agent-sg-01"
BASE = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)


def _heartbeat(*, sent_at: datetime) -> Heartbeat:
    return Heartbeat(
        schema_version=1,
        agent_id=AGENT_ID,
        instance_ids=["magic-prod-01"],
        sent_at_utc=sent_at,
        agent_version="0.1.0",
        uptime_seconds=100,
        status="healthy",
        parse_error_count_last5_min=0,
        callback_failures_last5_min=0,
        publish_queue_depth=0,
        publish_buffer_bytes=0,
        dropped_events_last5_min=0,
        active_alert_count=0,
        resource_usage=ResourceUsage(rss_mb=1.0, cpu_percent=0.1, active_tasks=1),
    )


def test_FR_QRY_018_stale_heartbeat_fires_backend_alert() -> None:
    registry = AgentRegistry()
    store = AlertStore()
    now = BASE + timedelta(seconds=90)
    clock = {"now": now}

    monitor = HeartbeatMonitor(
        registry=registry,
        alert_store=store,
        config=AlertingConfig(missing_heartbeat_threshold_seconds=60),
        now_fn=lambda: clock["now"],
    )

    registry.record_heartbeat(_heartbeat(sent_at=BASE), now=BASE)
    monitor.evaluate_once()

    listed = store.list_alerts(rule_name="AgentHeartbeatMissing")
    assert len(listed.alerts) == 1
    alert = listed.alerts[0]
    assert alert.source == "backend"
    assert alert.status == "firing"
    assert alert.agent_id == AGENT_ID


def test_FR_QRY_018_fresh_heartbeat_resolves_backend_alert() -> None:
    registry = AgentRegistry()
    store = AlertStore()
    clock = {"now": BASE + timedelta(seconds=90)}

    monitor = HeartbeatMonitor(
        registry=registry,
        alert_store=store,
        config=AlertingConfig(missing_heartbeat_threshold_seconds=60),
        now_fn=lambda: clock["now"],
    )

    registry.record_heartbeat(_heartbeat(sent_at=BASE), now=BASE)
    monitor.evaluate_once()
    active = store.list_alerts(
        status="active", rule_name="AgentHeartbeatMissing"
    )
    assert active.counts.active == 1

    fresh = BASE + timedelta(seconds=80)
    registry.record_heartbeat(_heartbeat(sent_at=fresh), now=fresh)
    clock["now"] = fresh
    monitor.on_heartbeat(AGENT_ID)

    active = store.list_alerts(status="active", rule_name="AgentHeartbeatMissing")
    assert active.counts.active == 0
    resolved = store.list_alerts(status="resolved", rule_name="AgentHeartbeatMissing")
    assert len(resolved.alerts) == 1
    assert resolved.alerts[0].source == "backend"
