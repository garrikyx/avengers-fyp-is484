"""UBS-129: Host Monitor sampling (FR-HLT-013, FR-HLT-015, FR-HLT-016, FR-MET-034).

The sampler is stubbed: these tests never touch psutil.
"""

from __future__ import annotations

import asyncio
import threading
import tracemalloc

import pytest
from telemetry_agent.health.host_monitor import (
    HostConfig,
    HostMonitor,
    default_disk_paths,
)


class StubSampler:
    """Answers from dicts; a value that is an Exception is raised instead."""

    def __init__(
        self,
        disks: dict[str, float | Exception] | None = None,
        memory: float | Exception = 0.5,
        usage: tuple[float, float] | Exception = (84.0, 1.8),
    ) -> None:
        self.disks = disks or {}
        self.memory = memory
        self.usage = usage

    def disk_used_ratio(self, path: str) -> float:
        value = self.disks[path]
        if isinstance(value, Exception):
            raise value
        return value

    def memory_used_ratio(self) -> float:
        if isinstance(self.memory, Exception):
            raise self.memory
        return self.memory

    def own_usage(self) -> tuple[float, float]:
        if isinstance(self.usage, Exception):
            raise self.usage
        return self.usage


def _monitor(sampler: StubSampler, *, memory: bool = True) -> HostMonitor:
    cfg = HostConfig(disk_paths=tuple(sampler.disks), memory=memory)
    return HostMonitor(cfg, sampler)


def test_fr_met_034_reports_disk_and_memory_ratios() -> None:
    monitor = _monitor(StubSampler(disks={"/data": 0.40}, memory=0.62))
    monitor.sample_once()
    assert monitor.gauges() == {
        "host_disk_used_ratio": 0.40,
        "host_disk_used_ratio:/data": 0.40,
        "host_memory_used_ratio": 0.62,
    }


def test_fr_met_034_disk_gauge_is_the_worst_mount() -> None:
    monitor = _monitor(StubSampler(disks={"/a": 0.2, "/b": 0.96, "/c": 0.5}))
    monitor.sample_once()
    assert monitor.gauges()["host_disk_used_ratio"] == 0.96


def test_fr_met_034_each_readable_mount_is_carried_under_its_own_key() -> None:
    monitor = _monitor(StubSampler(disks={"/a": 0.2, "C:\\": 0.96}))
    monitor.sample_once()
    gauges = monitor.gauges()
    assert gauges["host_disk_used_ratio:/a"] == 0.2
    assert gauges["host_disk_used_ratio:C:\\"] == 0.96  # the mount is verbatim
    assert gauges["host_disk_used_ratio"] == 0.96  # what HostDiskFull reads


def test_fr_met_034_nothing_is_reported_before_the_first_sample() -> None:
    assert _monitor(StubSampler(disks={"/data": 0.4})).gauges() == {}


def test_fr_met_034_memory_gauge_omitted_when_memory_disabled() -> None:
    monitor = _monitor(StubSampler(disks={"/data": 0.4}), memory=False)
    monitor.sample_once()
    assert "host_memory_used_ratio" not in monitor.gauges()


def test_fr_hlt_015_unreadable_disk_is_omitted_never_zero_and_counted() -> None:
    monitor = _monitor(StubSampler(disks={"/data": PermissionError("denied")}))
    monitor.sample_once()
    assert "host_disk_used_ratio" not in monitor.gauges()
    assert monitor.counters.snapshot()["host_sample_errors"] == 1


def test_fr_hlt_015_one_bad_mount_does_not_hide_the_readable_ones() -> None:
    monitor = _monitor(StubSampler(disks={"/a": OSError("gone"), "/b": 0.7}))
    monitor.sample_once()
    assert monitor.gauges()["host_disk_used_ratio"] == 0.7
    assert monitor.counters.snapshot()["host_sample_errors"] == 1


def test_fr_met_034_a_partly_unreadable_disk_is_visible_not_silently_healthy() -> None:
    """The unreadable mount has no per-mount gauge (never 0) and is counted on
    every tick, so the maximum is known to be over the readable mounts only."""
    monitor = _monitor(StubSampler(disks={"/a": PermissionError("x"), "/b": 0.3}))
    for _ in range(3):
        monitor.sample_once()
    gauges = monitor.gauges()
    assert "host_disk_used_ratio:/a" not in gauges
    assert gauges["host_disk_used_ratio:/b"] == 0.3
    assert gauges["host_disk_used_ratio"] == 0.3  # max over readable mounts
    assert monitor.counters.snapshot()["host_sample_errors"] == 3


def test_fr_hlt_015_unreadable_memory_is_omitted_and_other_gauges_survive() -> None:
    monitor = _monitor(
        StubSampler(disks={"/data": 0.4}, memory=NotImplementedError("platform"))
    )
    monitor.sample_once()
    assert monitor.gauges() == {
        "host_disk_used_ratio": 0.4,
        "host_disk_used_ratio:/data": 0.4,
    }
    assert monitor.counters.snapshot()["host_sample_errors"] == 1


def test_fr_hlt_015_a_failed_read_drops_the_stale_gauge_until_it_recovers() -> None:
    sampler = StubSampler(disks={"/data": 0.4})
    monitor = _monitor(sampler)
    monitor.sample_once()
    sampler.disks["/data"] = OSError("transient")
    monitor.sample_once()
    # A stale 0.4 must not be reported as current.
    assert "host_disk_used_ratio" not in monitor.gauges()
    sampler.disks["/data"] = 0.5
    monitor.sample_once()
    assert monitor.gauges()["host_disk_used_ratio"] == 0.5


def test_fr_met_034_ratios_are_clamped_to_unit_interval() -> None:
    monitor = _monitor(StubSampler(disks={"/data": 1.3}, memory=-0.1))
    monitor.sample_once()
    assert monitor.gauges() == {
        "host_disk_used_ratio": 1.0,
        "host_disk_used_ratio:/data": 1.0,
        "host_memory_used_ratio": 0.0,
    }


def test_fr_hlt_016_resource_usage_reports_own_rss_and_cpu() -> None:
    monitor = _monitor(StubSampler(usage=(84.0, 1.8)))
    assert monitor.resource_usage() is None  # unmeasured, not zero
    monitor.sample_once()
    usage = monitor.resource_usage()
    assert usage is not None
    assert (usage.rss_mb, usage.cpu_percent) == (84.0, 1.8)
    assert usage.active_tasks is None  # not measured outside run(): never 0


def test_fr_hlt_016_run_measures_the_event_loop_task_count() -> None:
    monitor = HostMonitor(
        HostConfig(disk_paths=("/data",), sample_interval_seconds=0.01),
        StubSampler(disks={"/data": 0.4}),
    )

    async def scenario() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(monitor.run(stop))
        await asyncio.sleep(0.05)
        stop.set()
        await asyncio.wait_for(task, 1)

    asyncio.run(scenario())
    usage = monitor.resource_usage()
    assert usage is not None
    assert usage.active_tasks is not None and usage.active_tasks >= 1


def test_fr_hlt_016_failed_usage_read_is_none_and_counted() -> None:
    monitor = _monitor(StubSampler(usage=OSError("no /proc")))
    monitor.sample_once()
    assert monitor.resource_usage() is None
    assert monitor.counters.snapshot()["host_sample_errors"] == 1


def test_fr_hlt_015_run_keeps_going_when_the_sampler_blows_up() -> None:
    class Exploding(StubSampler):
        def memory_used_ratio(self) -> float:
            raise RuntimeError("boom")

    monitor = HostMonitor(
        HostConfig(disk_paths=("/data",), sample_interval_seconds=0.01),
        Exploding(disks={"/data": 0.4}),
    )

    async def scenario() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(monitor.run(stop))
        await asyncio.sleep(0.15)
        stop.set()
        await asyncio.wait_for(task, 1)

    asyncio.run(scenario())
    assert monitor.counters.snapshot()["host_sample_errors"] >= 2
    assert monitor.gauges()["host_disk_used_ratio"] == 0.4


def test_nfr_perf_003_sampling_runs_off_the_event_loop_thread() -> None:
    """FR-HLT-015: blocking OS reads never run on the loop or parsing thread."""
    seen: list[int] = []

    class Recording(StubSampler):
        def memory_used_ratio(self) -> float:
            seen.append(threading.get_ident())
            return 0.5

    monitor = HostMonitor(
        HostConfig(disk_paths=("/data",), sample_interval_seconds=0.01),
        Recording(disks={"/data": 0.4}),
    )

    async def scenario() -> int:
        stop = asyncio.Event()
        task = asyncio.create_task(monitor.run(stop))
        await asyncio.sleep(0.05)
        stop.set()
        await asyncio.wait_for(task, 1)
        return threading.get_ident()

    loop_thread = asyncio.run(scenario())
    assert seen
    assert loop_thread not in seen


def test_nfr_perf_003_state_is_bounded_however_long_it_runs() -> None:
    monitor = _monitor(StubSampler(disks={"/a": 0.2, "/b": 0.3}))
    for _ in range(1000):
        monitor.sample_once()
    # one worst-mount gauge, two per-mount gauges, one memory gauge
    assert len(monitor.gauges()) == 4
    assert monitor.counters.snapshot() == {}  # nothing accumulates on success


def test_nfr_perf_003_memory_does_not_grow_with_the_number_of_samples() -> None:
    """Lightweight stand-in for the RSS budget (150 MB, spec 009): the Host
    Monitor keeps one immutable sample, so allocations after a warm-up must not
    scale with run length. `tracemalloc` counts Python allocations exactly, so
    unlike an RSS reading this is not flaky."""

    class FailingMount(StubSampler):
        def disk_used_ratio(self, path: str) -> float:
            if path == "/b":
                raise OSError("x")  # a new exception each time: no shared traceback
            return 0.2

    monitor = _monitor(FailingMount(disks={"/a": 0.2, "/b": 0.2}, memory=0.5))
    for _ in range(200):  # warm-up: caches, the counter key, interned strings
        monitor.sample_once()
    tracemalloc.start()
    try:
        before, _ = tracemalloc.get_traced_memory()
        for _ in range(20_000):
            monitor.sample_once(active_tasks=5)
        after, _ = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    # 20,000 retained samples would be tens of MB; one is a few KB.
    assert after - before < 64 * 1024


def test_fr_hlt_013_config_defaults_follow_spec_010() -> None:
    cfg = HostConfig()
    assert cfg.enabled is True
    assert cfg.sample_interval_seconds == 30.0
    assert cfg.disk_paths == default_disk_paths()
    assert cfg.memory is True
    assert cfg.process_name == ""


def test_fr_hlt_013_default_disk_path_is_spec_010s_except_on_windows() -> None:
    assert default_disk_paths("linux") == ("/var/log/magic",)
    assert default_disk_paths("darwin") == ("/var/log/magic",)
    (windows_path,) = default_disk_paths("win32")
    assert windows_path != "/var/log/magic"  # that path cannot exist on Windows


@pytest.mark.parametrize("interval", [0, -1, float("inf"), float("nan")])
def test_fr_hlt_013_bad_interval_is_rejected_by_the_config(interval: float) -> None:
    with pytest.raises(ValueError):
        HostConfig(sample_interval_seconds=interval)


def test_fr_met_034_mount_cap_and_blank_paths_are_rejected_by_the_config() -> None:
    with pytest.raises(ValueError):
        HostConfig(disk_paths=tuple(f"/m{i}" for i in range(9)))
    with pytest.raises(ValueError):
        HostConfig(disk_paths=("/ok", "  "))
