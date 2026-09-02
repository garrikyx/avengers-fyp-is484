"""Runnable demo of the Metrics Aggregator epic (MA-01/02/03).

    uv run python -m telemetry_agent.metrics.demo

Feeds a small, narrated set of synthetic FIX-derived events through the
real ingest paths (no Parser Engine involved — it doesn't extract fields
yet, so events are hand-built here the same way the tests do) and prints
what comes out: counters, reject-reason normalisation, cardinality
folding, correlation/latency, and window decay. Nothing here is asserted —
read the output, don't grep it.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import (
    COUNTER_DIMENSIONS,
    ReasonNormalizer,
    derive_counters,
    top_reject_reasons,
)
from telemetry_shared.models.parsed_message import (
    CancelRequestEvent,
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    reasons = ReasonNormalizer()
    config = AggregatorConfig(
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS},
        windows={"5s": 5, "1m": 60},
        max_label_sets=3,  # deliberately small, so folding is visible below
    )
    aggregator = MetricsAggregator(config=config, resolve_reject_reason=reasons.resolve)
    correlator = LatencyCorrelator(aggregator, ttl_seconds=5)

    def ingest(event: ParsedMessageEvent) -> None:
        correlator.ingest(event)
        aggregator.ingest_counters(event, derive_counters(event))

    now = datetime.now(tz=UTC)

    _section("MA-02: new order -> ack -> fill, and a rejected order")
    ingest(
        NewOrderEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            cl_ord_id="C1",
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
            cl_ord_id="C1",
            order_id="O1",
            exec_id="E1",
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
            cl_ord_id="C1",
            order_id="O1",
            exec_id="E2",
            exec_type="Trade",
            ord_status="Filled",
            symbol="AAPL",
            side="buy",
            last_qty=Decimal(100),
            leaves_qty=Decimal(0),
        )
    )
    ingest(
        NewOrderEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            cl_ord_id="C2",
            symbol="MSFT",
            side="sell",
            ord_type="market",
            order_qty=Decimal(50),
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            cl_ord_id="C2",
            order_id="O2",
            exec_id="E3",
            exec_type="Rejected",
            ord_status="Rejected",
            symbol="MSFT",
            side="sell",
            reject_reason_code="OrderExceedsLimit",
        )
    )
    ingest(
        ParsedMessageEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            msg_type="Reject",
            reject_reason_text="checksum invalid",
        )
    )
    ingest(
        ParsedMessageEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            msg_type="CustomVendorPing",
        )
    )  # unrecognised
    totals = aggregator.snapshot("1m", group_by=())[()].counters
    for metric in sorted(totals):
        print(f"  {metric} = {totals[metric]}")

    _section("MA-02: reject reasons, top-N, unmapped list")
    print("  top_reject_reasons:", top_reject_reasons(aggregator, "1m"))
    print("  unmapped_seen:", reasons.unmapped_seen)

    _section("MA-01: cardinality folding (isolated: 1 metric, cap=3, 5 symbols)")
    cap_demo = MetricsAggregator(
        config=AggregatorConfig(
            metric_dimensions={"orders_submitted": ("symbol",)}, max_label_sets=3
        )
    )
    for i, symbol in enumerate(["GOOG", "TSLA", "AMZN", "NFLX", "META"]):
        cap_demo.ingest_counters(
            NewOrderEvent(
                instance_id="magic-prod-01",
                session_id="MAGIC->EXCH1",
                event_time_utc=now,
                cl_ord_id=f"F{i}",
                symbol=symbol,
                side="buy",
                ord_type="limit",
                order_qty=Decimal(1),
            ),
            {"orders_submitted": Decimal(1)},
        )
    print(f"  cardinality_folded = {cap_demo.cardinality_folded}  (expect 2)")
    by_symbol = cap_demo.snapshot("1m", group_by=("symbol",))
    print(f"  __other__ row: {by_symbol.get(('__other__',))}")

    _section("MA-03: duplicate ack, orphan response, cancel latency")
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now + timedelta(milliseconds=50),
            cl_ord_id="C1",
            order_id="O1",
            exec_id="E1b",
            exec_type="New",
            ord_status="New",
            symbol="AAPL",
            side="buy",
        )
    )  # duplicate ack
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now,
            cl_ord_id="C-UNKNOWN",
            order_id="O9",
            exec_id="E9",
            exec_type="New",
            ord_status="New",
            symbol="AAPL",
            side="buy",
        )
    )  # orphan
    ingest(
        CancelRequestEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now + timedelta(milliseconds=40),
            cl_ord_id="X1",
            orig_cl_ord_id="C1",
            symbol="AAPL",
            side="buy",
            order_qty=Decimal(100),
        )
    )
    ingest(
        ExecutionReportEvent(
            instance_id="magic-prod-01",
            session_id="MAGIC->EXCH1",
            event_time_utc=now + timedelta(milliseconds=55),
            cl_ord_id="X1",
            order_id="O1",
            exec_id="E4",
            exec_type="Canceled",
            ord_status="Canceled",
            symbol="AAPL",
            side="buy",
        )
    )
    print(f"  correlator.stats = {correlator.stats}")

    _section(
        "MA-03: latency histograms (min_sample_size overridden — demo sample is tiny)"
    )
    hist_row = aggregator.snapshot("1m", group_by=())[()].histograms
    for metric in ("ack_latency_ms", "exec_latency_ms", "cancel_latency_ms"):
        hist = hist_row.get(metric)
        if hist is None:
            continue
        p50 = hist.percentile(0.5, min_sample_size=1)
        print(f"  {metric}: count={hist.count} sum_ms={hist.sum_ms} p50={p50}")

    _section("MA-01: window decay — waiting 6s for the 5s window to empty")
    before = aggregator.snapshot("5s", group_by=())
    before_total = before[()].counters if () in before else {}
    print(f"  before: {before_total}")
    time.sleep(6)
    after = aggregator.snapshot("5s", group_by=())
    after_total = after[()].counters if () in after else {}
    print(f"  after:  {after_total}  (decayed to nothing, as expected)")


if __name__ == "__main__":
    main()
