"""Connect MultiLogMonitor reads to PipelineBridge (FR-PIP-001/006)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime

from telemetry_agent.logs.log_monitor import LogMonitor, ReadLine
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.pipeline.supervisor import PipelineBridge
from telemetry_agent.pipeline.types import ParsedEvent


def source_meta_from_read_line(
    read_line: ReadLine,
    *,
    path: str,
    instance_id: str = "demo",
    log_type: str = "fix",
    file_set: str = "",
) -> SourceMeta:
    return SourceMeta(
        instance_id=instance_id,
        path=path,
        log_type=log_type,
        read_at=datetime.now(tz=UTC),
        dev=read_line.dev,
        inode=read_line.inode,
        byte_offset=read_line.byte_offset,
        byte_length=read_line.byte_length,
        file_set=file_set,
    )


def monitors_by_resolved_path(monitors: dict[str, LogMonitor]) -> dict[str, LogMonitor]:
    return {str(monitor.file_path.resolve()): monitor for monitor in monitors.values()}


class MonitorPipelineAdapter:
    """Polls files, enqueues lines, and processes commits in one loop."""

    def __init__(
        self,
        monitor: MultiLogMonitor,
        bridge: PipelineBridge,
        *,
        parser_chain: list[str],
        instance_id: str = "demo",
        log_type: str = "fix",
        on_stage: Callable[[str], None] | None = None,
    ) -> None:
        self._monitor = monitor
        self._bridge = bridge
        self._parser_chain = parser_chain
        self._instance_id = instance_id
        self._log_type = log_type
        self._on_stage = on_stage
        path_map = monitors_by_resolved_path(monitor.monitors)
        if bridge.committer is None:
            bridge.attach_committer(path_map)

    def _emit(self, message: str) -> None:
        if self._on_stage is not None:
            self._on_stage(message)

    def poll_once(
        self, poll_interval: float = 0.05, halt: threading.Event | None = None
    ) -> list[ParsedEvent]:
        """One pass over every file. Returns early once `halt` is set; lines read
        but not yet ingested stay uncommitted, so a restart re-reads them
        (FR-PIP-006)."""
        processed: list[ParsedEvent] = []
        any_line = False
        for name, monitor in self._monitor.monitors.items():
            path = str(monitor.file_path.resolve())  # once per pass, not per line
            for read_line in monitor.poll_lines():
                if halt is not None and halt.is_set():
                    return processed
                any_line = True
                if self._on_stage is not None:
                    self._emit(
                        f"[MONITOR] {name} @offset {read_line.byte_offset} "
                        f"({len(read_line.text)} chars)"
                    )
                meta = source_meta_from_read_line(
                    read_line,
                    path=path,
                    instance_id=self._instance_id,
                    log_type=self._log_type,
                    file_set=name,
                )
                # This thread is the only consumer of the event queue, so when the
                # line queue is full the workers are waiting on us: ingest first,
                # then wait briefly for a free slot (not the 0.5s put timeout).
                while not self._bridge.enqueue_line(
                    read_line.text.encode("utf-8"),
                    meta,
                    self._parser_chain,
                    timeout=0.01,
                ):
                    self._bridge.process_commits()
                    if halt is not None and halt.is_set():
                        return processed
                if self._on_stage is not None:
                    stats = self._bridge.stats()
                    self._emit(f"[QUEUE] line_depth={stats.line_queue_depth}")
        if not any_line:
            time.sleep(poll_interval)
        processed.extend(self._bridge.process_commits())
        return processed

    def run_until(
        self,
        *,
        max_lines: int | None = None,
        poll_interval: float = 0.05,
        idle_rounds: int = 3,
    ) -> Iterator[ParsedEvent]:
        """Yield parsed events until max_lines or idle_rounds with no new data."""
        seen = 0
        idle = 0
        while True:
            before = seen
            for event in self.poll_once(poll_interval=poll_interval):
                seen += 1
                yield event
                if max_lines is not None and seen >= max_lines:
                    return
            if seen == before:
                idle += 1
                if idle >= idle_rounds:
                    return
            else:
                idle = 0
