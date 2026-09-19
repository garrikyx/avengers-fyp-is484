"""Regression tests for two efficiency fixes: `merge()` must not sweep
every instance's ring on every write, and `read()`/`restarted_bucket_count`
must not scan a whole ring for a narrow time range. Both are provable only
by instrumentation, since a naive full scan and a bounded scan return the
same *correct* result for a well-formed query — the difference is purely
how much work it costs to get there.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore
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


class _CountingRing:
    """Wraps a ring's buckets without a `list`'s own `__iter__` — a plain
    `for x in ring` (the naive full scan this guards against) then falls
    back to the classic sequence protocol, calling `__getitem__` once per
    index until `IndexError`. Subclassing `list` instead would make this
    a no-op: `list.__iter__` bypasses `__getitem__` entirely in CPython,
    so a full scan would never increment `getitem_calls` and the test
    would pass whether or not the code under test still did one.
    """

    def __init__(self, items: object) -> None:
        self._items = list(items)
        self.getitem_calls = 0

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int):
        self.getitem_calls += 1
        return self._items[index]


def test_merge_evicts_only_the_ring_it_writes_to(monkeypatch) -> None:
    """The old `tick()` swept every instance's ring on every merge —
    O(instances x capacity) regardless of how many instances the write
    actually concerned. `merge()` must call `_evict_stale` exactly once,
    against only the instance being written to.
    """
    store = MetricStore(StreamProcessorConfig())
    now = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    for i in range(20):
        store.merge(
            _snapshot(instance_id=f"other-{i}", bucket_start_utc=now),
            canonical_start=now,
            now=now,
        )

    evicted_rings: list[object] = []
    original_evict_stale = MetricStore._evict_stale

    def spy(self: MetricStore, ring: object, evict_now: datetime) -> None:
        evicted_rings.append(ring)
        original_evict_stale(self, ring, evict_now)

    monkeypatch.setattr(MetricStore, "_evict_stale", spy)

    store.merge(
        _snapshot(instance_id="target", bucket_start_utc=now),
        canonical_start=now,
        now=now,
    )

    assert len(evicted_rings) == 1
    assert evicted_rings[0] is store._rings["target"]


def test_read_indexes_only_the_requested_span_not_the_whole_ring() -> None:
    """A query over one 10s bucket on a 6h-capacity (2160-bucket) ring
    must not touch anywhere near all 2160 slots.
    """
    store = MetricStore(StreamProcessorConfig())
    now = datetime(2026, 6, 12, 10, 0, 0, tzinfo=UTC)
    store.merge(
        _snapshot(instance_id="target", bucket_start_utc=now),
        canonical_start=now,
        now=now,
    )

    counting_ring = _CountingRing(store._rings["target"])
    store._rings["target"] = counting_ring

    groups = store.read(
        "target", from_utc=now, to_utc=now + timedelta(seconds=10)
    )

    assert groups and groups[0].counters["orders_submitted"] == 1
    # The requested range spans at most 2 canonical buckets; a full scan
    # of the default 2160-bucket ring would be two orders of magnitude
    # more indexing than this.
    assert counting_ring.getitem_calls <= 2


def test_restarted_bucket_count_also_indexes_only_the_requested_span() -> None:
    store = MetricStore(StreamProcessorConfig())
    now = datetime(2026, 6, 12, 10, 0, 0, tzinfo=UTC)
    store.merge(
        _snapshot(instance_id="target", bucket_start_utc=now),
        canonical_start=now,
        now=now,
    )

    counting_ring = _CountingRing(store._rings["target"])
    store._rings["target"] = counting_ring

    store.restarted_bucket_count(
        "target", from_utc=now, to_utc=now + timedelta(seconds=10)
    )

    assert counting_ring.getitem_calls <= 2
