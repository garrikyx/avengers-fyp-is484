"""FR-CBK-007 bounded queue, drop-oldest overflow tests."""

from __future__ import annotations

import asyncio

from telemetry_agent.callbacks.queue import DropOldestQueue


def test_FR_CBK_007_enqueue_under_capacity_never_drops() -> None:
    queue: DropOldestQueue[int] = DropOldestQueue(maxsize=3)
    assert queue.put_dropping_oldest(1) is False
    assert queue.put_dropping_oldest(2) is False
    assert queue.qsize() == 2


def test_FR_CBK_007_overflow_drops_oldest_and_increments_counter() -> None:
    drops: list[None] = []
    queue: DropOldestQueue[int] = DropOldestQueue(
        maxsize=2, on_drop=lambda: drops.append(None)
    )
    queue.put_dropping_oldest(1)
    queue.put_dropping_oldest(2)
    dropped = queue.put_dropping_oldest(3)

    assert dropped is True
    assert len(drops) == 1
    assert queue.qsize() == 2


def test_FR_CBK_007_oldest_item_is_the_one_dropped() -> None:
    queue: DropOldestQueue[int] = DropOldestQueue(maxsize=2)
    queue.put_dropping_oldest(1)
    queue.put_dropping_oldest(2)
    queue.put_dropping_oldest(3)  # drops 1

    async def drain() -> list[int]:
        return [await queue.get(), await queue.get()]

    remaining = asyncio.run(drain())
    assert remaining == [2, 3]
