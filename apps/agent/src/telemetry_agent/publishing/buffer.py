"""FR-PUB-004: a pending-item buffer bounded by both total bytes and
maximum age, drop-oldest on overflow, counted.

UBS-103 shipped an item-count-only version of this (a placeholder --
`FR-PUB-004`'s actual bound is bytes/age, not item count); UBS-104
replaces it with the spec-exact form.

Buffers individual snapshots/events/alerts rather than pre-built batches:
a batch is just "the next `max_batch_items` items off the front"
(`take`), which makes the 413 response (halve `maxBatchItems`, resend
fewer items) a matter of taking fewer items next time, not surgery on an
existing batch object. `requeue_front` puts un-sent items back at the
front, in original order, so they are retried -- and evicted -- before
anything newer.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import TelemetryEvent
from telemetry_shared.models.snapshot import Snapshot

PendingKind = Literal["snapshot", "event", "alert"]
PendingPayload = Snapshot | TelemetryEvent | AlertEvent


@dataclass(frozen=True, slots=True)
class PendingItem:
    kind: PendingKind
    payload: PendingPayload
    enqueued_at: datetime
    size_bytes: int


def _size_of(payload: PendingPayload) -> int:
    """Measured once at insert and cached on the `PendingItem` -- re-measuring
    on every eviction check would make overflow handling O(n) in
    serialization cost."""
    return len(payload.model_dump_json(by_alias=True).encode("utf-8"))


def make_pending_item(
    kind: PendingKind, payload: PendingPayload, enqueued_at: datetime
) -> PendingItem:
    return PendingItem(kind, payload, enqueued_at, _size_of(payload))


class PublishBuffer:
    """Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by
    both `max_bytes` (total serialized size) and `max_age_seconds` (how
    long the oldest item may sit unpublished).
    """

    def __init__(
        self,
        *,
        max_bytes: int,
        max_age_seconds: float,
        on_drop: Callable[[], None] | None = None,
    ) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes must be >= 1")
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be > 0")
        self._max_bytes = max_bytes
        self._max_age_seconds = max_age_seconds
        self._items: deque[PendingItem] = deque()
        self._total_bytes = 0
        self._on_drop = on_drop

    def append(self, item: PendingItem) -> None:
        self._items.append(item)
        self._total_bytes += item.size_bytes
        self._evict_overflow()

    def expire(self, now: datetime) -> int:
        """Drop items older than `max_age_seconds`. The deque is strictly
        insertion-ordered, so `enqueued_at` is monotonically non-decreasing
        -- only the head ever needs checking (O(dropped), not O(n)).
        Returns the number of items dropped.
        """
        dropped = 0
        while self._items and (
            now - self._items[0].enqueued_at
        ).total_seconds() > self._max_age_seconds:
            self._evict_one()
            dropped += 1
        return dropped

    def take(self, max_items: int) -> list[PendingItem]:
        """Remove and return up to `max_items` from the front."""
        count = min(max_items, len(self._items))
        taken = [self._items.popleft() for _ in range(count)]
        self._total_bytes -= sum(item.size_bytes for item in taken)
        return taken

    def requeue_front(self, items: list[PendingItem]) -> None:
        """Put previously-`take`n items back at the front, in original
        order -- they are the oldest data the buffer holds, so they are
        retried before, and evicted before, anything that arrived while
        they were in flight.
        """
        self._items.extendleft(reversed(items))
        self._total_bytes += sum(item.size_bytes for item in items)
        self._evict_overflow()

    def depth(self) -> int:
        return len(self._items)

    def total_bytes(self) -> int:
        return self._total_bytes

    def oldest_age_seconds(self, now: datetime) -> float | None:
        if not self._items:
            return None
        return (now - self._items[0].enqueued_at).total_seconds()

    def _evict_overflow(self) -> None:
        # `len > 1` guards a single item larger than the whole cap: it
        # stays (over cap) rather than self-evicting into an infinite
        # loop, and the next append evicts it normally once something
        # else exists to make room for.
        while self._total_bytes > self._max_bytes and len(self._items) > 1:
            self._evict_one()

    def _evict_one(self) -> None:
        evicted = self._items.popleft()
        self._total_bytes -= evicted.size_bytes
        if self._on_drop is not None:
            self._on_drop()

    def __len__(self) -> int:
        return len(self._items)
