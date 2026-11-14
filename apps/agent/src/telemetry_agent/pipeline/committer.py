"""Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.metrics.demo_sink import DemoMetricsSink
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.pipeline.deduper import ProcessedLineDeduper
from telemetry_agent.pipeline.event_queue import EventQueue
from telemetry_agent.pipeline.types import ParsedEvent


class PipelineCommitter:
    """Consumes ParsedEvent objects and commits file offsets after ingest."""

    def __init__(
        self,
        event_queue: EventQueue,
        deduper: ProcessedLineDeduper,
        monitors_by_path: dict[str, LogMonitor],
        *,
        sink: DemoMetricsSink | None = None,
        on_event: Callable[[ParsedEvent], None] | None = None,
    ) -> None:
        self._event_queue = event_queue
        self._deduper = deduper
        self._monitors_by_path = monitors_by_path
        self._sink = sink or DemoMetricsSink()
        self._on_event = on_event
        self._ingested = 0
        self._skipped_duplicates = 0
        self._pending: deque[SourceMeta] = deque()
        self._completed: set[SourceMeta] = set()

    @property
    def pending_lines(self) -> int:
        return len(self._pending)

    def expect(self, meta: SourceMeta) -> None:
        """Register source order before consuming any parsed results."""
        self._pending.append(meta)

    def _ack(self, meta: SourceMeta) -> None:
        monitor = self._monitors_by_path.get(meta.path)
        if monitor is not None:
            monitor.ack_line(meta.end_offset, dev=meta.dev, ino=meta.inode)

    def _complete(self, meta: SourceMeta) -> None:
        if not self._pending:
            self._ack(meta)  # direct component callers without a bridge
            return
        self._completed.add(meta)
        while self._pending and self._pending[0] in self._completed:
            ready = self._pending.popleft()
            self._completed.remove(ready)
            self._ack(ready)

    @property
    def sink(self) -> DemoMetricsSink:
        return self._sink

    @property
    def ingested(self) -> int:
        return self._ingested

    @property
    def skipped_duplicates(self) -> int:
        return self._skipped_duplicates

    def process_available(self, max_items: int | None = None) -> list[ParsedEvent]:
        events = self._event_queue.drain(max_items=max_items)
        processed: list[ParsedEvent] = []
        for event in events:
            if self._deduper.is_duplicate(event.meta):
                self._skipped_duplicates += 1
                self._complete(event.meta)
                continue
            self._sink.record_parse_result(event.result)
            if self._on_event is not None:
                self._on_event(event)
            self._deduper.mark_processed(event.meta)
            self._complete(event.meta)
            self._ingested += 1
            processed.append(event)
        return processed
