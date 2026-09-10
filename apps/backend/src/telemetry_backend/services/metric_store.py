"""Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006).

A per-instance ring of canonical buckets. Each bucket keeps one
`_SeriesContribution` per `(dimension-set, agentId, agent's own native
bucketStartUtc)` rather than a single pre-summed cell, so that:

- Counters merge by summation (`FR-STM-002`) computed at read time across
  every contributing native bucket — never stored pre-summed. Keying on the
  agent's own `bucketStartUtc` (not just `agentId`) matters when an agent's
  `bucketSeconds` is narrower than the canonical grid: two distinct native
  buckets from the same agent both landing in one canonical slot must
  accumulate, while the *same* native bucket redelivered by that agent
  (e.g. a retry that missed batchId-level dedupe) must overwrite its own
  prior contribution instead of double-adding.
- Ratios (`FR-STM-003`) and percentiles (`FR-STM-004`) are never computed
  here at all: `read()` returns summed counters and bucket-wise-merged
  histograms, and indicators/latency summaries are derived from those sums
  by the same `telemetry_shared.metrics` functions the agent uses for its
  own per-window snapshot — one implementation, never averaged.
- `restarted` (`FR-STM-006`) is preserved per bucket per agent rather than
  discarded on merge, so a query layer can tell a query "this instance was
  warming up during part of this range" instead of silently blending
  cold-start data into a steady-state answer.
- Gauges take the latest value by the contributing snapshot's own native
  `bucketStartUtc`, not by merge order (`FR-MET-028`) — this stage must
  accept out-of-order arrival (`FR-ING-005`), so a snapshot merged later
  is not necessarily the one that happened later.
- A snapshot that ages out of the store's own retention between being
  accepted upstream and reaching `merge()` is counted in
  `dropped_after_retention_total`, never silently dropped (`FR-STM-005`).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from telemetry_shared.metrics import (
    Histogram,
    build_latency_summary,
    compute_indicators,
)
from telemetry_shared.models.metrics import MetricsGroup
from telemetry_shared.models.snapshot import Snapshot

from telemetry_backend.config import StreamProcessorConfig

DimKey = tuple[tuple[str, str], ...]
# (agentId, agent's own native bucket epoch) — the unit that overwrites
# idempotently on redelivery; distinct keys always accumulate.
ContributionKey = tuple[str, int]


@dataclass(slots=True)
class _SeriesContribution:
    counters: dict[str, Decimal] = field(default_factory=dict)
    histograms: dict[str, Histogram] = field(default_factory=dict)


@dataclass(slots=True)
class _CanonicalBucket:
    """One canonical-grid time slot for one instance. `start` is the
    canonical bucket index (`epoch // canonicalBucketSeconds`); `None` means
    the slot is unused or was evicted.
    """

    start: int | None = None
    series: dict[DimKey, dict[ContributionKey, _SeriesContribution]] = field(
        default_factory=dict
    )
    gauges: dict[str, float] = field(default_factory=dict)
    # The native bucket epoch that produced `gauges`, so a later merge can
    # tell whether it is genuinely newer (FR-MET-028's "latest" is latest
    # *in time*, not latest *processed* — out-of-order arrival is exactly
    # what this stage must accept, so processing order alone is not enough).
    gauges_source_epoch: int | None = None
    contributing_agent_ids: set[str] = field(default_factory=set)
    # FR-STM-006: which agents reported this bucket as their post-restart
    # first bucket. Kept as a set (not collapsed to a bool) so a bucket fed
    # by several agents still shows exactly which ones were cold.
    restarted_agent_ids: set[str] = field(default_factory=set)

    def clear(self) -> None:
        self.start = None
        self.series.clear()
        self.gauges.clear()
        self.gauges_source_epoch = None
        self.contributing_agent_ids.clear()
        self.restarted_agent_ids.clear()


def _dim_key(dimensions: dict[str, str]) -> DimKey:
    return tuple(sorted(dimensions.items()))


class MetricStore:
    """In-memory, per-instance ring buffer of canonical buckets
    (`FR-QRY-001`, scoped here to a single replica — no cross-replica
    scatter-gather in this stage).
    """

    def __init__(self, config: StreamProcessorConfig | None = None) -> None:
        self._config = config or StreamProcessorConfig()
        self._capacity = max(
            self._config.retention_window_seconds
            // self._config.canonical_bucket_seconds,
            1,
        )
        self._rings: dict[str, list[_CanonicalBucket]] = {}
        # FR-STM-006: instance -> epoch seconds until which it is warmingUp.
        self._warming_until: dict[str, float] = {}
        # FR-STM-005: incremented if a snapshot reaches merge() but its
        # canonical bucket has already aged out of the store's own
        # retention window. `StreamProcessorConfig` validates
        # maxBucketAge <= retentionWindow so this should be unreachable via
        # `StreamProcessor`, but `merge()` is a public method another
        # caller could invoke directly — this is the defense-in-depth
        # counter that keeps that path from silently discarding data.
        self.dropped_after_retention_total = 0

    def _bucket_index(self, at: datetime) -> int:
        return int(at.timestamp() // self._config.canonical_bucket_seconds)

    def _ring_for(self, instance_id: str) -> list[_CanonicalBucket]:
        return self._rings.setdefault(
            instance_id, [_CanonicalBucket() for _ in range(self._capacity)]
        )

    def _get_bucket(
        self, instance_id: str, canonical_start: int, *, now: datetime
    ) -> _CanonicalBucket | None:
        oldest_valid = self._bucket_index(now) - self._capacity + 1
        if canonical_start < oldest_valid:
            # Older than the store's own retention. `merge()` counts this
            # in `dropped_after_retention_total` — it must never be a
            # silent no-op (FR-STM-005).
            return None
        ring = self._ring_for(instance_id)
        bucket = ring[canonical_start % self._capacity]
        if bucket.start != canonical_start:
            bucket.clear()
            bucket.start = canonical_start
        return bucket

    def _evict_stale(self, ring: list[_CanonicalBucket], now: datetime) -> None:
        """Evict buckets that have aged out of retention within *one*
        instance's ring — `O(capacity)`, not `O(instances × capacity)`.
        `_get_bucket` already clears-on-reuse the one slot a write lands
        on, so this exists only to reclaim *other* stale slots in the same
        ring that a write isn't currently touching (e.g. a symbol that
        stopped trading, in an instance that's still otherwise active).
        """
        oldest_valid = self._bucket_index(now) - self._capacity + 1
        for bucket in ring:
            if bucket.start is not None and bucket.start < oldest_valid:
                bucket.clear()

    def tick(self, now: datetime) -> None:
        """Evict stale buckets across every instance's ring. For a
        periodic background sweep (a future scheduler) — not the write
        path. `merge()` scopes eviction to just the ring it touches
        (`_evict_stale`); paying this whole-store cost on every single
        write does not scale with the number of instances.
        """
        for ring in self._rings.values():
            self._evict_stale(ring, now)

    def merge(
        self, snapshot: Snapshot, *, canonical_start: datetime, now: datetime
    ) -> None:
        """Merge one already-aligned, already-age-checked snapshot in.
        Idempotent per `(instanceId, canonicalStart, dimensions, agentId,
        agent's own bucketStartUtc)`: re-merging the identical native bucket
        from the same agent replaces that contribution rather than adding to
        it, while two different native buckets from the same agent that both
        land in this canonical slot both accumulate.
        """
        self._evict_stale(self._ring_for(snapshot.instance_id), now)
        bucket = self._get_bucket(
            snapshot.instance_id, self._bucket_index(canonical_start), now=now
        )
        if bucket is None:
            self.dropped_after_retention_total += 1
            return

        native_bucket_epoch = int(snapshot.bucket_start_utc.timestamp())
        bucket.contributing_agent_ids.add(snapshot.agent_id)
        if snapshot.gauges and (
            bucket.gauges_source_epoch is None
            or native_bucket_epoch >= bucket.gauges_source_epoch
        ):
            # FR-MET-028: gauges are instantaneous; the store takes the
            # latest report for this bucket, never a sum. "Latest" is by
            # the snapshot's own native bucketStartUtc, not by merge
            # order — this stage must accept out-of-order arrival
            # (FR-ING-005), so a snapshot processed later is not
            # necessarily the one that happened later.
            bucket.gauges = dict(snapshot.gauges)
            bucket.gauges_source_epoch = native_bucket_epoch
        if snapshot.restarted:
            bucket.restarted_agent_ids.add(snapshot.agent_id)
            new_until = canonical_start.timestamp() + self._config.warmup_window_seconds
            existing = self._warming_until.get(snapshot.instance_id)
            if existing is None or new_until > existing:
                self._warming_until[snapshot.instance_id] = new_until

        contribution_key: ContributionKey = (snapshot.agent_id, native_bucket_epoch)
        for entry in snapshot.series:
            per_contribution = bucket.series.setdefault(_dim_key(entry.dimensions), {})
            per_contribution[contribution_key] = _SeriesContribution(
                counters=dict(entry.counters),
                histograms={
                    name: payload.to_histogram()
                    for name, payload in entry.histograms.items()
                },
            )

    def is_warming_up(self, instance_id: str, *, at: datetime) -> bool:
        until = self._warming_until.get(instance_id)
        return until is not None and at.timestamp() < until

    def gauges(self, instance_id: str, *, at: datetime) -> dict[str, float]:
        """The latest gauge values for whichever canonical bucket contains
        `at` (`FR-MET-028`) — `{}` if the instance or bucket is unknown.
        """
        ring = self._rings.get(instance_id)
        if not ring:
            return {}
        bucket = ring[self._bucket_index(at) % self._capacity]
        if bucket.start != self._bucket_index(at):
            return {}
        return dict(bucket.gauges)

    def _in_range_buckets(
        self, ring: list[_CanonicalBucket], *, from_utc: datetime, to_utc: datetime
    ) -> Iterator[_CanonicalBucket]:
        """Yield only the buckets that could hold data for
        `[from_utc, to_utc]`, indexing directly into the ring rather than
        scanning every slot — `O(min(requested range, capacity))` instead
        of always `O(capacity)`, so a query over a few buckets on a
        6-hour ring doesn't pay for the other ~2000 it doesn't need.
        A range wider than `capacity` is clamped to the most recent
        `capacity` indices ending at `to_utc`'s bucket — nothing older
        could still be resident; the ring physically cannot hold it.
        """
        start_index = self._bucket_index(from_utc)
        end_index = self._bucket_index(to_utc)
        requested = end_index - start_index + 1
        span = max(min(requested, self._capacity), 0)
        for index in range(end_index - span + 1, end_index + 1):
            bucket = ring[index % self._capacity]
            if bucket.start == index:
                yield bucket

    def restarted_bucket_count(
        self, instance_id: str, *, from_utc: datetime, to_utc: datetime
    ) -> int:
        ring = self._rings.get(instance_id)
        if not ring:
            return 0
        return sum(
            1
            for bucket in self._in_range_buckets(ring, from_utc=from_utc, to_utc=to_utc)
            if bucket.restarted_agent_ids
        )

    def read(
        self,
        instance_id: str,
        *,
        from_utc: datetime,
        to_utc: datetime,
        group_by: tuple[str, ...] = (),
    ) -> list[MetricsGroup]:
        """Sum counters and merge histograms across every canonical bucket
        in range and every contributing agent, grouped by `group_by`
        (empty = the one window-wide total row). Ratios and latency
        summaries are derived from those sums, never from any single
        agent's own precomputed values (`FR-STM-003`/`FR-STM-004`).
        """
        ring = self._rings.get(instance_id)
        if not ring:
            return []

        merged: dict[DimKey, tuple[dict[str, Decimal], dict[str, Histogram]]] = {}

        for bucket in self._in_range_buckets(ring, from_utc=from_utc, to_utc=to_utc):
            for dim_key, per_contribution in bucket.series.items():
                dims = dict(dim_key)
                row_key = tuple(
                    sorted((dim, dims.get(dim, "unspecified")) for dim in group_by)
                )
                counters, histograms = merged.setdefault(row_key, ({}, {}))
                for contribution in per_contribution.values():
                    for metric, amount in contribution.counters.items():
                        counters[metric] = counters.get(metric, Decimal(0)) + amount
                    for metric, hist in contribution.histograms.items():
                        existing = histograms.get(metric)
                        if existing is None:
                            existing = Histogram()
                            histograms[metric] = existing
                        existing.merge(hist)

        window_seconds = max((to_utc - from_utc).total_seconds(), 0.0)
        return [
            MetricsGroup(
                dimensions=dict(row_key),
                counters=counters,
                indicators=compute_indicators(
                    counters,
                    min_sample_size=self._config.min_sample_size,
                    window_seconds=window_seconds,
                ),
                latency={
                    metric: build_latency_summary(
                        hist,
                        percentiles=self._config.default_percentiles,
                        min_sample_size=self._config.min_sample_size,
                    )
                    for metric, hist in histograms.items()
                },
            )
            for row_key, (counters, histograms) in merged.items()
        ]
