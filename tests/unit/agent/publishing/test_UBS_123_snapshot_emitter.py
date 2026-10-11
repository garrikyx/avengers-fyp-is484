"""UBS-123: `snapshot_bridge.SnapshotEmitter` unit tests."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_agent.config import load_agent_config
from telemetry_agent.main import Agent, build_agent
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LatencyCorrelator
from telemetry_agent.metrics.counters import BASE_DIMS, REJECT_DIMS, SESSION_DIMS
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult
from telemetry_agent.publishing.snapshot_bridge import SnapshotEmitter
from telemetry_shared.models.ingestion import TelemetryBatch
from telemetry_shared.models.snapshot import Snapshot

_METRIC_DIMENSIONS = {
    "orders_submitted": BASE_DIMS,
    "rejects_total": REJECT_DIMS,
    "logons": SESSION_DIMS,
}


class _CapturingSink:
    """Accepts (202) and keeps every batch."""

    def __init__(self) -> None:
        self.batches: list[TelemetryBatch] = []

    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> PublishResult:
        self.batches.append(TelemetryBatch.model_validate_json(body))
        return PublishResult(status_code=202, latency_ms=1.0)


class _Harness:
    """Real aggregator (1s buckets, 60s retention) and publisher behind the emitter."""

    def __init__(
        self,
        *,
        bucket_seconds: int = 10,
        with_correlator: bool = False,
        counters: CounterRegistry | None = None,
    ) -> None:
        config = AggregatorConfig(
            bucket_seconds=1,
            windows={"1m": 60},
            metric_dimensions=_METRIC_DIMENSIONS,
        )
        self.aggregator = MetricsAggregator(config=config, clock=lambda: 0.0)
        self.now = datetime.fromtimestamp(0, tz=UTC)
        self.sink = _CapturingSink()
        self.publisher = BackendPublisher(
            self.sink,
            parse_publish_config({"endpoint": "https://backend.example/t"}),
            agent_id="agent-1",
            application="Magic",
        )
        self.emitter = SnapshotEmitter(
            self.aggregator,
            self.publisher,
            bucket_seconds=bucket_seconds,
            agent_id="agent-1",
            application="Magic",
            instance_id="i1",
            correlator=(
                LatencyCorrelator(self.aggregator) if with_correlator else None
            ),
            counters=counters,
        )

    def orders(self, count: int, *, at: int) -> None:
        self.aggregator.ingest_agent_counters(
            dims=dict(
                zip(BASE_DIMS, ("i1", "s1", "AAPL", "buy", "limit"), strict=True)
            ),
            counters={"orders_submitted": Decimal(count)},
            at=datetime.fromtimestamp(at, tz=UTC),
        )

    def emit(self, at: int) -> int:
        now = datetime.fromtimestamp(at, tz=UTC)
        self.now = now
        self.aggregator.tick(now.timestamp())  # the evaluator ages first
        return self.emitter.emit(now)

    def published(self) -> list[Snapshot]:
        while self.publisher.queue_depth():
            asyncio.run(self.publisher.publish_once(now=self.now))
        return [snap for batch in self.sink.batches for snap in batch.snapshots]


def _starts(snaps: list[Snapshot]) -> list[int]:
    return [int(s.bucket_start_utc.timestamp()) for s in snaps]


def _orders(snap: Snapshot) -> Decimal:
    return sum(
        (s.counters.get("orders_submitted", Decimal(0)) for s in snap.series),
        Decimal(0),
    )


class TestSnapshotEmitter:
    def test_first_call_emits_only_the_latest_completed_bucket(self) -> None:
        h = _Harness()
        h.orders(1, at=1000)
        h.orders(2, at=1010)

        assert h.emit(1025) == 1  # current bucket [1020,1030)

        [snap] = h.published()
        assert _starts([snap]) == [1010]
        assert snap.bucket_seconds == 10
        assert _orders(snap) == Decimal(2)

    def test_second_call_before_the_next_bucket_completes_emits_nothing(
        self,
    ) -> None:
        h = _Harness()
        assert h.emit(1025) == 1
        assert h.emit(1029) == 0  # still inside [1020,1030)
        assert _starts(h.published()) == [1010]

    def test_late_tick_publishes_every_missed_bucket_oldest_first(self) -> None:
        h = _Harness()
        assert h.emit(1005) == 1  # emits [990,1000)
        h.orders(1, at=1001)
        h.orders(2, at=1012)
        h.orders(3, at=1025)
        h.orders(4, at=1039)
        h.orders(99, at=1040)  # current bucket -- not complete yet

        assert h.emit(1041) == 4

        snaps = h.published()[1:]
        assert _starts(snaps) == [1000, 1010, 1020, 1030]
        assert [_orders(s) for s in snaps] == [1, 2, 3, 4]

    def test_gap_beyond_retention_publishes_only_retained_buckets(self) -> None:
        """At t=1200 only [1150,1200) is fully retained; 1000-1140 are skipped."""
        h = _Harness()
        assert h.emit(1005) == 1  # emits [990,1000)
        h.orders(7, at=1185)

        assert h.emit(1200) == 5

        snaps = h.published()[1:]
        assert _starts(snaps) == [1150, 1160, 1170, 1180, 1190]
        assert [_orders(s) for s in snaps] == [0, 0, 0, 7, 0]
        assert h.emitter.counters.snapshot() == {"snapshot_buckets_skipped": 15}

    def test_skips_are_counted_on_a_shared_registry(self) -> None:
        shared = CounterRegistry()
        h = _Harness(counters=shared)
        h.emit(1005)
        h.emit(1200)
        assert h.emitter.counters is shared
        assert shared.snapshot() == {"snapshot_buckets_skipped": 15}

    def test_gauges_ride_only_on_the_newest_snapshot_of_a_call(self) -> None:
        h = _Harness(with_correlator=True)
        assert h.emit(1005) == 1  # left in the queue: depth 1

        assert h.emit(1035) == 3

        snaps = h.published()
        assert set(snaps[0].gauges) == {
            "consecutive_publish_failures",
            "publish_queue_depth",
            "pending_orders",
        }
        backfilled, newest = snaps[1:3], snaps[3]
        assert [s.gauges for s in backfilled] == [{}, {}]
        assert newest.gauges == {
            "consecutive_publish_failures": 0.0,
            "publish_queue_depth": 1.0,  # read once, before this call enqueued
            "pending_orders": 0.0,
        }

    @pytest.mark.parametrize("bucket_seconds", [0, -10])
    def test_rejects_non_positive_bucket_seconds(self, bucket_seconds: int) -> None:
        with pytest.raises(ValueError, match="bucket_seconds"):
            _Harness(bucket_seconds=bucket_seconds)

    def test_rejects_bucket_seconds_not_a_multiple_of_the_aggregators(
        self,
    ) -> None:
        aggregator = MetricsAggregator(
            config=AggregatorConfig(
                bucket_seconds=5, metric_dimensions=_METRIC_DIMENSIONS
            )
        )
        publisher = _Harness().publisher
        with pytest.raises(ValueError, match="multiple"):
            SnapshotEmitter(
                aggregator,
                publisher,
                bucket_seconds=12,
                agent_id="agent-1",
                application="Magic",
                instance_id="i1",
            )

    @pytest.mark.parametrize("bucket_seconds", [31, 60])
    def test_rejects_retention_shorter_than_two_wire_buckets(
        self, bucket_seconds: int
    ) -> None:
        with pytest.raises(ValueError, match="retention"):
            _Harness(bucket_seconds=bucket_seconds)  # 60s retention

    def test_accepts_retention_of_exactly_two_wire_buckets(self) -> None:
        h = _Harness(bucket_seconds=30)
        assert h.emit(1005) == 1

    def test_without_a_correlator_there_is_no_pending_orders_gauge(self) -> None:
        h = _Harness()
        h.emit(1005)
        [snap] = h.published()
        assert set(snap.gauges) == {
            "consecutive_publish_failures",
            "publish_queue_depth",
        }


_AGENT_CONFIG = """
agent:
  id: agent-123
  instanceIds: [magic-01]
logs:
  paths: [{tmp}/Fix.log]
  stateDir: {tmp}/state
rules:
  path: rules.yaml
publish:
  endpoint: https://backend.example/telemetry/batch
  metricsBucketSeconds: {bucket_seconds}
"""

_RULES = """
rules:
  - name: RejectSpike
    kind: threshold
    source: counter
    metric: orders_rejected
    operator: ">"
    tiers: [{severity: warning, threshold: 50}]
    window: 1m
"""

_ENV = {
    "MAGIC_TELEMETRY_ID_HASH_KEY": "k",
    "MAGIC_TELEMETRY_PUBLISH_TOKEN": "t",
}


def _build(tmp_path: Path, bucket_seconds: int) -> Agent:
    (tmp_path / "rules.yaml").write_text(_RULES, encoding="utf-8")
    path = tmp_path / "agent.yaml"
    path.write_text(
        _AGENT_CONFIG.format(tmp=tmp_path.as_posix(), bucket_seconds=bucket_seconds),
        encoding="utf-8",
    )
    return build_agent(load_agent_config(path), env=_ENV)


def test_build_agent_rejects_a_bucket_longer_than_retention_allows(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="retention"):
        _build(tmp_path, 600)  # default 900s retention < 2 x 600s


def test_build_agent_logs_emitter_skips_with_the_evaluator_counters(
    tmp_path: Path,
) -> None:
    agent = _build(tmp_path, 10)
    emitter = agent.evaluator._snapshot_emitter
    assert emitter is not None
    assert emitter.counters is agent.evaluator.counters
