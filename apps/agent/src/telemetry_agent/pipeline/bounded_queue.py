from __future__ import annotations

import threading
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

OverflowPolicy = Literal["block", "drop_oldest"]


@dataclass(frozen=True, slots=True)
class QueueSnapshot:
    depth: int
    capacity: int
    dropped_total: int


class BoundedQueue[T]:
    """Bounded queue with configurable overflow: block (default) or drop_oldest."""

    def __init__(
        self,
        capacity: int,
        *,
        overflow_policy: OverflowPolicy = "block",
    ) -> None:
        if capacity < 0:
            msg = f"capacity must be >= 0, got {capacity}"
            raise ValueError(msg)
        self._capacity = capacity
        self._overflow_policy = overflow_policy
        self._items: deque[T] = deque()
        self._dropped = 0
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def overflow_policy(self) -> OverflowPolicy:
        return self._overflow_policy

    @property
    def depth(self) -> int:
        with self._lock:
            return len(self._items)

    @property
    def dropped_total(self) -> int:
        with self._lock:
            return self._dropped

    def put(self, item: T, timeout: float | None = None) -> bool:
        """Enqueue. Blocks when full if policy is block; returns False on timeout."""
        with self._not_full:
            if self._capacity == 0:
                if self._overflow_policy == "drop_oldest":
                    self._dropped += 1
                return False
            if self._overflow_policy == "drop_oldest":
                if len(self._items) >= self._capacity:
                    self._items.popleft()
                    self._dropped += 1
                self._items.append(item)
                self._not_empty.notify()
                return True
            while len(self._items) >= self._capacity:
                if timeout is None:
                    self._not_full.wait()
                elif not self._not_full.wait(timeout=timeout):
                    return False
            self._items.append(item)
            self._not_empty.notify()
            return True

    def put_nowait(self, item: T) -> None:
        """Non-blocking put; drop_oldest only. Use put() for block mode."""
        if self._overflow_policy != "drop_oldest":
            msg = "put_nowait requires overflow_policy='drop_oldest'"
            raise RuntimeError(msg)
        self.put(item)

    def get(self, timeout: float | None = None) -> T | None:
        """Block until an item is available or timeout elapses."""
        with self._not_empty:
            if not self._items:
                if timeout is None:
                    while not self._items:
                        self._not_empty.wait()
                elif not self._not_empty.wait(timeout=timeout):
                    return None
            if not self._items:
                return None
            item = self._items.popleft()
            self._not_full.notify()
            return item

    def drain(self, max_items: int | None = None) -> list[T]:
        with self._lock:
            if max_items is None:
                items = list(self._items)
                self._items.clear()
            else:
                items = []
                while self._items and len(items) < max_items:
                    items.append(self._items.popleft())
            self._not_full.notify_all()
            return items

    def __iter__(self) -> Iterator[T]:
        while True:
            item = self.get(timeout=0.05)
            if item is None:
                break
            yield item

    def snapshot(self) -> QueueSnapshot:
        with self._lock:
            return QueueSnapshot(
                depth=len(self._items),
                capacity=self._capacity,
                dropped_total=self._dropped,
            )


# Backward-compatible alias used by drop-oldest tests.
BoundedDropOldestQueue = BoundedQueue
