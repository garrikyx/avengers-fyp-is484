"""Cross-cutting: MA-02 (counters.derive_counters) and MA-03
(correlation.LatencyCorrelator) writing into one *shared* MetricsAggregator
instance, the way a real agent runtime would drive them.

Every other test file in this package builds its own aggregator scoped to
just one producer's dimension table (COUNTER_DIMENSIONS or
LATENCY_DIMENSIONS alone) — so the "one shared store, two producers"
architecture claim behind MetricsAggregator itself was never previously
exercised with both producers live at once.
"""

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

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_ENVELOPE = dict(instance_id="magic-prod-01", session_id="MAGIC->EXCH1")


def _ingest(
    aggregator: MetricsAggregator,
    correlator: LatencyCorrelator,
    event: ParsedMessageEvent,
) -> None:
    aggregator.ingest_counters(event, derive_counters(event))
    correlator.ingest(event)


def _fixed_now() -> float:
    return _T0.timestamp()  # nothing in this test ages out, so "now" never moves


def test_counters_and_latency_coexist_on_one_shared_aggregator() -> None:
    config = AggregatorConfig(
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
    )
    aggregator = MetricsAggregator(config=config, clock=_fixed_now)
    correlator = LatencyCorrelator(aggregator, clock=_fixed_now)

    new_order = NewOrderEvent(
        **_ENVELOPE,
        event_time_utc=_T0,
        cl_ord_id="ORD-1",
        symbol="AAPL",
        side="buy",
        ord_type="limit",
        order_qty=Decimal(100),
    )
    ack = ExecutionReportEvent(
        **_ENVELOPE,
        event_time_utc=_T0 + timedelta(milliseconds=42),
        cl_ord_id="ORD-1",
        order_id="OID-1",
        exec_id="EXEC-1",
        exec_type="New",
        ord_status="New",
        symbol="AAPL",
        side="buy",
    )

    _ingest(aggregator, correlator, new_order)
    _ingest(aggregator, correlator, ack)

    row = aggregator.snapshot("1m", group_by=())[()]
    # MA-02's counter and MA-03's histogram both land on the same row of the
    # same snapshot() call — one store, not two separate ones.
    assert row.counters["orders_submitted"] == Decimal(1)
    assert row.counters["orders_acked"] == Decimal(1)
    assert row.histograms["ack_latency_ms"].count == 1
    assert row.histograms["ack_latency_ms"].sum_ms == Decimal(42)
