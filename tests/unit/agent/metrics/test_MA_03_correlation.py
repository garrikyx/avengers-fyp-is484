from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fixtures import FakeClock
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_shared.models.parsed_message import (
    CancelRejectEvent,
    CancelReplaceEvent,
    CancelRequestEvent,
    ExecutionReportEvent,
    NewOrderEvent,
)

_CLOCK_START = 1_700_000_000.0
# Derived from the same epoch FakeClock starts at below — the correlator
# compares event timestamps against the *clock*'s notion of "now", so both
# must be on the same timeline or TTL/decay math silently never triggers.
_T0 = datetime.fromtimestamp(_CLOCK_START, tz=UTC)
_ENVELOPE = dict(instance_id="magic-prod-01", session_id="MAGIC->EXCH1")


def new_order(cl_ord_id: str, at: datetime = _T0, **overrides: object) -> NewOrderEvent:
    fields: dict[str, object] = {
        **_ENVELOPE,
        "event_time_utc": at,
        "cl_ord_id": cl_ord_id,
        "symbol": "AAPL",
        "side": "buy",
        "ord_type": "limit",
        "order_qty": Decimal(100),
    }
    fields.update(overrides)
    return NewOrderEvent(**fields)  # type: ignore[arg-type]


def ack(cl_ord_id: str, at: datetime, **overrides: object) -> ExecutionReportEvent:
    fields: dict[str, object] = {
        **_ENVELOPE,
        "event_time_utc": at,
        "cl_ord_id": cl_ord_id,
        "order_id": f"OID-{cl_ord_id}",
        "exec_id": f"EXEC-{cl_ord_id}-ack",
        "exec_type": "New",
        "ord_status": "New",
        "symbol": "AAPL",
        "side": "buy",
    }
    fields.update(overrides)
    return ExecutionReportEvent(**fields)  # type: ignore[arg-type]


def cancel_request(
    cl_ord_id: str, orig_cl_ord_id: str, at: datetime = _T0
) -> CancelRequestEvent:
    return CancelRequestEvent(
        **_ENVELOPE,
        event_time_utc=at,
        cl_ord_id=cl_ord_id,
        orig_cl_ord_id=orig_cl_ord_id,
        symbol="AAPL",
        side="buy",
        order_qty=Decimal(100),
    )


def cancel_replace_request(
    cl_ord_id: str, orig_cl_ord_id: str, at: datetime = _T0
) -> CancelReplaceEvent:
    return CancelReplaceEvent(
        **_ENVELOPE,
        event_time_utc=at,
        cl_ord_id=cl_ord_id,
        orig_cl_ord_id=orig_cl_ord_id,
        symbol="AAPL",
        side="buy",
        ord_type="limit",
        order_qty=Decimal(100),
    )


def replaced(cl_ord_id: str, at: datetime) -> ExecutionReportEvent:
    return ExecutionReportEvent(
        **_ENVELOPE,
        event_time_utc=at,
        cl_ord_id=cl_ord_id,
        order_id=f"OID-{cl_ord_id}",
        exec_id=f"EXEC-{cl_ord_id}-replaced",
        exec_type="Replaced",
        ord_status="Replaced",
        symbol="AAPL",
        side="buy",
    )


def cancel_confirmed(cl_ord_id: str, at: datetime) -> ExecutionReportEvent:
    return ExecutionReportEvent(
        **_ENVELOPE,
        event_time_utc=at,
        cl_ord_id=cl_ord_id,
        order_id=f"OID-{cl_ord_id}",
        exec_id=f"EXEC-{cl_ord_id}-cxl",
        exec_type="Canceled",
        ord_status="Canceled",
        symbol="AAPL",
        side="buy",
    )


def cancel_rejected(
    cl_ord_id: str, orig_cl_ord_id: str, at: datetime
) -> CancelRejectEvent:
    return CancelRejectEvent(
        **_ENVELOPE,
        event_time_utc=at,
        cl_ord_id=cl_ord_id,
        orig_cl_ord_id=orig_cl_ord_id,
    )


def build() -> tuple[MetricsAggregator, LatencyCorrelator, FakeClock]:
    clock = FakeClock()
    aggregator = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(LATENCY_DIMENSIONS)), clock=clock
    )
    correlator = LatencyCorrelator(aggregator, clock=clock)
    return aggregator, correlator, clock


def test_normal_ack_records_latency() -> None:
    aggregator, correlator, _clock = build()

    correlator.ingest(new_order("ORD-1", at=_T0))
    correlator.ingest(ack("ORD-1", at=_T0 + timedelta(milliseconds=42)))

    grouped = aggregator.snapshot("1m", group_by=())
    hist = grouped[()].histograms["ack_latency_ms"]
    assert hist.count == 1
    assert hist.sum_ms == Decimal(42)
    assert correlator.stats.unmatched_orders == 0
    assert correlator.stats.orphan_responses == 0
    assert correlator.stats.latency_anomalies == 0


def test_missing_ack_evicted_by_ttl_counts_as_unmatched_not_zero_latency() -> None:
    aggregator, correlator, clock = build()

    correlator.ingest(new_order("ORD-1", at=_T0))
    clock.advance(15 * 60 + 1)  # past the default 15m TTL
    correlator.tick()

    assert correlator.stats.unmatched_orders == 1
    assert correlator.stats.ttl_evictions == 1
    grouped = aggregator.snapshot("15m", group_by=())
    assert grouped == {}  # no latency sample was ever recorded, not a 0


def test_duplicate_ack_is_not_recorded_twice() -> None:
    aggregator, correlator, _clock = build()

    correlator.ingest(new_order("ORD-1", at=_T0))
    correlator.ingest(ack("ORD-1", at=_T0 + timedelta(milliseconds=10)))
    correlator.ingest(ack("ORD-1", at=_T0 + timedelta(milliseconds=20)))  # duplicate

    grouped = aggregator.snapshot("1m", group_by=())
    hist = grouped[()].histograms["ack_latency_ms"]
    assert hist.count == 1
    assert hist.sum_ms == Decimal(10)
    # a duplicate is a silent no-op, not an anomaly
    assert correlator.stats.latency_anomalies == 0


def test_response_with_no_matching_order_is_an_orphan() -> None:
    aggregator, correlator, _clock = build()

    correlator.ingest(ack("ORD-UNKNOWN", at=_T0))

    assert correlator.stats.orphan_responses == 1
    assert aggregator.snapshot("1m", group_by=()) == {}


def test_negative_latency_from_a_skewed_transact_time_is_an_anomaly_not_zero() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(LATENCY_DIMENSIONS)), clock=clock
    )
    correlator = LatencyCorrelator(
        aggregator, clock=clock, timestamp_source="transact_time"
    )

    correlator.ingest(new_order("ORD-1", at=_T0, transact_time_utc=_T0))
    # response's transact_time is *before* the order's — a skewed/bogus clock,
    # not a real negative wait
    correlator.ingest(
        ack(
            "ORD-1",
            at=_T0 + timedelta(milliseconds=5),
            transact_time_utc=_T0 - timedelta(milliseconds=100),
        )
    )

    assert correlator.stats.latency_anomalies == 1
    assert aggregator.snapshot("1m", group_by=()) == {}


def test_first_fill_latency_uses_the_orders_own_first_seen_time() -> None:
    aggregator, correlator, _clock = build()

    correlator.ingest(new_order("ORD-1", at=_T0))
    correlator.ingest(ack("ORD-1", at=_T0 + timedelta(milliseconds=5)))
    correlator.ingest(
        ack(
            "ORD-1",
            at=_T0 + timedelta(milliseconds=30),
            exec_type="Trade",
            ord_status="Filled",
            last_qty=Decimal(100),
        )
    )

    grouped = aggregator.snapshot("1m", group_by=())
    assert grouped[()].histograms["ack_latency_ms"].sum_ms == Decimal(5)
    assert grouped[()].histograms["exec_latency_ms"].sum_ms == Decimal(30)


def test_cancel_success_records_cancel_latency_not_ack_latency() -> None:
    # spec 004 §4.4: cancel_latency_ms is 35=F -> 35=8 Canceled or 35=9 — a
    # distinct histogram from ack_latency_ms, which is scoped to 35=D only.
    aggregator, correlator, _clock = build()

    correlator.ingest(new_order("ORD-1", at=_T0))
    correlator.ingest(ack("ORD-1", at=_T0 + timedelta(milliseconds=5)))
    correlator.ingest(
        cancel_request(
            "ORD-2", orig_cl_ord_id="ORD-1", at=_T0 + timedelta(milliseconds=10)
        )
    )
    correlator.ingest(cancel_confirmed("ORD-2", at=_T0 + timedelta(milliseconds=25)))

    grouped = aggregator.snapshot("1m", group_by=())
    row = grouped[()]
    assert row.histograms["cancel_latency_ms"].sum_ms == Decimal(15)
    # the cancel confirmation must not be miscounted as an ack for ORD-1's
    # ack_latency_ms — only the one real ack from earlier is in there
    assert row.histograms["ack_latency_ms"].count == 1
    assert row.histograms["ack_latency_ms"].sum_ms == Decimal(5)


def test_cancel_rejected_via_35_9_records_cancel_latency() -> None:
    aggregator, correlator, _clock = build()

    correlator.ingest(new_order("ORD-1", at=_T0))
    correlator.ingest(
        cancel_request(
            "ORD-2", orig_cl_ord_id="ORD-1", at=_T0 + timedelta(milliseconds=10)
        )
    )
    correlator.ingest(
        cancel_rejected(
            "ORD-2", orig_cl_ord_id="ORD-1", at=_T0 + timedelta(milliseconds=18)
        )
    )

    grouped = aggregator.snapshot("1m", group_by=())
    assert grouped[()].histograms["cancel_latency_ms"].sum_ms == Decimal(8)
    assert correlator.stats.orphan_responses == 0


def test_cancel_reject_with_no_matching_request_is_an_orphan() -> None:
    aggregator, correlator, _clock = build()

    correlator.ingest(cancel_rejected("ORD-UNKNOWN", orig_cl_ord_id="ORD-0", at=_T0))

    assert correlator.stats.orphan_responses == 1
    assert aggregator.snapshot("1m", group_by=()) == {}


def test_cancel_replace_request_is_also_a_cancel_origin() -> None:
    # _CANCEL_ORIGIN_MSG_TYPES covers both OrderCancelRequest (35=F, exercised
    # above) and OrderCancelReplaceRequest (35=G) — only 35=F was exercised
    # elsewhere in this file.
    aggregator, correlator, _clock = build()

    correlator.ingest(new_order("ORD-1", at=_T0))
    correlator.ingest(ack("ORD-1", at=_T0 + timedelta(milliseconds=5)))
    correlator.ingest(
        cancel_replace_request(
            "ORD-2", orig_cl_ord_id="ORD-1", at=_T0 + timedelta(milliseconds=10)
        )
    )
    correlator.ingest(cancel_confirmed("ORD-2", at=_T0 + timedelta(milliseconds=25)))

    grouped = aggregator.snapshot("1m", group_by=())
    assert grouped[()].histograms["cancel_latency_ms"].sum_ms == Decimal(15)


def test_replace_confirmation_itself_records_no_latency() -> None:
    # OrderContext's own docstring: a replace's ExecType=Replaced
    # confirmation is a deliberate no-op — spec defines no histogram for it,
    # so nothing should be recorded even though the order *is* matched
    # (not an orphan).
    aggregator, correlator, _clock = build()

    correlator.ingest(cancel_replace_request("ORD-2", orig_cl_ord_id="ORD-1", at=_T0))
    correlator.ingest(replaced("ORD-2", at=_T0 + timedelta(milliseconds=10)))

    assert aggregator.snapshot("1m", group_by=()) == {}
    assert correlator.stats.orphan_responses == 0
    assert correlator.stats.latency_anomalies == 0


def test_hard_cap_eviction_evicts_the_oldest_and_counts_as_unmatched() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(LATENCY_DIMENSIONS)), clock=clock
    )
    correlator = LatencyCorrelator(aggregator, clock=clock, max_entries=2)

    correlator.ingest(new_order("ORD-1", at=_T0))
    correlator.ingest(new_order("ORD-2", at=_T0 + timedelta(milliseconds=1)))
    # 3rd tracked order over a cap of 2 evicts ORD-1, the oldest by first_seen_at
    correlator.ingest(new_order("ORD-3", at=_T0 + timedelta(milliseconds=2)))

    assert correlator.stats.cap_evictions == 1
    assert correlator.stats.unmatched_orders == 1

    # ORD-1 really was evicted, not just flagged: its own ack now finds nothing
    correlator.ingest(ack("ORD-1", at=_T0 + timedelta(milliseconds=3)))
    assert correlator.stats.orphan_responses == 1

    # "oldest-first" means ORD-3 (the newest) must still be tracked
    correlator.ingest(ack("ORD-3", at=_T0 + timedelta(milliseconds=4)))
    assert correlator.stats.orphan_responses == 1  # unchanged: ORD-3 matched


def test_implausibly_large_latency_is_an_anomaly_not_recorded() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(LATENCY_DIMENSIONS)), clock=clock
    )
    correlator = LatencyCorrelator(
        aggregator, clock=clock, max_plausible_ms=Decimal(1000)
    )

    correlator.ingest(new_order("ORD-1", at=_T0))
    # 5000ms > the configured 1000ms plausibility ceiling — positive, unlike
    # the skewed-clock anomaly test above, but still implausible
    correlator.ingest(ack("ORD-1", at=_T0 + timedelta(seconds=5)))

    assert correlator.stats.latency_anomalies == 1
    assert aggregator.snapshot("1m", group_by=()) == {}


def test_transact_time_source_computes_latency_from_transact_time() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(LATENCY_DIMENSIONS)), clock=clock
    )
    correlator = LatencyCorrelator(
        aggregator, clock=clock, timestamp_source="transact_time"
    )
    assert correlator.timestamp_source == "transact_time"

    correlator.ingest(new_order("ORD-1", at=_T0, transact_time_utc=_T0))
    # event_time is 10s later, but transact_time is only 42ms later — the
    # correlator must use the latter when configured to.
    correlator.ingest(
        ack(
            "ORD-1",
            at=_T0 + timedelta(seconds=10),
            transact_time_utc=_T0 + timedelta(milliseconds=42),
        )
    )

    grouped = aggregator.snapshot("1m", group_by=())
    assert grouped[()].histograms["ack_latency_ms"].sum_ms == Decimal(42)
