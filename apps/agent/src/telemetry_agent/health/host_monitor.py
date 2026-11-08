"""Host Monitor: host disk/memory gauges and the agent's own resource usage.

UBS-129; spec 002 §7.1 (FR-HLT-013, 015, 016), spec 004 §4.7 (FR-MET-034),
spec 010 `host:`. It reads OS counters only: never file contents, never a
command line, never Magic logs.

Every `host.sampleInterval` the monitor samples

- `host_disk_used_ratio`: used / total bytes of each `host.diskPaths`
  filesystem. The wire `Snapshot.gauges` and the rule engine's `Gauges` are
  flat (no dimensions), so the single gauge is the **worst mount** (the
  maximum); spec 004's `mount` dimension is not carried. One full filesystem
  is what `HostDiskFull` has to catch.
- `host_memory_used_ratio`: (total - available) / total physical memory.
- the agent process's own RSS and CPU, for the heartbeat `resourceUsage`.

**Omit, never zero (FR-MET-034, FR-HLT-015).** A read that fails (permission,
platform) leaves that gauge out of `gauges()` and increments
`host_sample_errors`; the other reads and the agent carry on. A rule then sees
"no data" instead of a false "disk empty". A failed sample also drops the
previous value, so a stale reading is never presented as current.

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
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Protocol

from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_shared.models.health import ResourceUsage

DISK_GAUGE = "host_disk_used_ratio"
MEMORY_GAUGE = "host_memory_used_ratio"
SAMPLE_ERRORS = "host_sample_errors"

DEFAULT_SAMPLE_INTERVAL_SECONDS = 30.0
# spec 010: the spec default; config/agent.yaml overrides it for dev machines.
DEFAULT_DISK_PATHS = ("/var/log/magic",)
# spec 004 `mount` dimension cap (§4.7).
MAX_DISK_PATHS = 8


@dataclass(frozen=True, slots=True)
class HostConfig:
    """spec 010 `host:` block."""

    enabled: bool = True
    sample_interval_seconds: float = DEFAULT_SAMPLE_INTERVAL_SECONDS
    disk_paths: tuple[str, ...] = DEFAULT_DISK_PATHS
    memory: bool = True
    # FR-HLT-014 (UBS-130): exact executable name; empty disables the gauge.
    process_name: str = ""


class HostSampler(Protocol):
    """Reads OS counters. Each method raises when the read is impossible."""

    def disk_used_ratio(self, path: str) -> float: ...

    def memory_used_ratio(self) -> float: ...

    def own_usage(self) -> tuple[float, float]:
        """(rss_mb, cpu_percent) of the agent process itself."""
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
        if not config.sample_interval_seconds > 0:
            raise ValueError("sample_interval_seconds must be > 0")
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

    def sample_once(self) -> None:
        """One tick. Never raises: a failed read is counted and omitted."""
        gauges: dict[str, float] = {}

        ratios: list[float] = []
        for path in self._config.disk_paths:
            ratio = self._read(partial(self._sampler.disk_used_ratio, path))
            if ratio is not None:
                ratios.append(ratio)
        if ratios:
            gauges[DISK_GAUGE] = max(ratios)

        if self._config.memory:
            memory = self._read(self._sampler.memory_used_ratio)
            if memory is not None:
                gauges[MEMORY_GAUGE] = memory

        usage: ResourceUsage | None = None
        try:
            rss_mb, cpu_percent = self._sampler.own_usage()
            usage = ResourceUsage(rss_mb=rss_mb, cpu_percent=cpu_percent)
        except Exception:
            self._record_error("own resource usage")

        self._sample = HostSample(gauges=gauges, resource_usage=usage)

    def _read(self, read: Callable[[], float]) -> float | None:
        try:
            return _ratio(read())
        except Exception:
            self._record_error("host gauge")
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
                await asyncio.to_thread(self.sample_once)
            except Exception:  # sample_once handles reads; belt and braces
                self._counters.increment(SAMPLE_ERRORS)
                self._logger.exception("host sample tick failed")
            try:
                await asyncio.wait_for(stop.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                continue


class PsutilSampler:
    """Production `HostSampler`. Reads counters only, never process arguments."""

    def __init__(self) -> None:
        import psutil

        self._psutil = psutil
        self._process = psutil.Process()
        self._process.cpu_percent(interval=None)  # first call is always 0.0

    def disk_used_ratio(self, path: str) -> float:
        usage = self._psutil.disk_usage(path)
        if usage.total <= 0:
            raise ValueError(f"filesystem for {path!r} reports no capacity")
        return float(usage.used / usage.total)

    def memory_used_ratio(self) -> float:
        memory = self._psutil.virtual_memory()
        if memory.total <= 0:
            raise ValueError("no physical memory reported")
        return float((memory.total - memory.available) / memory.total)

    def own_usage(self) -> tuple[float, float]:
        rss_mb = self._process.memory_info().rss / (1024 * 1024)
        return float(rss_mb), float(self._process.cpu_percent(interval=None))
