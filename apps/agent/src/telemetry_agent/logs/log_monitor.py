import logging
import os
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from .offset_tracker import OffsetTracker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileReadStatus:
    """Point-in-time read status for a single monitored file.

    Mirrors the fields spec 002 (`FR-LOG-010`) and spec 011 (health signals table,
    `files[].offset`) expect the Health Reporter to surface: byte offset progress and
    read lag, the time since the last line was successfully read.
    """

    path: str
    offset: int
    size: int | None
    last_read_at: datetime | None
    read_lag_ms: float | None

    @property
    def has_read_any_line(self) -> bool:
        return self.last_read_at is not None


class Harvester:
    """Reads lines from a single open file descriptor bound to a specific OS inode fingerprint."""

    def __init__(self, handle: TextIO, ino: int, dev: int, start_offset: int = 0):
        self.handle = handle
        self.ino = ino
        self.dev = dev
        self.offset = start_offset
        # FR-LOG-010: "timestamp of last line read" — unset until this harvester
        # yields a line. Left as None (not 0/epoch) so an idle-since-start file is
        # distinguishable from a genuinely fresh read (FR-HLT-004: never present a
        # data gap as a zero-value lag).
        self.last_read_at: datetime | None = None
        self.handle.seek(self.offset)

    def read_lines(self) -> Generator[str]:
        """Reads available complete lines from the file handle until EOF."""
        while line := self.handle.readline():
            self.offset = self.handle.tell()
            self.last_read_at = datetime.now(UTC)
            yield line.rstrip("\r\n")

    def seek(self, offset: int) -> None:
        """Repositions the file pointer and updates current offset."""
        self.handle.seek(offset)
        self.offset = offset

    def close(self) -> None:
        """Safely closes the underlying file descriptor."""
        if self.handle and not self.handle.closed:
            self.handle.close()


class LogMonitor:
    """Monitors file paths, handles rotations/truncations,

    spawns Harvesters, and syncs state to OffsetTracker.
    """

    def __init__(self, file_path: Path, offset_tracker: OffsetTracker | None = None):
        self.file_path = Path(file_path)
        self.offset_tracker = offset_tracker or OffsetTracker()
        self._harvester: Harvester | None = None

    def _get_file_stat(self) -> os.stat_result | None:
        try:
            return self.file_path.stat()
        except FileNotFoundError:
            return None

    def _start_harvester(self, stat_res: os.stat_result, offset: int | None = None) -> None:
        """Spawns a new Harvester bound to the active inode."""
        if self._harvester:
            self._harvester.close()

        # Retrieve saved offset from registry if not explicitly provided
        if offset is None:
            offset = self.offset_tracker.get_offset(stat_res.st_dev, stat_res.st_ino)

        # Guard against seeking past EOF (e.g., if truncated while agent was offline)
        if offset > stat_res.st_size:
            offset = 0

        handle = open(self.file_path, encoding="utf-8", errors="replace")
        self._harvester = Harvester(
            handle=handle,
            ino=stat_res.st_ino,
            dev=stat_res.st_dev,
            start_offset=offset,
        )
        self._sync_offset()

    def _drain_and_close_harvester(self) -> Generator[str]:
        """Drains an existing Harvester to EOF before closing."""
        if not self._harvester:
            return

        yield from self._harvester.read_lines()
        self._harvester.close()
        self._harvester = None

    def _sync_offset(self) -> None:
        """Flushes current Harvester state to the OffsetTracker."""
        if self._harvester:
            self.offset_tracker.update_offset(
                source_path=str(self.file_path),
                dev=self._harvester.dev,
                ino=self._harvester.ino,
                offset=self._harvester.offset,
            )

    def poll_lines(self) -> Generator[str]:
        """Polls for new log lines and manages Harvester lifecycle events."""
        stat_res = self._get_file_stat()

        if not stat_res:
            return

        # 1. Initial Startup: Query OffsetTracker and spawn harvester
        if self._harvester is None:
            self._start_harvester(stat_res)

        # 2. Rotation Detected (Inode / Device Mismatch)
        elif (stat_res.st_ino != self._harvester.ino) or (stat_res.st_dev != self._harvester.dev):
            yield from self._drain_and_close_harvester()
            self._start_harvester(stat_res, offset=0)

        # 3. Truncation Detected (File size shrank below stored offset)
        elif stat_res.st_size < self._harvester.offset:
            self._harvester.seek(0)
            self._sync_offset()

        # Stream lines from active harvester
        if self._harvester is None:
            return

        lines_read = False
        for line in self._harvester.read_lines():
            lines_read = True
            yield line

        # Persist registry state to disk if data was processed
        if lines_read:
            self._sync_offset()
            self.offset_tracker.save()

    def get_status(self, now: datetime | None = None) -> FileReadStatus:
        """Reports this file's current offset progress and read lag (`FR-LOG-010`).

        `read_lag_ms` is `now - last_read_at`: the time since the last line was
        successfully read from this file, not a byte count. It is `None` until at least
        one line has been read, since a lag of "0ms" would misreport a file the agent
        has never actually read from as perfectly healthy (`FR-HLT-004`).
        """
        now = now or datetime.now(UTC)
        stat_res = self._get_file_stat()
        size = stat_res.st_size if stat_res else None

        if self._harvester:
            offset = self._harvester.offset
        elif stat_res:
            offset = self.offset_tracker.get_offset(stat_res.st_dev, stat_res.st_ino)
        else:
            offset = 0

        last_read_at = self._harvester.last_read_at if self._harvester else None
        read_lag_ms: float | None = None
        if last_read_at is not None:
            read_lag_ms = (now - last_read_at).total_seconds() * 1000

        return FileReadStatus(
            path=str(self.file_path),
            offset=offset,
            size=size,
            last_read_at=last_read_at,
            read_lag_ms=read_lag_ms,
        )

    def close(self) -> None:
        """Safely shuts down the monitor and persists final byte offsets."""
        if self._harvester:
            self._sync_offset()
            self.offset_tracker.save()
            self._harvester.close()
            self._harvester = None
