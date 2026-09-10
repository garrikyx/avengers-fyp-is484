"""FR-STM-001, FR-ING-005, FR-STM-005: canonical window alignment, rejection
of buckets older than `maxBucketAge`, and late-but-in-window merge.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.stream_processor import (
    BUCKET_TOO_OLD,
    StreamProcessor,
    align_to_canonical,
)
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

DIMS = {"session": "MAGIC->EXCH1", "symbol": "ABC"}


def _snapshot(
    *,
    agent_id: str = "agent-a",
    instance_id: str = "magic-prod-01",
    bucket_start_utc: datetime,
    bucket_seconds: int = 10,
    counters: dict[str, int] | None = None,
    restarted: bool = False,
    gauges: dict[str, float] | None = None,
) -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id=agent_id,
        application="Magic",
        instance_id=instance_id,
        bucket_start_utc=bucket_start_utc,
        bucket_seconds=bucket_seconds,
        restarted=restarted,
        series=[
            SeriesEntry(
                dimensions=DIMS,
                counters={k: Decimal(v) for k, v in (counters or {}).items()},
            )
        ],
        gauges=gauges or {},
    )


def test_alignment_floors_a_phase_shifted_bucket_onto_the_canonical_grid() -> None:
    misaligned = datetime(2026, 6, 12, 4, 0, 37, tzinfo=UTC)
    expected = datetime(2026, 6, 12, 4, 0, 30, tzinfo=UTC)
    assert align_to_canonical(misaligned, 10) == expected


def test_alignment_is_a_no_op_when_already_on_the_grid() -> None:
    aligned = datetime(2026, 6, 12, 4, 0, 30, tzinfo=UTC)
    assert align_to_canonical(aligned, 10) == aligned


def test_two_raw_bucket_starts_in_one_canonical_window_merge_together() -> None:
    """An agent's own bucket boundary doesn't line up with the canonical
    grid, but two of its snapshots that both fall within the same canonical
    10s window must land in the same store bucket, not two.
    """
    processor = StreamProcessor(StreamProcessorConfig())
    now = datetime(2026, 6, 12, 4, 0, 40, tzinfo=UTC)

    first = _snapshot(
        bucket_start_utc=datetime(2026, 6, 12, 4, 0, 31, tzinfo=UTC),
        counters={"orders_submitted": 5},
    )
    second = _snapshot(
        bucket_start_utc=datetime(2026, 6, 12, 4, 0, 38, tzinfo=UTC),
        counters={"orders_acked": 3},
    )

    outcome_1 = processor.process_snapshot(first, now=now)
    outcome_2 = processor.process_snapshot(second, now=now)

    assert outcome_1.accepted and outcome_2.accepted
    assert outcome_1.canonical_bucket_start == outcome_2.canonical_bucket_start

    groups = processor.store.read(
        "magic-prod-01",
        from_utc=datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC),
        to_utc=datetime(2026, 6, 12, 4, 1, 0, tzinfo=UTC),
    )
    assert len(groups) == 1
    assert groups[0].counters["orders_submitted"] == 5
    assert groups[0].counters["orders_acked"] == 3


def test_bucket_older_than_max_bucket_age_is_rejected_and_counted_as_dropped() -> None:
    config = StreamProcessorConfig(max_bucket_age_seconds=3600)
    processor = StreamProcessor(config)
    now = datetime(2026, 6, 12, 6, 0, 0, tzinfo=UTC)
    too_old = _snapshot(
        bucket_start_utc=now - timedelta(hours=2, minutes=12),
        counters={"orders_submitted": 1},
    )

    outcome = processor.process_snapshot(too_old, now=now)

    assert outcome.accepted is False
    assert outcome.reason == BUCKET_TOO_OLD
    assert processor.dropped_buckets_total == 1
    groups = processor.store.read(
        "magic-prod-01", from_utc=now - timedelta(hours=6), to_utc=now
    )
    assert groups == []


def test_late_but_still_within_max_bucket_age_is_merged_not_dropped() -> None:
    config = StreamProcessorConfig(max_bucket_age_seconds=3600)
    processor = StreamProcessor(config)
    now = datetime(2026, 6, 12, 6, 0, 0, tzinfo=UTC)
    late = _snapshot(
        bucket_start_utc=now - timedelta(minutes=45),
        counters={"orders_submitted": 7},
    )

    outcome = processor.process_snapshot(late, now=now)

    assert outcome.accepted is True
    assert processor.dropped_buckets_total == 0
    groups = processor.store.read(
        "magic-prod-01", from_utc=now - timedelta(hours=1), to_utc=now
    )
    assert groups[0].counters["orders_submitted"] == 7


def test_merge_is_associative_regardless_of_arrival_order() -> None:
    """FR-ING-005: out-of-order snapshots for the same bucket must still
    merge to the same result, in either arrival order.
    """
    now = datetime(2026, 6, 12, 4, 1, 0, tzinfo=UTC)
    bucket_start = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)

    store_forward = MetricStore(StreamProcessorConfig())
    store_reversed = MetricStore(StreamProcessorConfig())
    snap_a = _snapshot(
        agent_id="agent-a",
        bucket_start_utc=bucket_start,
        counters={"orders_submitted": 4},
    )
    snap_b = _snapshot(
        agent_id="agent-b",
        bucket_start_utc=bucket_start,
        counters={"orders_submitted": 9},
    )

    store_forward.merge(snap_a, canonical_start=bucket_start, now=now)
    store_forward.merge(snap_b, canonical_start=bucket_start, now=now)
    store_reversed.merge(snap_b, canonical_start=bucket_start, now=now)
    store_reversed.merge(snap_a, canonical_start=bucket_start, now=now)

    window_end = bucket_start + timedelta(seconds=10)
    forward_groups = store_forward.read(
        "magic-prod-01", from_utc=bucket_start, to_utc=window_end
    )
    reversed_groups = store_reversed.read(
        "magic-prod-01", from_utc=bucket_start, to_utc=window_end
    )
    assert forward_groups[0].counters == reversed_groups[0].counters == {
        "orders_submitted": 13
    }


def test_config_rejects_max_bucket_age_greater_than_retention_window() -> None:
    """A snapshot the StreamProcessor accepts as within maxBucketAge must
    still be inside the store's own retention window, or merge() would have
    to drop it right after accepting it. Refusing the config outright is
    stronger than relying on a counter to catch that at runtime.
    """
    with pytest.raises(ValueError, match="max_bucket_age_seconds"):
        StreamProcessorConfig(
            max_bucket_age_seconds=7200, retention_window_seconds=3600
        )


def test_gauges_take_the_latest_value_by_native_time_not_by_arrival_order() -> None:
    """FR-MET-028 + FR-ING-005 together: gauges are last-write-wins, but
    this stage must accept out-of-order arrival — so "last" has to mean
    latest by the snapshot's own bucketStartUtc, not whichever snapshot
    merge() happened to see most recently.
    """
    store = MetricStore(StreamProcessorConfig())
    canonical_start = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    now = canonical_start + timedelta(seconds=30)

    newer = _snapshot(
        bucket_start_utc=canonical_start + timedelta(seconds=5),
        gauges={"pending_orders": 42},
    )
    older_arriving_late = _snapshot(
        bucket_start_utc=canonical_start,
        gauges={"pending_orders": 7},
    )

    # The newer native bucket is processed first...
    store.merge(newer, canonical_start=canonical_start, now=now)
    # ...then the older one arrives late and must not clobber it.
    store.merge(older_arriving_late, canonical_start=canonical_start, now=now)

    assert store.gauges("magic-prod-01", at=canonical_start) == {"pending_orders": 42}


def test_a_stale_direct_merge_is_counted_not_silently_dropped() -> None:
    """FR-STM-005: even if something calls MetricStore.merge() directly
    with a canonical_start that has already aged out of the store's own
    retention (bypassing the StreamProcessor's own maxBucketAge check),
    the drop must be observable, never a silent no-op.
    """
    config = StreamProcessorConfig(
        max_bucket_age_seconds=10, retention_window_seconds=10
    )
    store = MetricStore(config)
    now = datetime(2026, 6, 12, 5, 0, 0, tzinfo=UTC)
    long_gone = _snapshot(
        bucket_start_utc=now - timedelta(hours=1), counters={"orders_submitted": 1}
    )

    store.merge(long_gone, canonical_start=now - timedelta(hours=1), now=now)

    assert store.dropped_after_retention_total == 1
    groups = store.read(
        "magic-prod-01", from_utc=now - timedelta(hours=2), to_utc=now
    )
    assert groups == []
