"""UBS-69 / FR-ING-010: agent registry, backend-side staleness."""

from datetime import UTC, datetime, timedelta

import pytest
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_shared.models.ingestion import Heartbeat, ResourceUsage

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def hb(
    agent_id: str = "magic-agent-sg-01",
    *,
    sent_at: datetime | None = None,
    **kw: object,
) -> Heartbeat:
    base: dict[str, object] = {
        "schema_version": 1,
        "agent_id": agent_id,
        "instance_ids": ["magic-prod-01"],
        "sent_at_utc": sent_at or T0,
        "agent_version": "0.1.0",
        "uptime_seconds": 10,
        "status": "healthy",
        "parse_error_count_last5_min": 0,
        "callback_failures_last5_min": 0,
        "publish_queue_depth": 0,
        "publish_buffer_bytes": 0,
        "dropped_events_last5_min": 0,
        "active_alert_count": 0,
        "resource_usage": ResourceUsage(rss_mb=0, cpu_percent=0, active_tasks=0),
    }
    base.update(kw)
    return Heartbeat(**base)  # type: ignore[arg-type]


def make(threshold: float = 60.0) -> tuple[AgentRegistry, FakeClock]:
    clock = FakeClock()
    return AgentRegistry(missing_threshold_seconds=threshold, clock=clock), clock


def test_first_contact_is_reported_once() -> None:
    registry, _ = make()
    assert registry.record_heartbeat(hb()) is True
    assert registry.record_heartbeat(hb(sent_at=T0 + timedelta(seconds=10))) is False
    assert len(registry) == 1


def test_records_last_heartbeat_and_version() -> None:
    registry, clock = make()
    registry.record_heartbeat(hb(agent_version="0.1.0"))
    clock.advance(10)
    registry.record_heartbeat(
        hb(sent_at=T0 + timedelta(seconds=10), agent_version="0.2.0", status="degraded")
    )
    rec = registry.get("magic-agent-sg-01")
    assert rec is not None
    assert rec.agent_version == "0.2.0"
    assert rec.last_heartbeat_utc == T0 + timedelta(seconds=10)
    assert rec.first_seen_at == T0
    assert rec.received_at == T0 + timedelta(seconds=10)
    assert registry.status_of(rec) == "degraded"


def test_late_older_heartbeat_keeps_newer_doc_but_refreshes_liveness() -> None:
    registry, clock = make()
    registry.record_heartbeat(hb(sent_at=T0 + timedelta(seconds=30), status="degraded"))
    clock.advance(5)
    registry.record_heartbeat(hb(sent_at=T0, status="healthy"))  # stale on the wire
    rec = registry.get("magic-agent-sg-01")
    assert rec is not None
    assert rec.heartbeat.status == "degraded"  # view does not roll back
    assert rec.received_at == T0 + timedelta(seconds=5)  # but the agent is alive


def test_agent_clock_stepped_backwards_does_not_go_missing() -> None:
    """NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on
    every subsequent heartbeat, yet the agent is heartbeating and must stay live."""
    registry, clock = make(threshold=60)
    registry.record_heartbeat(hb(sent_at=T0 + timedelta(minutes=5)))
    for i in range(1, 12):  # 110s of 10s heartbeats, all "older" than the first
        clock.advance(10)
        registry.record_heartbeat(hb(sent_at=T0 + timedelta(seconds=10 * i)))
    rec = registry.get("magic-agent-sg-01")
    assert rec is not None
    assert registry.status_of(rec) == "healthy"
    assert registry.heartbeat_age_ms(rec) == 0


def test_missing_after_threshold_measured_on_backend_clock() -> None:
    """An agent whose clock is far ahead still goes missing when it stops sending."""
    registry, clock = make(threshold=60)
    registry.record_heartbeat(hb(sent_at=T0 + timedelta(hours=3)))  # skewed agent clock
    rec = registry.get("magic-agent-sg-01")
    assert rec is not None
    clock.advance(60)
    assert registry.is_stale(rec) is False  # exactly at threshold is not stale
    assert registry.status_of(rec) == "healthy"
    clock.advance(0.001)
    assert registry.status_of(rec) == "missing"
    assert registry.heartbeat_age_ms(rec) == 60_001


def test_stale_agents_lists_only_the_silent_ones() -> None:
    registry, clock = make(threshold=30)
    registry.record_heartbeat(hb("a"))
    registry.record_heartbeat(hb("b"))
    clock.advance(20)
    registry.record_heartbeat(hb("b", sent_at=T0 + timedelta(seconds=20)))
    clock.advance(15)  # a: 35s silent, b: 15s
    assert registry.stale_agents() == ["a"]
    assert [r.agent_id for r in registry.all()] == ["a", "b"]


def test_remove_decommissions_agent() -> None:
    registry, _ = make()
    registry.record_heartbeat(hb("a"))
    assert registry.remove("a") is True
    assert registry.remove("a") is False
    assert registry.get("a") is None


def test_explicit_received_at_overrides_clock() -> None:
    registry, clock = make()
    registry.record_heartbeat(hb(), received_at=T0 - timedelta(seconds=100))
    rec = registry.get("magic-agent-sg-01")
    assert rec is not None
    assert registry.status_of(rec, at=clock()) == "missing"


def test_rejects_non_positive_threshold() -> None:
    with pytest.raises(ValueError):
        AgentRegistry(missing_threshold_seconds=0)
