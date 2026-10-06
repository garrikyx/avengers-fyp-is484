"""Bounded asynchronous hand-off for HTTP ingestion."""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from datetime import UTC, datetime

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import (
    WIRE_DIMENSION_KEYS,
    Heartbeat,
    TelemetryEvent,
)
from telemetry_shared.models.snapshot import Snapshot

from telemetry_backend.services.stream_processor import (
    StreamProcessor,
    align_to_canonical,
)

_SeriesKey = tuple[tuple[str, str], ...]
_CardinalityBucketKey = tuple[str, int]

# spec 004 §5 / FR-ING-007. The vocabulary itself is shared with the agent
# (FR-MET-030's "one shared table") so the two sides cannot drift.
ALLOWED_DIMENSION_KEYS: frozenset[str] = WIRE_DIMENSION_KEYS

# spec 003 §4 is the security allowlist for values that may leave an agent.
# The backend repeats that allowlist at its own trust boundary (NFR-SEC-002).
ALLOWED_EVENT_FIELD_KEYS: frozenset[str] = frozenset(
    {
        "fixVersion",
        "msgType",
        "seqNum",
        "senderCompId",
        "targetCompId",
        "sendingTime",
        "transactTime",
        "clOrdIdHash",
        "origClOrdIdHash",
        "orderIdHash",
        "execIdHash",
        "execType",
        "ordStatus",
        "symbol",
        "side",
        "ordType",
        "orderQty",
        "lastQty",
        "cumQty",
        "leavesQty",
        "ordRejReason",
        "rejectReasonText",
        "refSeqNum",
        "refMsgType",
        "sessionRejectReason",
    }
)


@dataclass(slots=True, frozen=True)
class IngestionValidationIssue:
    """One safe, field-level reason an ingestion request was rejected."""

    code: str
    field: str
    issue: str


@dataclass(slots=True, frozen=True)
class AcceptedIngestion:
    """Validated data ready for downstream processing."""

    snapshots: tuple[Snapshot, ...] = ()
    events: tuple[TelemetryEvent, ...] = ()
    alerts: tuple[AlertEvent, ...] = ()
    heartbeat: Heartbeat | None = None


class IngestionService:
    """Owns a bounded queue and one background consumer."""

    def __init__(
        self,
        *,
        queue_size: int = 10_000,
        stream_processor: StreamProcessor | None = None,
    ) -> None:
        self._queue: asyncio.Queue[AcceptedIngestion] = asyncio.Queue(
            maxsize=queue_size
        )
        self.stream_processor = stream_processor or StreamProcessor()
        self.rejected_payloads_total = 0
        self.queue_overflow_total = 0
        self.accepted_payloads_total = 0
        self._cardinality_lock = threading.Lock()
        self._admitted_series_by_bucket: dict[
            _CardinalityBucketKey, dict[_SeriesKey, int]
        ] = {}

    @property
    def queue_depth(self) -> int:
        return self._queue.qsize()

    def record_rejection(self) -> None:
        self.rejected_payloads_total += 1

    def validate_and_reserve(
        self, item: AcceptedIngestion
    ) -> tuple[IngestionValidationIssue, ...]:
        """Apply the backend-side allowlists and bucket cardinality cap.

        Pydantic has already validated the wire shape before this method is
        called. These checks validate dictionary *keys*, whose vocabulary is
        security-sensitive and cannot be expressed by ``dict[str, ...]``'s
        value type alone. They run before enqueue so a caller receives a
        deterministic 400 instead of a series being silently discarded later
        by the Metric Store's final memory-safety guard.
        """
        issues: list[IngestionValidationIssue] = []
        candidate_series = self._series_by_canonical_bucket(item)

        for snapshot_index, snapshot in enumerate(item.snapshots):
            for series_index, series in enumerate(snapshot.series):
                for key in sorted(set(series.dimensions) - ALLOWED_DIMENSION_KEYS):
                    issues.append(
                        IngestionValidationIssue(
                            code="unknown_dimension",
                            field=(
                                f"snapshots.{snapshot_index}.series.{series_index}."
                                f"dimensions.{_safe_key(key)}"
                            ),
                            issue="dimension key is not allowlisted",
                        )
                    )

        for event_index, event in enumerate(item.events):
            for key in sorted(set(event.dimensions) - ALLOWED_DIMENSION_KEYS):
                issues.append(
                    IngestionValidationIssue(
                        code="unknown_dimension",
                        field=f"events.{event_index}.dimensions.{_safe_key(key)}",
                        issue="dimension key is not allowlisted",
                    )
                )
            for key in sorted(set(event.fields) - ALLOWED_EVENT_FIELD_KEYS):
                issues.append(
                    IngestionValidationIssue(
                        code="invalid_field",
                        field=f"events.{event_index}.fields.{_safe_key(key)}",
                        issue="event field key is not allowlisted",
                    )
                )

        if issues:
            return tuple(issues)

        with self._cardinality_lock:
            self._discard_expired_cardinality_reservations()
            for bucket_key, series_keys in candidate_series.items():
                admitted = self._admitted_series_by_bucket.get(bucket_key, {})
                total = len(set(admitted) | series_keys)
                if total <= self.stream_processor.config.max_series_per_bucket:
                    continue
                snapshot_index = next(
                    index
                    for index, snapshot in enumerate(item.snapshots)
                    if self._canonical_bucket_key(snapshot) == bucket_key
                )
                issues.append(
                    IngestionValidationIssue(
                        code="cardinality_exceeded",
                        field=f"snapshots.{snapshot_index}.series",
                        issue=(
                            f"bucket would contain {total} distinct series; "
                            "maxSeriesPerBucket is "
                            f"{self.stream_processor.config.max_series_per_bucket}"
                        ),
                    )
                )

            if issues:
                return tuple(issues)

            for bucket_key, series_keys in candidate_series.items():
                admitted = self._admitted_series_by_bucket.setdefault(bucket_key, {})
                for series_key in series_keys:
                    admitted[series_key] = admitted.get(series_key, 0) + 1

        return ()

    def release_cardinality_reservation(self, item: AcceptedIngestion) -> None:
        """Undo an admission reservation when the bounded queue is full."""
        with self._cardinality_lock:
            for (
                bucket_key,
                series_keys,
            ) in self._series_by_canonical_bucket(item).items():
                admitted = self._admitted_series_by_bucket.get(bucket_key)
                if admitted is None:
                    continue
                for series_key in series_keys:
                    count = admitted.get(series_key)
                    if count is None:
                        continue
                    if count == 1:
                        del admitted[series_key]
                    else:
                        admitted[series_key] = count - 1
                if not admitted:
                    del self._admitted_series_by_bucket[bucket_key]

    def _series_by_canonical_bucket(
        self, item: AcceptedIngestion
    ) -> dict[_CardinalityBucketKey, set[_SeriesKey]]:
        series_by_bucket: dict[_CardinalityBucketKey, set[_SeriesKey]] = {}
        for snapshot in item.snapshots:
            series_by_bucket.setdefault(
                self._canonical_bucket_key(snapshot), set()
            ).update(
                tuple(sorted(series.dimensions.items())) for series in snapshot.series
            )
        return series_by_bucket

    def _canonical_bucket_key(self, snapshot: Snapshot) -> _CardinalityBucketKey:
        canonical_start = align_to_canonical(
            snapshot.bucket_start_utc,
            self.stream_processor.config.canonical_bucket_seconds,
        )
        return snapshot.instance_id, int(canonical_start.timestamp())

    def _discard_expired_cardinality_reservations(self) -> None:
        config = self.stream_processor.config
        current_epoch = int(
            datetime.now(UTC).timestamp() // config.canonical_bucket_seconds
        )
        retention_buckets = max(
            config.retention_window_seconds // config.canonical_bucket_seconds,
            1,
        )
        oldest_valid_epoch = current_epoch - retention_buckets + 1
        for bucket_key in tuple(self._admitted_series_by_bucket):
            if bucket_key[1] < oldest_valid_epoch:
                del self._admitted_series_by_bucket[bucket_key]

    def enqueue(self, item: AcceptedIngestion) -> bool:
        """Try to hand off without waiting; False means callers return 503."""
        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull:
            self.queue_overflow_total += 1
            return False
        self.accepted_payloads_total += 1
        return True

    async def run(self) -> None:
        """Keep store work off FastAPI's request path.

        A single consumer preserves the existing in-memory store's sequential
        mutation semantics. `to_thread` also ensures a merge never occupies
        the event loop that accepts the next request.
        """
        while True:
            item = await self._queue.get()
            try:
                if item.snapshots:
                    await asyncio.to_thread(
                        self.stream_processor.process_batch,
                        list(item.snapshots),
                        now=datetime.now(UTC),
                    )
            finally:
                self._queue.task_done()


def _safe_key(key: str) -> str:
    """Bound an attacker-controlled key before including it in an error path."""
    return key[:100]
