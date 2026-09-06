from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fixtures import FakeClock
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_shared.models.parsed_message import NewOrderEvent, ParsedMessageEvent


def make_event(ts: float, **overrides: object) -> ParsedMessageEvent:
    fields: dict[str, object] = {
        "event_time_utc": datetime.fromtimestamp(ts, tz=UTC),
        "instance_id": "magic-prod-01",
        "session_id": "MAGIC->EXCH1",
        "cl_ord_id": "ORD-1",
        "symbol": "AAPL",
        "side": "buy",
        "ord_type": "limit",
        "order_qty": Decimal(100),
    }
    fields.update(overrides)
    return NewOrderEvent(**fields)  # type: ignore[arg-type]


def minimal_aggregator(
    clock: FakeClock, **config_overrides: object
) -> MetricsAggregator:
    config = AggregatorConfig(
        metric_dimensions={"messages_total": ("instance_id",)},
        **config_overrides,  # type: ignore[arg-type]
    )
    return MetricsAggregator(config=config, clock=clock)


def total_count(
    aggregator: MetricsAggregator, window: str, metric: str = "messages_total"
) -> Decimal:
    row = aggregator.snapshot(window, group_by=()).get(())
    if row is None:
        return Decimal(0)
    return row.counters.get(metric, Decimal(0))


def test_10k_events_in_60s_window_returns_correct_count() -> None:
    clock = FakeClock()
    aggregator = minimal_aggregator(clock)

    for _ in range(10_000):
        aggregator.ingest_counters(make_event(clock()), {"messages_total": Decimal(1)})

    assert total_count(aggregator, "1m") == Decimal(10_000)


def test_idle_window_decays_to_zero_after_expiry() -> None:
    clock = FakeClock()
    aggregator = minimal_aggregator(clock)

    for _ in range(10_000):
        aggregator.ingest_counters(make_event(clock()), {"messages_total": Decimal(1)})
    assert total_count(aggregator, "1m") == Decimal(10_000)

    clock.advance(61)

    assert total_count(aggregator, "1m") == Decimal(0)


def test_cardinality_cap_folds_overflow_into_other_and_preserves_total() -> None:
    clock = FakeClock()
    config = AggregatorConfig(
        metric_dimensions={"messages_total": ("symbol",)}, max_label_sets=3
    )
    aggregator = MetricsAggregator(config=config, clock=clock)

    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    for symbol in symbols:
        for _ in range(10):
            aggregator.ingest_counters(
                make_event(clock(), symbol=symbol), {"messages_total": Decimal(1)}
            )

    grouped = aggregator.snapshot("1m", group_by=("symbol",))
    assert len(grouped) == 4  # 3 real labels + __other__
    assert ("__other__",) in grouped

    grouped_total = sum(row.counters["messages_total"] for row in grouped.values())
    assert grouped_total == total_count(aggregator, "1m") == Decimal(50)


def test_cardinality_cap_resets_per_bucket_not_for_process_lifetime() -> None:
    # FR-MET-029: "top-N sketch per bucket" — the admission registry lives on
    # the bucket and clears when the bucket is reused, not on the aggregator
    # for its whole lifetime. A symbol admitted in bucket N can still be
    # admitted on its own merits in a later, unrelated bucket even if bucket
    # N's cap was already full — because a new bucket starts its own count
    # from zero.
    clock = FakeClock()
    config = AggregatorConfig(
        metric_dimensions={"messages_total": ("symbol",)}, max_label_sets=1
    )
    aggregator = MetricsAggregator(config=config, clock=clock)

    aggregator.ingest_counters(
        make_event(clock(), symbol="AAA"), {"messages_total": Decimal(1)}
    )
    aggregator.ingest_counters(
        make_event(clock(), symbol="BBB"), {"messages_total": Decimal(1)}
    )  # folded

    clock.advance(2)  # new 1s bucket

    aggregator.ingest_counters(
        make_event(clock(), symbol="BBB"), {"messages_total": Decimal(1)}
    )

    grouped = aggregator.snapshot("1m", group_by=("symbol",))
    assert grouped[("BBB",)].counters["messages_total"] == Decimal(
        1
    )  # admitted on its own, new bucket
    assert grouped[("__other__",)].counters["messages_total"] == Decimal(
        1
    )  # from the first bucket


def test_snapshot_rejects_group_by_outside_known_dimensions() -> None:
    aggregator = minimal_aggregator(FakeClock())
    with pytest.raises(ValueError, match="known_dimensions|instance_id"):
        aggregator.snapshot("1m", group_by=("nonexistent_dimension",))


def test_ingest_counters_rejects_an_undeclared_metric() -> None:
    aggregator = minimal_aggregator(FakeClock())
    with pytest.raises(KeyError, match="FR-MET-030"):
        aggregator.ingest_counters(
            make_event(1_700_000_000.0), {"undeclared_metric": Decimal(1)}
        )


def test_metric_absent_from_results_when_its_dims_do_not_cover_group_by() -> None:
    # FR-MET-030 in action: a metric whose declared dims don't include the
    # requested group_by dimension is simply absent, not an error.
    clock = FakeClock()
    config = AggregatorConfig(
        metric_dimensions={
            "orders_new": ("symbol",),
            "business_rejects": ("symbol", "reject_reason"),
        }
    )
    aggregator = MetricsAggregator(config=config, clock=clock)

    aggregator.ingest_counters(make_event(clock()), {"orders_new": Decimal(1)})
    aggregator.ingest_counters(
        make_event(clock(), reject_reason_code="PriceExceedsLimit"),
        {"business_rejects": Decimal(1)},
    )

    grouped = aggregator.snapshot("1m", group_by=("symbol", "reject_reason"))
    # orders_new has no reject_reason dimension, so it cannot appear in a
    # result grouped by reject_reason at all.
    assert all("orders_new" not in row.counters for row in grouped.values())
    assert any("business_rejects" in row.counters for row in grouped.values())


def test_cardinality_folded_counts_every_fold_from_either_cap() -> None:
    # FR-MET-029: "values beyond the cap are folded into __other__ and
    # metrics.cardinality_folded is incremented" — an observability signal
    # that folding is actually happening, not just a silent relabel.
    clock = FakeClock()
    config = AggregatorConfig(
        metric_dimensions={"messages_total": ("symbol",)}, max_label_sets=2
    )
    aggregator = MetricsAggregator(config=config, clock=clock)

    for symbol in ("AAA", "BBB", "CCC", "DDD"):  # first 2 admitted, next 2 folded
        aggregator.ingest_counters(
            make_event(clock(), symbol=symbol), {"messages_total": Decimal(1)}
        )

    assert aggregator.cardinality_folded == 2


def test_max_series_per_bucket_caps_total_across_all_metrics() -> None:
    # FR-MET-030: "series count per instance per bucket MUST be capped at
    # maxSeriesPerBucket" — a separate, tighter guard than max_label_sets:
    # two metrics can each be under their own per-metric cap yet still sum
    # past the bucket-wide total.
    clock = FakeClock()
    config = AggregatorConfig(
        metric_dimensions={"metric_a": ("symbol",), "metric_b": ("symbol",)},
        max_label_sets=10,  # generous per-metric cap, not the binding one here
        max_series_per_bucket=3,
    )
    aggregator = MetricsAggregator(config=config, clock=clock)

    aggregator.ingest_counters(
        make_event(clock(), symbol="AAA"), {"metric_a": Decimal(1)}
    )
    aggregator.ingest_counters(
        make_event(clock(), symbol="BBB"), {"metric_a": Decimal(1)}
    )
    aggregator.ingest_counters(
        make_event(clock(), symbol="CCC"), {"metric_b": Decimal(1)}
    )
    # 4th distinct (metric, symbol) series in the same bucket — over the
    # bucket-wide cap of 3, even though metric_b alone is nowhere near 10.
    aggregator.ingest_counters(
        make_event(clock(), symbol="DDD"), {"metric_b": Decimal(1)}
    )

    grouped = aggregator.snapshot("1m", group_by=("symbol",))
    b_series = {
        label: row.counters.get("metric_b", Decimal(0))
        for label, row in grouped.items()
    }
    assert b_series.get(("CCC",)) == Decimal(1)
    assert b_series.get(("DDD",)) is None  # folded, not its own row
    assert b_series.get(("__other__",)) == Decimal(1)
    assert aggregator.cardinality_folded == 1


def test_missing_dimension_value_becomes_unspecified_not_the_string_none() -> None:
    # Regression: symbol/side/ord_type are None on plenty of real messages
    # (admin messages, OrderCancelReject) — _dimension_value() used to
    # stringify that straight to the literal text "None", indistinguishable
    # from a symbol actually named "None".
    clock = FakeClock()
    config = AggregatorConfig(metric_dimensions={"messages_total": ("symbol",)})
    aggregator = MetricsAggregator(config=config, clock=clock)

    event = ParsedMessageEvent(
        event_time_utc=datetime.fromtimestamp(clock(), tz=UTC),
        instance_id="magic-prod-01",
        session_id="MAGIC->EXCH1",
        msg_type="Heartbeat",
    )
    aggregator.ingest_counters(event, {"messages_total": Decimal(1)})

    grouped = aggregator.snapshot("1m", group_by=("symbol",))
    assert grouped[("unspecified",)].counters["messages_total"] == Decimal(1)
    assert ("None",) not in grouped


def test_group_by_multiple_dimensions_respects_the_requested_order() -> None:
    clock = FakeClock()
    config = AggregatorConfig(metric_dimensions={"orders": ("symbol", "side")})
    aggregator = MetricsAggregator(config=config, clock=clock)

    aggregator.ingest_counters(
        make_event(clock(), symbol="AAPL", side="buy"), {"orders": Decimal(1)}
    )

    # group_by asks for the reverse of the metric's own declared dimension
    # order — the result key must follow group_by, not the metric's order.
    grouped = aggregator.snapshot("1m", group_by=("side", "symbol"))
    assert grouped[("buy", "AAPL")].counters["orders"] == Decimal(1)


def test_snapshot_rejects_an_unknown_window_name() -> None:
    aggregator = minimal_aggregator(FakeClock())
    with pytest.raises(ValueError, match="unknown window"):
        aggregator.snapshot("2m", group_by=())


def test_stale_event_is_dropped_even_when_its_ring_slot_collides_with_now() -> None:
    # capacity is 900 buckets @1s (max window / bucket_seconds); an event
    # exactly `capacity` seconds in the past maps to the *same* ring index
    # as "now" (offset % capacity == 0). This specifically proves
    # _get_bucket's "drop, don't corrupt a live slot" comment, rather than
    # testing an old timestamp that happens not to collide.
    clock = FakeClock()
    aggregator = minimal_aggregator(clock)
    capacity = aggregator.config.capacity

    stale_ts = clock() - capacity
    aggregator.ingest_counters(make_event(stale_ts), {"messages_total": Decimal(1)})
    aggregator.ingest_counters(make_event(clock()), {"messages_total": Decimal(1)})

    assert total_count(aggregator, "15m") == Decimal(1)
