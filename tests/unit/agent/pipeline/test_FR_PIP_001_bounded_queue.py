import time

from telemetry_agent.pipeline.bounded_queue import BoundedQueue


def test_drop_oldest_policy_discards_oldest_on_overflow() -> None:
    queue: BoundedQueue[int] = BoundedQueue(
        capacity=2,
        overflow_policy="drop_oldest",
    )

    queue.put_nowait(1)
    queue.put_nowait(2)
    queue.put_nowait(3)

    assert queue.depth == 2
    assert queue.dropped_total == 1
    assert queue.drain() == [2, 3]


def test_block_policy_waits_for_capacity() -> None:
    queue: BoundedQueue[int] = BoundedQueue(capacity=1, overflow_policy="block")
    assert queue.put(1)

    def delayed_get() -> None:
        time.sleep(0.05)
        assert queue.get(timeout=1.0) == 1

    import threading

    thread = threading.Thread(target=delayed_get)
    thread.start()
    start = time.monotonic()
    assert queue.put(2, timeout=1.0) is True
    thread.join(timeout=1.0)
    assert time.monotonic() - start >= 0.04
    assert queue.dropped_total == 0


def test_zero_capacity_rejects_without_storing() -> None:
    queue: BoundedQueue[str] = BoundedQueue(
        capacity=0,
        overflow_policy="drop_oldest",
    )

    queue.put_nowait("line")
    queue.put_nowait("line2")

    assert queue.depth == 0
    assert queue.dropped_total == 2
