"""FR-QRY-004: the store MUST be safe under concurrent read/write via a
per-instance lock, not one global lock.
"""

import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore
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
