"""UBS-60: publish queue depth in the heartbeat, watermark rules, trend."""

import json
from datetime import UTC, datetime

import pytest
from telemetry_agent.health.config import HealthThresholds
from telemetry_agent.health.heartbeat import (
    BufferingHeartbeatSink,
    HeartbeatEmitter,
    heartbeat_json,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_shared.models.health import AgentHeartbeat

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


class FakeQueue:
    def __init__(self, depth: int = 0) -> None:
        self.depth = depth

    def __call__(self) -> int:
        return self.depth


def make(
    depth: int | None = None, **thresholds: int
) -> tuple[HealthReporter, FakeQueue]:
    queue = FakeQueue(depth or 0)
    reporter = HealthReporter(
        {},
        thresholds=HealthThresholds(**thresholds),
        clock=lambda: T0,
        queue_depth_provider=queue if depth is not None else None,
    )
    return reporter, queue


# --- FR-HLT-004: no Publisher => null ----------------------------------------------


def test_queue_depth_is_none_without_a_provider() -> None:
    reporter, _ = make()
    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))
    assert wire["publishQueueDepth"] is None
    assert reporter.build_heartbeat().status == "healthy"


def test_provider_can_be_registered_later_and_removed() -> None:
    reporter, _ = make()
    reporter.set_queue_depth_provider(lambda: 3)
    assert reporter.snapshot().publish_queue_depth == 3
    reporter.set_queue_depth_provider(None)
    assert reporter.snapshot().publish_queue_depth is None


# --- AC: depth in payload, near real time ----------------------------------------


def test_depth_is_read_fresh_on_every_snapshot() -> None:
    reporter, queue = make(depth=2)
    assert reporter.snapshot().publish_queue_depth == 2
    queue.depth = 7
    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))
    assert wire["publishQueueDepth"] == 7


def test_negative_provider_values_are_clamped() -> None:
    reporter, _ = make(depth=-4)
    assert reporter.snapshot().publish_queue_depth == 0


# --- AC: trend derivable from consecutive snapshots -------------------------------


def test_trend_across_consecutive_snapshots() -> None:
    reporter, queue = make(depth=5)
    assert reporter.snapshot().publish_queue_trend is None  # first sample
    queue.depth = 9
    assert reporter.snapshot().publish_queue_trend == "rising"
    assert reporter.snapshot().publish_queue_trend == "flat"
    queue.depth = 1
    assert reporter.snapshot().publish_queue_trend == "draining"


# --- AC: watermarks => degraded / unhealthy ------------------------------------------


def test_below_high_watermark_is_healthy() -> None:
    reporter, _ = make(depth=9, publish_queue_high_watermark=10)
    assert reporter.build_heartbeat().status == "healthy"


def test_at_high_watermark_is_degraded_with_reason_and_trend() -> None:
    reporter, queue = make(depth=8, publish_queue_high_watermark=10)
    reporter.snapshot()
    queue.depth = 10
    hb = reporter.build_heartbeat()
    assert hb.status == "degraded"
    assert hb.status_reasons == [
        "publish queue depth 10, rising at or above high watermark 10"
    ]


def test_at_critical_watermark_is_unhealthy() -> None:
    reporter, _ = make(
        depth=100, publish_queue_high_watermark=10, publish_queue_critical_watermark=100
    )
    hb = reporter.build_heartbeat()
    assert hb.status == "unhealthy"
    assert hb.status_reasons == [
        "publish queue depth 100 at or above critical watermark 100"
    ]


def test_watermarks_are_configurable() -> None:
    reporter, _ = make(
        depth=50, publish_queue_high_watermark=200, publish_queue_critical_watermark=400
    )
    assert reporter.build_heartbeat().status == "healthy"


def test_draining_queue_recovers_to_healthy() -> None:
    reporter, queue = make(depth=40, publish_queue_high_watermark=10)
    assert reporter.build_heartbeat().status == "degraded"
    queue.depth = 3
    hb = reporter.build_heartbeat()
    assert hb.status == "healthy"
    assert hb.status_reasons == []


# --- BufferingHeartbeatSink: the demo's queue --------------------------------------


class Flaky:
    def __init__(self) -> None:
        self.up = True
        self.delivered: list[AgentHeartbeat] = []

    def __call__(self, hb: AgentHeartbeat) -> None:
        if not self.up:
            raise ConnectionError("backend down")
        self.delivered.append(hb)


def test_buffer_fills_while_downstream_is_down_and_drains_in_order() -> None:
    downstream = Flaky()
    buffered = BufferingHeartbeatSink(downstream, max_items=10)
    reporter, _ = make()
    reporter.set_queue_depth_provider(lambda: len(buffered))
    emitter = HeartbeatEmitter(reporter, buffered)

    emitter.tick()
    assert len(buffered) == 0 and emitter.sent_count == 1

    downstream.up = False
    for _ in range(3):
        emitter.tick()
    assert len(buffered) == 3 and emitter.failed_count == 3
    assert reporter.snapshot().publish_queue_depth == 3

    downstream.up = True
    emitter.tick()  # delivers the 3 queued (oldest first) plus this one
    assert len(buffered) == 0
    assert [hb.uptime_seconds for hb in downstream.delivered] == [0.0] * 5
    assert len(downstream.delivered) == 5


def test_buffer_drops_oldest_when_full() -> None:
    downstream = Flaky()
    downstream.up = False
    buffered = BufferingHeartbeatSink(downstream, max_items=2)
    reporter, _ = make()
    emitter = HeartbeatEmitter(reporter, buffered)
    for _ in range(5):
        emitter.tick()
    assert len(buffered) == 2
    assert buffered.dropped_count == 3


def test_buffer_rejects_zero_capacity() -> None:
    with pytest.raises(ValueError):
        BufferingHeartbeatSink(Flaky(), max_items=0)


def test_queue_depth_reaches_the_wire_through_the_buffer() -> None:
    downstream = Flaky()
    downstream.up = False
    buffered = BufferingHeartbeatSink(downstream, max_items=50)
    reporter, _ = make(publish_queue_high_watermark=3)
    reporter.set_queue_depth_provider(lambda: len(buffered))
    emitter = HeartbeatEmitter(reporter, buffered)
    last = None
    for _ in range(4):
        last = emitter.tick()
    assert last is not None
    # the 4th heartbeat was built while 3 were already queued
    assert last.publish_queue_depth == 3
    assert last.status == "degraded"
