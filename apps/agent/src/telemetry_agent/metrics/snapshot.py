"""MA-04: calculated indicators and snapshot output.

Wraps the already-tested `MetricsAggregator.snapshot()` (MA-01) with the
layer its two real consumers need: the Rule Engine (alert evaluation) and the
Backend Publisher. Nothing here mutates aggregator/correlator state — this is
a pure read-and-compute path, so it can never block ingest.

Field names, ratio formulas, and the `null`-on-zero-denominator rule follow
spec 004 §4.5 verbatim. The output shape (`telemetry_shared.models.metrics.
MetricsSnapshot`) mirrors the backend's `POST /telemetry/query/metrics`
response (spec 007 §3).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_agent.metrics.aggregator import MetricsAggregator
from telemetry_agent.metrics.correlation import LatencyCorrelator
from telemetry_agent.metrics.histogram import DEFAULT_MIN_SAMPLE_SIZE, Histogram
from telemetry_shared.models.metrics import (
    Gauges,
    Indicator,
    Indicators,
    LatencySummary,
    MetricsGroup,
    MetricsSnapshot,
    WindowBounds,
)

DEFAULT_PERCENTILES: tuple[int, ...] = (50, 95, 99)


@dataclass(slots=True, frozen=True)
class _RatioDef:
    name: str
    numerator: str
    denominator: tuple[str, ...]


# spec 004 §4.5's own formulas, verbatim. `parse_error_rate`'s counters
# (`parse_errors`, `log_lines_read`) have no producer yet — nothing in
# counters.py or the (unbuilt) Log Monitor emits them — so this ratio will
# read as `value=None, low_confidence=True` until that wiring lands. Kept
# here now so the Rule Engine's contract doesn't need to change when it does.
_RATIO_DEFS: tuple[_RatioDef, ...] = (
    _RatioDef("reject_rate", "orders_rejected", ("orders_acked", "orders_rejected")),
    _RatioDef("fill_rate", "executions", ("orders_acked",)),
    _RatioDef("cancel_rate", "orders_canceled", ("orders_submitted",)),
    _RatioDef("parse_error_rate", "parse_errors", ("log_lines_read",)),
)


def _compute_ratio(
    counters: dict[str, Decimal], ratio: _RatioDef, min_sample_size: int
) -> Indicator:
    numerator = counters.get(ratio.numerator, Decimal(0))
    denominator = sum(
        (counters.get(dim, Decimal(0)) for dim in ratio.denominator), Decimal(0)
    )
    if denominator == 0:
        return Indicator(value=None, denominator=0, low_confidence=True)
    return Indicator(
        value=float(numerator / denominator),
        denominator=int(denominator),
        low_confidence=denominator < min_sample_size,
    )


def _compute_indicators(
    counters: dict[str, Decimal], *, min_sample_size: int, window_seconds: int
) -> Indicators:
    ratios = {
        ratio.name: _compute_ratio(counters, ratio, min_sample_size)
        for ratio in _RATIO_DEFS
    }
    throughput = float(counters.get("orders_submitted", Decimal(0))) / window_seconds
    return Indicators(
        reject_rate=ratios["reject_rate"],
        fill_rate=ratios["fill_rate"],
        cancel_rate=ratios["cancel_rate"],
        parse_error_rate=ratios["parse_error_rate"],
        throughput=throughput,
    )


def _build_latency_summary(
    histogram: Histogram, *, percentiles: Sequence[int], min_sample_size: int
) -> LatencySummary:
    values = {
        p: histogram.percentile(p / 100, min_sample_size=min_sample_size)
        for p in percentiles
    }
    avg = float(histogram.sum_ms / histogram.count) if histogram.count > 0 else None
    return LatencySummary(
        p50=float(values[50]) if 50 in values and values[50] is not None else None,
        p95=float(values[95]) if 95 in values and values[95] is not None else None,
        p99=float(values[99]) if 99 in values and values[99] is not None else None,
        avg=avg,
        count=histogram.count,
    )


def _build_gauges(
    aggregator: MetricsAggregator, correlator: LatencyCorrelator | None
) -> Gauges:
    if correlator is None:
        pending_orders = 0
        oldest_pending_age_seconds = None
    else:
        pending_orders = correlator.pending_order_count()
        oldest_pending_age_seconds = correlator.oldest_pending_age_seconds()
    return Gauges(
        pending_orders=pending_orders,
        oldest_pending_age_seconds=oldest_pending_age_seconds,
        seconds_since_last_event=aggregator.seconds_since_last_event(),
    )


def snapshot(
    aggregator: MetricsAggregator,
    window: str,
    group_by: Sequence[str] = (),
    *,
    correlator: LatencyCorrelator | None = None,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
    now: datetime | None = None,
) -> MetricsSnapshot:
    """Serialisable, per-window snapshot: counters, computed indicators,
    latency summaries, grouped breakdowns, window bounds, and generation
    time — the one contract the Rule Engine and Backend Publisher both
    consume.

    Pure read + arithmetic over `aggregator.snapshot()` (which does the
    window/group_by validation this deliberately doesn't repeat) — no I/O,
    no locks, so this can never block a concurrent `ingest_counters`/
    `observe_latency` call.
    """
    group_by = tuple(group_by)
    rows = aggregator.snapshot(window, group_by)
    window_seconds = aggregator.config.windows[window]
    now = now or datetime.now(UTC)

    groups = [
        MetricsGroup(
            dimensions=dict(zip(group_by, label, strict=True)),
            counters=row.counters,
            indicators=_compute_indicators(
                row.counters,
                min_sample_size=min_sample_size,
                window_seconds=window_seconds,
            ),
            latency={
                metric: _build_latency_summary(
                    hist, percentiles=percentiles, min_sample_size=min_sample_size
                )
                for metric, hist in row.histograms.items()
            },
        )
        for label, row in rows.items()
    ]

    return MetricsSnapshot(
        window=window,
        window_bounds=WindowBounds(
            from_utc=now - timedelta(seconds=window_seconds), to_utc=now
        ),
        generated_at_utc=now,
        group_by=group_by,
        gauges=_build_gauges(aggregator, correlator),
        groups=groups,
    )
