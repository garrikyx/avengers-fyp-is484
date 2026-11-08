"""UBS-130: Magic process liveness gauge (FR-HLT-014, FR-MET-034, spec 005 §1.2).

The sampler is stubbed with a process-name list; these tests never touch psutil.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest
from telemetry_agent.health.host_monitor import HostConfig, HostMonitor, PsutilSampler


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

    def process_running(self, name: str) -> bool:
        self.process_reads += 1
        if isinstance(self.names, Exception):
            raise self.names
        return name in set(self.names)


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


def _fake_proc(root: Path, comms: dict[int, str | None]) -> Path:
    """A fake /proc: `comm` (kernel name) and `cmdline` (sentinel) per pid. A
    pid mapped to None has no readable `comm`, like a process that just exited."""
    for pid, comm in comms.items():
        pdir = root / str(pid)
        pdir.mkdir(parents=True)
        (pdir / "cmdline").write_bytes(b"/opt/secret --password=hunter2\x00")
        if comm is not None:
            (pdir / "comm").write_text(comm + "\n")
    (root / "self").mkdir()  # non-numeric entries are not processes
    return root


def _linux(root: Path) -> PsutilSampler:
    return PsutilSampler(platform="linux", proc_root=root)


def test_fr_hlt_014_linux_reads_comm_and_never_the_command_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fake_proc(tmp_path, {1: "init", 42: "magic.exe"})
    opened: list[str] = []
    real_read_text = Path.read_text

    def spy(self: Path, *args: Any, **kwargs: Any) -> str:
        opened.append(self.name)
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", spy)
    sampler = _linux(root)
    assert sampler.process_running("magic.exe") is True
    assert sampler.process_running("sshd") is False
    assert opened and set(opened) == {"comm"}


def test_fr_hlt_014_linux_names_over_15_chars_match_the_kernel_truncation(
    tmp_path: Path,
) -> None:
    # The kernel keeps 15 characters of the executable name in `comm`.
    root = _fake_proc(tmp_path, {7: "magic-trading-e"})
    sampler = _linux(root)
    assert sampler.process_running("magic-trading-engine") is True
    assert sampler.process_running("magic-trading-other") is False
    assert sampler.process_running("magic") is False


def test_fr_hlt_014_a_process_that_exits_mid_scan_is_skipped(tmp_path: Path) -> None:
    root = _fake_proc(tmp_path, {1: "init", 2: None, 3: "magic.exe"})
    assert _linux(root).process_running("magic.exe") is True


def test_fr_hlt_014_an_empty_process_list_is_unreadable_not_down(
    tmp_path: Path,
) -> None:
    with pytest.raises(OSError):
        _linux(_fake_proc(tmp_path, {})).process_running("magic.exe")


def test_fr_hlt_014_all_names_unreadable_is_unreadable_not_down(
    tmp_path: Path,
) -> None:
    root = _fake_proc(tmp_path, {1: None, 2: None})
    with pytest.raises(OSError):
        _linux(root).process_running("magic.exe")


def test_fr_hlt_014_missing_proc_root_is_unreadable_not_down(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        _linux(tmp_path / "nope").process_running("magic.exe")


def test_fr_hlt_014_real_sampler_never_reads_a_command_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import psutil

    def forbidden(self: object) -> list[str]:
        raise AssertionError("the command line must never be read")

    monkeypatch.setattr(psutil.Process, "cmdline", forbidden)
    sampler = PsutilSampler()
    if sys.platform.startswith("linux"):
        own = Path("/proc/self/comm").read_text().strip()
    elif sys.platform == "win32":
        own = psutil.Process().name()
    else:
        # psutil's own name()/exe() fall back to cmdline() on POSIX, so macOS
        # and BSD are unsupported: unreadable (omitted), never read or "down".
        with pytest.raises(OSError):
            sampler.process_running("anything")
        return
    assert sampler.process_running(own) is True
    assert sampler.process_running("no-such-executable-xyz") is False


def test_fr_hlt_014_unsupported_platform_is_unreadable_not_down() -> None:
    with pytest.raises(OSError):
        PsutilSampler(platform="darwin").process_running("magic")
