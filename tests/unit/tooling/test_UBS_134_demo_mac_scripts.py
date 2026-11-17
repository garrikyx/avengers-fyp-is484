"""UBS-134 macOS demo scripts: present, executable in git, valid bash, and
offering the same commands as the Windows launcher."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MAC = ROOT / "scripts" / "demo_mac"
BAT = ROOT / "scripts" / "demo_windows.bat"
COMPONENTS = (
    "backend",
    "magic_stub",
    "simulator",
    "agent",
    "teams_bot",
    "mcp",
    "playground",
)
RUNNABLE = (*COMPONENTS, "demo")


def _bash() -> str | None:
    found = shutil.which("bash")
    # Windows' System32 bash.exe is the WSL launcher, not a usable bash.
    if found is None or "system32" in found.lower():
        return None
    return found


@pytest.mark.parametrize("name", RUNNABLE)
def test_each_script_exists_with_a_bash_shebang(name: str) -> None:
    script = MAC / f"{name}.sh"
    assert script.is_file(), script
    assert script.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash\n")


@pytest.mark.parametrize("name", RUNNABLE)
def test_each_script_is_executable_in_git(name: str) -> None:
    if shutil.which("git") is None:
        pytest.skip("git not available")
    out = subprocess.run(
        ["git", "ls-files", "-s", f"scripts/demo_mac/{name}.sh"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    if not out:
        pytest.skip("script not committed yet")
    assert out.startswith("100755"), out


@pytest.mark.parametrize("name", (*RUNNABLE, "_env"))
def test_each_script_is_valid_bash(name: str) -> None:
    bash = _bash()
    if bash is None:
        pytest.skip("bash not available")
    result = subprocess.run(
        [bash, "-n", str(MAC / f"{name}.sh")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_demo_sh_offers_every_windows_launcher_command() -> None:
    bat = BAT.read_text(encoding="utf-8")
    bat_cmds = set(re.findall(r'if /i "%CMD%"=="([a-z-]+)"', bat))
    demo = (MAC / "demo.sh").read_text(encoding="utf-8")
    mac_cmds = set(re.findall(r"^  ([a-z-]+)\)", demo, flags=re.MULTILINE))
    assert bat_cmds, "no commands found in demo_windows.bat"
    assert bat_cmds <= mac_cmds, bat_cmds - mac_cmds
    assert {"run", "ask"} <= mac_cmds


def test_component_scripts_use_the_demo_configs() -> None:
    text = {n: (MAC / f"{n}.sh").read_text(encoding="utf-8") for n in COMPONENTS}
    assert "config/demo/backend.yaml" in text["backend"]
    assert "config/demo/agent.yaml" in text["agent"]
    assert "--app-faults" in text["simulator"]
    assert "ANONYMOUS_ALLOWED=true" in text["teams_bot"]
    assert "-e http://localhost:3978/api/messages" in text["playground"]
