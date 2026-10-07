"""UBS-58/60: the Health Reporter reaches the backend only through the Backend
Publisher (`health/publishing.py`)."""

from datetime import UTC, datetime

from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.publishing import (
    connect_reporter_to_publisher,
    drop_hook,
    heartbeat_provider,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_shared.models.ingestion import Heartbeat

T0 = datetime(2026, 10, 7, 4, 0, 0, tzinfo=UTC)


def _reporter() -> HealthReporter:
    return HealthReporter(
        {},
        heartbeat=HeartbeatConfig(agent_id="agent-a", instance_ids=("magic-01",)),
        clock=lambda: T0,
    )


class FakePublisher:
    def __init__(self, depth: int = 3, buffered: int = 2048) -> None:
        self.depth = depth
        self.buffered = buffered

    def queue_depth(self) -> int:
        return self.depth

    def buffer_bytes(self) -> int:
        return self.buffered


def test_provider_returns_a_fresh_wire_heartbeat_each_call() -> None:
    reporter = _reporter()
    provide = heartbeat_provider(reporter)

    first = provide()
    reporter.record_parse_error()
    second = provide()

    assert isinstance(first, Heartbeat)
    assert first.agent_id == "agent-a"
    assert first.instance_ids == ["magic-01"]
    assert first.parse_error_count_last5_min == 0
    assert second.parse_error_count_last5_min == 1  # built at call time


def test_connect_points_outbox_signals_at_the_publisher() -> None:
    reporter = _reporter()
    publisher = FakePublisher(depth=3, buffered=2048)

    connect_reporter_to_publisher(reporter, publisher)  # type: ignore[arg-type]
    hb = reporter.build_heartbeat()
    assert hb.publish_queue_depth == 3
    assert hb.publish_buffer_bytes == 2048
    assert hb.dropped_events_last5_min == 0  # producer wired: 0, not null

    publisher.depth = 7
    assert reporter.build_heartbeat().publish_queue_depth == 7  # live, not copied


def test_drop_hook_counts_each_evicted_item() -> None:
    reporter = _reporter()
    on_drop = drop_hook(reporter)
    on_drop()
    on_drop()
    assert reporter.build_heartbeat().dropped_events_last5_min == 2
