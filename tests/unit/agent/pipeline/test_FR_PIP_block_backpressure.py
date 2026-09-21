import threading
import time

from telemetry_agent.pipeline.bounded_queue import BoundedQueue


def test_full_queue_blocks_producer_without_drops() -> None:
    queue: BoundedQueue[int] = BoundedQueue(capacity=2, overflow_policy="block")
    assert queue.put(1)
    assert queue.put(2)

    released = threading.Event()

    def consumer() -> None:
        time.sleep(0.05)
        assert queue.get(timeout=1.0) == 1
        released.set()

    thread = threading.Thread(target=consumer)
    thread.start()

    start = time.monotonic()
    assert queue.put(3, timeout=1.0) is True
    elapsed = time.monotonic() - start
    thread.join(timeout=1.0)

    assert elapsed >= 0.04
    assert queue.dropped_total == 0
    assert queue.depth == 2
