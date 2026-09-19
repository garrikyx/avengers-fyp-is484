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
from datetime import UTC, datetime, timedelta

from telemetry_agent.metrics.aggregator import MetricsAggregator
from telemetry_agent.metrics.correlation import LatencyCorrelator
from telemetry_shared.metrics import (
    DEFAULT_MIN_SAMPLE_SIZE,
    DEFAULT_PERCENTILES,
    build_latency_summary,
    compute_indicators,
)
from telemetry_shared.models.metrics import (
    Gauges,
    MetricsGroup,
    MetricsSnapshot,
    WindowBounds,
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
            indicators=compute_indicators(
                row.counters,
                min_sample_size=min_sample_size,
                window_seconds=window_seconds,
            ),
            latency={
                metric: build_latency_summary(
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
