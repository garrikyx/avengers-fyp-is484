"""Turns the Metrics Aggregator's completed buckets into spec 004 §3 wire
snapshots (`FR-MET-024`) for the Backend Publisher.

Not MA-04's `snapshot()`: that is a summed, overlapping window with ratios
already computed — the Rule Engine's input. Publishing a window on every
tick would add the same events into the backend once per tick. This reads
one bucket at a time (`MetricsAggregator.take_completed_buckets`) so each
snapshot carries that bucket's deltas only, and the backend's merge stays a
plain sum.

Per completed bucket this sends one snapshot per instance (FR-MET-024) —
including instances that were idle, as a snapshot with no series: that is
what carries the gauges (FR-MET-028) through a quiet period, so the
backend's `seconds_since_last_event` keeps rising rather than freezing at
the last busy bucket. For buckets with data it:

- splits by `instance_id` — a series dimension in the aggregator, but the
  snapshot's own top-level `instanceId` on the wire;
- renames every other dimension to its wire key, since the backend rejects
  the whole batch on any key outside `WIRE_DIMENSION_KEYS`;
- groups counters and histograms sharing one dimension set into one
  `SeriesEntry` — metrics with different declared dimensions (FR-MET-030)
  stay in different series rather than being padded with "unspecified".

Hands each snapshot to a plain callable rather than importing `publishing/`
(the same layering rule `metrics.snapshot` keeps): the composition root
passes `BackendPublisher.enqueue_snapshot`. Push, not pull — the publisher
skips its tick entirely while halted or backing off, and a pull model would
stop draining the aggregator for exactly as long as the backend is down.
Pushed snapshots instead wait in the publisher's own byte/age-bounded
buffer, where any loss is counted (`FR-PUB-004`).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from telemetry_agent.metrics.aggregator import (
    INSTANCE_DIMENSION,
    MetricsAggregator,
    RawBucket,
)
from telemetry_agent.metrics.correlation import LatencyCorrelator
from telemetry_agent.metrics.snapshot import build_gauges
from telemetry_shared.metrics.histogram import Histogram
from telemetry_shared.models.snapshot import HistogramPayload, SeriesEntry, Snapshot

_SCHEMA_VERSION: Literal[1] = 1

# Aggregator dimension (a `ParsedMessageEvent` attribute) -> wire key
# (`telemetry_shared.models.ingestion.WIRE_DIMENSION_KEYS`). Every dimension
# in counters.COUNTER_DIMENSIONS / correlation.LATENCY_DIMENSIONS except
# `instance_id` must appear here; a test enforces it.
WIRE_DIMENSION: dict[str, str] = {
    "session_id": "session",
    "symbol": "symbol",
    "side": "side",
    "ord_type": "ordType",
    "reject_reason": "rejectReason",
    "reason": "reason",
}

SnapshotSink = Callable[[Snapshot], None]
PublishFailuresProvider = Callable[[], int | None]
QueueDepthProvider = Callable[[], int]
ReadLagProvider = Callable[[], float | None]

_DimsKey = tuple[tuple[str, str], ...]


class SnapshotEmitter:
    def __init__(
        self,
        aggregator: MetricsAggregator,
        *,
        agent_id: str,
        application: str,
        instance_ids: Iterable[str],
        correlator: LatencyCorrelator | None = None,
        consecutive_publish_failures: PublishFailuresProvider | None = None,
        publish_queue_depth: QueueDepthProvider | None = None,
        read_lag_ms: ReadLagProvider | None = None,
    ) -> None:
        """`instance_ids` are the configured instances, each owed a snapshot
        for every completed bucket whether or not it had data.

        The gauge providers are read at collect time, not stored, so each
        gauge tracks its live source (`BackendPublisher.consecutive_failures`
        / `.queue_depth`, `HealthReporter.overall_read_lag_ms`). Leave one
        `None` when its source isn't wired and that gauge is omitted
        (`FR-MET-031`: unknown must never read as 0).
        """
        self._aggregator = aggregator
        self._agent_id = agent_id
        self._application = application
        self._instance_ids = tuple(instance_ids)
        self._correlator = correlator
        self._publish_failures = consecutive_publish_failures
        self._publish_queue_depth = publish_queue_depth
        self._read_lag_ms = read_lag_ms
        # Start (epoch seconds) of the oldest bucket not yet covered for
        # idle instances; `None` until the first collect.
        self._next_uncovered: int | None = None
        self._seen_instances: set[str] = set()

    def collect(self, *, now: float | None = None) -> list[Snapshot]:
        """Snapshots for every bucket completed since the last call, oldest
        first: the buckets with data (including any re-dirtied by a late
        event, FR-MET-003), plus a series-less snapshot for each configured
        instance idle in a newly completed bucket. Synchronous and cheap —
        safe to call from the event loop."""
        now = self._aggregator.now() if now is None else now
        width = self._aggregator.config.bucket_seconds
        newest_closed = int(now // width) * width - width
        metric_dimensions = self._aggregator.config.metric_dimensions

        by_start: dict[int, dict[str, list[SeriesEntry]]] = {}
        for raw in self._aggregator.take_completed_buckets(now=now):
            by_start[int(raw.start_utc.timestamp())] = _series_by_instance(
                raw, metric_dimensions
            )
        for start in self._newly_completed(newest_closed, width):
            per_instance = by_start.setdefault(start, {})
            for instance_id in self._instance_ids:
                per_instance.setdefault(instance_id, [])
        if not by_start:
            return []

        # FR-MET-028: gauges are values at bucket close and the backend keeps
        # the latest by bucket time, so only the newest closed bucket carries
        # them — never an older bucket re-published for a late event.
        gauges = self._gauges()
        snapshots: list[Snapshot] = []
        for start in sorted(by_start):
            for instance_id, series in by_start[start].items():
                snapshots.append(
                    Snapshot(
                        schema_version=_SCHEMA_VERSION,
                        agent_id=self._agent_id,
                        application=self._application,
                        instance_id=instance_id,
                        bucket_start_utc=datetime.fromtimestamp(start, tz=UTC),
                        bucket_seconds=width,
                        # FR-LOG-021: the first snapshot per instance from
                        # this process, so the backend annotates the possible
                        # re-read duplication instead of silently absorbing it.
                        restarted=instance_id not in self._seen_instances,
                        series=series,
                        gauges=gauges if start == newest_closed else {},
                    )
                )
                self._seen_instances.add(instance_id)
        return snapshots

    def _newly_completed(self, newest_closed: int, width: int) -> range:
        """Bucket starts completed since the last call. The first call
        covers only the newest closed bucket — there is nothing to say about
        time before this process existed — and a stalled loop never backfills
        past the aggregator's own retention."""
        oldest_retained = newest_closed - (self._aggregator.config.capacity - 1) * width
        first = (
            newest_closed
            if self._next_uncovered is None
            else max(self._next_uncovered, oldest_retained)
        )
        if first <= newest_closed:
            self._next_uncovered = newest_closed + width
        return range(first, newest_closed + 1, width)

    async def run(
        self,
        on_snapshot: SnapshotSink,
        stop: asyncio.Event | None = None,
        *,
        interval_seconds: float | None = None,
    ) -> None:
        """Collects every `interval_seconds` (default: one bucket width)
        until `stop` is set."""
        stop = stop or asyncio.Event()
        interval = interval_seconds or self._aggregator.config.bucket_seconds
        while not stop.is_set():
            for snapshot in self.collect():
                on_snapshot(snapshot)
            try:
                await asyncio.wait_for(stop.wait(), timeout=interval)
            except TimeoutError:
                continue

    def _gauges(self) -> dict[str, float]:
        failures = (
            self._publish_failures() if self._publish_failures is not None else None
        )
        gauges: dict[str, float | None] = build_gauges(
            self._aggregator, self._correlator, failures
        ).model_dump()
        if self._publish_queue_depth is not None:
            gauges["publish_queue_depth"] = self._publish_queue_depth()
        if self._read_lag_ms is not None:
            gauges["read_lag_ms"] = self._read_lag_ms()
        # spec 004 §3 gauge names are snake_case; a `None` gauge is unknown,
        # and is left out rather than reported as 0.
        return {
            name: float(value) for name, value in gauges.items() if value is not None
        }


def _series_by_instance(
    raw: RawBucket, metric_dimensions: dict[str, tuple[str, ...]]
) -> dict[str, list[SeriesEntry]]:
    counters: dict[tuple[str, _DimsKey], dict[str, Decimal]] = {}
    histograms: dict[tuple[str, _DimsKey], dict[str, Histogram]] = {}
    for metric, counter_series in raw.counters.items():
        dims = metric_dimensions[metric]
        for label, value in counter_series.items():
            counters.setdefault(_series_key(dims, label), {})[metric] = value
    for metric, hist_series in raw.histograms.items():
        dims = metric_dimensions[metric]
        for label, hist in hist_series.items():
            histograms.setdefault(_series_key(dims, label), {})[metric] = hist

    result: dict[str, list[SeriesEntry]] = {}
    for key in sorted(counters.keys() | histograms.keys()):
        instance_id, wire_dims = key
        result.setdefault(instance_id, []).append(
            SeriesEntry(
                dimensions=dict(wire_dims),
                counters=counters.get(key, {}),
                histograms={
                    name: _histogram_payload(hist)
                    for name, hist in histograms.get(key, {}).items()
                },
            )
        )
    return result


def _series_key(dims: tuple[str, ...], label: tuple[str, ...]) -> tuple[str, _DimsKey]:
    instance_id = ""
    wire_dims: list[tuple[str, str]] = []
    for dim, value in zip(dims, label, strict=True):
        if dim == INSTANCE_DIMENSION:
            instance_id = value
        else:
            wire_dims.append((WIRE_DIMENSION[dim], value))
    return instance_id, tuple(sorted(wire_dims))


def _histogram_payload(hist: Histogram) -> HistogramPayload:
    return HistogramPayload(
        count=hist.count,
        sum=hist.sum_ms,
        min=hist.min_ms,
        max=hist.max_ms,
        buckets=dict(hist.buckets),
    )
