"""Shared test support for `telemetry_agent.actions` (UBS-35).

Command actions run `sys.executable` with a small script as its fixed argv,
so the tests start a real child process the same way on Windows and Linux.
`sys.executable` is what goes in `allowedCommands`.
"""

from __future__ import annotations

import sys
import textwrap
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agent.actions.config import ActionDef, ActionType
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_shared.models.alerts import AlertEvent

PYTHON = Path(sys.executable)

# Writes its argv and stdin to the file named by its first argument, then
# exits with the code in its second (default 0).
RECORDER = textwrap.dedent(
    """
    import json, sys
    out, code = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0
    data = sys.stdin.buffer.read().decode("utf-8")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"argv": sys.argv[1:], "stdin": data}, f)
    sys.exit(code)
    """
)

SLEEPER = textwrap.dedent(
    """
    import sys, time
    time.sleep(float(sys.argv[1]))
    """
)


def write_script(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def command_action(
    name: str = "cleanup",
    *,
    args: tuple[str, ...] = (),
    timeout_seconds: float = 10.0,
    dry_run: bool = False,
    command: Path = PYTHON,
) -> ActionDef:
    return ActionDef(
        name=name,
        type=ActionType.COMMAND,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
        command=command,
        args=args,
    )


def callback_action(
    name: str = "ops-webhook",
    *,
    endpoint: str = "https://ops.example/hooks/telemetry",
    timeout_seconds: float = 10.0,
    dry_run: bool = False,
) -> ActionDef:
    return ActionDef(
        name=name,
        type=ActionType.CALLBACK,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
        callbacks=parse_callbacks_config(
            {"endpoint": endpoint, "dryRun": dry_run, "maxAttempts": 1}
        ),
    )


def make_alert(
    *,
    alert_id: str = "alert-1",
    rule_name: str = "HostDiskFull",
    status: str = "firing",
    notification_count: int = 1,
    severity: str = "critical",
) -> AlertEvent:
    now = datetime.now(UTC)
    return AlertEvent(
        alert_id=alert_id,
        rule_name=rule_name,
        severity=severity,
        status=status,
        application="Magic",
        instance_id="magic-prod-01",
        agent_id="magic-agent-sg-01",
        matched_condition="disk_used_ratio > 0.9 (observed 0.95); $(rm -rf /)",
        observed_value=0.95,
        threshold=0.9,
        first_observed_utc=now,
        last_observed_utc=now,
        notification_count=notification_count,
    )
