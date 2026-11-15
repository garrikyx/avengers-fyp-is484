"""Host Monitor: host disk/memory gauges and the agent's own resource usage.

UBS-129; spec 002 §7.1 (FR-HLT-013, 015, 016), spec 004 §4.7 (FR-MET-034),
spec 010 `host:`. It reads OS counters only: never file contents, never a
command line, never Magic logs.

Every `host.sampleInterval` the monitor samples

- `host_disk_used_ratio`: 1 - free / total bytes of each `host.diskPaths`
  filesystem (the free/total pair of FR-HLT-013). The wire `Snapshot.gauges` and
  the rule engine's `Gauges` are flat (no dimensions), so spec 004's `mount`
  dimension is encoded in the key (`telemetry_shared.metrics.host`): the plain
  gauge is the **worst mount** (the maximum over the readable mounts), which is
  what `HostDiskFull` reads, and every readable mount also gets
  `host_disk_used_ratio:<mount>`. A mount that cannot be read is left out of
  both and counted in `host_sample_errors`, so the maximum is over the readable
  mounts only: a missing per-mount key is how to tell that the worst mount may
  be the unreadable one.
- `host_memory_used_ratio`: (total - available) / total physical memory.
- the agent process's own RSS, CPU and event-loop task count, for the heartbeat
  `resourceUsage`.

UBS-130 adds `magic_process_up` (FR-HLT-014): 1.0 if a running process's
executable name equals `host.process.name` exactly, else 0.0. The match is by
name only: no command line or argument is ever read, and no case folding is
applied (spec 002 says "exact executable name"). While `host.process.name` is
empty the gauge is not reported, nothing is read and nothing is counted, so
`ApplicationDown` stays inactive. If the process list cannot be read, or yields
no names at all, the gauge is omitted (and `host_sample_errors` counted), never
0: an unreadable list is "no data", not "Magic is down". The consequence is that
a host where the agent may not list processes never raises `ApplicationDown`.
How the names are read is `PsutilSampler`'s concern (see there): psutil's
`Process.name()` is not used because on POSIX it reads the command line.

**Omit, never zero (FR-MET-034, FR-HLT-015).** A read that fails (permission,
platform) leaves that gauge out of `gauges()` and increments
`host_sample_errors`; the other reads and the agent carry on. A rule then sees
"no data" instead of a false "disk empty". A failed sample also drops the
previous value, so a stale reading is never presented as current.
`host_sample_errors` is the monitor's own counter registry; the evaluator feeds
it into the aggregator like the other agent counters (`metrics.agent_counters`),
so it is queryable and on the wire as a windowed series, not just a shutdown log.

**Threading (FR-HLT-015).** `run()` does each blocking sample in a worker
thread (`asyncio.to_thread`), so it never touches the parsing path or blocks
the event loop. A sample builds a fresh immutable `HostSample` and publishes
it with one attribute assignment, so readers on other threads (the rule
evaluator, the snapshot emitter, the heartbeat) need no lock and never see a
half-written sample.

The sampler is a `Protocol`: tests stub it and never import psutil.
`PsutilSampler` is the production implementation.
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Protocol

from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_shared.metrics.host import (
    HOST_DISK_USED_RATIO,
    HOST_MEMORY_USED_RATIO,
    MAGIC_PROCESS_UP,
    disk_mount_gauge,
)
from telemetry_shared.models.health import ResourceUsage

SAMPLE_ERRORS = "host_sample_errors"

DEFAULT_SAMPLE_INTERVAL_SECONDS = 30.0
# spec 004 `mount` dimension cap (§4.7).
MAX_DISK_PATHS = 8
# The kernel keeps at most 15 characters of an executable name in `comm`.
LINUX_COMM_MAX = 15


def default_disk_paths(platform: str | None = None) -> tuple[str, ...]:
    """spec 010's default `/var/log/magic` where it can exist (POSIX); on
    Windows, which has no such path, the system drive root, so the default does
    not count a read error on every tick."""
    if (platform or sys.platform) == "win32":
        return (os.path.abspath(os.sep),)
    return ("/var/log/magic",)


DEFAULT_DISK_PATHS = default_disk_paths()


@dataclass(frozen=True, slots=True)
class HostConfig:
    """spec 010 `host:` block. Owns its own validation (`ValueError`)."""

    enabled: bool = True
    sample_interval_seconds: float = DEFAULT_SAMPLE_INTERVAL_SECONDS
    disk_paths: tuple[str, ...] = DEFAULT_DISK_PATHS
    memory: bool = True
    # FR-HLT-014 (UBS-130): exact executable name; empty disables the gauge.
    process_name: str = ""

    def __post_init__(self) -> None:
        if not 0 < self.sample_interval_seconds < math.inf:
            raise ValueError("sampleInterval must be finite and > 0")
        if len(self.disk_paths) > MAX_DISK_PATHS:
            raise ValueError(f"diskPaths lists more than {MAX_DISK_PATHS}")
        if any(not p.strip() for p in self.disk_paths):
            raise ValueError("diskPaths entries must be non-empty paths")


class HostSampler(Protocol):
    """Reads OS counters. Each method raises when the read is impossible."""

    def disk_used_ratio(self, path: str) -> float: ...

    def memory_used_ratio(self) -> float: ...

    def own_usage(self) -> tuple[float, float]:
        """(rss_mb, cpu_percent) of the agent process itself."""
        ...

    def process_running(self, name: str) -> bool:
        """Whether a running process's executable name is exactly `name`
        (FR-HLT-014). An implementation must not read command lines, and must
        raise rather than answer False when it cannot list the processes."""
        ...


@dataclass(frozen=True, slots=True)
class HostSample:
    gauges: dict[str, float] = field(default_factory=dict)
    resource_usage: ResourceUsage | None = None


def _ratio(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError(f"non-finite ratio {value!r}")
    return min(1.0, max(0.0, value))


class HostMonitor:
    def __init__(
        self,
        config: HostConfig,
        sampler: HostSampler,
        *,
        counters: CounterRegistry | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._sampler = sampler
        self._counters = CounterRegistry() if counters is None else counters
        self._logger = logger or logging.getLogger(__name__)
        self._sample = HostSample()

    @property
    def counters(self) -> CounterRegistry:
        return self._counters

    @property
    def interval_seconds(self) -> float:
        return self._config.sample_interval_seconds

    def gauges(self) -> dict[str, float]:
        """Gauges read on the latest sample; an unreadable one is absent."""
        return dict(self._sample.gauges)

    def resource_usage(self) -> ResourceUsage | None:
        """The agent's own RSS/CPU from the latest sample; None if unread."""
        return self._sample.resource_usage

    def sample_once(self, active_tasks: int | None = None) -> None:
        """One tick. Never raises: a failed read is counted and omitted.

        `active_tasks` is the event loop's task count. It cannot be read from
        this worker thread, so `run()` reads it on the loop and passes it in.
        """
        gauges: dict[str, float] = {}

        mounts: dict[str, float] = {}
        for path in self._config.disk_paths:
            ratio = self._read_ratio(partial(self._sampler.disk_used_ratio, path))
            if ratio is not None:
                mounts[path] = ratio
        if mounts:
            gauges[HOST_DISK_USED_RATIO] = max(mounts.values())
            for path, ratio in mounts.items():
                gauges[disk_mount_gauge(path)] = ratio

        if self._config.memory:
            memory = self._read_ratio(self._sampler.memory_used_ratio)
            if memory is not None:
                gauges[HOST_MEMORY_USED_RATIO] = memory

        if self._config.process_name:
            up = self._read_process_up(self._config.process_name)
            if up is not None:
                gauges[MAGIC_PROCESS_UP] = up

        usage: ResourceUsage | None = None
        try:
            rss_mb, cpu_percent = self._sampler.own_usage()
            usage = ResourceUsage(
                rss_mb=rss_mb, cpu_percent=cpu_percent, active_tasks=active_tasks
            )
        except Exception:
            self._record_error("own resource usage")

        self._sample = HostSample(gauges=gauges, resource_usage=usage)

    def _read_ratio(self, read: Callable[[], float]) -> float | None:
        try:
            return _ratio(read())
        except Exception:
            self._record_error("host gauge")
            return None

    def _read_process_up(self, name: str) -> float | None:
        try:
            return 1.0 if self._sampler.process_running(name) else 0.0
        except Exception:
            self._record_error("process list")
            return None

    def _record_error(self, what: str) -> None:
        self._counters.increment(SAMPLE_ERRORS)
        self._logger.debug("host sample failed: %s", what, exc_info=True)

    async def run(self, stop: asyncio.Event | None = None) -> None:
        """Sample every interval until `stop` is set; the first tick is
        immediate. Nothing a tick does can end the loop (FR-HLT-015)."""
        stop = stop or asyncio.Event()
        while not stop.is_set():
            try:
                await asyncio.to_thread(self.sample_once, len(asyncio.all_tasks()))
            except Exception:  # sample_once handles reads; belt and braces
                self._counters.increment(SAMPLE_ERRORS)
                self._logger.exception("host sample tick failed")
            try:
                await asyncio.wait_for(stop.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                continue


class PsutilSampler:
    """Production `HostSampler`. Reads counters only, never process arguments."""

    def __init__(
        self, *, platform: str | None = None, proc_root: Path = Path("/proc")
    ) -> None:
        import psutil

        platform = platform or sys.platform
        self._linux = platform.startswith("linux")
        self._windows = platform == "win32"
        self._proc_root = proc_root
        self._psutil = psutil
        self._process = psutil.Process()
        self._process.cpu_percent(interval=None)  # first call is always 0.0

    def disk_used_ratio(self, path: str) -> float:
        usage = self._psutil.disk_usage(path)
        if usage.total <= 0:
            raise ValueError(f"filesystem for {path!r} reports no capacity")
        # Space the agent's user can still write, not `used / total`: on APFS
        # `used` is per-volume while `free` is shared across the container, and
        # on ext4 `free` already excludes the root-reserved blocks. This is the
        # same free/total pair FR-HLT-013 names.
        return float(1.0 - usage.free / usage.total)

    def memory_used_ratio(self) -> float:
        memory = self._psutil.virtual_memory()
        if memory.total <= 0:
            raise ValueError("no physical memory reported")
        return float((memory.total - memory.available) / memory.total)

    def process_running(self, name: str) -> bool:
        """Exact executable-name match, never reading a command line.

        psutil's `Process.name()` cannot be used: on POSIX it reads the command
        line (`cmdline()`) whenever the OS name is 15+ characters, to un-truncate
        it (verified against psutil 7.2.2). So the names come from sources that
        carry no arguments:

        - Linux: `/proc/<pid>/comm`, the kernel's executable name. It is
          truncated to 15 characters, so a configured name longer than that is
          compared by its first 15 (`LINUX_COMM_MAX`); two executables sharing
          that prefix cannot be told apart. `comm` is also what a process that
          renames itself (`prctl`) shows.
        - Windows: `name`, which psutil takes from the process table and never
          from a command line (only POSIX does that).
        - anywhere else (macOS, BSD): unsupported. psutil's `exe()` also falls
          back to the command line on POSIX when it is denied, so there is no
          public psutil call that is safe there; this raises and the gauge is
          omitted rather than the command line being read.

        Raises `OSError` when no process name could be read at all: an
        unreadable list is "no data", never "Magic is down" (FR-MET-034).
        """
        if self._linux:
            names = self._linux_comms()
        elif self._windows:
            names = self._windows_names()
        else:
            raise OSError("process listing is supported on Linux and Windows only")
        if not names:
            raise OSError("no process names could be read")
        return (name[:LINUX_COMM_MAX] if self._linux else name) in names

    def _linux_comms(self) -> set[str]:
        names: set[str] = set()
        with os.scandir(self._proc_root) as entries:  # OSError: caller counts it
            for entry in entries:
                if not entry.name.isdigit():
                    continue
                try:
                    comm = (Path(entry.path) / "comm").read_text(errors="replace")
                except OSError:  # exited mid-scan, or hidden from this user
                    continue
                names.add(comm.rstrip("\n"))
        return names

    def _windows_names(self) -> set[str]:
        names: set[str] = set()
        for proc in self._psutil.process_iter(attrs=["name"]):
            # A process that exits or denies access mid-scan has None here.
            value = proc.info.get("name")
            if value:
                names.add(value)
        return names

    def own_usage(self) -> tuple[float, float]:
        rss_mb = self._process.memory_info().rss / (1024 * 1024)
        return float(rss_mb), float(self._process.cpu_percent(interval=None))
