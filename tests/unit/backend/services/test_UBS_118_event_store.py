"""UBS-118: EventStore append, dedupe, filters, retention, truncation."""

from __future__ import annotations

from datetime import timedelta

from telemetry_backend.config import EventStoreConfig
from telemetry_backend.services.event_store import EventStore

from tests.unit.backend.services.event_fixtures import (
    BASE_TIME,
    INSTANCE_ID,
    make_telemetry_event,
)


def test_append_and_get_event_by_id() -> None:
    store = EventStore()
    event = make_telemetry_event(event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60")
    store.append(event)

    fetched = store.get_event("01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60")
    assert fetched is not None
    assert fetched.event_type == "agent.started"


def test_append_is_idempotent_on_event_id() -> None:
    store = EventStore()
    event = make_telemetry_event(event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60")
    store.append(event)
    store.append(event)

    listed = store.list_events()
    assert len(listed.events) == 1


def test_list_events_filters_and_sorts_by_timestamp_desc() -> None:
    store = EventStore()
    store.append(
        make_telemetry_event(
            event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f61",
            event_type="agent.started",
            timestamp_utc=BASE_TIME,
        )
    )
    store.append(
        make_telemetry_event(
            event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f62",
            event_type="fix.order_reject",
            timestamp_utc=BASE_TIME + timedelta(minutes=5),
            severity="warning",
            dimensions={"session": "MAGIC->EXCH1", "symbol": "ABC"},
        )
    )

    filtered = store.list_events(event_type="fix.order_reject")
    assert len(filtered.events) == 1
    assert filtered.events[0].event_type == "fix.order_reject"

    since = store.list_events(since=BASE_TIME + timedelta(minutes=1))
    assert len(since.events) == 1
    assert since.events[0].event_type == "fix.order_reject"

    all_events = store.list_events()
    assert [event.event_type for event in all_events.events] == [
        "fix.order_reject",
        "agent.started",
    ]


def test_list_events_reports_truncation() -> None:
    store = EventStore()
    for index in range(5):
        store.append(
            make_telemetry_event(
                event_id=f"01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f6{index}",
                timestamp_utc=BASE_TIME + timedelta(seconds=index),
            )
        )

    listed = store.list_events(limit=2)
    assert len(listed.events) == 2
    assert listed.truncated is True


def test_retention_evicts_oldest_events_per_instance() -> None:
    store = EventStore(EventStoreConfig(recent_event_limit=2))
    first = make_telemetry_event(
        event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60",
        timestamp_utc=BASE_TIME,
    )
    second = make_telemetry_event(
        event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f61",
        timestamp_utc=BASE_TIME + timedelta(seconds=1),
    )
    third = make_telemetry_event(
        event_id="01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f62",
        timestamp_utc=BASE_TIME + timedelta(seconds=2),
    )
    store.append(first)
    store.append(second)
    store.append(third)

    assert store.get_event(str(first.event_id)) is None
    assert store.get_event(str(second.event_id)) is not None
    assert store.get_event(str(third.event_id)) is not None
    assert len(store.list_events(instance_id=INSTANCE_ID).events) == 2


def test_get_event_returns_none_for_invalid_or_missing_id() -> None:
    store = EventStore()
    assert store.get_event("not-a-uuid") is None
    assert store.get_event("01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60") is None
