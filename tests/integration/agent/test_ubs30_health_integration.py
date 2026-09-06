"""Integration tests for UBS-30 (FR-LOG-010, FR-HLT-001).

Unlike tests/unit/agent/health/test_reporter.py and
tests/unit/agent/logs/test_log_monitor_status.py, which each exercise one
class in isolation with hand-built fixtures, these tests wire the real
pieces together against real files on disk: LogMonitor + Harvester +
OffsetTracker + MultiLogMonitor + HealthReporter, and (for the heartbeat
test) the telemetry_shared pydantic models that carry this data over the
wire. The goal is to catch the failure modes that only show up when the
components are actually plumbed together: rotation, truncation, a
simulated agent restart, and the read-lag -> degraded -> heartbeat path
end to end.

There is no real end-to-end test yet (spinning up the actual agent
process) because apps/agent/src/telemetry_agent/main.py is still an
empty stub - see docs/plan/ubs30-notes.md. This suite is the closest
practical equivalent until that entrypoint exists.
"""

from datetime import timedelta
from pathlib import Path

from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_shared.models.health import AgentHeartbeat


def test_multi_file_health_reflects_real_tailing(tmp_path: Path) -> None:
    """HealthReporter wired to a real MultiLogMonitor, not a hand-built dict."""
    fix_path = tmp_path / "Fix.log"
    app_path = tmp_path / "Application.log"
    fix_path.write_text("35=D|11=ORD-1|\n")
    app_path.write_text("")

    multi = MultiLogMonitor(
        [fix_path, app_path], registry_path=tmp_path / "offsets.json"
    )
    try:
        for monitor in multi.monitors.values():
            list(monitor.poll_lines())

        reporter = HealthReporter(multi.monitors)
        statuses = reporter.file_statuses()

        assert statuses["Fix.log"].offset == len("35=D|11=ORD-1|\n")
        assert statuses["Fix.log"].last_read_at is not None
        assert statuses["Application.log"].last_read_at is None
        assert reporter.is_degraded(statuses) is False
    finally:
        multi.close()


def test_health_reporter_survives_log_rotation(tmp_path: Path) -> None:
    """Simulates logrotate: old file renamed away, new file created at the same path."""
    log_path = tmp_path / "app.log"
    log_path.write_text("old-1\nold-2\n")
    tracker = OffsetTracker(registry_path=tmp_path / "offsets.json")
    monitor = LogMonitor(log_path, offset_tracker=tracker)
    reporter = HealthReporter({"app.log": monitor})

    list(monitor.poll_lines())
    pre_rotate = reporter.file_statuses()["app.log"]
    assert pre_rotate.offset == len("old-1\nold-2\n")
    assert pre_rotate.last_read_at is not None

    log_path.rename(tmp_path / "app.log.1")
    log_path.write_text("new-1\n")

    lines = list(monitor.poll_lines())
    assert lines == ["new-1"]

    post_rotate = reporter.file_statuses()["app.log"]
    assert post_rotate.offset == len("new-1\n")
    assert post_rotate.last_read_at is not None
    assert post_rotate.last_read_at >= pre_rotate.last_read_at
    monitor.close()


def test_health_reporter_handles_truncation(tmp_path: Path) -> None:
    """Same inode, smaller size in place - e.g. a logger truncates instead
    of rotating."""
    log_path = tmp_path / "app.log"
    log_path.write_text("aaaa\nbbbb\n")
    tracker = OffsetTracker(registry_path=tmp_path / "offsets.json")
    monitor = LogMonitor(log_path, offset_tracker=tracker)
    reporter = HealthReporter({"app.log": monitor})

    list(monitor.poll_lines())
    assert reporter.file_statuses()["app.log"].offset == len("aaaa\nbbbb\n")

    with open(log_path, "w") as f:
        f.write("c\n")

    list(monitor.poll_lines())
    status = reporter.file_statuses()["app.log"]
    assert status.offset == len("c\n")
    assert status.size == len("c\n")
    monitor.close()


def test_offset_persists_across_simulated_restart(tmp_path: Path) -> None:
    """Offset survives a clean shutdown + fresh process, but read-lag
    knowledge does not.

    This is a real operational nuance worth locking down explicitly: right
    after a restart, get_status() must report the persisted offset (so
    progress isn't lost), but last_read_at/read_lag_ms must come back as
    None rather than 0 - there has been no read yet in this process, and
    reporting a lag of 0 would misleadingly look "perfectly healthy"
    instead of "unknown until the next line is read".
    """
    log_path = tmp_path / "app.log"
    registry_path = tmp_path / "offsets.json"
    log_path.write_text("line-1\nline-2\n")

    tracker1 = OffsetTracker(registry_path=registry_path)
    monitor1 = LogMonitor(log_path, offset_tracker=tracker1)
    list(monitor1.poll_lines())
    monitor1.close()  # persists offset, simulates a clean shutdown

    tracker2 = OffsetTracker(registry_path=registry_path)
    monitor2 = LogMonitor(log_path, offset_tracker=tracker2)
    reporter = HealthReporter({"app.log": monitor2})

    pre_poll_status = reporter.file_statuses()["app.log"]
    assert pre_poll_status.offset == len("line-1\nline-2\n")
    assert pre_poll_status.last_read_at is None
    assert pre_poll_status.read_lag_ms is None

    with open(log_path, "a") as f:
        f.write("line-3\n")
    list(monitor2.poll_lines())

    post_poll_status = reporter.file_statuses()["app.log"]
    assert post_poll_status.offset == len("line-1\nline-2\nline-3\n")
    assert post_poll_status.last_read_at is not None
    monitor2.close()


def test_degraded_status_flows_into_heartbeat_payload(tmp_path: Path) -> None:
    """FR-HLT-001: degraded read lag has to survive the actual heartbeat wire format."""
    log_path = tmp_path / "Fix.log"
    log_path.write_text("35=D|11=ORD-1|\n")
    tracker = OffsetTracker(registry_path=tmp_path / "offsets.json")
    monitor = LogMonitor(log_path, offset_tracker=tracker)
    reporter = HealthReporter({"Fix.log": monitor}, degraded_threshold_ms=5_000.0)

    list(monitor.poll_lines())
    last_read_at = reporter.file_statuses()["Fix.log"].last_read_at
    assert last_read_at is not None

    stale_now = last_read_at + timedelta(seconds=6)
    statuses = reporter.file_statuses(now=stale_now)
    assert reporter.is_degraded(statuses) is True

    heartbeat = AgentHeartbeat(
        agent_id="agent-1",
        instance_id="instance-1",
        timestamp=stale_now,
        cpu_percent=12.5,
        memory_mb=256.0,
        queue_depth=0,
        files=list(statuses.values()),
        read_lag_ms=reporter.overall_read_lag_ms(statuses.values()),
    )

    # Round-trip through JSON: the actual wire format the heartbeat is published as.
    rehydrated = AgentHeartbeat.model_validate_json(heartbeat.model_dump_json())
    assert rehydrated.read_lag_ms is not None
    assert rehydrated.read_lag_ms > 5_000.0
    assert rehydrated.files[0].path == str(log_path)
    monitor.close()


def test_multi_file_group_tolerates_one_file_disappearing(tmp_path: Path) -> None:
    """One file being deleted out from under the agent must not crash
    the health report."""
    fix_path = tmp_path / "Fix.log"
    app_path = tmp_path / "Application.log"
    fix_path.write_text("line\n")
    app_path.write_text("line\n")

    multi = MultiLogMonitor(
        [fix_path, app_path], registry_path=tmp_path / "offsets.json"
    )
    try:
        for m in multi.monitors.values():
            list(m.poll_lines())

        app_path.unlink()

        reporter = HealthReporter(multi.monitors)
        statuses = reporter.file_statuses()  # must not raise

        assert statuses["Application.log"].size is None
        assert statuses["Fix.log"].size is not None
    finally:
        multi.close()
