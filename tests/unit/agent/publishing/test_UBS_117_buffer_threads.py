"""FR-PUB-007: parser thread appends while the event loop drains/requeues."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Thread

from telemetry_agent.publishing.buffer import PublishBuffer, make_pending_item

from tests.unit.agent.publishing.publish_fixtures import make_event


def test_concurrent_append_and_drain_preserve_items_and_byte_accounting():
    buffer = PublishBuffer(max_bytes=10_000_000, max_age_seconds=900)

    def produce():
        for _ in range(300):
            buffer.append(make_pending_item("event", make_event(), datetime.now(UTC)))

    def consume():
        taken = []
        for _ in range(300):
            items = buffer.take(5)
            buffer.requeue_front(items)  # a retry can overlap the producer
            taken.extend(buffer.take(3))
        return taken

    with ThreadPoolExecutor(max_workers=4) as pool:
        producers = [pool.submit(produce) for _ in range(3)]
        consumer = pool.submit(consume)
        for job in producers:
            job.result(timeout=5)
        taken = consumer.result(timeout=5) + buffer.take(1000)
    assert len(taken) == 900
    assert len({item.payload.event_id for item in taken}) == 900
    assert buffer.depth() == buffer.total_bytes() == 0


def test_drop_hook_runs_outside_buffer_lock():
    completed = []

    def dropped():
        reader = Thread(target=lambda: completed.append(buffer.depth()), daemon=True)
        reader.start()
        reader.join(timeout=1)
        assert not reader.is_alive()

    buffer = PublishBuffer(max_bytes=1, max_age_seconds=900, on_drop=dropped)
    buffer.append(make_pending_item("event", make_event(), datetime.now(UTC)))
    buffer.append(make_pending_item("event", make_event(), datetime.now(UTC)))
    assert completed == [1]
