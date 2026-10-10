"""UBS-115/UBS-123: `snapshot_bridge.build_snapshot`/`SnapshotEmitter` tests.

`build_snapshot` is the converter the ticket asked for: aggregator buckets
(query-shaped, `MetricRow` per dimension-group) into the wire `Snapshot`
(series/gauges). The one thing this file specifically pins down is the
correctness detail that bit the naive version of this converter: dimension
families overlap (`SESSION_DIMS` is a subset of `BASE_DIMS`, which is a
subset of `REJECT_DIMS`), so a metric must appear exactly once in the
output, at its own native dimensionality — never folded into a coarser
family too.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LatencyCorrelator
from telemetry_agent.metrics.counters import BASE_DIMS, REJECT_DIMS, SESSION_DIMS
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishResult
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.snapshot_bridge import SnapshotEmitter, build_snapshot
from telemetry_shared.models.ingestion import TelemetryBatch
from telemetry_shared.models.snapshot import Snapshot

_METRIC_DIMENSIONS = {
    "orders_submitted": BASE_DIMS,
    "rejects_total": REJECT_DIMS,
    "logons": SESSION_DIMS,
}


def _aggregator() -> MetricsAggregator:
    config = AggregatorConfig(bucket_seconds=1, metric_dimensions=_METRIC_DIMENSIONS)
    return MetricsAggregator(config=config, clock=lambda: 100.0)


def test_each_metric_appears_exactly_once_at_its_own_native_dimensions() -> None:
    aggregator = _aggregator()
    at = datetime.fromtimestamp(100, tz=UTC)
    aggregator.ingest_agent_counters(
        dims=dict(zip(BASE_DIMS, ("i1", "s1", "AAPL", "buy", "limit"), strict=True)),
        counters={"orders_submitted": Decimal(5)},
        at=at,
    )
    aggregator.ingest_agent_counters(
        dims=dict(
            zip(
                REJECT_DIMS,
                ("i1", "s1", "AAPL", "buy", "limit", "UnknownSymbol"),
                strict=True,
            )
        ),
        counters={"rejects_total": Decimal(2)},
        at=at,
    )
    aggregator.ingest_agent_counters(
        dims=dict(zip(SESSION_DIMS, ("i1", "s1"), strict=True)),
        counters={"logons": Decimal(1)},
        at=at,
    )

    snap = build_snapshot(
        aggregator,
        bucket_start=100,
        bucket_seconds=1,
        agent_id="agent-1",
        application="Magic",
        instance_id="i1",
    )

    # Three metrics in, three series out -- not folded together, not
    # duplicated across a coarser family that happens to be a superset.
    by_metric = {metric: series for series in snap.series for metric in series.counters}
    assert set(by_metric) == {"orders_submitted", "rejects_total", "logons"}
    assert by_metric["orders_submitted"].counters["orders_submitted"] == Decimal(5)
    assert by_metric["rejects_total"].counters["rejects_total"] == Decimal(2)
    assert by_metric["rejects_total"].dimensions["rejectReason"] == "UnknownSymbol"
    assert by_metric["logons"].counters["logons"] == Decimal(1)
    assert "symbol" not in by_metric["logons"].dimensions


def test_wire_identity_fields_and_bucket_window() -> None:
    snap = build_snapshot(
        _aggregator(),
        bucket_start=120,
        bucket_seconds=10,
        agent_id="agent-1",
        application="Magic",
        instance_id="magic-prod-01",
        gauges={"pending_orders": 3.0},
    )
    assert snap.schema_version == 1
    assert snap.agent_id == "agent-1"
    assert snap.application == "Magic"
    assert snap.instance_id == "magic-prod-01"
    assert snap.bucket_start_utc == datetime.fromtimestamp(120, tz=UTC)
    assert snap.bucket_seconds == 10
    assert snap.gauges == {"pending_orders": 3.0}


def test_build_snapshot_is_pure_and_repeatable() -> None:
    """Same bucket, called twice: equal output -- a publish retry that
    rebuilds the batch must not change what it sends."""
    aggregator = _aggregator()
    at = datetime.fromtimestamp(100, tz=UTC)
    aggregator.ingest_agent_counters(
        dims=dict(zip(BASE_DIMS, ("i1", "s1", "AAPL", "buy", "limit"), strict=True)),
        counters={"orders_submitted": Decimal(5)},
        at=at,
    )

    def _build() -> Snapshot:
        return build_snapshot(
            aggregator,
            bucket_start=100,
            bucket_seconds=1,
            agent_id="agent-1",
            application="Magic",
            instance_id="i1",
        )

    assert _build() == _build()


class _CapturingSink:
    """Accepts every batch (202) and keeps it, so a test can read back
    exactly what the publisher would have put on the wire."""

    def __init__(self) -> None:
        self.batches: list[TelemetryBatch] = []

    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> PublishResult:
        self.batches.append(TelemetryBatch.model_validate_json(body))
        return PublishResult(status_code=202, latency_ms=1.0)


class _Harness:
    """A real `MetricsAggregator` (1s buckets, 60s retention) and a real
    `BackendPublisher` over a capturing sink, driven through
    `SnapshotEmitter.emit`."""

    def __init__(
        self, *, bucket_seconds: int = 10, with_correlator: bool = False
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
        """The UBS-123 bug: a tick 35s late used to publish only the latest
        completed bucket, silently losing the three before it."""
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
        """60s of 1s buckets retained: at t=1200 the aggregator still holds
        [1141,1200), so the oldest wire bucket it *fully* holds is
        [1150,1160). The 15 buckets from 1000 to 1140 are gone and must be
        counted, not published as plausible-looking zeros."""
        h = _Harness()
        assert h.emit(1005) == 1  # emits [990,1000)
        h.orders(7, at=1185)

        assert h.emit(1200) == 5

        snaps = h.published()[1:]
        assert _starts(snaps) == [1150, 1160, 1170, 1180, 1190]
        assert [_orders(s) for s in snaps] == [0, 0, 0, 7, 0]
        assert h.emitter.counters.snapshot() == {"snapshot_buckets_skipped": 15}

    def test_gauges_ride_only_on_the_newest_snapshot_of_a_call(self) -> None:
        """Gauges are point-in-time readings taken now; stamping them onto
        backfilled buckets would claim a value nobody observed then."""
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

    def test_without_a_correlator_there_is_no_pending_orders_gauge(self) -> None:
        h = _Harness()
        h.emit(1005)
        [snap] = h.published()
        assert set(snap.gauges) == {
            "consecutive_publish_failures",
            "publish_queue_depth",
        }
