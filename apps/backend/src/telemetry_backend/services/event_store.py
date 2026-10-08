"""In-memory Event Store (UBS-118)."""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from telemetry_shared.models.events_query import EventsListResponse
from telemetry_shared.models.ingestion import TelemetryEvent

from telemetry_backend.config import EventStoreConfig


@dataclass(slots=True)
class _InstanceEvents:
    order: deque[str] = field(default_factory=deque)
    events: dict[str, TelemetryEvent] = field(default_factory=dict)


class EventStore:
    """Per-instance bounded event history."""

    def __init__(self, config: EventStoreConfig | None = None) -> None:
        self._config = config or EventStoreConfig()
        self._instances: dict[str, _InstanceEvents] = {}
        self._instance_locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _get_instance(self, instance_id: str) -> tuple[_InstanceEvents, threading.Lock]:
        with self._locks_guard:
            if instance_id not in self._instances:
                self._instances[instance_id] = _InstanceEvents()
                self._instance_locks[instance_id] = threading.Lock()
            return self._instances[instance_id], self._instance_locks[instance_id]

    def append(self, event: TelemetryEvent) -> None:
        """Store one event, idempotent on `event_id`."""
        instance, lock = self._get_instance(event.instance_id)
        event_key = str(event.event_id)
        with lock:
            if event_key in instance.events:
                return
            instance.events[event_key] = event
            instance.order.append(event_key)
            self._evict_if_needed(instance)

    def _evict_if_needed(self, instance: _InstanceEvents) -> None:
        while len(instance.order) > self._config.recent_event_limit:
            oldest_id = instance.order.popleft()
            instance.events.pop(oldest_id, None)

    def _iter_all_events(self) -> Iterable[TelemetryEvent]:
        for instance_id in list(self._instances):
            instance, lock = self._get_instance(instance_id)
            with lock:
                yield from instance.events.values()

    @staticmethod
    def _matches_filters(
        event: TelemetryEvent,
        *,
        application: str | None,
        instance_id: str | None,
        event_type: str | None,
        severity: str | None,
        since: datetime | None,
    ) -> bool:
        if application is not None and event.application != application:
            return False
        if instance_id is not None and event.instance_id != instance_id:
            return False
        if event_type is not None and event.event_type != event_type:
            return False
        if severity is not None and event.severity != severity:
            return False
        if since is not None and event.timestamp_utc < since:
            return False
        return True

    def list_events(
        self,
        *,
        application: str | None = None,
        instance_id: str | None = None,
        event_type: str | None = None,
        severity: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> EventsListResponse:
        candidates: list[TelemetryEvent] = []
        for event in self._iter_all_events():
            if not self._matches_filters(
                event,
                application=application,
                instance_id=instance_id,
                event_type=event_type,
                severity=severity,
                since=since,
            ):
                continue
            candidates.append(event)

        candidates.sort(key=lambda e: e.timestamp_utc, reverse=True)
        truncated = len(candidates) > limit
        return EventsListResponse(
            events=candidates[:limit],
            truncated=truncated,
        )

    def get_event(self, event_id: str) -> TelemetryEvent | None:
        try:
            parsed = UUID(event_id)
        except ValueError:
            return None
        event_key = str(parsed)
        for instance_id in list(self._instances):
            instance, lock = self._get_instance(instance_id)
            with lock:
                event = instance.events.get(event_key)
                if event is not None:
                    return event
        return None
