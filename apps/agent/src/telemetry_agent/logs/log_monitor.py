import logging
import os
import time
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional, TextIO

from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_agent.logs.status import FileReadStatus

logger = logging.getLogger(__name__)


class Harvester:
    """Reads lines from a single open file descriptor bound to a specific OS inode fingerprint."""

    handle: TextIO
    ino: int
    dev: int
    offset: int
    last_read_at: datetime | None

    def __init__(self, handle: TextIO, ino: int, dev: int, start_offset: int = 0):
        self.handle = handle
        self.ino = ino
        self.dev = dev
        self.offset = start_offset
        self.last_read_at = None
        self.handle.seek(self.offset)

    def read_lines(self) -> Generator[str]:
        """Reads available complete lines from the file handle until EOF."""
        while True:
            line_start = self.handle.tell()
            line = self.handle.readline()
            if not line:
                return

            # ``readline`` returns an unterminated final fragment at EOF.  It
            # is not a complete log event yet, so leave the descriptor at its
            # start.  The next poll will read it together with the appended
            # bytes instead of publishing a split (or duplicate) line.
            if not line.endswith(("\n", "\r")):
                self.handle.seek(line_start)
                return

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

    def __init__(
        self,
        file_path: Path,
        offset_tracker: OffsetTracker | None = None,
        *,
        checkpoint_interval: float = 5.0,
        rotation_drain_timeout: float = 5.0,
    ):
        if checkpoint_interval <= 0:
            raise ValueError("checkpoint_interval must be greater than zero")
        if rotation_drain_timeout < 0:
            raise ValueError("rotation_drain_timeout cannot be negative")

        self.file_path = Path(file_path)
        self.offset_tracker = offset_tracker or OffsetTracker()
        self._harvester: Harvester | None = None
        self._retired_harvesters: list[tuple[Harvester, float]] = []
        self._checkpoint_interval = checkpoint_interval
        self._rotation_drain_timeout = rotation_drain_timeout
        self._last_checkpoint = time.monotonic()
        self._state_dirty = False
        self._startup_recovery_pending = True
        self._startup_backfill_harvesters: list[Harvester] = []

    def _get_file_stat(self) -> os.stat_result | None:
        try:
            return self.file_path.stat()
        except FileNotFoundError:
            return None

    def _start_harvester(self, offset: int | None = None) -> None:
        """Spawns a new Harvester bound to the active inode."""
        handle = open(self.file_path, encoding="utf-8", errors="replace")
        # The path can rotate between stat() and open(); bind to the file
        # descriptor actually opened rather than the earlier path identity.
        opened_stat = os.fstat(handle.fileno())
        try:
            if offset is None:
                offset = self.offset_tracker.get_offset(
                    opened_stat.st_dev, opened_stat.st_ino
                )
            if offset > opened_stat.st_size:
                offset = 0

            self._harvester = Harvester(
                handle=handle,
                ino=opened_stat.st_ino,
                dev=opened_stat.st_dev,
                start_offset=offset,
            )
        except Exception:
            handle.close()
            raise
        self._sync_offset()

    def _start_recovery_harvester(self, path: Path) -> Harvester | None:
        """Open a rotated sibling from before this monitor started.

        The registry is keyed by device and inode, so an archive continues
        from its saved byte position instead of being replayed after a
        restart.  A vanished archive is expected during log cleanup and is
        simply ignored.
        """
        try:
            handle = open(path, encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return None

        try:
            opened_stat = os.fstat(handle.fileno())
            offset = self.offset_tracker.get_offset(
                opened_stat.st_dev, opened_stat.st_ino
            )
            if offset > opened_stat.st_size:
                offset = 0
            return Harvester(
                handle=handle,
                ino=opened_stat.st_ino,
                dev=opened_stat.st_dev,
                start_offset=offset,
            )
        except Exception:
            handle.close()
            raise

    def _prepare_startup_recovery(self) -> None:
        """Find retained rotations that were created while the agent was down.

        This intentionally scans only once, before the active file is read.
        Subsequent rotations are handled through the active file descriptor;
        treating every ``*.log.*`` file as live would otherwise replay old
        archives on every poll.
        """
        if not self._startup_recovery_pending:
            return
        self._startup_recovery_pending = False

        candidates: list[tuple[int, Path]] = []
        for path in self.file_path.parent.glob(f"{self.file_path.name}.*"):
            if path.suffix in {".gz", ".bz2", ".xz", ".zip"}:
                continue
            try:
                stat_res = path.stat()
            except FileNotFoundError:
                # Rotation cleanup may remove an archive while it is scanned.
                continue
            if path.is_file():
                candidates.append((stat_res.st_mtime_ns, path))
        # Modification time is the best portable ordering available across
        # rotation schemes such as ``.1`` and date-based suffixes.
        candidates.sort(key=lambda candidate: candidate[0])
        for _, path in candidates:
            harvester = self._start_recovery_harvester(path)
            if harvester is not None:
                self._startup_backfill_harvesters.append(harvester)

    def _retire_harvester(self) -> None:
        """Keep a rotated descriptor alive to collect its final writes."""
        if self._harvester:
            deadline = time.monotonic() + self._rotation_drain_timeout
            self._retired_harvesters.append((self._harvester, deadline))
            self._harvester = None

    def _sync_harvester(self, harvester: Harvester) -> None:
        self.offset_tracker.update_offset(
            source_path=str(self.file_path),
            dev=harvester.dev,
            ino=harvester.ino,
            offset=harvester.offset,
        )
        self._state_dirty = True

    def _sync_offset(self) -> None:
        """Flushes current Harvester state to the OffsetTracker."""
        if self._harvester:
            self._sync_harvester(self._harvester)

    def _checkpoint_if_due(self, *, force: bool = False) -> None:
        """Persist progress even when a continuously busy file never reaches EOF."""
        if not self._state_dirty:
            return
        checkpoint_due = (
            time.monotonic() - self._last_checkpoint >= self._checkpoint_interval
        )
        if force or checkpoint_due:
            self.offset_tracker.save()
            self._last_checkpoint = time.monotonic()
            self._state_dirty = False

    def _read_harvester(self, harvester: Harvester) -> Generator[str]:
        for line in harvester.read_lines():
            self._sync_harvester(harvester)
            self._checkpoint_if_due()
            yield line

    def _drain_retired_harvesters(self) -> Generator[str]:
        """Drain rotated files without delaying their active replacements."""
        remaining: list[tuple[Harvester, float]] = []
        now = time.monotonic()
        for harvester, deadline in self._retired_harvesters:
            yield from self._read_harvester(harvester)
            if now >= deadline:
                harvester.close()
            else:
                remaining.append((harvester, deadline))
        self._retired_harvesters = remaining

    def _drain_startup_recovery(self) -> Generator[str]:
        """Read retained offline rotations once, then release their handles."""
        for harvester in self._startup_backfill_harvesters:
            try:
                yield from self._read_harvester(harvester)
            finally:
                harvester.close()
        self._startup_backfill_harvesters = []

    def poll_lines(self) -> Generator[str]:
        """Polls for new log lines and manages Harvester lifecycle events."""
        # If rotation happened while the process was stopped, the active path
        # alone cannot reveal the old inode.  Backfill retained sibling files
        # before tailing the replacement active file.
        self._prepare_startup_recovery()
        yield from self._drain_startup_recovery()

        stat_res = self._get_file_stat()
        active_harvester = self._harvester

        # 1. Initial Startup: Query OffsetTracker and spawn harvester
        if stat_res and active_harvester is None:
            self._start_harvester()

        # 2. Rotation Detected (Inode / Device Mismatch)
        elif stat_res and active_harvester and (
            (stat_res.st_ino != active_harvester.ino)
            or (stat_res.st_dev != active_harvester.dev)
        ):
            self._retire_harvester()
            self._start_harvester(offset=0)

        # 3. Truncation Detected (File size shrank below stored offset)
        elif (
            stat_res
            and active_harvester
            and stat_res.st_size < active_harvester.offset
        ):
            active_harvester.seek(0)
            self._sync_offset()

        yield from self._drain_retired_harvesters()

        # Stream lines from active harvester
        if self._harvester is None:
            self._checkpoint_if_due()
            return

        yield from self._read_harvester(self._harvester)
        self._checkpoint_if_due()

    def get_status(self, now: datetime | None = None) -> FileReadStatus:
        """Offset + read lag for this file (UBS-30). See docs/plan/ubs30-notes.md."""
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
            self._harvester.close()
            self._harvester = None
        for harvester, _ in self._retired_harvesters:
            self._sync_harvester(harvester)
            harvester.close()
        self._retired_harvesters = []
        for harvester in self._startup_backfill_harvesters:
            self._sync_harvester(harvester)
            harvester.close()
        self._startup_backfill_harvesters = []
        self._checkpoint_if_due(force=True)
