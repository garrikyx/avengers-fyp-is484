from datetime import datetime, timedelta, timezone
from pathlib import Path

from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker


def make_monitor(tmp_path: Path, name: str = "app.log") -> tuple[LogMonitor, Path]:
    log_path = tmp_path / name
    log_path.write_text("")
    tracker = OffsetTracker(registry_path=tmp_path / "offsets.json")
    return LogMonitor(log_path, offset_tracker=tracker), log_path


def test_status_before_any_read_has_no_lag(tmp_path: Path) -> None:
    monitor, log_path = make_monitor(tmp_path)
    log_path.write_text("line one\nline two\n")

    status = monitor.get_status()

    assert status.path == str(log_path)
    assert status.offset == 0
    assert status.size == len("line one\nline two\n")
    assert status.last_read_at is None
    assert status.read_lag_ms is None
    assert status.has_read_any_line is False


def test_status_after_read_reports_elapsed_lag(tmp_path: Path) -> None:
    monitor, log_path = make_monitor(tmp_path)
    log_path.write_text("line one\nline two\n")

    list(monitor.poll_lines())  # consume both lines, sets last_read_at

    status = monitor.get_status()
    assert status.last_read_at is not None
    assert status.read_lag_ms is not None
    assert status.read_lag_ms >= 0
    assert status.offset == len("line one\nline two\n")

    # Simulate three elapsed seconds by supplying an explicit "now".
    later = status.last_read_at + timedelta(seconds=3)
    lagged_status = monitor.get_status(now=later)
    assert lagged_status.read_lag_ms is not None
    assert 2990 <= lagged_status.read_lag_ms <= 3010


def test_status_reports_offset_progress_between_polls(tmp_path: Path) -> None:
    monitor, log_path = make_monitor(tmp_path)
    log_path.write_text("first\n")
    list(monitor.poll_lines())
    first_status = monitor.get_status()
    assert first_status.offset == len("first\n")

    with open(log_path, "a") as f:
        f.write("second\n")
    list(monitor.poll_lines())
    second_status = monitor.get_status()

    assert second_status.offset == len("first\nsecond\n")
    assert second_status.offset > first_status.offset
    assert second_status.last_read_at is not None
    assert first_status.last_read_at is not None
    assert second_status.last_read_at >= first_status.last_read_at


def test_status_missing_file_has_no_size_but_does_not_raise(tmp_path: Path) -> None:
    tracker = OffsetTracker(registry_path=tmp_path / "offsets.json")
    monitor = LogMonitor(tmp_path / "does_not_exist.log", offset_tracker=tracker)

    status = monitor.get_status()

    assert status.size is None
    assert status.offset == 0
    assert status.read_lag_ms is None
