"""Shared metrics store (spec 004 §3): a time-bucketed ring buffer holding
both counters and histograms per bucket per label-set.

Agent-internal — plain dataclasses, not a telemetry_shared contract. Fully
generic: it knows nothing about specific counter or histogram names. The
per-metric dimension declaration (FR-MET-030) and the counter-derivation
policy are supplied by the caller (counters.py, correlation.py) — this file
only knows how to resolve a *named* dimension from an event, store, expire,
cap, and re-aggregate.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from telemetry_agent.metrics.histogram import Histogram
from telemetry_shared.models.parsed_message import ParsedMessageEvent

Clock = Callable[[], float]

OTHER_LABEL = "__other__"

DEFAULT_WINDOWS = {"1m": 60, "5m": 300, "15m": 900}


def default_resolve_reject_reason(event: ParsedMessageEvent) -> str:
    """Fallback reject_reason resolver: no normalisation map, just the raw
    value. counters.py's ReasonNormalizer.resolve is the real one used in
    production wiring — this default exists so the aggregator is usable
    standalone (e.g. in its own tests) without importing counters.py.
    """
    return str(event.reject_reason_code or event.reject_reason_text or "unspecified")


def _dimension_value(
    event: ParsedMessageEvent,
    dim: str,
    resolve_reject_reason: Callable[[ParsedMessageEvent], str],
) -> str:
    if dim == "reject_reason":
        return resolve_reject_reason(event)
    value = getattr(event, dim)
    # A dim like ord_type/side/symbol is None on plenty of real messages
    # (admin messages, OrderCancelReject) — str(None) would silently mint
    # the literal label "None", indistinguishable from a real symbol named
    # "None". "unspecified" matches the same convention already used for
    # "nothing populated" elsewhere (ReasonNormalizer.resolve,
    # default_resolve_reject_reason).
    return "unspecified" if value is None else str(value)


@dataclass(slots=True)
class AggregatorConfig:
    """Bucket granularity, retained windows, and the per-metric dimension
    table (FR-MET-030): "the permitted dimension set per metric MUST be
    declared in one shared table". `metric_dimensions` is that table — it has
    no built-in default because the aggregator has no built-in knowledge of
    metric names; the caller supplies it (typically
    counters.COUNTER_DIMENSIONS | correlatiowantn.LATENCY_DIMENSIONS merged).
    """

    bucket_seconds: int = 1
    windows: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_WINDOWS))
    metric_dimensions: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # FR-MET-029: cap on distinct label-sets *per metric* per bucket.
    max_label_sets: int = 5000
    # FR-MET-030: cap on total series (summed across every metric) per
    # bucket — a separate, tighter guard than max_label_sets, since many
    # metrics each individually under their own cap can still sum to an
    # unbounded total.
    max_series_per_bucket: int = 2000

    @property
    def capacity(self) -> int:
        return max(self.windows.values()) // self.bucket_seconds

    @property
    def known_dimensions(self) -> frozenset[str]:
        return frozenset(
            dim for dims in self.metric_dimensions.values() for dim in dims
        )


@dataclass(slots=True)
class MetricRow:
    """One grouped row from a snapshot: counters and histograms kept apart,
    matching spec 004 §3's own shape (`series[].counters{}` and
    `series[].histograms{}` as separate sub-objects) rather than one dict
    typed `Decimal | Histogram` — every consumer of counters alone (e.g.
    counters.top_reject_reasons) would otherwise have to type-narrow the
    union on every single read.
    """

    counters: dict[str, Decimal] = field(default_factory=dict)
    histograms: dict[str, Histogram] = field(default_factory=dict)


@dataclass(slots=True)
class _Bucket:
    """One time slot in the ring. `start` is None when the slot is empty.

    Storage is keyed by metric name first, then by that metric's own
    label-value tuple (FR-MET-030: different metrics carry different
    dimension sets, so there is no single composite key that fits all of
    them). The per-metric `admitted` set is the cardinality cap's admission
    registry (FR-MET-029: "top-N sketch *per bucket*") — it lives on the
    bucket, not the aggregator, so it resets when the bucket is reused rather
    than growing for the life of the process.
    """

    start: int | None = None
    counters: dict[str, dict[tuple[str, ...], Decimal]] = field(default_factory=dict)
    histograms: dict[str, dict[tuple[str, ...], Histogram]] = field(
        default_factory=dict
    )
    admitted: dict[str, set[tuple[str, ...]]] = field(default_factory=dict)
    # Total series admitted across every metric (FR-MET-030's maxSeriesPerBucket).
    total_admitted: int = 0

    def clear(self) -> None:
        self.start = None
        self.counters.clear()
        self.histograms.clear()
        self.admitted.clear()
        self.total_admitted = 0


class MetricsAggregator:
    """Time-bucketed ring buffer backing both counters and histograms.

    Two write paths, both agent-internal callers: `ingest_counters` (direct
    per-event counter increments, driven by counters.derive_counters) and
    `observe_latency` (derived histogram samples, driven by
    correlation.LatencyCorrelator). One read path: `snapshot`.
    """

    def __init__(
        self,
        config: AggregatorConfig | None = None,
        clock: Clock = time.time,
        resolve_reject_reason: Callable[
            [ParsedMessageEvent], str
        ] = default_resolve_reject_reason,
    ) -> None:
        self.config = config or AggregatorConfig()
        self._clock = clock
        self._resolve_reject_reason = resolve_reject_reason
        self._buckets = [_Bucket() for _ in range(self.config.capacity)]
        # FR-MET-029: incremented whenever a label-set folds to __other__,
        # for either cap — an observability signal that folding is actually
        # happening, not just silent relabelling.
        self.cardinality_folded = 0

    def _bucket_start(self, ts: float) -> int:
        return int(ts // self.config.bucket_seconds)

    def tick(self, now: float | None = None) -> None:
        """Evict any bucket that has fallen outside the retained capacity.

        Independent of ingest: called opportunistically by ingest/snapshot,
        and intended to also be called on a schedule by the agent's runtime
        loop, so an idle aggregator's counters decay even without new events
        or queries arriving.
        """
        now = self._clock() if now is None else now
        oldest_valid = self._bucket_start(now) - self.config.capacity + 1
        for bucket in self._buckets:
            if bucket.start is not None and bucket.start < oldest_valid:
                bucket.clear()

    def _get_bucket(self, ts: float, *, now: float) -> _Bucket | None:
        start = self._bucket_start(ts)
        oldest_valid = self._bucket_start(now) - self.config.capacity + 1
        if start < oldest_valid:
            return (
                None  # older than the retained window; drop, don't corrupt a live slot
            )
        bucket = self._buckets[start % self.config.capacity]
        if bucket.start != start:
            bucket.clear()
            bucket.start = start
        return bucket

    def _dims_for(self, metric: str) -> tuple[str, ...]:
        try:
            return self.config.metric_dimensions[metric]
        except KeyError as exc:
            msg = f"metric {metric!r} has no declared dimension set (FR-MET-030)"
            raise KeyError(msg) from exc

    def _admit_label(
        self, bucket: _Bucket, metric: str, label: tuple[str, ...]
    ) -> tuple[str, ...]:
        admitted = bucket.admitted.setdefault(metric, set())
        if label in admitted:
            return label
        at_metric_cap = len(admitted) >= self.config.max_label_sets
        at_bucket_cap = bucket.total_admitted >= self.config.max_series_per_bucket
        if at_metric_cap or at_bucket_cap:
            self.cardinality_folded += 1
            return (OTHER_LABEL,) * len(label)
        admitted.add(label)
        bucket.total_admitted += 1
        return label

    def ingest_counters(
        self, event: ParsedMessageEvent, counters: dict[str, Decimal]
    ) -> None:
        now = self._clock()
        self.tick(now)
        bucket = self._get_bucket(event.event_time_utc.timestamp(), now=now)
        if bucket is None:
            return
        for metric, amount in counters.items():
            dims = self._dims_for(metric)
            label = tuple(
                _dimension_value(event, dim, self._resolve_reject_reason)
                for dim in dims
            )
            label = self._admit_label(bucket, metric, label)
            series = bucket.counters.setdefault(metric, {})
            series[label] = series.get(label, Decimal(0)) + amount

    def observe_latency(
        self,
        *,
        metric: str,
        dims_event: ParsedMessageEvent,
        value_ms: Decimal,
        at: datetime,
    ) -> None:
        now = self._clock()
        self.tick(now)
        bucket = self._get_bucket(at.timestamp(), now=now)
        if bucket is None:
            return
        dims = self._dims_for(metric)
        label = tuple(
            _dimension_value(dims_event, dim, self._resolve_reject_reason)
            for dim in dims
        )
        label = self._admit_label(bucket, metric, label)
        series = bucket.histograms.setdefault(metric, {})
        series.setdefault(label, Histogram()).record(value_ms)

    def snapshot(
        self, window: str, group_by: Sequence[str] = ()
    ) -> dict[tuple[str, ...], MetricRow]:
        """Sum counters and merge histograms across the buckets covering
        `window`, grouped by `group_by`. A metric whose declared dimensions
        don't cover the full `group_by` request is simply absent from the
        result (FR-MET-030 in action: querying by reject_reason only surfaces
        reject-shaped metrics) — that is not an error, unlike `group_by`
        naming a dimension no metric declares at all.

        Series are never written with a zero value (every write is a
        positive increment or a recorded sample), so FR-MET-027's "omit
        all-zero series" holds structurally — there is nothing to filter.
        """
        if window not in self.config.windows:
            raise ValueError(
                f"unknown window {window!r}; configured: {list(self.config.windows)}"
            )
        group_by = tuple(group_by)
        if not set(group_by) <= self.config.known_dimensions:
            raise ValueError(
                f"group_by must be a subset of {sorted(self.config.known_dimensions)}"
            )

        now = self._clock()
        self.tick(now)
        window_buckets = self.config.windows[window] // self.config.bucket_seconds
        cutoff = self._bucket_start(now) - window_buckets + 1

        result: dict[tuple[str, ...], MetricRow] = {}
        for bucket in self._buckets:
            if bucket.start is None or bucket.start < cutoff:
                continue
            self._merge_counters(bucket, group_by, result)
            self._merge_histograms(bucket, group_by, result)
        return result

    def _row_key(
        self, dims: tuple[str, ...], group_by: tuple[str, ...], label: tuple[str, ...]
    ) -> tuple[str, ...]:
        if label == (OTHER_LABEL,) * len(dims):
            return (OTHER_LABEL,) * len(group_by)
        indices = [dims.index(dim) for dim in group_by]
        return tuple(label[i] for i in indices)

    def _merge_counters(
        self,
        bucket: _Bucket,
        group_by: tuple[str, ...],
        result: dict[tuple[str, ...], MetricRow],
    ) -> None:
        for metric, series in bucket.counters.items():
            dims = self.config.metric_dimensions[metric]
            if not set(group_by) <= set(dims):
                continue
            for label, value in series.items():
                row = result.setdefault(
                    self._row_key(dims, group_by, label), MetricRow()
                )
                row.counters[metric] = row.counters.get(metric, Decimal(0)) + value

    def _merge_histograms(
        self,
        bucket: _Bucket,
        group_by: tuple[str, ...],
        result: dict[tuple[str, ...], MetricRow],
    ) -> None:
        for metric, series in bucket.histograms.items():
            dims = self.config.metric_dimensions[metric]
            if not set(group_by) <= set(dims):
                continue
            for label, hist in series.items():
                row = result.setdefault(
                    self._row_key(dims, group_by, label), MetricRow()
                )
                existing = row.histograms.get(metric)
                if existing is None:
                    existing = Histogram()
                    row.histograms[metric] = existing
                existing.merge(hist)
