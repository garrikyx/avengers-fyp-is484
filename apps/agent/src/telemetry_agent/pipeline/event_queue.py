"""Parser → aggregator bounded event queue (FR-PIP-004)."""

from __future__ import annotations

from telemetry_agent.pipeline.bounded_queue import (
    BoundedQueue,
    OverflowPolicy,
    QueueSnapshot,
)
from telemetry_agent.pipeline.types import ParsedEvent


class EventQueue:
    """Handoff from parser workers to downstream stages."""

    def __init__(
        self,
        capacity: int = 256,
        *,
        overflow_policy: OverflowPolicy = "block",
    ) -> None:
        self._queue: BoundedQueue[ParsedEvent] = BoundedQueue(
            capacity,
            overflow_policy=overflow_policy,
        )

    def put(self, item: ParsedEvent, timeout: float | None = None) -> bool:
        return self._queue.put(item, timeout=timeout)

    def put_nowait(self, item: ParsedEvent) -> None:
        self._queue.put_nowait(item)

    def get(self, timeout: float | None = None) -> ParsedEvent | None:
        return self._queue.get(timeout=timeout)

    def drain(self, max_items: int | None = None) -> list[ParsedEvent]:
        return self._queue.drain(max_items=max_items)

    @property
    def depth(self) -> int:
        return self._queue.depth

    @property
    def capacity(self) -> int:
        return self._queue.capacity

    @property
    def events_dropped(self) -> int:
        return self._queue.dropped_total

    def snapshot(self) -> QueueSnapshot:
        return self._queue.snapshot()
