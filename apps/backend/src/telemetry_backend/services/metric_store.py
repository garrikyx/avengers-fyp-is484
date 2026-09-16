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

import logging
import threading
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

logger = logging.getLogger(__name__)

DimKey = tuple[tuple[str, str], ...]
# (agentId, agent's own native bucket epoch) — the unit that overwrites
# idempotently on redelivery; distinct keys always accumulate.
ContributionKey = tuple[str, int]

# NFR-SCA-006: memory MUST be documented as bytes-per-series-per-bucket so
# capacity can be computed rather than guessed. These are conservative fixed
# estimates, not `sys.getsizeof` introspection — a `_SeriesContribution`
# holds a handful of Decimal-valued counters plus an 11-bucket histogram of
# ints/Decimals, plus CPython dict/dataclass overhead; an empty
# `_CanonicalBucket` shell (its own dicts/sets) costs far less. Both are
# rounded up for headroom rather than measured exactly, since `FR-QRY-003`
# asks for an estimate, not an exact accounting.
_BYTES_PER_SERIES_CONTRIBUTION = 512
_BYTES_PER_BUCKET_OVERHEAD = 128

# FR-QRY-003: how often `merge()` itself samples memory pressure. `tick()`
# alone isn't reachable without an external scheduler this repo doesn't have
# yet, so the write path must be self-sufficient — but `estimated_memory_bytes()`
# is O(total buckets across every instance), so every single `merge()` call
# checking it would reintroduce the whole-store cost `_evict_stale`'s
# per-ring scoping was written to avoid. Throttling to once per interval
# keeps the check off the hot path while still catching sustained pressure
# well within one retention window.
_MEMORY_CHECK_INTERVAL_SECONDS = 5


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
        # FR-QRY-004: one lock per instance, not one global lock — two
        # different instances' merges/reads never block each other.
        # `_locks_guard` protects only the moment a *new* instance's
        # ring+lock pair is first created, so two threads racing to
        # first-touch the same new instance don't each create a separate
        # lock for it.
        self._instance_locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()
        # FR-QRY-003: throttles how often `merge()` samples memory pressure
        # (see `_MEMORY_CHECK_INTERVAL_SECONDS`). A non-blocking try-lock,
        # not a per-instance one: skipping a check some other thread is
        # already mid-way through is fine, but a writer must never block on
        # it — that would defeat the point of per-instance locking above.
        self._memory_check_lock = threading.Lock()
        self._last_memory_check_epoch: float | None = None
        # FR-QRY-005: set once real data has actually been merged in, and
        # never unset — see `is_ready`'s consumer (`StreamProcessor`) for
        # why this must be sticky rather than "is the store non-empty right
        # now" (a legitimately quiet period must read as caught-up-and-idle,
        # not as warming again).
        self.has_data = False
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
        # FR-MET-030-equivalent cardinality guard: a series whose
        # dimension-set would exceed `max_series_per_bucket` for its
        # canonical bucket is dropped and counted here, not silently
        # merged in — cross-agent merge is exactly the case where per-bucket
        # cardinality could otherwise grow unboundedly with agent count.
        self.dropped_series_over_cap_total = 0
        # FR-QRY-003: buckets evicted by `_shed_oldest_tier` under memory
        # pressure, as opposed to ordinary retention-window eviction.
        self.shed_buckets_total = 0

    def _bucket_index(self, at: datetime) -> int:
        return int(at.timestamp() // self._config.canonical_bucket_seconds)

    def _get_or_create_instance(
        self, instance_id: str
    ) -> tuple[list[_CanonicalBucket], threading.Lock]:
        ring = self._rings.get(instance_id)
        lock = self._instance_locks.get(instance_id)
        if ring is not None and lock is not None:
            return ring, lock
        with self._locks_guard:
            ring = self._rings.setdefault(
                instance_id, [_CanonicalBucket() for _ in range(self._capacity)]
            )
            lock = self._instance_locks.setdefault(instance_id, threading.Lock())
        return ring, lock

    def _existing_instance(
        self, instance_id: str
    ) -> tuple[list[_CanonicalBucket], threading.Lock] | None:
        ring = self._rings.get(instance_id)
        if ring is None:
            return None
        return ring, self._instance_locks[instance_id]

    def _get_bucket(
        self, ring: list[_CanonicalBucket], canonical_start: int, *, now: datetime
    ) -> _CanonicalBucket | None:
        oldest_valid = self._bucket_index(now) - self._capacity + 1
        if canonical_start < oldest_valid:
            # Older than the store's own retention. `merge()` counts this
            # in `dropped_after_retention_total` — it must never be a
            # silent no-op (FR-STM-005).
            return None
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
        """Evict stale buckets across every instance's ring and check
        memory pressure. For a periodic background sweep (a future
        scheduler) — not the write path. `merge()` scopes eviction to just
        the ring it touches (`_evict_stale`); paying this whole-store cost
        on every single write does not scale with the number of instances.
        """
        for instance_id in list(self._rings.keys()):
            found = self._existing_instance(instance_id)
            if found is None:
                continue
            ring, lock = found
            with lock:
                self._evict_stale(ring, now)
        self._run_memory_check(now)

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
        ring, lock = self._get_or_create_instance(snapshot.instance_id)
        with lock:
            self._evict_stale(ring, now)
            bucket = self._get_bucket(
                ring, self._bucket_index(canonical_start), now=now
            )
            if bucket is None:
                self.dropped_after_retention_total += 1
                return
            self.has_data = True

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
                new_until = (
                    canonical_start.timestamp() + self._config.warmup_window_seconds
                )
                existing = self._warming_until.get(snapshot.instance_id)
                if existing is None or new_until > existing:
                    self._warming_until[snapshot.instance_id] = new_until

            contribution_key: ContributionKey = (snapshot.agent_id, native_bucket_epoch)
            for entry in snapshot.series:
                dim_key = _dim_key(entry.dimensions)
                if (
                    dim_key not in bucket.series
                    and len(bucket.series) >= self._config.max_series_per_bucket
                ):
                    self.dropped_series_over_cap_total += 1
                    continue
                per_contribution = bucket.series.setdefault(dim_key, {})
                per_contribution[contribution_key] = _SeriesContribution(
                    counters=dict(entry.counters),
                    histograms={
                        name: payload.to_histogram()
                        for name, payload in entry.histograms.items()
                    },
                )
        # Outside the instance lock: `_shed_oldest_tier` (which this may
        # trigger) acquires every instance's lock in turn, including this
        # one — calling it while still holding this instance's lock above
        # would deadlock.
        self._maybe_check_memory_pressure(now)

    def estimated_memory_bytes(self) -> int:
        """FR-QRY-003 / NFR-SCA-006: an approximate gauge, not an exact
        accounting — see the module-level byte constants for the estimate
        this multiplies out. Deliberately lock-free: a periodic estimate
        tolerates reading a bucket mid-write, and locking every instance to
        scan the whole store would contend with the write path this
        component exists to keep uncontended.
        """
        total_buckets = 0
        total_contributions = 0
        for ring in self._rings.values():
            for bucket in ring:
                if bucket.start is not None:
                    total_buckets += 1
                    total_contributions += sum(
                        len(contributions) for contributions in bucket.series.values()
                    )
        return (
            total_buckets * _BYTES_PER_BUCKET_OVERHEAD
            + total_contributions * _BYTES_PER_SERIES_CONTRIBUTION
        )

    def _maybe_check_memory_pressure(self, now: datetime) -> None:
        """FR-QRY-003 for the write path: `merge()` calls this on every
        write, but a real check only runs at most once per
        `_MEMORY_CHECK_INTERVAL_SECONDS` — `tick()` (an explicit periodic
        sweep) is not reachable without a scheduler this repo doesn't build
        yet, so the write path must be able to trip the warn/shed thresholds
        on its own. A non-blocking try-lock: if another thread is already
        mid-check, this call simply skips rather than stalling the writer
        that triggered it.
        """
        if not self._memory_check_lock.acquire(blocking=False):
            return
        try:
            last = self._last_memory_check_epoch
            if (
                last is not None
                and now.timestamp() - last < _MEMORY_CHECK_INTERVAL_SECONDS
            ):
                return
            self._run_memory_check(now)
        finally:
            self._memory_check_lock.release()

    def _run_memory_check(self, now: datetime) -> None:
        self._last_memory_check_epoch = now.timestamp()
        self._check_memory_pressure(now)

    def _check_memory_pressure(self, now: datetime) -> None:
        limit_bytes = self._config.memory_limit_mb * 1024 * 1024
        used_percent = self.estimated_memory_bytes() / limit_bytes * 100
        if used_percent >= self._config.memory_shed_percent:
            shed = self._shed_oldest_tier(now)
            self.shed_buckets_total += shed
            logger.warning(
                "MetricStore memory at %.1f%% of %dMB limit (>= shed "
                "threshold %.0f%%); shed %d buckets from the oldest "
                "retention tier",
                used_percent,
                self._config.memory_limit_mb,
                self._config.memory_shed_percent,
                shed,
            )
        elif used_percent >= self._config.memory_warn_percent:
            logger.warning(
                "MetricStore memory at %.1f%% of %dMB limit (>= warn threshold %.0f%%)",
                used_percent,
                self._config.memory_limit_mb,
                self._config.memory_warn_percent,
            )

    def _shed_oldest_tier(self, now: datetime) -> int:
        """FR-QRY-003: shed the oldest retention tier rather than being
        OOM-killed. Evicts the older half of every instance's *retained*
        buckets — a uniform, cheap approximation of "oldest tier" rather
        than a cross-instance LRU, which would need globally comparable
        bucket ages this store doesn't track.
        """
        shed_before = self._bucket_index(now) - self._capacity // 2 + 1
        shed_count = 0
        for instance_id, ring in list(self._rings.items()):
            lock = self._instance_locks[instance_id]
            with lock:
                for bucket in ring:
                    if bucket.start is not None and bucket.start < shed_before:
                        bucket.clear()
                        shed_count += 1
        return shed_count

    def is_warming_up(self, instance_id: str, *, at: datetime) -> bool:
        found = self._existing_instance(instance_id)
        if found is None:
            return False
        _, lock = found
        with lock:
            until = self._warming_until.get(instance_id)
            return until is not None and at.timestamp() < until

    def gauges(self, instance_id: str, *, at: datetime) -> dict[str, float]:
        """The latest gauge values for whichever canonical bucket contains
        `at` (`FR-MET-028`) — `{}` if the instance or bucket is unknown.
        """
        found = self._existing_instance(instance_id)
        if found is None:
            return {}
        ring, lock = found
        with lock:
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
        found = self._existing_instance(instance_id)
        if found is None:
            return 0
        ring, lock = found
        with lock:
            return sum(
                1
                for bucket in self._in_range_buckets(
                    ring, from_utc=from_utc, to_utc=to_utc
                )
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
        found = self._existing_instance(instance_id)
        if found is None:
            return []
        ring, lock = found

        merged: dict[DimKey, tuple[dict[str, Decimal], dict[str, Histogram]]] = {}

        with lock:
            in_range = self._in_range_buckets(ring, from_utc=from_utc, to_utc=to_utc)
            for bucket in in_range:
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
