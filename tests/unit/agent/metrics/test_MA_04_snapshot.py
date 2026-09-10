"""MA-04: calculated indicators and snapshot output."""

from datetime import UTC, datetime
from decimal import Decimal

from fixtures import EXPECTED_TOTALS, FakeClock, hand_labelled_events
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_shared.models.parsed_message import NewOrderEvent, ParsedMessageEvent

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_ENVELOPE = dict(instance_id="magic-prod-01", session_id="MAGIC->EXCH1")


def _shared_config() -> AggregatorConfig:
    return AggregatorConfig(
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
    )


def _ingest_all(
    aggregator: MetricsAggregator,
    correlator: LatencyCorrelator,
    events: list[ParsedMessageEvent],
) -> None:
    for event in events:
        aggregator.ingest_counters(event, derive_counters(event))
        correlator.ingest(event)


def test_indicators_computed_from_hand_labelled_fixture() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(config=_shared_config(), clock=clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)
    _ingest_all(aggregator, correlator, hand_labelled_events())

    snap = snapshot(aggregator, "5m", now=_T0)
    row = snap.groups[0]

    assert row.counters == {k: v for k, v in EXPECTED_TOTALS.items()}

    reject_denom = EXPECTED_TOTALS["orders_acked"] + EXPECTED_TOTALS["orders_rejected"]
    assert row.indicators.reject_rate.value == float(
        EXPECTED_TOTALS["orders_rejected"] / reject_denom
    )
    assert row.indicators.reject_rate.denominator == int(reject_denom)
    assert row.indicators.reject_rate.low_confidence is True  # denom(2) < 20

    assert row.indicators.fill_rate.value == float(
        EXPECTED_TOTALS["executions"] / EXPECTED_TOTALS["orders_acked"]
    )
    assert row.indicators.cancel_rate.value == float(
        EXPECTED_TOTALS["orders_canceled"] / EXPECTED_TOTALS["orders_submitted"]
    )

    # Nothing feeds parse_errors/log_lines_read yet — formula-ready, no data.
    assert row.indicators.parse_error_rate.value is None
    assert row.indicators.parse_error_rate.denominator == 0
    assert row.indicators.parse_error_rate.low_confidence is True

    assert row.indicators.throughput == float(EXPECTED_TOTALS["orders_submitted"]) / 300


def test_low_confidence_false_once_denominator_meets_threshold() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(config=_shared_config(), clock=clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)
    _ingest_all(aggregator, correlator, hand_labelled_events())

    snap = snapshot(aggregator, "5m", now=_T0, min_sample_size=2)
    row = snap.groups[0]

    # orders_acked(1) + orders_rejected(1) == 2 >= min_sample_size(2).
    assert row.indicators.reject_rate.low_confidence is False
    assert row.indicators.reject_rate.value == 0.5


def test_ratio_is_null_when_denominator_is_zero() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(config=_shared_config(), clock=clock)
    order = NewOrderEvent(
        **_ENVELOPE,
        event_time_utc=_T0,
        cl_ord_id_hash="ORD-1",
        symbol="AAPL",
        side="buy",
        ord_type="limit",
        order_qty=Decimal(100),
    )
    aggregator.ingest_counters(order, derive_counters(order))

    snap = snapshot(aggregator, "5m", now=_T0)
    row = snap.groups[0]

    # orders_submitted=1, orders_acked=0 -> fillRate denominator is 0.
    assert row.indicators.fill_rate.value is None
    assert row.indicators.fill_rate.denominator == 0
    assert row.indicators.fill_rate.low_confidence is True
    # throughput is not a ratio: still computed from orders_submitted alone.
    assert row.indicators.throughput == 1 / 300


def test_grouped_breakdown_by_symbol() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(config=_shared_config(), clock=clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)
    _ingest_all(aggregator, correlator, hand_labelled_events())

    snap = snapshot(aggregator, "5m", group_by=("symbol",), now=_T0)
    by_symbol = {tuple(g.dimensions.values()): g for g in snap.groups}

    assert by_symbol[("AAPL",)].counters["orders_submitted"] == Decimal(1)
    assert by_symbol[("MSFT",)].counters["orders_submitted"] == Decimal(1)
    assert snap.group_by == ("symbol",)


def test_window_bounds_and_generated_at_use_the_injected_now() -> None:
    aggregator = MetricsAggregator(config=_shared_config(), clock=FakeClock())
    snap = snapshot(aggregator, "5m", now=_T0)

    assert snap.generated_at_utc == _T0
    bounds = snap.window_bounds
    assert bounds.to_utc == _T0
    assert (bounds.to_utc - bounds.from_utc).total_seconds() == 300
    assert snap.window == "5m"


def test_gauges_reflect_pending_orders_and_event_staleness() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(config=_shared_config(), clock=clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)

    order = NewOrderEvent(
        **_ENVELOPE,
        event_time_utc=datetime.fromtimestamp(clock(), tz=UTC),
        cl_ord_id_hash="ORD-STUCK",
        symbol="AAPL",
        side="buy",
        ord_type="limit",
        order_qty=Decimal(100),
    )
    aggregator.ingest_counters(order, derive_counters(order))
    correlator.ingest(order)  # never acked -> stays pending

    clock.advance(12)

    snap = snapshot(aggregator, "5m", correlator=correlator, now=_T0)
    assert snap.gauges.pending_orders == 1
    assert snap.gauges.oldest_pending_age_seconds == 12
    assert snap.gauges.seconds_since_last_event == 12


def test_gauges_are_empty_without_a_correlator() -> None:
    aggregator = MetricsAggregator(config=_shared_config(), clock=FakeClock())
    snap = snapshot(aggregator, "5m", now=_T0)

    assert snap.gauges.pending_orders == 0
    assert snap.gauges.oldest_pending_age_seconds is None
    assert snap.gauges.seconds_since_last_event is None  # nothing ingested yet


def test_latency_summary_present_for_recorded_histograms() -> None:
    clock = FakeClock()
    aggregator = MetricsAggregator(config=_shared_config(), clock=clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)
    _ingest_all(aggregator, correlator, hand_labelled_events())

    snap = snapshot(aggregator, "5m", now=_T0)
    row = snap.groups[0]

    assert "ack_latency_ms" in row.latency
    latency = row.latency["ack_latency_ms"]
    assert latency.count == 1
    assert latency.approximate is True
    # Below the default min_sample_size(20) -> percentiles null, not fabricated.
    assert latency.p50 is None
