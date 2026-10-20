"""FR-CBK-015/016/017: a `command` action runs a fixed argv with no shell, the
alert JSON on stdin, and a timeout (UBS-35)."""

import asyncio
import json
import time
from pathlib import Path

from action_fixtures import (
    RECORDER,
    SLEEPER,
    command_action,
    make_alert,
    write_script,
)
from telemetry_agent.actions.runner import ActionRunner


def _runner(*actions: object) -> ActionRunner:
    catalogue = {a.name: a for a in actions}  # type: ignore[attr-defined]
    return ActionRunner(catalogue, lambda _rule: tuple(catalogue), secret=b"s")


def test_alert_json_goes_on_stdin_and_argv_is_exactly_the_config(
    tmp_path: Path,
) -> None:
    script = write_script(tmp_path, "record.py", RECORDER)
    out = tmp_path / "out.json"
    # Shell metacharacters in the configured args must arrive literally.
    action = command_action(args=(str(script), str(out), "0", "; echo pwned", "$(id)"))
    runner = _runner(action)

    outcome = asyncio.run(runner.execute(make_alert(), "cleanup"))

    assert outcome == "ok"
    recorded = json.loads(out.read_text(encoding="utf-8"))
    assert recorded["argv"] == [str(out), "0", "; echo pwned", "$(id)"]
    body = json.loads(recorded["stdin"])
    assert body["alertId"] == "alert-1"
    assert body["ruleName"] == "HostDiskFull"
    assert body["schemaVersion"] == 1
    # Alert text (which comes from log data) stays data: only on stdin.
    assert "$(rm -rf /)" in body["matchedCondition"]
    assert all("rm -rf" not in arg for arg in recorded["argv"])
    assert runner.counters.snapshot()["action_runs:cleanup:ok"] == 1


def test_a_non_zero_exit_is_counted_as_failed(tmp_path: Path) -> None:
    script = write_script(tmp_path, "record.py", RECORDER)
    action = command_action(args=(str(script), str(tmp_path / "o.json"), "3"))
    runner = _runner(action)

    assert asyncio.run(runner.execute(make_alert(), "cleanup")) == "failed"
    assert runner.counters.snapshot()["action_runs:cleanup:failed"] == 1


def test_a_command_that_overruns_its_timeout_is_killed(tmp_path: Path) -> None:
    script = write_script(tmp_path, "sleep.py", SLEEPER)
    action = command_action(args=(str(script), "30"), timeout_seconds=0.5)
    runner = _runner(action)

    started = time.monotonic()
    outcome = asyncio.run(runner.execute(make_alert(), "cleanup"))

    assert outcome == "timeout"
    assert time.monotonic() - started < 10
    counters = runner.counters.snapshot()
    assert counters["action_runs:cleanup:timeout"] == 1
    assert counters["action_run_ms:cleanup"] >= 400


def test_a_missing_executable_is_an_error_not_a_crash(tmp_path: Path) -> None:
    action = command_action(command=tmp_path / "no-such-binary")
    runner = _runner(action)

    assert asyncio.run(runner.execute(make_alert(), "cleanup")) == "error"
    assert runner.counters.snapshot()["action_runs:cleanup:error"] == 1


def test_dry_run_logs_and_never_starts_the_process(tmp_path: Path) -> None:
    script = write_script(tmp_path, "record.py", RECORDER)
    out = tmp_path / "out.json"
    action = command_action(args=(str(script), str(out)), dry_run=True)
    runner = _runner(action)

    assert asyncio.run(runner.execute(make_alert(), "cleanup")) == "dry_run"
    assert not out.exists()
    assert runner.counters.snapshot()["action_runs:cleanup:dry_run"] == 1


def test_an_action_removed_by_reload_is_skipped(tmp_path: Path) -> None:
    runner = _runner(command_action())
    runner.replace_catalogue({})
    assert asyncio.run(runner.execute(make_alert(), "cleanup")) == "unknown"
