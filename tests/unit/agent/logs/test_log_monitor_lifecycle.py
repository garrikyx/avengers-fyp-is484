import json
import os
import time
from pathlib import Path

from telemetry_agent.logs.log_monitor import LogMonitor, ReadLine
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker


def _line_texts(lines: list[ReadLine]) -> list[str]:
    return [line.text for line in lines]


def test_checkpoints_offsets_while_file_is_still_busy(tmp_path: Path) -> None:
    """A long-running stream must checkpoint before it reaches EOF."""
    log_path = tmp_path / "Fix.log"
    state_path = tmp_path / "offsets.json"
    log_path.write_text("first\nsecond\n")

    monitor = LogMonitor(
        log_path,
        OffsetTracker(state_path),
        checkpoint_interval=0.01,
    )
    stream = monitor.poll_lines()
    assert next(stream).text == "first"

    time.sleep(0.02)
    assert next(stream).text == "second"

    state = json.loads(state_path.read_text())
    assert state[0]["offset"] == len("first\nsecond\n")
    monitor.close()


def test_rotation_drains_late_writes_from_old_descriptor(tmp_path: Path) -> None:
    """A late write to the renamed file is read during the drain window."""
    active_path = tmp_path / "Application.log"
    active_path.write_text("old\n")
    monitor = LogMonitor(
        active_path,
        OffsetTracker(tmp_path / "offsets.json"),
        rotation_drain_timeout=0.1,
    )
    assert _line_texts(list(monitor.poll_lines())) == ["old"]

    rotated_path = tmp_path / "Application.log.1"
    active_path.rename(rotated_path)
    active_path.write_text("new\n")
    assert _line_texts(list(monitor.poll_lines())) == ["new"]

    with rotated_path.open("a") as handle:
        handle.write("late-old\n")
    assert _line_texts(list(monitor.poll_lines())) == ["late-old"]
    monitor.close()


def test_restart_recovers_retained_rotation_created_while_offline(
    tmp_path: Path,
) -> None:
    """A restart backfills retained archives before reading the new active log."""
    active_path = tmp_path / "Application.log"
    state_path = tmp_path / "offsets.json"
    active_path.write_text("before-stop\n")

    first_monitor = LogMonitor(active_path, OffsetTracker(state_path))
    assert _line_texts(list(first_monitor.poll_lines())) == ["before-stop"]
    first_monitor.close()

    rotated_path = tmp_path / "Application.log.1"
    active_path.rename(rotated_path)
    with rotated_path.open("a") as handle:
        handle.write("written-while-offline\n")
    active_path.write_text("new-active-file\n")

    restarted_monitor = LogMonitor(active_path, OffsetTracker(state_path))
    assert _line_texts(list(restarted_monitor.poll_lines())) == [
        "written-while-offline",
        "new-active-file",
    ]
    restarted_monitor.close()


def test_restart_backfills_multiple_rotations_created_while_offline(
    tmp_path: Path,
) -> None:
    """A restart recovers every retained archive, oldest archive first."""
    active_path = tmp_path / "Application.log"
    state_path = tmp_path / "offsets.json"
    active_path.write_text("read-before-stop\n")

    first_monitor = LogMonitor(active_path, OffsetTracker(state_path))
    assert _line_texts(list(first_monitor.poll_lines())) == ["read-before-stop"]
    first_monitor.close()

    newest_archive = tmp_path / "Application.log.1"
    oldest_archive = tmp_path / "Application.log.2"
    active_path.replace(newest_archive)
    with newest_archive.open("a") as handle:
        handle.write("first-offline-line\n")

    active_path.write_text("second-offline-line\n")
    newest_archive.replace(oldest_archive)
    active_path.replace(newest_archive)
    active_path.write_text("active-after-restart\n")

    # Make the intended chronological order explicit rather than depending on
    # filesystem timestamp resolution during this test.
    timestamp = time.time_ns()
    os.utime(oldest_archive, ns=(timestamp, timestamp))
    os.utime(newest_archive, ns=(timestamp + 1, timestamp + 1))
    os.utime(active_path, ns=(timestamp + 2, timestamp + 2))

    restarted_monitor = LogMonitor(active_path, OffsetTracker(state_path))
    assert _line_texts(list(restarted_monitor.poll_lines())) == [
        "first-offline-line",
        "second-offline-line",
        "active-after-restart",
    ]
    restarted_monitor.close()


def test_does_not_emit_an_unterminated_line_until_it_is_complete(tmp_path: Path) -> None:
    log_path = tmp_path / "Fix.log"
    log_path.write_text("partial")
    monitor = LogMonitor(log_path, OffsetTracker(tmp_path / "offsets.json"))

    assert _line_texts(list(monitor.poll_lines())) == []
    with log_path.open("a") as handle:
        handle.write(" line\n")
    assert _line_texts(list(monitor.poll_lines())) == ["partial line"]
    monitor.close()


def test_multi_monitor_validates_read_mode(tmp_path: Path) -> None:
    assert (
        MultiLogMonitor([], tmp_path / "tail.json", read_mode="tail").read_mode
        == "tail"
    )
    assert (
        MultiLogMonitor([], tmp_path / "interval.json", read_mode="interval").read_mode
        == "interval"
    )
