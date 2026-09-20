"""FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)."""

from datetime import UTC, datetime, timedelta

from telemetry_backend.services import data_completeness
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_shared.models.health import AgentHeartbeat

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


def hb(agent_id: str) -> AgentHeartbeat:
    return AgentHeartbeat(
        agent_id=agent_id,
        instance_ids=["i"],
        sent_at_utc=T0,
        agent_version="0.1.0",
        uptime_seconds=1,
        status="healthy",
    )


def registry_with(*agent_ids: str, threshold: float = 60) -> AgentRegistry:
    registry = AgentRegistry(missing_threshold_seconds=threshold, clock=lambda: T0)
    for agent_id in agent_ids:
        registry.record_heartbeat(hb(agent_id))
    return registry


def test_all_reporting_is_complete() -> None:
    dc = data_completeness.build(registry_with("a", "b"), T0)
    assert dc.agents_expected == 2 and dc.agents_reporting == 2
    assert dc.stale_agents == [] and dc.confidence == "complete"


def test_one_stale_agent_is_partial() -> None:
    registry = registry_with("a", "b")
    registry.record_heartbeat(hb("b"), received_at=T0 - timedelta(seconds=90))
    dc = data_completeness.build(registry, T0)
    assert dc.stale_agents == ["b"]
    assert dc.agents_reporting == 1
    assert dc.confidence == "partial"


def test_all_stale_is_degraded() -> None:
    dc = data_completeness.build(registry_with("a"), T0 + timedelta(minutes=5))
    assert dc.confidence == "degraded" and dc.agents_reporting == 0


def test_expected_agent_never_seen_counts_as_stale() -> None:
    dc = data_completeness.build(
        registry_with("a"), T0, expected_agent_ids=["a", "ghost"]
    )
    assert dc.stale_agents == ["ghost"]
    assert dc.confidence == "partial"


def test_no_agents_expected_is_complete_not_degraded() -> None:
    dc = data_completeness.build(registry_with(), T0)
    assert dc.confidence == "complete" and dc.agents_expected == 0


def test_bucket_level_gaps_downgrade_complete_to_partial() -> None:
    dc = data_completeness.build(registry_with("a"), T0, restarted_buckets=2)
    assert dc.confidence == "partial" and dc.restarted_buckets == 2


def test_wire_shape_is_camel_case() -> None:
    wire = data_completeness.build(registry_with("a"), T0).model_dump(by_alias=True)
    assert set(wire) == {
        "agentsExpected",
        "agentsReporting",
        "staleAgents",
        "restartedBuckets",
        "droppedBatchesReported",
        "confidence",
    }
