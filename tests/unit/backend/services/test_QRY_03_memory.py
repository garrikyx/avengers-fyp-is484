"""FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the
store logs a warning above `memoryWarnPercent` and sheds the oldest
retention tier above `memorySheddPercent` rather than being OOM-killed.

`estimated_memory_bytes()` is monkeypatched in the warn/shed tests rather
than filled by real series, so these assert `tick()`'s threshold behaviour
without needing millions of series to cross a 4096MB default budget.
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.metric_store import (
    _MEMORY_CHECK_INTERVAL_SECONDS,
    MetricStore,
)
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

DIMS = {"session": "MAGIC->EXCH1", "symbol": "ABC"}


def _snapshot(*, instance_id: str, bucket_start_utc: datetime) -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id="agent-a",
        application="Magic",
        instance_id=instance_id,
        bucket_start_utc=bucket_start_utc,
        bucket_seconds=10,
        series=[
            SeriesEntry(dimensions=DIMS, counters={"orders_submitted": Decimal(1)})
        ],
    )


def test_estimated_memory_bytes_is_zero_for_an_empty_store() -> None:
    store = MetricStore(StreamProcessorConfig())
    assert store.estimated_memory_bytes() == 0


def test_estimated_memory_bytes_grows_with_merged_series_and_shrinks_on_eviction() -> (
    None
):
    config = StreamProcessorConfig(
        canonical_bucket_seconds=10,
        retention_window_seconds=100,
        max_bucket_age_seconds=100,
    )
    store = MetricStore(config)
    now = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    store.merge(
        _snapshot(instance_id="target", bucket_start_utc=now),
        canonical_start=now,
        now=now,
    )

    used = store.estimated_memory_bytes()
    assert used > 0

    # Advance well past retention and sweep — the merged bucket's *content*
    # must be evicted and the gauge must drop accordingly, but the ring's
    # own allocated shell stays resident (it's reused, not freed) — so the
    # estimate shrinks, it does not zero out.
    far_future = now + timedelta(seconds=config.retention_window_seconds * 2)
    store.tick(far_future)
    assert 0 < store.estimated_memory_bytes() < used


def test_tick_logs_a_warning_above_memory_warn_percent_but_does_not_shed(
    monkeypatch, caplog
) -> None:
    config = StreamProcessorConfig(
        memory_limit_mb=100, memory_warn_percent=75, memory_shed_percent=90
    )
    store = MetricStore(config)
    monkeypatch.setattr(
        store, "estimated_memory_bytes", lambda: int(100 * 1024 * 1024 * 0.80)
    )

    with caplog.at_level(logging.WARNING):
        store.tick(datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC))

    assert any("memory" in record.message.lower() for record in caplog.records)
    assert store.shed_buckets_total == 0


def test_tick_sheds_the_oldest_half_of_every_ring_above_memory_shed_percent(
    monkeypatch,
) -> None:
    config = StreamProcessorConfig(
        canonical_bucket_seconds=10,
        retention_window_seconds=100,  # capacity == 10
        max_bucket_age_seconds=100,
        memory_limit_mb=100,
        memory_warn_percent=75,
        memory_shed_percent=90,
    )
    store = MetricStore(config)
    now = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    for i in range(10):
        bucket_start = now - timedelta(seconds=10 * (9 - i))
        store.merge(
            _snapshot(instance_id="target", bucket_start_utc=bucket_start),
            canonical_start=bucket_start,
            now=now,
        )

    filled_before = sum(1 for b in store._rings["target"] if b.start is not None)
    assert filled_before == 10

    monkeypatch.setattr(
        store, "estimated_memory_bytes", lambda: int(100 * 1024 * 1024 * 0.95)
    )
    store.tick(now)

    filled_after = sum(1 for b in store._rings["target"] if b.start is not None)
    assert filled_after < filled_before
    assert store.shed_buckets_total == filled_before - filled_after
    assert store.shed_buckets_total > 0


def test_merge_alone_can_trigger_shedding_without_an_external_tick(monkeypatch) -> None:
    """Nothing in this repo calls `tick()` on a schedule yet — the real
    write path (`merge()`) must be able to trip the shed threshold on its
    own, or `FR-QRY-003` protects nothing in a running system.
    """
    config = StreamProcessorConfig(
        canonical_bucket_seconds=10,
        retention_window_seconds=100,  # capacity == 10
        max_bucket_age_seconds=100,
        memory_limit_mb=100,
        memory_warn_percent=75,
        memory_shed_percent=90,
    )
    store = MetricStore(config)
    now = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    for i in range(10):
        bucket_start = now - timedelta(seconds=10 * (9 - i))
        store.merge(
            _snapshot(instance_id="target", bucket_start_utc=bucket_start),
            canonical_start=bucket_start,
            now=now,
        )

    filled_before = sum(1 for b in store._rings["target"] if b.start is not None)
    assert filled_before == 10
    # The (unthrottled, first-ever) check during setup saw real, low usage —
    # it must not have shed anything on its own.
    assert store.shed_buckets_total == 0

    monkeypatch.setattr(
        store, "estimated_memory_bytes", lambda: int(100 * 1024 * 1024 * 0.95)
    )

    # One more merge, comfortably past the throttle interval but still
    # within the same 10s canonical bucket as `now` (so ordinary retention
    # eviction's own window doesn't shift and cannot explain what gets
    # evicted below) — `store.tick()` is never called anywhere in this test.
    trigger_now = now + timedelta(seconds=_MEMORY_CHECK_INTERVAL_SECONDS + 1)
    store.merge(
        _snapshot(instance_id="target", bucket_start_utc=now),
        canonical_start=now,
        now=trigger_now,
    )

    filled_after = sum(1 for b in store._rings["target"] if b.start is not None)
    assert filled_after < filled_before
    assert store.shed_buckets_total > 0


def test_merges_within_the_throttle_interval_do_not_re_check_memory(
    monkeypatch,
) -> None:
    """The write-path check must not cost an `estimated_memory_bytes()`
    scan on every single `merge()` call — only throttled, or it reintroduces
    the whole-store cost the per-ring eviction scoping elsewhere was written
    to avoid.
    """
    store = MetricStore(StreamProcessorConfig())
    now = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    calls = 0
    real_estimate = store.estimated_memory_bytes

    def counting_estimate() -> int:
        nonlocal calls
        calls += 1
        return real_estimate()

    monkeypatch.setattr(store, "estimated_memory_bytes", counting_estimate)

    for i in range(5):
        store.merge(
            _snapshot(instance_id="target", bucket_start_utc=now),
            canonical_start=now,
            now=now + timedelta(milliseconds=i),
        )

    assert calls == 1


def test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell() -> (
    None
):
    """`_get_or_create_instance` eagerly allocates a full-`capacity` ring of
    real `_CanonicalBucket` objects the moment an instance is first touched,
    regardless of how much data it ever sends. Once this instance's one
    bucket ages out, the gauge must still reflect the `capacity` real shell
    objects still resident — not read as 0, which would make a replica with
    many lightly-used instances invisible to its own memory gauge.
    """
    config = StreamProcessorConfig(
        canonical_bucket_seconds=10,
        retention_window_seconds=100,  # capacity == 10
        max_bucket_age_seconds=100,
    )
    store = MetricStore(config)
    now = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    store.merge(
        _snapshot(instance_id="quiet", bucket_start_utc=now),
        canonical_start=now,
        now=now,
    )
    used_with_data = store.estimated_memory_bytes()

    far_future = now + timedelta(seconds=config.retention_window_seconds * 2)
    store.tick(far_future)

    assert len(store._rings["quiet"]) == 10  # the shell is still fully allocated
    used_after_content_eviction = store.estimated_memory_bytes()
    # Content is gone, so this is less than it was — but the still-resident
    # shell must not have vanished from the estimate entirely.
    assert 0 < used_after_content_eviction < used_with_data


def test_shedding_never_evicts_a_bucket_written_in_the_same_cycle_at_small_capacity(
    monkeypatch,
) -> None:
    """At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must
    still keep at least the current bucket (`keep_count = max(capacity // 2,
    1)`) rather than shedding the bucket a caller just wrote in this same
    cycle. Shedding at `capacity == 1` should be a no-op, since there is no
    real "older half" to speak of.
    """
    config = StreamProcessorConfig(
        canonical_bucket_seconds=10,
        retention_window_seconds=10,  # capacity == 1
        max_bucket_age_seconds=10,
        memory_limit_mb=100,
        memory_warn_percent=75,
        memory_shed_percent=90,
    )
    store = MetricStore(config)
    now = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    store.merge(
        _snapshot(instance_id="target", bucket_start_utc=now),
        canonical_start=now,
        now=now,
    )
    assert sum(1 for b in store._rings["target"] if b.start is not None) == 1

    monkeypatch.setattr(
        store, "estimated_memory_bytes", lambda: int(100 * 1024 * 1024 * 0.95)
    )
    trigger_now = now + timedelta(seconds=_MEMORY_CHECK_INTERVAL_SECONDS + 1)
    store.merge(
        _snapshot(instance_id="target", bucket_start_utc=now),
        canonical_start=now,
        now=trigger_now,
    )

    assert sum(1 for b in store._rings["target"] if b.start is not None) == 1
    assert store.shed_buckets_total == 0
