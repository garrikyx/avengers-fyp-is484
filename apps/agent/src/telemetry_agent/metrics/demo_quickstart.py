"""Minimal walkthrough of the Metrics Aggregator (MA-01–04).

    uv run python -m telemetry_agent.metrics.demo_quickstart

Three orders, start to finish: two accepted and filled, one rejected
outright. Enough variety to show a real — if low-confidence — rejectRate,
not just zeros, while still skipping the robustness edge cases (cardinality
folding, orphan responses, duplicate acks, window decay) that the fuller
`metrics/demo.py` (`make metrics-demo`) covers instead. Aligned with
docs/plan/ma-epic-implementation-summary.md §§1-6.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_shared.models.parsed_message import (
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)


def _step(title: str) -> None:
    print(f"\n--- {title} ---")


def main() -> None:
    config = AggregatorConfig(
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
    )
    aggregator = MetricsAggregator(config=config)
    correlator = LatencyCorrelator(aggregator)

    def ingest(event: ParsedMessageEvent) -> None:
        correlator.ingest(event)
        aggregator.ingest_counters(event, derive_counters(event))

    now = datetime.now(tz=UTC)

    print("=" * 60)
    print("METRICS AGGREGATOR — three orders: two accepted, one rejected")
    print("=" * 60)

    _step("1. Order C1 — limit buy, 100 AAPL: submit, ack (8ms), fill (30ms)")
    ingest(
        NewOrderEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            cl_ord_id_hash="C1",
            symbol="AAPL",
            side="buy",
            ord_type="limit",
            order_qty=Decimal(100),
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now + timedelta(milliseconds=8),
            cl_ord_id_hash="C1",
            order_id_hash="O1",
            exec_id_hash="E1",
            exec_type="New",
            ord_status="New",
            symbol="AAPL",
            side="buy",
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now + timedelta(milliseconds=30),
            cl_ord_id_hash="C1",
            order_id_hash="O1",
            exec_id_hash="E2",
            exec_type="Trade",
            ord_status="Filled",
            symbol="AAPL",
            side="buy",
            last_qty=Decimal(100),
            leaves_qty=Decimal(0),
        )
    )
    print("  orders_submitted, orders_acked, executions, fills_full all += 1")
    print("  ack_latency_ms records 8ms, exec_latency_ms records 30ms")

    _step("2. Order C2 — limit buy, 50 MSFT: submit, ack (5ms), fill (18ms)")
    ingest(
        NewOrderEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            cl_ord_id_hash="C2",
            symbol="MSFT",
            side="buy",
            ord_type="limit",
            order_qty=Decimal(50),
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now + timedelta(milliseconds=5),
            cl_ord_id_hash="C2",
            order_id_hash="O2",
            exec_id_hash="E3",
            exec_type="New",
            ord_status="New",
            symbol="MSFT",
            side="buy",
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now + timedelta(milliseconds=18),
            cl_ord_id_hash="C2",
            order_id_hash="O2",
            exec_id_hash="E4",
            exec_type="Trade",
            ord_status="Filled",
            symbol="MSFT",
            side="buy",
            last_qty=Decimal(50),
            leaves_qty=Decimal(0),
        )
    )
    print("  a second, independent order — same shape, different numbers")
    print("  ack_latency_ms records 5ms, exec_latency_ms records 18ms")

    _step("3. Order C3 — market sell, 200 GOOG: submit, rejected immediately")
    ingest(
        NewOrderEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            cl_ord_id_hash="C3",
            symbol="GOOG",
            side="sell",
            ord_type="market",
            order_qty=Decimal(200),
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            cl_ord_id_hash="C3",
            order_id_hash="O3",
            exec_id_hash="E5",
            exec_type="Rejected",
            ord_status="Rejected",
            symbol="GOOG",
            side="sell",
            reject_reason_code="OrderExceedsLimit",
        )
    )
    print("  orders_submitted += 1, orders_rejected += 1 — no ack, no fill,")
    print("  and no latency sample: it never reached the correlator's happy exit")

    _step("4. Read — MA-01's bucketed store, summed over the 1m window")
    row = aggregator.snapshot("1m", group_by=())[()]
    for metric, value in sorted(row.counters.items()):
        print(f"  {metric} = {value}")

    _step("5. MA-04 — same 1m window, grouped by side this time")
    snap = snapshot(aggregator, "1m", group_by=("side",), correlator=correlator)
    for group in sorted(snap.groups, key=lambda g: g.dimensions["side"]):
        side = group.dimensions["side"]
        fill_rate = group.indicators.fill_rate
        reject_rate = group.indicators.reject_rate
        print(
            f"  side={side:<4} fillRate={fill_rate.value}"
            f"  rejectRate={reject_rate.value}"
            f"  (denominator={reject_rate.denominator})"
        )


if __name__ == "__main__":
    main()
