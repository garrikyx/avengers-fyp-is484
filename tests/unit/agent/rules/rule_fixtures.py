"""Shared test support for the rules package: builds `MetricsSnapshot`
fixtures directly (no `MetricsAggregator` involved) since the Rule Engine is
a pure snapshot consumer (see `telemetry_agent.rules.engine`'s own
docstring) — these helpers exist purely to keep individual tests terse.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from telemetry_shared.models.metrics import (
    Gauges,
    Indicator,
    Indicators,
    LatencySummary,
    MetricsGroup,
    MetricsSnapshot,
    WindowBounds,
)

WINDOW_SECONDS = {"1m": 60, "5m": 300, "15m": 900}


def make_indicator(
    value: float | None = None, denominator: int = 0, low_confidence: bool = True
) -> Indicator:
    return Indicator(
        value=value, denominator=denominator, low_confidence=low_confidence
    )


def make_indicators(
    *,
    reject_rate: Indicator | None = None,
    fill_rate: Indicator | None = None,
    cancel_rate: Indicator | None = None,
    parse_error_rate: Indicator | None = None,
    throughput: float = 0.0,
) -> Indicators:
    return Indicators(
        reject_rate=reject_rate or make_indicator(),
        fill_rate=fill_rate or make_indicator(),
        cancel_rate=cancel_rate or make_indicator(),
        parse_error_rate=parse_error_rate or make_indicator(),
        throughput=throughput,
    )


def make_latency(
    p95: float | None, count: int, *, p50: float | None = None, p99: float | None = None
) -> LatencySummary:
    avg = p95 if p95 is not None else None
    return LatencySummary(p50=p50, p95=p95, p99=p99, avg=avg, count=count)


def make_gauges(
    *,
    pending_orders: int = 0,
    oldest_pending_age_seconds: float | None = None,
    seconds_since_last_event: float | None = None,
) -> Gauges:
    return Gauges(
        pending_orders=pending_orders,
        oldest_pending_age_seconds=oldest_pending_age_seconds,
        seconds_since_last_event=seconds_since_last_event,
    )


def make_snapshot(
    *,
    now: datetime,
    window: str = "5m",
    counters: dict[str, Decimal] | None = None,
    indicators: Indicators | None = None,
    latency: dict[str, LatencySummary] | None = None,
    gauges: Gauges | None = None,
    dimensions: dict[str, str] | None = None,
    empty: bool = False,
) -> MetricsSnapshot:
    """`empty=True` builds a snapshot with zero groups (nothing ingested
    this window at all) — the same shape `snapshot()` produces on a cold
    aggregator (MA-04's own `test_gauges_are_empty_without_a_correlator`).
    """
    window_seconds = WINDOW_SECONDS[window]
    groups = (
        []
        if empty
        else [
            MetricsGroup(
                dimensions=dimensions or {},
                counters=counters or {},
                indicators=indicators or make_indicators(),
                latency=latency or {},
            )
        ]
    )
    return MetricsSnapshot(
        window=window,
        window_bounds=WindowBounds(
            from_utc=now - timedelta(seconds=window_seconds), to_utc=now
        ),
        generated_at_utc=now,
        group_by=(),
        gauges=gauges or make_gauges(),
        groups=groups,
    )
