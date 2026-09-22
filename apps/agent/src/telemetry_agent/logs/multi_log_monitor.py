"""Multi-file polling and lifecycle management for the Log Monitor."""

import time
from collections.abc import Generator, Iterable
from datetime import datetime
from pathlib import Path

from telemetry_agent.logs.log_monitor import LogMonitor, ReadLine
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_agent.logs.status import FileReadStatus


class MultiLogMonitor:
    """Round-robin wrapper over one LogMonitor per file and shared offsets."""

    def __init__(
        self,
        log_paths: Iterable[Path],
        registry_path: Path = Path("offsets.json"),
        *,
        read_mode: str = "tail",
        checkpoint_interval: float = 5.0,
        rotation_drain_timeout: float = 5.0,
        auto_commit: bool = False,
        commit_on_read: bool | None = None,
    ) -> None:
        if read_mode not in {"tail", "interval"}:
            raise ValueError("read_mode must be 'tail' or 'interval'")

        self.registry_path = Path(registry_path)
        self.read_mode = read_mode
        self._offset_tracker = OffsetTracker(registry_path=self.registry_path)
        self._auto_commit = auto_commit
        if commit_on_read is None:
            commit_on_read = not auto_commit
        self._commit_on_read = commit_on_read
        self._monitors: dict[str, LogMonitor] = {
            Path(path).name: LogMonitor(
                Path(path),
                offset_tracker=self._offset_tracker,
                checkpoint_interval=checkpoint_interval,
                rotation_drain_timeout=rotation_drain_timeout,
                commit_on_read=commit_on_read,
            )
            for path in log_paths
        }

    @property
    def monitors(self) -> dict[str, LogMonitor]:
        """Underlying monitors, keyed by their configured filenames."""
        return self._monitors

    def stream_lines(
        self, poll_interval: float = 1.0
    ) -> Generator[tuple[str, ReadLine]]:
        """Yield ``(source_name, ReadLine)`` from every configured file.

        Tail mode polls immediately while data is flowing and waits only while
        idle. Interval mode waits for ``poll_interval`` after every scan.
        """
        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than zero")

        while True:
            any_line = False
            for name, monitor in self._monitors.items():
                for read_line in monitor.poll_lines():
                    any_line = True
                    if self._auto_commit:
                        monitor.ack_line(read_line.end_offset)
                    yield name, read_line
            if self.read_mode == "interval" or not any_line:
                time.sleep(poll_interval)

    def get_statuses(self, now: datetime | None = None) -> dict[str, FileReadStatus]:
        """Return offset and read-lag state for every configured file."""
        return {
            name: monitor.get_status(now=now)
            for name, monitor in self._monitors.items()
        }

    def close(self) -> None:
        """Checkpoint and close all file monitors."""
        for monitor in self._monitors.values():
            monitor.close()
