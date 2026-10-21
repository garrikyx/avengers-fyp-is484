"""UBS-36: test mode over real simulator output, through the real CLI.

The simulator (`apps/simulator`) writes sponsor-format Application.log and
Fix.log lines for a few seconds. A `draft` signature rule, bound to an
action, is then replayed with

    telemetry-agent --config agent.yaml --test-rule ... --replay ... --json

in a separate process. The report has to agree with the log itself: the rule
fires on the matching line, the action shows up as
"would run" on the first firing, and nothing is dispatched. The config points
publish and callbacks at a closed local port, so an attempt to send anything
would also show up as an error.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SIMULATOR = REPO / "apps" / "simulator" / "src" / "simulator" / "mock_logger.py"
PYTHON = Path(sys.executable).as_posix()

_CONFIG = """
agent:
  id: magic-agent-backtest
  instanceIds: [magic-backtest-01]
logs:
  paths: [./logs/Application.log, ./logs/Fix.log]
  appLogPatterns: ['^\\d{{2}}:\\d{{2}}:\\d{{2}}\\.\\d+ <\\d+> \\[[NWEIF]+\\]']
parsing:
  errorSignatures:
    - label: connection_timeout
      match: "timed out after"
rules:
  path: rules.yaml
actions:
  allowedCommands: ['{python}']
publish:
  endpoint: http://127.0.0.1:9/telemetry/batch
  allowInsecureEndpoint: true
callbacks:
  endpoint: http://127.0.0.1:9/magic
  allowInsecureCallback: true
"""

_RULES = """
actions:
  - name: page-ops
    type: command
    command: '{python}'
    args: ['-c', 'raise SystemExit("must not run in test mode")']
    dryRun: false
rules:
  - name: VenueConnectTimeouts
    kind: signature
    source: counter
    metric: app_error_signatures
    signature: connection_timeout
    operator: ">="
    tiers: [{{severity: warning, threshold: 1}}]
    window: 1m
    for: 0s
    resolveAfter: 30s
    state: draft
    actions: [page-ops]
"""


def _simulate(workdir: Path, seconds: float) -> None:
    process = subprocess.Popen(
        [sys.executable, str(SIMULATOR), "--interval", "0.002"],
        cwd=workdir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(seconds)
    finally:
        process.kill()
        process.wait()


def _test_rule(workdir: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "telemetry_agent.main",
            "--config",
            "agent.yaml",
            "--test-rule",
            "VenueConnectTimeouts",
            "--replay",
            "logs/Application.log",
            "logs/Fix.log",
            "--json",
        ],
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_a_draft_rule_replayed_over_simulator_logs(tmp_path: Path) -> None:
    (tmp_path / "agent.yaml").write_text(
        _CONFIG.format(python=PYTHON), encoding="utf-8"
    )
    (tmp_path / "rules.yaml").write_text(_RULES.format(python=PYTHON), encoding="utf-8")
    _simulate(tmp_path, seconds=5)
    # The simulator picks its lines at random; make sure at least one is the
    # venue timeout (its own VENUE_EVENTS wording, local time like it writes).
    stamp = datetime.now().strftime("%H:%M:%S.%f")
    with (tmp_path / "logs" / "Application.log").open(
        "a", encoding="utf-8", newline="\n"
    ) as f:
        f.write(
            f"{stamp} <123456> [E] VS_101: VS <SGX|101@SGX|status Connecting|"
            "in/out seq 0/0 timed out after 00:00:30\n"
        )
    app_log = (tmp_path / "logs" / "Application.log").read_text(encoding="utf-8")
    fix_log = (tmp_path / "logs" / "Fix.log").read_text(encoding="utf-8")
    matches = app_log.count("timed out after")

    report = _test_rule(tmp_path)

    assert report["state"] == "draft"
    assert report["lines"] == len(app_log.splitlines()) + len(fix_log.splitlines())
    assert matches > 0
    assert report["fired"] is True
    assert report["dispatched"] == 0
    # Every simulator line carries a timestamp, so the replay spans the few
    # seconds it ran plus the rule's tail (window + resolveAfter), not a day.
    span = datetime.fromisoformat(str(report["replayTo"])) - datetime.fromisoformat(
        str(report["replayFrom"])
    )
    assert span < timedelta(minutes=5)
    firings = [t for t in report["transitions"] if t["status"] == "firing"]
    assert firings[0]["wouldRun"] == ["page-ops"]
    assert all(t["wouldRun"] == [] for t in firings[1:])
    assert firings[0]["payload"]["ruleName"] == "VenueConnectTimeouts"
    assert report["transitions"][-1]["status"] == "resolved"
