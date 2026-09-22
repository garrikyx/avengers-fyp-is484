"""Bounded asynchronous hand-off for HTTP ingestion."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import Heartbeat, TelemetryEvent
from telemetry_shared.models.snapshot import Snapshot

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
    ) -> None:
        self._queue: asyncio.Queue[AcceptedIngestion] = asyncio.Queue(
            maxsize=queue_size
        )
        self.stream_processor = stream_processor or StreamProcessor()
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
            try:
                if item.snapshots:
                    await asyncio.to_thread(
                        self.stream_processor.process_batch,
                        list(item.snapshots),
                        now=datetime.now(UTC),
                    )
            finally:
                self._queue.task_done()
