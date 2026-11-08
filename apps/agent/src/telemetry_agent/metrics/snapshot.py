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

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta

from telemetry_agent.metrics.aggregator import MetricsAggregator
from telemetry_agent.metrics.correlation import LatencyCorrelator
from telemetry_shared.metrics import (
    DEFAULT_MIN_SAMPLE_SIZE,
    DEFAULT_PERCENTILES,
    build_latency_summary,
    compute_indicators,
)
from telemetry_shared.metrics.host import (
    HOST_DISK_USED_RATIO,
    HOST_MEMORY_USED_RATIO,
    MAGIC_PROCESS_UP,
)
from telemetry_shared.models.metrics import (
    Gauges,
    MetricsGroup,
    MetricsSnapshot,
    WindowBounds,
)


def _build_gauges(
    aggregator: MetricsAggregator,
    correlator: LatencyCorrelator | None,
    consecutive_publish_failures: int | None,
    host_gauges: Mapping[str, float] | None = None,
) -> Gauges:
    host = host_gauges or {}
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
        consecutive_publish_failures=consecutive_publish_failures,
        host_disk_used_ratio=host.get(HOST_DISK_USED_RATIO),
        host_memory_used_ratio=host.get(HOST_MEMORY_USED_RATIO),
        magic_process_up=host.get(MAGIC_PROCESS_UP),
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
    consecutive_publish_failures: int | None = None,
    host_gauges: Mapping[str, float] | None = None,
) -> MetricsSnapshot:
    """Serialisable, per-window snapshot: counters, computed indicators,
    latency summaries, grouped breakdowns, window bounds, and generation
    time — the one contract the Rule Engine and Backend Publisher both
    consume.

    Pure read + arithmetic over `aggregator.snapshot()` (which does the
    window/group_by validation this deliberately doesn't repeat) — no I/O,
    no locks, so this can never block a concurrent `ingest_counters`/
    `observe_latency` call.

    `consecutive_publish_failures` (`FR-MET-031`) is passed in as a plain
    value rather than read from a publisher: `metrics/` must not import
    `publishing/` (the same layering rule `metrics.agent_counters` keeps
    against `callbacks/`), and taking a value instead of a callable keeps
    this function the pure read it advertises. Callers hand in
    `BackendPublisher.consecutive_failures`; leaving it `None` means no
    publisher is wired, which reads as no-fire rather than as healthy.

    `host_gauges` (FR-MET-034, UBS-129) is the Host Monitor's latest readings
    handed in the same way (`health/` is not imported here): a gauge missing
    from the mapping stays `None`, so a rule reads "no data", never 0.
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
        gauges=_build_gauges(
            aggregator, correlator, consecutive_publish_failures, host_gauges
        ),
        groups=groups,
    )
