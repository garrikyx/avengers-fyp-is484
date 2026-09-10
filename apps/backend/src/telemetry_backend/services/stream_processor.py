"""Stream Processor (spec 006 §3): window alignment and the ingest-side half
of the late/old-bucket decision, sitting between the (future) Ingestion
Service and the `MetricStore`.

`FR-STM-001`'s alignment rule, stated once here and nowhere else: a
snapshot's `bucketStartUtc` is floor-divided onto the backend's own
canonical grid —

    canonicalStart = floor(bucketStartUtc / canonicalBucketSeconds) *
                      canonicalBucketSeconds

— the same rule the agent already applies to its own ring buffer
(`telemetry_agent.metrics.aggregator.MetricsAggregator._bucket_start`).
This is deterministic and needs no agent cooperation: it is correct
whether the drift is phase (clock skew, process-start offset) or width
(an agent configured with a different `bucketSeconds` than the backend's
canonical grid). The one thing it does not do is split a snapshot across
two canonical buckets when its width is wider than the canonical grid —
that would require guessing a sub-bucket distribution the backend has no
data for, which is precisely the kind of fabricated precision spec 004/006
avoid elsewhere (`FR-QRY-012`'s `approximate`/`null` conventions).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from telemetry_shared.models.snapshot import Snapshot

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore

BUCKET_TOO_OLD = "bucket_too_old"


def align_to_canonical(
    bucket_start_utc: datetime, canonical_bucket_seconds: int
) -> datetime:
    """FR-STM-001: floor `bucket_start_utc` onto the canonical grid."""
    epoch = bucket_start_utc.timestamp()
    canonical_epoch = (epoch // canonical_bucket_seconds) * canonical_bucket_seconds
    return datetime.fromtimestamp(canonical_epoch, tz=UTC)


@dataclass(slots=True, frozen=True)
class SnapshotOutcome:
    accepted: bool
    canonical_bucket_start: datetime
    reason: str | None = None
    detail: str | None = None


class StreamProcessor:
    """Aligns, age-checks, and merges snapshots into a `MetricStore`.

    Non-blocking and side-effect-free beyond the store it owns: no I/O, no
    auth, no dedupe — those are the Ingestion Service's job (`FR-ING-002`
    through `FR-ING-004`), upstream of this stage.
    """

    def __init__(
        self,
        config: StreamProcessorConfig | None = None,
        store: MetricStore | None = None,
    ) -> None:
        self._config = config or StreamProcessorConfig()
        self.store = store or MetricStore(self._config)
        # FR-STM-005: dropped (too-old) buckets MUST be observable, not
        # silently discarded. A future `/metrics` endpoint reads this.
        self.dropped_buckets_total = 0

    def process_snapshot(
        self, snapshot: Snapshot, *, now: datetime | None = None
    ) -> SnapshotOutcome:
        now = now or datetime.now(UTC)
        canonical_start = align_to_canonical(
            snapshot.bucket_start_utc, self._config.canonical_bucket_seconds
        )
        age_seconds = (now - canonical_start).total_seconds()

        if age_seconds > self._config.max_bucket_age_seconds:
            self.dropped_buckets_total += 1
            age_human = f"{age_seconds:.0f}s"
            limit_human = f"{self._config.max_bucket_age_seconds}s"
            return SnapshotOutcome(
                accepted=False,
                canonical_bucket_start=canonical_start,
                reason=BUCKET_TOO_OLD,
                detail=f"bucketStartUtc is {age_human} old; limit is {limit_human}",
            )

        self.store.merge(snapshot, canonical_start=canonical_start, now=now)
        return SnapshotOutcome(accepted=True, canonical_bucket_start=canonical_start)

    def process_batch(
        self, snapshots: list[Snapshot], *, now: datetime | None = None
    ) -> list[SnapshotOutcome]:
        now = now or datetime.now(UTC)
        return [self.process_snapshot(s, now=now) for s in snapshots]
