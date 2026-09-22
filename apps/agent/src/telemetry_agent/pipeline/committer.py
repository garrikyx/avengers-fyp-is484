"""Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)."""

from __future__ import annotations

from collections.abc import Callable

from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.metrics.demo_sink import DemoMetricsSink
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
                monitor = self._monitors_by_path.get(event.meta.path)
                if monitor is not None:
                    monitor.ack_line(event.meta.end_offset)
                continue
            self._sink.record_parse_result(event.result)
            self._deduper.mark_processed(event.meta)
            monitor = self._monitors_by_path.get(event.meta.path)
            if monitor is not None:
                monitor.ack_line(event.meta.end_offset)
            if self._on_event is not None:
                self._on_event(event)
            self._ingested += 1
            processed.append(event)
        return processed
