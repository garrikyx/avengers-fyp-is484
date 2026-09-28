"""Bounded asynchronous hand-off for HTTP ingestion."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import Heartbeat, TelemetryEvent
from telemetry_shared.models.snapshot import Snapshot

from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.heartbeat_monitor import HeartbeatMonitor
from telemetry_backend.services.stream_processor import StreamProcessor


@dataclass(slots=True, frozen=True)
class AcceptedIngestion:
    """Validated data ready for downstream processing."""

    snapshots: tuple[Snapshot, ...] = ()
    events: tuple[TelemetryEvent, ...] = ()
    alerts: tuple[AlertEvent, ...] = ()
    heartbeat: Heartbeat | None = None


class IngestionService:
    """Owns a bounded queue and one background consumer."""

    def __init__(
        self,
        *,
        queue_size: int = 10_000,
        stream_processor: StreamProcessor | None = None,
        alert_store: AlertStore | None = None,
        agent_registry: AgentRegistry | None = None,
        heartbeat_monitor: HeartbeatMonitor | None = None,
    ) -> None:
        self._queue: asyncio.Queue[AcceptedIngestion] = asyncio.Queue(
            maxsize=queue_size
        )
        self.stream_processor = stream_processor or StreamProcessor()
        self.alert_store = alert_store or AlertStore()
        self.agent_registry = agent_registry or AgentRegistry()
        self.heartbeat_monitor = heartbeat_monitor
        self.rejected_payloads_total = 0
        self.queue_overflow_total = 0
        self.accepted_payloads_total = 0

    @property
    def queue_depth(self) -> int:
        return self._queue.qsize()

    def record_rejection(self) -> None:
        self.rejected_payloads_total += 1

    def enqueue(self, item: AcceptedIngestion) -> bool:
        """Try to hand off without waiting; False means callers return 503."""
        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull:
            self.queue_overflow_total += 1
            return False
        self.accepted_payloads_total += 1
        return True

    async def run(self) -> None:
        """Keep store work off FastAPI's request path.

        A single consumer preserves the existing in-memory store's sequential
        mutation semantics. `to_thread` also ensures a merge never occupies
        the event loop that accepts the next request.
        """
        while True:
            item = await self._queue.get()
            now = datetime.now(UTC)
            try:
                if item.snapshots:
                    await asyncio.to_thread(
                        self.stream_processor.process_batch,
                        list(item.snapshots),
                        now=now,
                    )
                if item.alerts:
                    await asyncio.to_thread(
                        self._process_alerts,
                        list(item.alerts),
                        now,
                    )
                if item.heartbeat is not None:
                    await asyncio.to_thread(
                        self._process_heartbeat,
                        item.heartbeat,
                        now,
                    )
            finally:
                self._queue.task_done()

    def _process_alerts(
        self, alerts: list[AlertEvent], now: datetime
    ) -> None:
        for alert in alerts:
            self.alert_store.merge(alert, source="agent", now=now)

    def _process_heartbeat(self, heartbeat: Heartbeat, now: datetime) -> None:
        self.agent_registry.record_heartbeat(heartbeat, now=now)
        if self.heartbeat_monitor is not None:
            self.heartbeat_monitor.on_heartbeat(heartbeat.agent_id)
