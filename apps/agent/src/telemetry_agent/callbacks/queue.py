"""FR-CBK-007: bounded pending queue, drop-oldest on overflow."""

from __future__ import annotations

import asyncio
from collections.abc import Callable


class DropOldestQueue[T]:
    """Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow
    policy (`FR-CBK-007`): a full queue drops its oldest item to make room
    for the new one, rather than blocking the caller or rejecting the new
    item.
    """

    def __init__(
        self, maxsize: int, *, on_drop: Callable[[], None] | None = None
    ) -> None:
        self._queue: asyncio.Queue[T] = asyncio.Queue(maxsize=maxsize)
        self._on_drop = on_drop

    def put_dropping_oldest(self, item: T) -> bool:
        """Enqueue `item`, non-blocking. Returns True if an existing item
        was dropped to make room.
        """
        try:
            self._queue.put_nowait(item)
            return False
        except asyncio.QueueFull:
            self._queue.get_nowait()
            self._queue.put_nowait(item)
            if self._on_drop is not None:
                self._on_drop()
            return True

    async def get(self) -> T:
        return await self._queue.get()

    def qsize(self) -> int:
        return self._queue.qsize()
