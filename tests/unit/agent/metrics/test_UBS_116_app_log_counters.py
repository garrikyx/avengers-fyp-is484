"""UBS-116: Application.log telemetry becomes counters a rule can read,
grouped by signature and bounded by the cardinality caps."""

from datetime import UTC, datetime
from decimal import Decimal

from telemetry_agent.metrics.aggregator import (
    OTHER_LABEL,
    AggregatorConfig,
    MetricsAggregator,
)
from telemetry_agent.metrics.counters import (
    COUNTER_DIMENSIONS,
    ComponentLimiter,
    app_log_counter_dims,
    derive_app_log_counters,
)
from telemetry_agent.parser.applog.telemetry import AppLogTelemetry

T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)


def _tel(
    level: str = "I", component: str = "VS_1", signature: str | None = None
) -> AppLogTelemetry:
    return AppLogTelemetry(
        timestamp="10:00:00.000000",
        thread_id="1",
        level=level,
        component=component,
        message="msg",
        error_signature=signature,
    )


def _aggregator(**config: int) -> MetricsAggregator:
    return MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS), **config),
        clock=lambda: T0.timestamp(),
    )


def _ingest(
    aggregator: MetricsAggregator, tel: AppLogTelemetry, limiter: ComponentLimiter
) -> None:
    aggregator.ingest_agent_counters(
        dims=app_log_counter_dims(
            tel, instance_id="inst", component=limiter.admit(tel.component)
        ),
        counters=derive_app_log_counters(tel),
        at=T0,
    )


def test_info_line_counts_only_as_a_line() -> None:
    assert derive_app_log_counters(_tel(level="I")) == {"app_log_lines": Decimal(1)}


def test_error_and_fatal_levels_count_as_errors() -> None:
    assert "app_log_errors" in derive_app_log_counters(_tel(level="E"))
    assert "app_log_errors" in derive_app_log_counters(_tel(level="F"))
    assert "app_log_errors" not in derive_app_log_counters(_tel(level="W"))


def test_signature_counts_regardless_of_level() -> None:
    counters = derive_app_log_counters(_tel(level="W", signature="out_of_memory"))

    assert counters["app_error_signatures"] == 1
    assert "app_log_errors" not in counters


def test_every_app_log_metric_declares_its_dimensions() -> None:
    tel = _tel(level="F", signature="out_of_memory")
    dims = app_log_counter_dims(tel, instance_id="inst", component="VS_1")

    for metric in derive_app_log_counters(tel):
        assert set(COUNTER_DIMENSIONS[metric]) <= set(dims)


def test_signature_counts_can_be_grouped_by_signature() -> None:
    aggregator = _aggregator()
    limiter = ComponentLimiter()
    for signature in ["out_of_memory"] * 3 + ["db_connection_lost"] + [None] * 2:
        _ingest(aggregator, _tel(level="E", signature=signature), limiter)

    grouped = aggregator.snapshot("1m", group_by=("error_signature",))

    assert {
        label: row.counters["app_error_signatures"] for label, row in grouped.items()
    } == {
        ("out_of_memory",): 3,
        ("db_connection_lost",): 1,
    }
    total = aggregator.snapshot("1m")[()].counters
    assert total["app_log_lines"] == 6
    assert total["app_log_errors"] == 6


def test_component_limiter_folds_past_its_cap() -> None:
    limiter = ComponentLimiter(max_labels=2)

    assert [limiter.admit(c) for c in ["A", "B", "C", "A", "D"]] == [
        "A",
        "B",
        OTHER_LABEL,
        "A",
        OTHER_LABEL,
    ]
    assert limiter.folded == 2


def test_component_flood_cannot_crowd_out_other_series() -> None:
    # A per-bucket series budget the unbounded components alone would exhaust.
    aggregator = _aggregator(max_series_per_bucket=20)
    limiter = ComponentLimiter(max_labels=5)
    for i in range(100):
        _ingest(aggregator, _tel(level="E", component=f"VS_{i}"), limiter)

    by_component = aggregator.snapshot("1m", group_by=("component",))
    assert len(by_component) == 6  # 5 admitted + __other__
    assert by_component[(OTHER_LABEL,)].counters["app_log_errors"] == 95

    # Budget left for the next metric: a parser counter still gets its own row.
    aggregator.ingest_agent_counters(
        dims={"instance_id": "inst"}, counters={"log_lines_read": Decimal(1)}, at=T0
    )
    assert aggregator.cardinality_folded == 0
