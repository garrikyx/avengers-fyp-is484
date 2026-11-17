"""Connect MultiLogMonitor reads to PipelineBridge (FR-PIP-001/006)."""

from __future__ import annotations

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
        self._paths = {
            name: str(m.file_path.resolve()) for name, m in monitor.monitors.items()
        }
        if bridge.committer is None:
            bridge.attach_committer(path_map)

    def _emit(self, message: str) -> None:
        if self._on_stage is not None:
            self._on_stage(message)

    def poll_once(
        self,
        poll_interval: float = 0.05,
        *,
        should_stop: Callable[[], bool] | None = None,
    ) -> list[ParsedEvent]:
        processed: list[ParsedEvent] = []
        any_line = False
        for name, monitor in self._monitor.monitors.items():
            read_count = 0
            for read_line in monitor.poll_lines():
                # UBS-140 / NFR-REL-004: a continuous writer or a full line
                # queue must not keep the pump alive after shutdown. Read-ahead
                # is safe: FR-PIP-006 leaves these offsets uncommitted, so the
                # next agent reads the unfinished lines from the source file.
                if should_stop is not None and should_stop():
                    return self._bridge.process_commits()
                any_line = True
                if self._on_stage is not None:
                    self._emit(
                        f"[MONITOR] {name} @offset {read_line.byte_offset} "
                        f"({len(read_line.text)} chars)"
                    )
                meta = source_meta_from_read_line(
                    read_line,
                    path=self._paths[name],
                    instance_id=self._instance_id,
                    log_type=self._log_type,
                    file_set=name,
                )
                while not self._bridge.enqueue_line(
                    read_line.text.encode("utf-8"),
                    meta,
                    self._parser_chain,
                    timeout=0,
                ):
                    processed.extend(self._bridge.process_commits())
                    if should_stop is not None and should_stop():
                        return processed
                    # This thread also drains the downstream queue. Waiting
                    # on input capacity starves that drain and stalls workers.
                    time.sleep(0.001)
                processed.extend(self._bridge.process_commits())
                if self._on_stage is not None:
                    stats = self._bridge.stats()
                    self._emit(f"[QUEUE] line_depth={stats.line_queue_depth}")
                read_count += 1
                if read_count >= 256:
                    # Bound returned events and give other files a turn even
                    # when a writer never lets this file reach EOF.
                    break
            monitor.checkpoint_if_due()
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
