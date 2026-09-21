"""Pipeline bridge wiring monitor enqueue to parser workers (M1.5)."""

from __future__ import annotations

from collections.abc import Sequence

from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.metrics.demo_sink import DemoMetricsSink
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.committer import PipelineCommitter
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.deduper import ProcessedLineDeduper
from telemetry_agent.pipeline.event_queue import EventQueue
from telemetry_agent.pipeline.line_queue import LineQueue
from telemetry_agent.pipeline.stats import PipelineStats
from telemetry_agent.pipeline.types import ParsedEvent, QueuedLine
from telemetry_agent.pipeline.workers import ParserWorkerPool


class PipelineBridge:
    """Bounded queues and parser workers between log monitor and downstream stages."""

    def __init__(
        self,
        config: PipelineConfig | None = None,
        registry: Registry | None = None,
        *,
        monitors_by_path: dict[str, LogMonitor] | None = None,
    ) -> None:
        cfg = config or PipelineConfig()
        policy = cfg.overflow_policy
        self._config = cfg
        self._line_queue = LineQueue(
            cfg.line_queue_size,
            overflow_policy=policy,
        )
        self._event_queue = EventQueue(
            cfg.event_queue_size,
            overflow_policy=policy,
        )
        self._registry = registry or Registry()
        self._deduper = ProcessedLineDeduper(
            capacity=cfg.dedupe_capacity,
            ttl_seconds=cfg.dedupe_ttl_seconds,
        )
        self._workers = ParserWorkerPool.from_config(
            self._line_queue,
            self._event_queue,
            self._registry,
            cfg,
        )
        self._committer: PipelineCommitter | None = None
        if monitors_by_path is not None:
            self._committer = PipelineCommitter(
                event_queue=self._event_queue,
                deduper=self._deduper,
                monitors_by_path=monitors_by_path,
            )

    @property
    def line_queue(self) -> LineQueue:
        return self._line_queue

    @property
    def event_queue(self) -> EventQueue:
        return self._event_queue

    @property
    def deduper(self) -> ProcessedLineDeduper:
        return self._deduper

    @property
    def committer(self) -> PipelineCommitter | None:
        return self._committer

    def attach_committer(
        self,
        monitors_by_path: dict[str, LogMonitor],
        *,
        sink: DemoMetricsSink | None = None,
    ) -> PipelineCommitter:
        self._committer = PipelineCommitter(
            event_queue=self._event_queue,
            deduper=self._deduper,
            monitors_by_path=monitors_by_path,
            sink=sink,
        )
        return self._committer

    def start(self) -> None:
        self._workers.start()

    def stop(self, wait: bool = True) -> None:
        self._workers.stop(wait=wait)

    def enqueue_line(
        self,
        line: bytes,
        meta: SourceMeta,
        parser_chain: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> bool:
        """Monitor handoff (FR-PIP-001). Blocks by default when queue is full."""
        if timeout is None:
            timeout = self._config.put_timeout_seconds
        return self._line_queue.put(
            QueuedLine(
                line=line,
                meta=meta,
                parser_chain=tuple(parser_chain),
            ),
            timeout=timeout,
        )

    def drain_events(self, max_items: int | None = None) -> list[ParsedEvent]:
        return self._event_queue.drain(max_items=max_items)

    def process_commits(self, max_items: int | None = None) -> list[ParsedEvent]:
        if self._committer is None:
            return self.drain_events(max_items=max_items)
        return self._committer.process_available(max_items=max_items)

    def stats(self) -> PipelineStats:
        return PipelineStats(
            line_queue_depth=self._line_queue.depth,
            line_queue_capacity=self._line_queue.capacity,
            event_queue_depth=self._event_queue.depth,
            event_queue_capacity=self._event_queue.capacity,
            lines_dropped=self._line_queue.lines_dropped,
            events_dropped=self._event_queue.events_dropped,
        )
