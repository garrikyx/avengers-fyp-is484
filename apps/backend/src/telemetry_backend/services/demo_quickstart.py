"""Minimal walkthrough of the Stream Processor & Metric Store — built on
the exact same story as the Metrics Aggregator quickstart, one level up.

    uv run python -m telemetry_backend.services.demo_quickstart

agent-sg-01 replays the identical 3-order story from
`telemetry_agent.metrics.demo_quickstart` (two accepted and filled, one
rejected). agent-hk-01 replays the same shape at higher volume — a busier
session, same mostly-accepted-occasionally-rejected pattern. Each agent's
raw MA-01 bucket is bridged into the wire `Snapshot` format — the
conversion a real Backend Publisher (spec 002, not built yet) would do —
then fed through the real `StreamProcessor`/`MetricStore` code path.

Demo-only shortcut, not a production pattern: real code would never have
the backend import `telemetry_agent` directly — a real Backend Publisher
runs inside the agent process and sends an already-serialised `Snapshot`
over HTTP. Both sides are inlined here only so this reads as one
continuous story instead of two disconnected examples. See
docs/plan/ma-epic-implementation-summary.md §7 for the full mechanics.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_shared.models.parsed_message import (
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)
from telemetry_shared.models.snapshot import HistogramPayload, SeriesEntry, Snapshot

from telemetry_backend.services.stream_processor import StreamProcessor

INSTANCE = "magic-prod-01"
SESSION = "MAGIC->EXCH1"

Ingest = Callable[[ParsedMessageEvent], None]


def _step(title: str) -> None:
    print(f"\n--- {title} ---")


def _new_aggregator() -> tuple[MetricsAggregator, Ingest]:
    config = AggregatorConfig(
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
    )
    aggregator = MetricsAggregator(config=config)
    correlator = LatencyCorrelator(aggregator)

    def ingest(event: ParsedMessageEvent) -> None:
        correlator.ingest(event)
        aggregator.ingest_counters(event, derive_counters(event))

    return aggregator, ingest


def _accept_and_fill(
    ingest: Ingest,
    *,
    cl_ord_id_hash: str,
    symbol: str,
    qty: int,
    now: datetime,
    ack_ms: int,
    fill_ms: int,
) -> None:
    order_id_hash = f"O-{cl_ord_id_hash}"
    ingest(
        NewOrderEvent(
            instance_id=INSTANCE,
            session_id=SESSION,
            event_time_utc=now,
            cl_ord_id_hash=cl_ord_id_hash,
            symbol=symbol,
            side="buy",
            ord_type="limit",
            order_qty=Decimal(qty),
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id=INSTANCE,
            session_id=SESSION,
            event_time_utc=now + timedelta(milliseconds=ack_ms),
            cl_ord_id_hash=cl_ord_id_hash,
            order_id_hash=order_id_hash,
            exec_id_hash=f"{cl_ord_id_hash}-ack",
            exec_type="New",
            ord_status="New",
            symbol=symbol,
            side="buy",
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id=INSTANCE,
            session_id=SESSION,
            event_time_utc=now + timedelta(milliseconds=fill_ms),
            cl_ord_id_hash=cl_ord_id_hash,
            order_id_hash=order_id_hash,
            exec_id_hash=f"{cl_ord_id_hash}-fill",
            exec_type="Trade",
            ord_status="Filled",
            symbol=symbol,
            side="buy",
            last_qty=Decimal(qty),
            leaves_qty=Decimal(0),
        )
    )


def _reject(
    ingest: Ingest, *, cl_ord_id_hash: str, symbol: str, qty: int, now: datetime
) -> None:
    ingest(
        NewOrderEvent(
            instance_id=INSTANCE,
            session_id=SESSION,
            event_time_utc=now,
            cl_ord_id_hash=cl_ord_id_hash,
            symbol=symbol,
            side="sell",
            ord_type="market",
            order_qty=Decimal(qty),
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id=INSTANCE,
            session_id=SESSION,
            event_time_utc=now,
            cl_ord_id_hash=cl_ord_id_hash,
            order_id_hash=f"O-{cl_ord_id_hash}",
            exec_id_hash=f"{cl_ord_id_hash}-rej",
            exec_type="Rejected",
            ord_status="Rejected",
            symbol=symbol,
            side="sell",
            reject_reason_code="OrderExceedsLimit",
        )
    )


def _run_singapore_session() -> MetricsAggregator:
    """The exact 3-order story from the Metrics Aggregator quickstart:
    two accepted and filled, one rejected.
    """
    aggregator, ingest = _new_aggregator()
    now = datetime.now(tz=UTC)
    _accept_and_fill(
        ingest,
        cl_ord_id_hash="C1",
        symbol="AAPL",
        qty=100,
        now=now,
        ack_ms=8,
        fill_ms=30,
    )
    _accept_and_fill(
        ingest,
        cl_ord_id_hash="C2",
        symbol="MSFT",
        qty=50,
        now=now,
        ack_ms=5,
        fill_ms=18,
    )
    _reject(ingest, cl_ord_id_hash="C3", symbol="GOOG", qty=200, now=now)
    return aggregator


def _run_hong_kong_session() -> MetricsAggregator:
    """Same shape, busier day: 98 accepted and filled, 1 rejected."""
    aggregator, ingest = _new_aggregator()
    now = datetime.now(tz=UTC)
    for i in range(99):
        cl_ord_id_hash = f"H{i}"
        if i == 49:
            _reject(
                ingest, cl_ord_id_hash=cl_ord_id_hash, symbol="AAPL", qty=100, now=now
            )
        else:
            ack_ms = 5 + (i % 10)
            fill_ms = ack_ms + 10 + (i % 5)
            _accept_and_fill(
                ingest,
                cl_ord_id_hash=cl_ord_id_hash,
                symbol="AAPL",
                qty=100,
                now=now,
                ack_ms=ack_ms,
                fill_ms=fill_ms,
            )
    return aggregator


def _bridge_to_snapshot(
    aggregator: MetricsAggregator, *, agent_id: str, bucket_start_utc: datetime
) -> Snapshot:
    """The conversion a real Backend Publisher would do: turn one agent's
    raw MA-01 buckets into the wire `Snapshot` shape, one series per
    label-set — grouped by `side`, so the Metric Store has a real
    dimension to aggregate on rather than one flat, undifferentiated blob.
    """
    rows = aggregator.snapshot("1m", group_by=("side",))
    series = [
        SeriesEntry(
            dimensions={"side": side},
            counters=row.counters,
            histograms={
                name: HistogramPayload(
                    count=hist.count,
                    sum=hist.sum_ms,
                    min=hist.min_ms,
                    max=hist.max_ms,
                    buckets=dict(hist.buckets),
                )
                for name, hist in row.histograms.items()
            },
        )
        for (side,), row in rows.items()
    ]
    return Snapshot(
        schema_version=1,
        agent_id=agent_id,
        application="Magic",
        instance_id=INSTANCE,
        bucket_start_utc=bucket_start_utc,
        bucket_seconds=10,
        series=series,
    )


def main() -> None:
    print("=" * 60)
    print("STREAM PROCESSOR & METRIC STORE — the same story, two agents")
    print("=" * 60)

    _step("1. Two agents, two independent Metrics Aggregators")
    sg_aggregator = _run_singapore_session()
    hk_aggregator = _run_hong_kong_session()
    sg_row = sg_aggregator.snapshot("1m", group_by=())[()]
    hk_row = hk_aggregator.snapshot("1m", group_by=())[()]
    print("  agent-sg-01: the exact 3-order story from the MA quickstart")
    print(
        f"    orders_acked={sg_row.counters['orders_acked']}"
        f" orders_rejected={sg_row.counters['orders_rejected']}"
    )
    print("  agent-hk-01: same shape, a busier session")
    print(
        f"    orders_acked={hk_row.counters['orders_acked']}"
        f" orders_rejected={hk_row.counters['orders_rejected']}"
    )

    _step("2. Bridge each agent's raw bucket into the wire Snapshot format")
    canonical_window_start = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    sg_bucket_start = datetime(2026, 6, 12, 4, 0, 3, tzinfo=UTC)  # 3s into the window
    hk_bucket_start = datetime(2026, 6, 12, 4, 0, 7, tzinfo=UTC)  # 7s into the window
    agent_sg = _bridge_to_snapshot(
        sg_aggregator, agent_id="agent-sg-01", bucket_start_utc=sg_bucket_start
    )
    agent_hk = _bridge_to_snapshot(
        hk_aggregator, agent_id="agent-hk-01", bucket_start_utc=hk_bucket_start
    )
    print(f"  agent-sg-01 bucketStartUtc = {sg_bucket_start.time()}")
    print(f"  agent-hk-01 bucketStartUtc = {hk_bucket_start.time()}")

    _step("3. Stream Processor aligns both onto the same 10s canonical bucket")
    processor = StreamProcessor()
    outcome_sg = processor.process_snapshot(agent_sg, now=canonical_window_start)
    outcome_hk = processor.process_snapshot(agent_hk, now=canonical_window_start)
    sg_canonical = outcome_sg.canonical_bucket_start.time()
    hk_canonical = outcome_hk.canonical_bucket_start.time()
    print(f"  agent-sg-01 -> canonical bucket {sg_canonical}")
    print(f"  agent-hk-01 -> canonical bucket {hk_canonical}")
    print("  both landed in the same bucket, despite arriving 4 seconds apart")

    _step("4. Metric Store — counters sum across agents, never overwrite")
    groups = processor.store.read(
        INSTANCE, from_utc=canonical_window_start, to_utc=canonical_window_start
    )
    counters = groups[0].counters
    for metric, value in sorted(counters.items()):
        print(f"  {metric} = {value}")

    _step("5. Same read, grouped by side, across both agents")
    grouped = processor.store.read(
        INSTANCE,
        from_utc=canonical_window_start,
        to_utc=canonical_window_start,
        group_by=("side",),
    )
    for group in sorted(grouped, key=lambda g: g.dimensions["side"]):
        side = group.dimensions["side"]
        fill_rate = group.indicators.fill_rate
        reject_rate = group.indicators.reject_rate
        print(
            f"  side={side:<4} fillRate={fill_rate.value}"
            f"  rejectRate={reject_rate.value}"
            f"  (denominator={reject_rate.denominator})"
        )

    _step("6. Ratio recomputed from summed counters — never averaged per agent")
    sg_acked = sg_row.counters["orders_acked"]
    sg_rejected = sg_row.counters["orders_rejected"]
    hk_acked = hk_row.counters["orders_acked"]
    hk_rejected = hk_row.counters["orders_rejected"]
    sg_rate = float(sg_rejected / (sg_acked + sg_rejected))
    hk_rate = float(hk_rejected / (hk_acked + hk_rejected))
    naive_average = (sg_rate + hk_rate) / 2
    reject_rate = groups[0].indicators.reject_rate
    print(
        f"  agent-sg-01 alone: rejectRate = {sg_rate:.4f}"
        "  (1 rejected / 3 orders, a quiet session)"
    )
    print(
        f"  agent-hk-01 alone: rejectRate = {hk_rate:.4f}"
        "  (1 rejected / 99 orders, a busy one)"
    )
    print(f"  wrong:   averaging those two gives {naive_average:.4f}")
    print(
        f"  correct: rejectRate = {reject_rate.value:.4f}"
        f"  (summed first — {reject_rate.denominator} orders total)"
    )

    _step("7. Histogram merges bucket-wise — never averages percentiles")
    latency = groups[0].latency["ack_latency_ms"]
    print(f"  count = {latency.count}  (agent-sg-01's 2 samples + agent-hk-01's 98)")
    print(
        f"  p50   = {latency.p50:.1f}ms"
        "  (enough combined samples to trust this, unlike either agent alone)"
    )


if __name__ == "__main__":
    main()
