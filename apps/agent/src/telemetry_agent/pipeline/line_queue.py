"""Monitor → parser bounded line queue (FR-PIP-001, FR-PIP-002)."""

from __future__ import annotations

from telemetry_agent.pipeline.bounded_queue import (
    BoundedQueue,
    OverflowPolicy,
    QueueSnapshot,
)
from telemetry_agent.pipeline.types import QueuedLine


class LineQueue:
    """Handoff from the log monitor to parser workers."""

    def __init__(
        self,
        capacity: int = 2048,
        *,
        overflow_policy: OverflowPolicy = "block",
    ) -> None:
        self._queue: BoundedQueue[QueuedLine] = BoundedQueue(
            capacity,
            overflow_policy=overflow_policy,
        )

    def put(self, item: QueuedLine, timeout: float | None = None) -> bool:
        return self._queue.put(item, timeout=timeout)

    def put_nowait(self, item: QueuedLine) -> None:
        self._queue.put_nowait(item)

    def get(self, timeout: float | None = None) -> QueuedLine | None:
        return self._queue.get(timeout=timeout)

    @property
    def depth(self) -> int:
        return self._queue.depth

    @property
    def capacity(self) -> int:
        return self._queue.capacity

    @property
    def lines_dropped(self) -> int:
        return self._queue.dropped_total

    def snapshot(self) -> QueueSnapshot:
        return self._queue.snapshot()
