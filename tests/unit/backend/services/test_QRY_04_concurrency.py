"""FR-QRY-004: the store MUST be safe under concurrent read/write via a
per-instance lock, not one global lock.
"""

import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

BUCKET_START = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
NOW = BUCKET_START + timedelta(seconds=5)


def _snapshot(*, instance_id: str, agent_id: str, symbol: str) -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id=agent_id,
        application="Magic",
        instance_id=instance_id,
        bucket_start_utc=BUCKET_START,
        bucket_seconds=10,
        series=[
            SeriesEntry(
                dimensions={"symbol": symbol},
                counters={"orders_submitted": Decimal(1)},
            )
        ],
    )


def test_existing_instance_does_not_raise_on_a_half_created_instance() -> None:
    """`_get_or_create_instance` sets `_rings[instance_id]` before
    `_instance_locks[instance_id]`, both inside one `_locks_guard` section.
    A lock-free reader (`_existing_instance`, used by `read`/`gauges`/
    `is_warming_up`/`restarted_bucket_count`) can observe the ring without
    the lock existing yet if it lands in that window — it must return
    `None` (nothing here yet), not raise `KeyError`. Simulated directly
    rather than raced, since the real window is a handful of bytecodes wide
    and not reliably hittable by thread-timing luck.
    """
    store = MetricStore(StreamProcessorConfig())
    store._rings["half-created"] = []  # ring present, lock deliberately absent

    assert store._existing_instance("half-created") is None


def test_shed_oldest_tier_does_not_raise_on_a_half_created_instance() -> None:
    """`_shed_oldest_tier` iterates `_rings.items()` and indexed
    `_instance_locks` directly — the same half-created-instance window as
    `_existing_instance`. A shed pass racing a brand-new instance's first
    write must skip it gracefully, not raise `KeyError`.
    """
    store = MetricStore(StreamProcessorConfig())
    store._rings["half-created"] = []

    shed_count = store._shed_oldest_tier(BUCKET_START)

    assert shed_count == 0


def test_two_instances_get_two_independent_locks() -> None:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        _snapshot(instance_id="a", agent_id="agent-1", symbol="AAA"),
        canonical_start=BUCKET_START,
        now=NOW,
    )
    store.merge(
        _snapshot(instance_id="b", agent_id="agent-1", symbol="AAA"),
        canonical_start=BUCKET_START,
        now=NOW,
    )

    assert store._instance_locks["a"] is not store._instance_locks["b"]


def test_a_write_to_one_instance_does_not_block_a_write_to_another() -> None:
    store = MetricStore(StreamProcessorConfig())
    # Touch "b" once so its lock exists before the holder thread grabs it.
    store.merge(
        _snapshot(instance_id="b", agent_id="agent-1", symbol="AAA"),
        canonical_start=BUCKET_START,
        now=NOW,
    )

    release = threading.Event()
    holding = threading.Event()

    def hold_b_lock() -> None:
        with store._instance_locks["b"]:
            holding.set()
            release.wait(timeout=5)

    holder = threading.Thread(target=hold_b_lock)
    holder.start()
    try:
        assert holding.wait(timeout=5)

        completed = threading.Event()

        def write_a() -> None:
            store.merge(
                _snapshot(instance_id="a", agent_id="agent-1", symbol="AAA"),
                canonical_start=BUCKET_START,
                now=NOW,
            )
            completed.set()

        writer = threading.Thread(target=write_a)
        writer.start()
        writer.join(timeout=2)
        assert completed.is_set(), "write to instance 'a' blocked on instance 'b's lock"
    finally:
        release.set()
        holder.join(timeout=5)


def test_concurrent_merges_into_the_same_instance_do_not_lose_updates() -> None:
    """A per-instance lock must still serialise writes *within* one
    instance — safety here is not just 'different instances don't block
    each other', it's also 'one instance's ring is never corrupted by
    concurrent writers'.
    """
    store = MetricStore(StreamProcessorConfig())
    symbols = [f"SYM{i}" for i in range(50)]

    def write(symbol: str) -> None:
        store.merge(
            _snapshot(instance_id="shared", agent_id="agent-1", symbol=symbol),
            canonical_start=BUCKET_START,
            now=NOW,
        )

    threads = [threading.Thread(target=write, args=(symbol,)) for symbol in symbols]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    groups = store.read(
        "shared",
        from_utc=BUCKET_START,
        to_utc=BUCKET_START + timedelta(seconds=10),
        group_by=("symbol",),
    )
    assert len(groups) == len(symbols)
    assert sum(group.counters["orders_submitted"] for group in groups) == len(symbols)


def test_concurrent_drops_across_many_instances_are_all_counted() -> None:
    """`dropped_after_retention_total` is a single store-wide counter
    incremented from many different instances' own per-instance-locked
    sections — a bare `+= 1` there could lose an update when different
    instances are written to concurrently (each holding a *different* lock,
    so the increments themselves race). `_counters_lock` must prevent that.
    """
    config = StreamProcessorConfig(
        canonical_bucket_seconds=10,
        retention_window_seconds=10,  # capacity == 1
        max_bucket_age_seconds=10,
    )
    store = MetricStore(config)
    far_future = BUCKET_START + timedelta(seconds=config.retention_window_seconds * 5)
    instance_count = 50

    def drop_one(instance_id: str) -> None:
        # canonical_start (BUCKET_START) is far outside retention relative
        # to `now` (far_future) — every one of these is rejected as too old.
        store.merge(
            _snapshot(instance_id=instance_id, agent_id="agent-1", symbol="AAA"),
            canonical_start=BUCKET_START,
            now=far_future,
        )

    threads = [
        threading.Thread(target=drop_one, args=(f"instance-{i}",))
        for i in range(instance_count)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert store.dropped_after_retention_total == instance_count


def test_concurrent_stale_rejections_across_many_instances_are_all_counted() -> None:
    """`StreamProcessor.dropped_buckets_total` is incremented outside any
    per-instance lock — the same race class `MetricStore`'s own counters
    were fixed for. A real Ingestion Service would call `process_snapshot`
    from a FastAPI threadpool, so concurrent requests are the realistic
    case, not an edge case.
    """
    config = StreamProcessorConfig(max_bucket_age_seconds=10)
    processor = StreamProcessor(config)
    far_future = BUCKET_START + timedelta(seconds=config.max_bucket_age_seconds * 5)
    instance_count = 50

    def reject_one(instance_id: str) -> None:
        processor.process_snapshot(
            _snapshot(instance_id=instance_id, agent_id="agent-1", symbol="AAA"),
            now=far_future,
        )

    threads = [
        threading.Thread(target=reject_one, args=(f"instance-{i}",))
        for i in range(instance_count)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert processor.dropped_buckets_total == instance_count
