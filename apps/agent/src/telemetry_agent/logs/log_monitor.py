import logging
import os
import time
from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_agent.logs.status import FileReadStatus

logger = logging.getLogger(__name__)


def _open_shared(path: Path) -> TextIO:
    """Open a log for reading without blocking the writer's rotation.

    On Windows a plain ``open()`` denies delete sharing, so a rename or
    unlink by the log writer fails with WinError 32 while the agent holds
    the file.  Opening with ``FILE_SHARE_DELETE`` gives the POSIX behaviour
    the monitor relies on: the descriptor keeps following the renamed file.
    A missing path still raises ``FileNotFoundError``.
    """
    if os.name != "nt":
        return open(path, encoding="utf-8", errors="replace")

    import ctypes
    import msvcrt
    from ctypes import wintypes

    generic_read = 0x80000000
    share_read_write_delete = 0x1 | 0x2 | 0x4
    open_existing = 3
    file_attribute_normal = 0x80
    invalid_handle = wintypes.HANDLE(-1).value

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE

    handle = create_file(
        str(path),
        generic_read,
        share_read_write_delete,
        None,
        open_existing,
        file_attribute_normal,
        None,
    )
    if handle == invalid_handle:
        # WinError maps ERROR_FILE_NOT_FOUND to FileNotFoundError.
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY)
    except Exception:
        kernel32.CloseHandle(wintypes.HANDLE(handle))
        raise
    return open(fd, encoding="utf-8", errors="replace")


@dataclass(frozen=True, slots=True)
class ReadLine:
    """One complete log line with stable byte identity for idempotent ingest."""

    text: str
    byte_offset: int
    byte_length: int
    dev: int
    inode: int

    @property
    def end_offset(self) -> int:
        return self.byte_offset + self.byte_length


class Harvester:
    """Reads lines from a descriptor bound to a specific OS inode fingerprint."""

    handle: TextIO
    ino: int
    dev: int
    offset: int
    last_read_at: datetime | None

    def __init__(
        self, handle: TextIO, ino: int, dev: int, start_offset: int = 0
    ) -> None:
        self.handle = handle
        self.ino = ino
        self.dev = dev
        self.offset = start_offset
        self.last_read_at = None
        self.handle.seek(self.offset)

    def read_lines(self) -> Generator[ReadLine]:
        """Reads available complete lines from the file handle until EOF."""
        while True:
            line_start = self.handle.tell()
            raw = self.handle.readline()
            if not raw:
                return

            # ``readline`` returns an unterminated final fragment at EOF.  It
            # is not a complete log event yet, so leave the descriptor at its
            # start.  The next poll will read it together with the appended
            # bytes instead of publishing a split (or duplicate) line.
            if not raw.endswith(("\n", "\r")):
                self.handle.seek(line_start)
                return

            end = self.handle.tell()
            self.offset = end
            self.last_read_at = datetime.now(UTC)
            yield ReadLine(
                text=raw.rstrip("\r\n"),
                byte_offset=line_start,
                byte_length=end - line_start,
                dev=self.dev,
                inode=self.ino,
            )

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

    spawns Harvesters, and syncs committed state to OffsetTracker.
    """

    def __init__(
        self,
        file_path: Path,
        offset_tracker: OffsetTracker | None = None,
        *,
        checkpoint_interval: float = 5.0,
        rotation_drain_timeout: float = 5.0,
        commit_on_read: bool = True,
        log_stall_threshold: float = 300.0,
        monotonic: Callable[[], float] = time.monotonic,
        on_event: Callable[[str], None] | None = None,
    ) -> None:
        if checkpoint_interval <= 0:
            raise ValueError("checkpoint_interval must be greater than zero")
        if rotation_drain_timeout < 0:
            raise ValueError("rotation_drain_timeout cannot be negative")
        if log_stall_threshold <= 0:
            raise ValueError("log_stall_threshold must be greater than zero")

        self.file_path = Path(file_path)
        self.offset_tracker = offset_tracker or OffsetTracker()
        self._harvester: Harvester | None = None
        self._retired_harvesters: list[tuple[Harvester, float]] = []
        self._checkpoint_interval = checkpoint_interval
        self._rotation_drain_timeout = rotation_drain_timeout
        self._commit_on_read = commit_on_read
        self._last_checkpoint = time.monotonic()
        self._state_dirty = False
        self._startup_recovery_pending = True
        self._startup_backfill_harvesters: list[Harvester] = []
        self.on_event = on_event
        self._monotonic = monotonic
        self._log_stall_threshold = log_stall_threshold
        self._last_activity = monotonic()
        self._stall_reported = False

    def _emit(self, event_type: str) -> None:
        if self.on_event is not None:
            try:
                self.on_event(event_type)
            except Exception:
                # An observation must never interrupt log consumption.
                logger.warning("log lifecycle event hook failed")

    def _check_stall(self) -> None:
        if (
            not self._stall_reported
            and self._monotonic() - self._last_activity >= self._log_stall_threshold
        ):
            self._stall_reported = True
            self._emit("log.stalled")

    def _get_file_stat(self) -> os.stat_result | None:
        try:
            return self.file_path.stat()
        except FileNotFoundError:
            return None

    def _start_harvester(self, offset: int | None = None) -> None:
        """Spawns a new Harvester bound to the active inode."""
        handle = _open_shared(self.file_path)
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
        if self._commit_on_read:
            self._sync_harvester(self._harvester)

    def _start_recovery_harvester(self, path: Path) -> Harvester | None:
        """Open a rotated sibling from before this monitor started.

        The registry is keyed by device and inode, so an archive continues
        from its saved byte position instead of being replayed after a
        restart.  A vanished archive is expected during log cleanup and is
        simply ignored.
        """
        try:
            handle = _open_shared(path)
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

    def _read_harvester(self, harvester: Harvester) -> Generator[ReadLine]:
        for read_line in harvester.read_lines():
            self._last_activity = self._monotonic()
            self._stall_reported = False
            if self._commit_on_read:
                self._sync_harvester(harvester)
                self._checkpoint_if_due()
            yield read_line

    def _drain_retired_harvesters(self) -> Generator[ReadLine]:
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

    def _drain_startup_recovery(self) -> Generator[ReadLine]:
        """Read retained offline rotations once, then release their handles."""
        for harvester in self._startup_backfill_harvesters:
            try:
                yield from self._read_harvester(harvester)
            finally:
                harvester.close()
        self._startup_backfill_harvesters = []

    def poll_lines(self) -> Generator[ReadLine]:
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
        elif (
            stat_res
            and active_harvester
            and (
                (stat_res.st_ino != active_harvester.ino)
                or (stat_res.st_dev != active_harvester.dev)
            )
        ):
            self._retire_harvester()
            self._start_harvester(offset=0)
            self._emit("log.rotated")

        # 3. Truncation Detected (File size shrank below stored offset)
        elif (
            stat_res and active_harvester and stat_res.st_size < active_harvester.offset
        ):
            active_harvester.seek(0)
            self._emit("log.truncated")
            if self._commit_on_read:
                self._sync_harvester(active_harvester)

        yield from self._drain_retired_harvesters()

        # Stream lines from active harvester
        if self._harvester is None:
            self._check_stall()
            self._checkpoint_if_due()
            return

        yield from self._read_harvester(self._harvester)
        self._check_stall()
        self._checkpoint_if_due()

    def ack_line(self, end_offset: int) -> None:
        """Advance committed offset after successful parse+ingest (FR-PIP-006)."""
        if self._harvester is None:
            return
        self.offset_tracker.commit_offset(
            source_path=str(self.file_path),
            dev=self._harvester.dev,
            ino=self._harvester.ino,
            offset=end_offset,
        )
        self._state_dirty = True

    def flush_commits(self) -> None:
        """Persist committed offsets to disk (checkpoint / shutdown)."""
        self.offset_tracker.save()
        self._last_checkpoint = time.monotonic()
        self._state_dirty = False

    def get_status(self, now: datetime | None = None) -> FileReadStatus:
        """Offset + read lag for this file (UBS-30). See docs/plan/ubs30-notes.md."""
        now = now or datetime.now(UTC)
        stat_res = self._get_file_stat()
        size = stat_res.st_size if stat_res else None

        committed = 0
        if stat_res:
            committed = self.offset_tracker.get_offset(stat_res.st_dev, stat_res.st_ino)

        if self._harvester:
            offset = self._harvester.offset
        elif stat_res:
            offset = committed
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
            committed_offset=committed,
        )

    def close(self) -> None:
        """Safely shuts down the monitor and persists committed byte offsets."""
        if self._harvester:
            if self._commit_on_read:
                self._sync_harvester(self._harvester)
            self._harvester.close()
            self._harvester = None
        for harvester, _ in self._retired_harvesters:
            if self._commit_on_read:
                self._sync_harvester(harvester)
            harvester.close()
        self._retired_harvesters = []
        for harvester in self._startup_backfill_harvesters:
            if self._commit_on_read:
                self._sync_harvester(harvester)
            harvester.close()
        self._startup_backfill_harvesters = []
        self._checkpoint_if_due(force=True)
