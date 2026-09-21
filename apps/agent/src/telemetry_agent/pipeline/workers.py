"""Parser worker pool pulling from the line queue (FR-PIP-003)."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from telemetry_agent.parser.protocol import (
    LineClassification,
    ParseResult,
    SourceMeta,
)
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.event_queue import EventQueue
from telemetry_agent.pipeline.line_queue import LineQueue
from telemetry_agent.pipeline.types import ParsedEvent


class ParserWorkerPool:
    """CPU-bound parser workers; no I/O inside the pool (FR-PRS-003)."""

    def __init__(
        self,
        line_queue: LineQueue,
        event_queue: EventQueue,
        registry: Registry,
        worker_count: int,
        *,
        put_timeout: float = 0.5,
        poll_timeout: float = 0.1,
    ) -> None:
        self._line_queue = line_queue
        self._event_queue = event_queue
        self._registry = registry
        self._worker_count = worker_count
        self._put_timeout = put_timeout
        self._poll_timeout = poll_timeout
        self._stop = threading.Event()
        self._executor: ThreadPoolExecutor | None = None

    @classmethod
    def from_config(
        cls,
        line_queue: LineQueue,
        event_queue: EventQueue,
        registry: Registry,
        config: PipelineConfig,
    ) -> ParserWorkerPool:
        return cls(
            line_queue=line_queue,
            event_queue=event_queue,
            registry=registry,
            worker_count=config.resolved_worker_count(),
            put_timeout=config.put_timeout_seconds,
        )

    def start(self) -> None:
        if self._executor is not None:
            return
        self._stop.clear()
        self._executor = ThreadPoolExecutor(
            max_workers=self._worker_count,
            thread_name_prefix="parser-worker",
        )
        for _ in range(self._worker_count):
            self._executor.submit(self._worker_loop)

    def stop(self, wait: bool = True) -> None:
        self._stop.set()
        if self._executor is not None:
            self._executor.shutdown(wait=wait, cancel_futures=False)
            self._executor = None

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            queued = self._line_queue.get(timeout=self._poll_timeout)
            if queued is None:
                continue
            result = self._parse(queued.line, queued.meta, queued.parser_chain)
            event = ParsedEvent(meta=queued.meta, result=result, line=queued.line)
            while not self._stop.is_set():
                if self._event_queue.put(event, timeout=self._put_timeout):
                    break

    def _parse(
        self,
        line: bytes,
        meta: SourceMeta,
        parser_chain: tuple[str, ...],
    ) -> ParseResult:
        parser, _confidence = self._registry.select(list(parser_chain), line)
        if parser is None:
            return ParseResult(classification=LineClassification.UNSUPPORTED)
        return parser.parse(line, meta)
