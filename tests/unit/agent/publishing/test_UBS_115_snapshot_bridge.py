"""UBS-115: `snapshot_bridge.build_snapshot` unit tests.

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

from datetime import UTC, datetime
from decimal import Decimal

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import BASE_DIMS, REJECT_DIMS, SESSION_DIMS
from telemetry_agent.publishing.snapshot_bridge import build_snapshot
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
    by_metric = {
        metric: series
        for series in snap.series
        for metric in series.counters
    }
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
