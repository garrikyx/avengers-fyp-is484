import logging
import os
from pathlib import Path
from typing import Generator, Optional, TextIO

from .offset_tracker import OffsetTracker

logger = logging.getLogger(__name__)


class Harvester:
    """Reads lines from a single open file descriptor bound to a specific OS inode fingerprint."""

    def __init__(self, handle: TextIO, ino: int, dev: int, start_offset: int = 0):
        self.handle = handle
        self.ino = ino
        self.dev = dev
        self.offset = start_offset
        self.handle.seek(self.offset)

    def read_lines(self) -> Generator[str, None, None]:
        """Reads available complete lines from the file handle until EOF."""
        while line := self.handle.readline():
            self.offset = self.handle.tell()
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

    def __init__(self, file_path: Path, offset_tracker: Optional[OffsetTracker] = None):
        self.file_path = Path(file_path)
        self.offset_tracker = offset_tracker or OffsetTracker()
        self._harvester: Optional[Harvester] = None

    def _get_file_stat(self) -> Optional[os.stat_result]:
        try:
            return self.file_path.stat()
        except FileNotFoundError:
            return None

    def _start_harvester(self, stat_res: os.stat_result, offset: Optional[int] = None) -> None:
        """Spawns a new Harvester bound to the active inode."""
        if self._harvester:
            self._harvester.close()

        # Retrieve saved offset from registry if not explicitly provided
        if offset is None:
            offset = self.offset_tracker.get_offset(stat_res.st_dev, stat_res.st_ino)

        # Guard against seeking past EOF (e.g., if truncated while agent was offline)
        if offset > stat_res.st_size:
            offset = 0

        handle = open(self.file_path, "r", encoding="utf-8", errors="replace")
        self._harvester = Harvester(
            handle=handle,
            ino=stat_res.st_ino,
            dev=stat_res.st_dev,
            start_offset=offset,
        )
        self._sync_offset()

    def _drain_and_close_harvester(self) -> Generator[str, None, None]:
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

    def poll_lines(self) -> Generator[str, None, None]:
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
        lines_read = False
        for line in self._harvester.read_lines():
            lines_read = True
            yield line

        # Persist registry state to disk if data was processed
        if lines_read:
            self._sync_offset()
            self.offset_tracker.save()

    def close(self) -> None:
        """Safely shuts down the monitor and persists final byte offsets."""
        if self._harvester:
            self._sync_offset()
            self.offset_tracker.save()
            self._harvester.close()
            self._harvester = None