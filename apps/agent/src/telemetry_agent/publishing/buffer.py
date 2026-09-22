"""FR-PUB-004 (UBS-103 slice): a bounded pending-item buffer, drop-oldest
on overflow.

Buffers individual snapshots/events/alerts rather than pre-built batches:
a batch is just "the next `max_batch_items` items off the front"
(`take`), which makes the 413 response (halve `maxBatchItems`, resend
fewer items) a matter of taking fewer items next time, not surgery on an
existing batch object. `requeue_front` puts un-sent items back at the
front, in original order, so they are retried — and evicted — before
anything newer.

Byte-size and age bounds (`FR-PUB-004`'s full form) and counted-drop
exposure via the Health Reporter are UBS-104's extension, mirroring how
UBS-33 built the retry loop on top of UBS-32's plain `DropOldestQueue`.
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


class PublishBuffer:
    """Bounded FIFO of `PendingItem`s, drop-oldest on overflow."""

    def __init__(
        self, max_items: int, *, on_drop: Callable[[], None] | None = None
    ) -> None:
        if max_items < 1:
            raise ValueError("max_items must be >= 1")
        self._max_items = max_items
        self._items: deque[PendingItem] = deque()
        self._on_drop = on_drop

    def append(self, item: PendingItem) -> None:
        self._items.append(item)
        self._evict_overflow()

    def take(self, max_items: int) -> list[PendingItem]:
        """Remove and return up to `max_items` from the front."""
        count = min(max_items, len(self._items))
        return [self._items.popleft() for _ in range(count)]

    def requeue_front(self, items: list[PendingItem]) -> None:
        """Put previously-`take`n items back at the front, in original
        order — they are the oldest data the buffer holds, so they are
        retried before, and evicted before, anything that arrived while
        they were in flight.
        """
        self._items.extendleft(reversed(items))
        self._evict_overflow()

    def depth(self) -> int:
        return len(self._items)

    def _evict_overflow(self) -> None:
        while len(self._items) > self._max_items:
            self._items.popleft()
            if self._on_drop is not None:
                self._on_drop()

    def __len__(self) -> int:
        return len(self._items)
