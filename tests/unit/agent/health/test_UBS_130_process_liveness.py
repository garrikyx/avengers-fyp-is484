"""UBS-130: Magic process liveness gauge (FR-HLT-014, FR-MET-034, spec 005 §1.2).

The sampler is stubbed with a process-name list; these tests never touch psutil.
"""

from __future__ import annotations

from collections.abc import Iterable

import pytest
from telemetry_agent.health.host_monitor import HostConfig, HostMonitor


class StubSampler:
    def __init__(self, names: Iterable[str] | Exception = ()) -> None:
        self.names = names
        self.process_reads = 0

    def disk_used_ratio(self, path: str) -> float:
        return 0.4

    def memory_used_ratio(self) -> float:
        return 0.5

    def own_usage(self) -> tuple[float, float]:
        return 84.0, 1.8

    def process_names(self) -> Iterable[str]:
        self.process_reads += 1
        if isinstance(self.names, Exception):
            raise self.names
        return self.names


def _monitor(sampler: StubSampler, process_name: str = "magic.exe") -> HostMonitor:
    cfg = HostConfig(disk_paths=("/data",), process_name=process_name)
    return HostMonitor(cfg, sampler)


def test_fr_hlt_014_running_process_reports_one() -> None:
    monitor = _monitor(StubSampler(["init", "magic.exe", "sshd"]))
    monitor.sample_once()
    assert monitor.gauges()["magic_process_up"] == 1.0


def test_fr_hlt_014_missing_process_reports_zero() -> None:
    monitor = _monitor(StubSampler(["init", "sshd"]))
    monitor.sample_once()
    assert monitor.gauges()["magic_process_up"] == 0.0


@pytest.mark.parametrize(
    "other", ["magic.exe.bak", "notmagic.exe", "magic", "MAGIC.EXE"]
)
def test_fr_hlt_014_match_is_the_exact_executable_name(other: str) -> None:
    monitor = _monitor(StubSampler([other]))
    monitor.sample_once()
    assert monitor.gauges()["magic_process_up"] == 0.0


def test_fr_hlt_014_process_return_flips_the_gauge_back() -> None:
    sampler = StubSampler(["sshd"])
    monitor = _monitor(sampler)
    monitor.sample_once()
    sampler.names = ["sshd", "magic.exe"]
    monitor.sample_once()
    assert monitor.gauges()["magic_process_up"] == 1.0


def test_fr_hlt_014_empty_process_name_reports_nothing_and_reads_nothing() -> None:
    sampler = StubSampler(["magic.exe"])
    monitor = _monitor(sampler, process_name="")
    monitor.sample_once()
    assert "magic_process_up" not in monitor.gauges()
    assert sampler.process_reads == 0
    assert "host_sample_errors" not in monitor.counters.snapshot()


def test_fr_met_034_unreadable_process_list_is_omitted_never_zero_and_counted() -> None:
    monitor = _monitor(StubSampler(PermissionError("denied")))
    monitor.sample_once()
    gauges = monitor.gauges()
    assert "magic_process_up" not in gauges
    assert gauges["host_disk_used_ratio"] == 0.4  # other gauges survive
    assert monitor.counters.snapshot()["host_sample_errors"] == 1


def test_fr_met_034_a_failed_read_does_not_keep_the_previous_up_value() -> None:
    sampler = StubSampler(["magic.exe"])
    monitor = _monitor(sampler)
    monitor.sample_once()
    sampler.names = OSError("gone")
    monitor.sample_once()
    assert "magic_process_up" not in monitor.gauges()


def test_fr_hlt_014_psutil_sampler_lists_this_process_by_name() -> None:
    import os

    import psutil
    from telemetry_agent.health.host_monitor import PsutilSampler

    names = set(PsutilSampler().process_names())
    assert psutil.Process(os.getpid()).name() in names


def test_fr_hlt_014_psutil_sampler_requests_only_the_name_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import psutil
    from telemetry_agent.health.host_monitor import PsutilSampler

    requested: list[object] = []

    class _Proc:
        def __init__(self, name: str | None) -> None:
            self.info = {"name": name}

    def fake_process_iter(attrs: list[str] | None = None) -> list[_Proc]:
        requested.append(attrs)
        return [_Proc("magic.exe"), _Proc(None)]  # None: access denied mid-scan

    monkeypatch.setattr(psutil, "process_iter", fake_process_iter)
    assert list(PsutilSampler().process_names()) == ["magic.exe"]
    assert requested == [["name"]]  # never cmdline / exe (FR-HLT-014)
