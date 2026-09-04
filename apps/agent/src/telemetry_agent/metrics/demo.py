"""Runnable, narrated demo of the Metrics Aggregator epic (MA-01/02/03).

    uv run python -m telemetry_agent.metrics.demo

Feeds a small, hand-built set of synthetic FIX-derived events through the
real ingest paths (no Parser Engine involved — it doesn't extract fields
yet, so events are constructed here the same way the tests do) and narrates
each step: what business event is happening, which piece of the
implementation it exercises, and what the resulting numbers mean.

Six scenarios, run in order, all on one shared aggregator + correlator:
  1. MA-01 + MA-02 — an order's lifecycle turns into counters
  2. MA-02          — reject-reason normalisation, top-N, unmapped list
  3. MA-01          — cardinality cap folds overflow into __other__
  4. MA-03          — correlation: duplicate ack, orphan, cancel latency
  5. MA-03          — latency histograms / percentiles
  6. MA-01          — window decay (data ages out of a short window)

Nothing here is asserted — it's meant to be read and narrated aloud, not
grepped.
"""

from __future__ import annotations

import textwrap
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

TOTAL_SCENARIOS = 6


def _wrap(text: str, indent: int) -> None:
    pad = " " * indent
    for line in textwrap.wrap(" ".join(text.split()), width=78 - indent):
        print(f"{pad}{line}")


def _banner(n: int, title: str, ticket: str) -> None:
    rule = "=" * 78
    print(f"\n{rule}")
    print(f"SCENARIO {n}/{TOTAL_SCENARIOS} — {title}  [{ticket}]")
    print(rule)


def _story(text: str) -> None:
    print("\nSTORY")
    _wrap(text, 2)


def _implementation(text: str) -> None:
    print("\nIMPLEMENTATION")
    _wrap(text, 2)


def _watch(text: str) -> None:
    print("\nWATCH FOR")
    _wrap(text, 2)


def _result(label: str) -> None:
    print(f"\nRESULT — {label}")


def _line(metric: str, value: object, note: str = "") -> None:
    left = f"  {metric} = {value}"
    print(f"{left:<40} # {note}" if note else left)


def main() -> None:
    reasons = ReasonNormalizer()
    config = AggregatorConfig(
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS},
        windows={"5s": 5, "1m": 60},
        max_label_sets=3,  # deliberately small, so folding is visible in scenario 3
    )
    aggregator = MetricsAggregator(config=config, resolve_reject_reason=reasons.resolve)
    correlator = LatencyCorrelator(aggregator, ttl_seconds=5)

    def ingest(event: ParsedMessageEvent) -> None:
        correlator.ingest(event)
        aggregator.ingest_counters(event, derive_counters(event))

    now = datetime.now(tz=UTC)

    print("=" * 78)
    print("METRICS AGGREGATOR DEMO — MA-01 store / MA-02 counters / MA-03 correlation")
    print("=" * 78)
    _wrap(
        "One FIX session, MAGIC->EXCH1, on instance magic-prod-01. The aggregator "
        "is configured with two windows: a real 1m window, plus a 5s window that "
        "exists only so window decay is visible live in scenario 6. The "
        "cardinality cap (max_label_sets) is set to 3 instead of the production "
        "default of 5,000, so scenario 3's folding is visible without needing "
        "thousands of symbols.",
        0,
    )

    # ------------------------------------------------------------------
    _banner(1, "A trader's order lifecycle becomes counters", "MA-01 store + MA-02 counters")
    _story(
        "A trader submits a limit buy for 100 AAPL. 8ms later the exchange acks "
        "it (ExecType=New). 22ms after that it fills completely (Trade, "
        "leaves_qty=0). At the same time, a second trader's market sell for 50 "
        "MSFT is rejected by the exchange (OrderExceedsLimit), a FIX "
        "session-level Reject comes in for a bad checksum, and one message of a "
        "type this system doesn't recognise arrives too."
    )
    _implementation(
        "Each event goes through counters.derive_counters(event) to get a "
        "sparse dict of metric -> amount, then aggregator.ingest_counters() "
        "resolves the declared dimensions for that metric, builds a label "
        "tuple, and writes into the shared ring buffer — MA-01's store."
    )
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
    _result("1m window, all 7 events summed")
    notes = {
        "messages_total": "every event counts here, recognised or not",
        "orders_submitted": "the AAPL buy (C1) + the MSFT sell (C2)",
        "order_qty": "100 (AAPL) + 50 (MSFT)",
        "orders_acked": "only AAPL got an ExecType=New ack",
        "executions": "the AAPL Trade fill",
        "executed_qty": "100 shares filled on AAPL",
        "fills_full": "leaves_qty=0 on that fill",
        "orders_rejected": "the MSFT sell, ExecType=Rejected",
        "session_rejects": "the 35=3 Reject, checksum invalid",
        "rejects_total": "orders_rejected + session_rejects, kept separate above",
        "unclassified_messages": "CustomVendorPing isn't in KNOWN_MSG_TYPES",
    }
    for metric in sorted(totals):
        _line(metric, totals[metric], notes.get(metric, ""))

    # ------------------------------------------------------------------
    _banner(2, "Turning raw reject reasons into canonical labels", "MA-02 reject reasons")
    _story(
        "Two rejects happened above: the MSFT sell carried a known reason code "
        "(OrderExceedsLimit), and the session Reject only had free text "
        "('checksum invalid') that isn't in the canonical reason map."
    )
    _implementation(
        "ReasonNormalizer.resolve() is the dimension resolver the aggregator "
        "calls for the 'reject_reason' dimension. Known codes pass through, "
        "identity-mapped from spec 003's canonical names; anything unmapped "
        "folds to the label 'Other' and gets recorded — truncated, capped at "
        "50 entries — in unmapped_seen, so the map can be extended from what's "
        "actually seen in production."
    )
    _result("top_reject_reasons + unmapped_seen")
    print(f"  top_reject_reasons: {top_reject_reasons(aggregator, '1m')}")
    print(f"  unmapped_seen:      {reasons.unmapped_seen}")
    _watch(
        "The raw text 'checksum invalid' never becomes the dimension value "
        "itself — only the label 'Other' does. The raw text only shows up in "
        "unmapped_seen, truncated, for someone to review and extend the map "
        "later."
    )

    # ------------------------------------------------------------------
    _banner(3, "Protecting the store from cardinality blowup", "MA-01 cardinality cap")
    _story(
        "Five different, mostly illiquid symbols trade in the same second. In "
        "production the cap is 5,000 distinct label-sets per metric (plus a "
        "tighter 2,000-per-bucket total across all metrics) — high enough that "
        "this never bites in practice. For this scenario only, a fresh "
        "aggregator is configured with the cap turned down to 3, so the "
        "folding behaviour is actually visible."
    )
    _implementation(
        "_admit_label() checks the per-metric admitted-label set and the "
        "bucket-wide total before accepting a new label; once either cap is "
        "hit, the label is replaced with the '__other__' sentinel and "
        "cardinality_folded increments — so the folding is itself an "
        "observable metric, not silent data loss."
    )
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
    by_symbol = cap_demo.snapshot("1m", group_by=("symbol",))
    _result("5 symbols submitted, cap=3")
    _line(
        "cardinality_folded",
        cap_demo.cardinality_folded,
        "expected 2 — GOOG/TSLA/AMZN admitted, NFLX/META folded",
    )
    _line("__other__ row", by_symbol.get(("__other__",)), "NFLX + META summed under one label")

    # ------------------------------------------------------------------
    _banner(4, "Correlating responses back to the right order", "MA-03 correlation")
    _story(
        "Three things happen next, each exercising a different edge case: the "
        "exchange retransmits the same ack for the AAPL order (a duplicate); "
        "an ExecutionReport arrives for an order (C-UNKNOWN) this system never "
        "saw submitted — e.g. lost on reconnect; and, independently, a cancel "
        "request (X1, referencing the original order C1) is confirmed by the "
        "exchange 15ms later, exercising the cancel-latency path on its own "
        "order context."
    )
    _implementation(
        "LatencyCorrelator.ingest() tracks open orders by (session_id, "
        "cl_ord_id), routes each response by the tracked entry's own "
        "origin_msg_type (not the incoming message's type), and guards "
        "ack/fill/cancel with a once-only flag so a retransmit is a silent "
        "no-op rather than a second latency sample. No tracked entry at all "
        "-> orphan_responses, never a fake zero latency."
    )
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
    stats = correlator.stats
    _result("correlator.stats after all of the above")
    _line("ttl_evictions", stats.ttl_evictions, "none expired yet (ttl_seconds=5 for this demo)")
    _line("cap_evictions", stats.cap_evictions, "max_entries never hit")
    _line("unmatched_orders", stats.unmatched_orders, "ttl_evictions + cap_evictions")
    _line("orphan_responses", stats.orphan_responses, "the C-UNKNOWN ExecutionReport")
    _line(
        "latency_anomalies",
        stats.latency_anomalies,
        "none here — see MA-03 AC5 for the negative/implausible-latency path",
    )
    _watch(
        "The duplicate ack doesn't appear anywhere in these stats — it's "
        "neither an anomaly nor an orphan, just silently ignored via the "
        "ack_recorded flag."
    )

    # ------------------------------------------------------------------
    _banner(5, "Millisecond deltas become latency percentiles", "MA-03 histograms")
    _story(
        "Three response times were captured above: 8ms from the AAPL order to "
        "its ack, 30ms from the same order to its fill, and 15ms from the "
        "cancel request to its confirmation."
    )
    _implementation(
        "Histogram.record() buckets each sample into fixed boundaries (1, 5, "
        "10, 25, 50, 100, 250, 500, 1000, 5000ms, +Inf) in constant memory per "
        "series. percentile() linearly interpolates within the bucket holding "
        "the target rank. In production it refuses to answer below 20 samples "
        "(FR-QRY-007, avoids a misleadingly precise number) — here "
        "min_sample_size is overridden to 1, since the whole demo only "
        "produces one sample per histogram."
    )
    hist_row = aggregator.snapshot("1m", group_by=())[()].histograms
    _result("p50 per latency metric")
    for metric in ("ack_latency_ms", "exec_latency_ms", "cancel_latency_ms"):
        hist = hist_row.get(metric)
        if hist is None:
            continue
        p50 = hist.percentile(0.5, min_sample_size=1)
        _line(metric, f"count={hist.count} sum_ms={hist.sum_ms} p50={p50}")

    # ------------------------------------------------------------------
    _banner(6, "Old data actually ages out of a window", "MA-01 window decay")
    _story(
        "In production, windows are 1m/5m/15m over a 1s-bucket ring buffer. "
        "This aggregator is also tracking a 5s window purely so decay is "
        "visible live, without a real multi-minute wait. Everything ingested "
        "above already sits in the same handful of one-second buckets, all of "
        "which are about to fall outside that 5s window."
    )
    _implementation(
        "tick() runs on every ingest/snapshot call — not yet an independent "
        "timer (a known gap, see the implementation review) — and clears any "
        "ring slot whose bucket_start has fallen outside the retained window. "
        "snapshot() calls tick() itself, so a query never returns stale data "
        "even if nothing has been ingested recently."
    )
    before = aggregator.snapshot("5s", group_by=())
    before_total = before[()].counters if () in before else {}
    _result("5s window, right now")
    for metric in sorted(before_total):
        _line(metric, before_total[metric])
    print(
        "\n  ...waiting 6s for the 5s window to fully lapse. Good moment to "
        "mention\n  that a real deployment drives tick() from the agent's own "
        "runtime timer,\n  not a sleep() — this demo just doesn't have one to "
        "hook into."
    )
    time.sleep(6)
    after = aggregator.snapshot("5s", group_by=())
    after_total = after[()].counters if () in after else {}
    _result("5s window, 6s later")
    if after_total:
        for metric in sorted(after_total):
            _line(metric, after_total[metric])
    else:
        print("  (empty — every bucket that held this data has aged out, as expected)")

    print("\n" + "=" * 78)
    print("End of demo. MA-01 (store/decay/cardinality), MA-02 (counters/reasons),")
    print("and MA-03 (correlation/latency) all ran on one shared aggregator + ")
    print("correlator instance.")
    print("Mechanics:    docs/plan/ma-epic-implementation-summary.md")
    print("Known gaps:   docs/plan/ma-epic-implementation-review.md")
    print("=" * 78)


if __name__ == "__main__":
    main()
