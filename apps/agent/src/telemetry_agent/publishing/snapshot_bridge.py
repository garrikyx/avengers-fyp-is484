"""UBS-115: converts `MetricsAggregator` buckets into the wire `Snapshot`.

`TelemetryBatch.snapshots` expects the bucket-oriented `Snapshot` (series +
gauges, `FR-MET-024`), but the aggregator's native read surface
(`MetricsAggregator.bucket_delta`) returns `MetricRow`s keyed by whatever
`group_by` dimensions were queried — this module is the one place that
reshapes one into the other, filtered to the FR-ING-007 dimension allowlist.

Dimension families are not disjoint (e.g. `SESSION_DIMS` is a subset of
`BASE_DIMS`, which is a subset of `REJECT_DIMS`), so querying the aggregator
once per family and merging every result verbatim would publish some
metrics twice — once at their own native granularity and again folded into
a coarser family that happens to be a superset. `build_snapshot` avoids
this by querying once per *distinct* dims tuple and keeping, from each
query, only the metrics whose own declared dims equal that tuple exactly.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from telemetry_shared.metrics.dimensions import (
    ALLOWED_DIMENSION_KEYS,
    DIMENSION_KEY_ALIASES,
)
from telemetry_shared.metrics.histogram import Histogram
from telemetry_shared.models.snapshot import HistogramPayload, SeriesEntry, Snapshot

from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_agent.metrics.aggregator import MetricsAggregator
from telemetry_agent.metrics.correlation import LatencyCorrelator
from telemetry_agent.publishing.publisher import BackendPublisher


def _to_wire_dimensions(
    dims: tuple[str, ...], label: tuple[str, ...]
) -> dict[str, str]:
    """Rename each internal dim to its wire name and drop anything not
    allowlisted (FR-ING-007). Defensive, not expected to ever trigger today
    — every internal dimension currently maps onto an allowlisted name —
    but it is the first line of defence the backend's own check is the
    second line of, so a future internal dimension added without a matching
    wire-contract update degrades to "fewer labels" rather than a rejected
    batch.
    """
    wire: dict[str, str] = {}
    for dim, value in zip(dims, label, strict=True):
        wire_key = DIMENSION_KEY_ALIASES.get(dim, dim)
        if wire_key in ALLOWED_DIMENSION_KEYS:
            wire[wire_key] = value
    return wire


def _to_payload(histogram: Histogram) -> HistogramPayload:
    return HistogramPayload(
        count=histogram.count,
        sum=histogram.sum_ms,
        min=histogram.min_ms,
        max=histogram.max_ms,
        buckets=dict(histogram.buckets),
    )


def build_snapshot(
    aggregator: MetricsAggregator,
    bucket_start: int,
    bucket_seconds: int,
    *,
    agent_id: str,
    application: str,
    instance_id: str,
    gauges: Mapping[str, float] | None = None,
    restarted: bool = False,
) -> Snapshot:
    """One `Snapshot` for the closed interval `[bucket_start, bucket_start +
    bucket_seconds)`. Pure — calling this twice with the same arguments
    reads the same aggregator state and produces an equal `Snapshot` (modulo
    aggregator eviction), so retries are naturally safe.
    """
    series: list[SeriesEntry] = []
    distinct_shapes = set(aggregator.config.metric_dimensions.values())

    for dims in distinct_shapes:
        rows = aggregator.bucket_delta(bucket_start, bucket_seconds, group_by=dims)
        native_metrics = {
            metric
            for metric, declared in aggregator.config.metric_dimensions.items()
            if declared == dims
        }
        for label, row in rows.items():
            counters = {
                metric: value
                for metric, value in row.counters.items()
                if metric in native_metrics
            }
            histograms = {
                metric: hist
                for metric, hist in row.histograms.items()
                if metric in native_metrics
            }
            if not counters and not histograms:
                # Everything in this row belonged to a strictly wider shape
                # (picked up only because its dims are a superset of `dims`)
                # and is published once, at its own native shape, elsewhere.
                continue
            series.append(
                SeriesEntry(
                    dimensions=_to_wire_dimensions(dims, label),
                    counters=counters,
                    histograms={
                        name: _to_payload(hist) for name, hist in histograms.items()
                    },
                )
            )

    return Snapshot(
        schema_version=1,
        agent_id=agent_id,
        application=application,
        instance_id=instance_id,
        bucket_start_utc=datetime.fromtimestamp(bucket_start, tz=UTC),
        bucket_seconds=bucket_seconds,
        restarted=restarted,
        series=series,
        gauges=dict(gauges) if gauges else {},
    )


class SnapshotEmitter:
    """UBS-123: publishes every completed wire bucket once, oldest first."""

    def __init__(
        self,
        aggregator: MetricsAggregator,
        publisher: BackendPublisher,
        *,
        bucket_seconds: int,
        agent_id: str,
        application: str,
        instance_id: str,
        correlator: LatencyCorrelator | None = None,
        counters: CounterRegistry | None = None,
    ) -> None:
        if bucket_seconds <= 0:
            raise ValueError("bucket_seconds must be > 0")
        native = aggregator.config.bucket_seconds
        if bucket_seconds % native != 0:
            raise ValueError(
                f"bucket_seconds={bucket_seconds} must be a whole multiple of "
                f"the aggregator's bucket_seconds={native}"
            )
        retention = aggregator.config.capacity * native
        if retention < 2 * bucket_seconds:
            raise ValueError(
                f"aggregator retention {retention}s must cover at least two "
                f"bucket_seconds={bucket_seconds} buckets"
            )
        self._aggregator = aggregator
        self._publisher = publisher
        self._bucket_seconds = bucket_seconds
        self._agent_id = agent_id
        self._application = application
        self._instance_id = instance_id
        self._correlator = correlator
        self._last_emitted: int | None = None
        self._counters = CounterRegistry() if counters is None else counters

    @property
    def counters(self) -> CounterRegistry:
        return self._counters

    def _read_gauges(self) -> dict[str, float]:
        gauges = {
            "consecutive_publish_failures": float(self._publisher.consecutive_failures),
            "publish_queue_depth": float(self._publisher.queue_depth()),
        }
        if self._correlator is not None:
            gauges["pending_orders"] = float(self._correlator.pending_order_count())
        return gauges

    def emit(self, now: datetime) -> int:
        """Enqueue missed and latest buckets; returns how many were enqueued."""
        width = self._bucket_seconds
        latest = int(now.timestamp() // width) * width - width
        first = latest if self._last_emitted is None else self._last_emitted + width
        oldest_second = self._aggregator.oldest_retained_start(now.timestamp())
        earliest = -(-oldest_second // width) * width
        if first < earliest:
            skipped = (min(earliest, latest + width) - first) // width
            self._counters.increment("snapshot_buckets_skipped", skipped)
            first = earliest
            if first > latest:
                # The whole gap is gone; don't count it again next call.
                self._last_emitted = latest
        if first > latest:
            return 0

        gauges = self._read_gauges()
        emitted = 0
        for start in range(first, latest + 1, width):
            snap = build_snapshot(
                self._aggregator,
                start,
                width,
                agent_id=self._agent_id,
                application=self._application,
                instance_id=self._instance_id,
                gauges=gauges if start == latest else None,
            )
            self._publisher.enqueue_snapshot(snap, now=now)
            self._last_emitted = start
            emitted += 1
        return emitted
