"""UBS-118: IngestionService stores events from the background worker."""

from __future__ import annotations

import asyncio

from telemetry_backend.services.event_store import EventStore
from telemetry_backend.services.ingestion import AcceptedIngestion, IngestionService

from tests.unit.backend.services.event_fixtures import make_telemetry_event


async def _drain_one(service: IngestionService) -> None:
    item = await service._queue.get()
    try:
        if item.events:
            await asyncio.to_thread(service._process_events, list(item.events))
    finally:
        service._queue.task_done()


def test_process_events_appends_to_event_store() -> None:
    store = EventStore()
    service = IngestionService(event_store=store, heartbeat_monitor=None)
    event = make_telemetry_event(event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60")

    service._process_events([event])

    stored = store.get_event("01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60")
    assert stored is not None
    assert stored.event_type == event.event_type


def test_run_drains_events_from_queue() -> None:
    store = EventStore()
    service = IngestionService(event_store=store, heartbeat_monitor=None)
    event = make_telemetry_event(event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60")
    assert service.enqueue(AcceptedIngestion(events=(event,)))

    asyncio.run(_drain_one(service))

    assert service.queue_depth == 0
    assert store.get_event("01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60") is not None
