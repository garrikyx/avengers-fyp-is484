from datetime import timedelta
from pathlib import Path

from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker


def make_monitor(tmp_path: Path, name: str, content: str) -> LogMonitor:
    log_path = tmp_path / name
    log_path.write_text(content)
    tracker = OffsetTracker(registry_path=tmp_path / f"{name}.offsets.json")
    return LogMonitor(log_path, offset_tracker=tracker)


def test_file_statuses_keys_match_monitor_names(tmp_path: Path) -> None:
    fix = make_monitor(tmp_path, "Fix.log", "35=D|11=ORD-1|\n")
    app = make_monitor(tmp_path, "Application.log", "")
    list(fix.poll_lines())

    reporter = HealthReporter({"Fix.log": fix, "Application.log": app})
    statuses = reporter.file_statuses()

    assert set(statuses.keys()) == {"Fix.log", "Application.log"}
    assert statuses["Fix.log"].offset == len("35=D|11=ORD-1|\n")
    assert statuses["Fix.log"].last_read_at is not None
    assert statuses["Application.log"].last_read_at is None


def test_overall_read_lag_ignores_files_with_no_reads_yet(tmp_path: Path) -> None:
    fix = make_monitor(tmp_path, "Fix.log", "line\n")
    app = make_monitor(tmp_path, "Application.log", "")  # never written to, never read
    list(fix.poll_lines())

    reporter = HealthReporter({"Fix.log": fix, "Application.log": app})
    statuses = reporter.file_statuses()
    fix_read_at = statuses["Fix.log"].last_read_at
    assert fix_read_at is not None

    later = fix_read_at + timedelta(seconds=2)
    later_statuses = reporter.file_statuses(now=later)

    overall = reporter.overall_read_lag_ms(later_statuses.values())
    assert overall is not None
    assert 1990 <= overall <= 2010


def test_overall_read_lag_is_none_when_nothing_has_been_read(tmp_path: Path) -> None:
    app = make_monitor(tmp_path, "Application.log", "")
    reporter = HealthReporter({"Application.log": app})

    assert reporter.overall_read_lag_ms() is None
    assert reporter.degraded_reasons() == []
    assert reporter.is_degraded() is False


def test_degraded_reasons_flag_files_over_threshold(tmp_path: Path) -> None:
    fix = make_monitor(tmp_path, "Fix.log", "line\n")
    list(fix.poll_lines())

    reporter = HealthReporter({"Fix.log": fix}, degraded_threshold_ms=5_000.0)
    healthy_statuses = reporter.file_statuses()
    assert reporter.degraded_reasons(healthy_statuses) == []
    assert reporter.is_degraded(healthy_statuses) is False

    stale_now = healthy_statuses["Fix.log"].last_read_at + timedelta(seconds=6)
    stale_statuses = reporter.file_statuses(now=stale_now)

    reasons = reporter.degraded_reasons(stale_statuses)
    assert len(reasons) == 1
    assert "Fix.log" in reasons[0]
    assert reporter.is_degraded(stale_statuses) is True


def test_degraded_threshold_is_configurable(tmp_path: Path) -> None:
    fix = make_monitor(tmp_path, "Fix.log", "line\n")
    list(fix.poll_lines())

    strict_reporter = HealthReporter({"Fix.log": fix}, degraded_threshold_ms=1.0)
    baseline = strict_reporter.file_statuses()["Fix.log"].last_read_at
    stale_now = baseline + timedelta(milliseconds=50)
    statuses = strict_reporter.file_statuses(now=stale_now)

    assert strict_reporter.is_degraded(statuses) is True
