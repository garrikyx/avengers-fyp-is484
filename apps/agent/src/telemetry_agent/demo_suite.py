"""Deterministic local demo for Log Monitor lifecycle behaviour.

Run with ``uv run telemetry-log-demo`` from the repository root.
"""

import argparse
import json
import time
from pathlib import Path
from uuid import uuid4

from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor


def print_section(title: str) -> None:
    print(f"\n{'=' * 68}\n{title}\n{'=' * 68}")


def poll_available(monitor: MultiLogMonitor) -> list[tuple[str, str]]:
    """Read every available line without entering the infinite stream loop."""
    return [
        (name, line)
        for name, file_monitor in monitor.monitors.items()
        for line in file_monitor.poll_lines()
    ]


def print_lines(lines: list[tuple[str, str]]) -> None:
    for source, line in lines:
        print(f"  [{source}] {line}")


def run_demo(workdir: Path) -> None:
    run_dir = workdir / f"log-monitor-{uuid4().hex[:8]}"
    run_dir.mkdir(parents=True, exist_ok=False)
    registry = run_dir / "offsets.json"
    app_log = run_dir / "Application.log"
    fix_log = run_dir / "Fix.log"

    print(f"Demo files: {run_dir.resolve()}")
    monitor = MultiLogMonitor(
        [app_log, fix_log],
        registry_path=registry,
        read_mode="tail",
        checkpoint_interval=0.01,
        rotation_drain_timeout=0.5,
    )

    try:
        print_section("1. Multi-file tailing")
        app_log.write_text("APP startup\nAPP connected\n")
        fix_log.write_text("FIX order-1\n")

        initial_lines = poll_available(monitor)
        print_lines(initial_lines)
        assert initial_lines == [
            ("Application.log", "APP startup"),
            ("Application.log", "APP connected"),
            ("Fix.log", "FIX order-1"),
        ]
        print("PASS: both files were tailed in round-robin order.")

        print_section("2. Rename-and-create rotation with old-file draining")
        rotated_app_log = run_dir / "Application.log.1"
        app_log.rename(rotated_app_log)
        app_log.write_text("APP new-file line\n")
        with rotated_app_log.open("a") as handle:
            handle.write("APP late line from old file\n")

        rotation_lines = poll_available(monitor)
        print_lines(rotation_lines)
        assert rotation_lines == [
            ("Application.log", "APP late line from old file"),
            ("Application.log", "APP new-file line"),
        ]
        print("PASS: the old descriptor drained while the replacement was read.")

        print_section("3. Periodic offset checkpoint while the file is busy")
        with fix_log.open("a") as handle:
            handle.write("FIX checkpoint-1\nFIX checkpoint-2\n")

        fix_monitor = monitor.monitors["Fix.log"]
        active_stream = fix_monitor.poll_lines()
        assert next(active_stream) == "FIX checkpoint-1"
        time.sleep(0.02)
        assert next(active_stream) == "FIX checkpoint-2"

        saved_state = json.loads(registry.read_text())
        saved_fix_state = next(
            state
            for state in saved_state
            if state["source"] == str(fix_log.resolve())
        )
        assert saved_fix_state["offset"] == fix_monitor.get_status().offset
        print(f"  Saved FIX offset: {saved_fix_state['offset']}")
        print("PASS: progress was checkpointed before the stream reached EOF.")
    finally:
        monitor.close()

    print_section("4. Restart recovery without replaying old lines")
    with app_log.open("a") as handle:
        handle.write("APP written while monitor was offline\n")
    with fix_log.open("a") as handle:
        handle.write("FIX written while monitor was offline\n")

    restarted_monitor = MultiLogMonitor(
        [app_log, fix_log], registry_path=registry, read_mode="tail"
    )
    try:
        recovered_lines = poll_available(restarted_monitor)
        print_lines(recovered_lines)
        assert recovered_lines == [
            ("Application.log", "APP written while monitor was offline"),
            ("Fix.log", "FIX written while monitor was offline"),
        ]
        print("PASS: restart resumed from saved offsets without replaying history.")
    finally:
        restarted_monitor.close()

    print_section("5. Read-mode configuration")
    interval_monitor = MultiLogMonitor(
        [], registry_path=run_dir / "interval-offsets.json", read_mode="interval"
    )
    try:
        assert interval_monitor.read_mode == "interval"
        print("PASS: tail and interval modes are accepted by MultiLogMonitor.")
    finally:
        interval_monitor.close()

    print(f"\nAll Log Monitor checks passed. Artifacts retained at: {run_dir.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Log Monitor demo suite.")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path("demo_logs"),
        help="directory for a new isolated demo run (default: ./demo_logs)",
    )
    args = parser.parse_args()
    run_demo(args.workdir)


if __name__ == "__main__":
    main()
