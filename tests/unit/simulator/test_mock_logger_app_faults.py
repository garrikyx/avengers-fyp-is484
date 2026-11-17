"""The simulator's `--app-faults` switch (UBS-134 demo).

`None` (the default) must keep the original mix, where [F] lines turn up at
random. A number makes [F] lines deliberate: only OutOfMemoryError, at that
rate, so a demo can keep AppOutOfMemory and AppLogFailure quiet and then fire
them on cue.
"""

from __future__ import annotations

import random

from simulator.mock_logger import OUT_OF_MEMORY, generate_application_log

_TS = "12:00:00.000000"


def _lines(n: int, fault_rate: float | None) -> list[str]:
    return [generate_application_log(_TS, fault_rate=fault_rate) for _ in range(n)]


def test_a_zero_fault_rate_writes_no_fatal_lines() -> None:
    random.seed(1)
    assert not [line for line in _lines(2000, 0.0) if "[F]" in line]


def test_a_full_fault_rate_writes_only_out_of_memory_lines() -> None:
    lines = _lines(50, 1.0)
    assert all("[F] MAIN: " + OUT_OF_MEMORY in line for line in lines)


def test_a_partial_fault_rate_mixes_faults_with_normal_lines() -> None:
    random.seed(3)
    lines = _lines(2000, 0.1)
    faults = [line for line in lines if "[F]" in line]
    assert 100 < len(faults) < 300
    assert all(OUT_OF_MEMORY in line for line in faults)


def test_the_default_keeps_random_fatal_lines() -> None:
    random.seed(5)
    assert any("[F]" in line for line in _lines(2000, None))
