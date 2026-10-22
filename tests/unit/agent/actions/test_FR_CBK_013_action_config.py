"""FR-CBK-013/014/015: the `actions:` block, `rules[].actions` and
`allowedCommands` are validated at load time (UBS-35, spec 005 §5)."""

from pathlib import Path

import pytest
from action_fixtures import PYTHON
from telemetry_agent.actions.config import (
    ActionConfigError,
    ActionType,
    load_action_catalogue,
    parse_actions,
    parse_allowed_commands,
)
from telemetry_agent.config import AgentConfigError, load_agent_config
from telemetry_agent.rules.config_loader import RuleConfigError, load_rules_from_yaml
from telemetry_agent.rules.types import RuleState

_RULE = """
  - name: HostDiskFull
    kind: threshold
    source: counter
    metric: disk_full_events
    operator: ">"
    tiers: [{severity: critical, threshold: 0}]
    window: 1m
"""


def _rules_file(tmp_path: Path, actions: str, rule_extra: str = "") -> Path:
    path = tmp_path / "rules.yaml"
    path.write_text(
        f"actions:\n{actions}\nrules:\n{_RULE}{rule_extra}", encoding="utf-8"
    )
    return path


_COMMAND = f"""
  - name: disk-cleanup
    type: command
    command: {PYTHON.as_posix()}
    args: ["--older-than", "7d"]
    timeout: 30s
"""

_CALLBACK = """
  - name: ops-webhook
    type: callback
    endpoint: https://ops.internal.example/hooks/telemetry
"""


def test_command_and_callback_actions_parse_with_safe_defaults(
    tmp_path: Path,
) -> None:
    path = _rules_file(tmp_path, _COMMAND + _CALLBACK)
    catalogue = load_action_catalogue(path, allowed_commands=[PYTHON])

    command = catalogue["disk-cleanup"]
    assert command.type is ActionType.COMMAND
    assert command.command == PYTHON
    assert command.args == ("--older-than", "7d")
    assert command.timeout_seconds == 30
    assert command.dry_run is True  # FR-CBK-017 default

    callback = catalogue["ops-webhook"]
    assert callback.type is ActionType.CALLBACK
    assert callback.dry_run is True
    assert callback.timeout_seconds == 60
    assert callback.callbacks is not None
    assert callback.callbacks.endpoint.endswith("/hooks/telemetry")


def test_a_rule_names_its_actions(tmp_path: Path) -> None:
    path = _rules_file(tmp_path, _COMMAND, "    actions: [disk-cleanup]\n")
    (rule,) = load_rules_from_yaml(path)
    assert rule.actions == ("disk-cleanup",)


def test_an_unknown_action_name_fails_the_load(tmp_path: Path) -> None:
    path = _rules_file(tmp_path, _COMMAND, "    actions: [disk-cleanup, reboot]\n")
    with pytest.raises(RuleConfigError, match=r"'HostDiskFull'.*\['reboot'\]"):
        load_rules_from_yaml(path)


def test_a_command_must_be_on_the_operators_allowlist(tmp_path: Path) -> None:
    path = _rules_file(tmp_path, _COMMAND)
    with pytest.raises(ActionConfigError, match="not in .*allowedCommands"):
        load_action_catalogue(path, allowed_commands=[])


def test_a_command_must_be_an_absolute_path() -> None:
    entry = {"name": "x", "type": "command", "command": "cleanup-disk"}
    with pytest.raises(ActionConfigError, match="absolute path"):
        parse_actions([entry], allowed_commands=[PYTHON])
    with pytest.raises(ActionConfigError, match="absolute path"):
        parse_allowed_commands(["cleanup-disk"])


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ({"name": "x", "type": "command"}, "needs `command`"),
        ({"name": "x", "type": "callback"}, "needs `endpoint`"),
        (
            {"name": "x", "type": "callback", "endpoint": "https://a", "args": ["y"]},
            "command action only",
        ),
        ({"name": "x", "type": "shell", "command": "/bin/sh"}, "type"),
        ({"name": "x", "type": "callback", "endpoint": "https://a", "x": 1}, "extra"),
        (
            {"name": "x", "type": "callback", "endpoint": "http://plain.example"},
            "must be https",
        ),
        (
            {"name": "x", "type": "callback", "endpoint": "https://a", "timeout": "0s"},
            "timeout must be > 0",
        ),
        (
            {"name": "x", "type": "callback", "endpoint": "https://a", "timeout": "1d"},
            "invalid duration",
        ),
    ],
)
def test_malformed_actions_are_rejected_with_a_descriptive_error(
    entry: dict[str, object], message: str
) -> None:
    with pytest.raises(ActionConfigError, match=message):
        parse_actions([entry], allowed_commands=[PYTHON])


def test_duplicate_action_names_are_rejected() -> None:
    entry = {"name": "x", "type": "callback", "endpoint": "https://a"}
    with pytest.raises(ActionConfigError, match="duplicate action name 'x'"):
        parse_actions([entry, entry], allowed_commands=[])


def test_rule_state_defaults_to_active_and_accepts_draft(tmp_path: Path) -> None:
    path = _rules_file(tmp_path, "  []", "    state: draft\n")
    (rule,) = load_rules_from_yaml(path)
    assert rule.state is RuleState.DRAFT

    path.write_text(f"rules:\n{_RULE}", encoding="utf-8")
    (rule,) = load_rules_from_yaml(path)
    assert rule.state is RuleState.ACTIVE

    path.write_text(f"rules:\n{_RULE}    state: paused\n", encoding="utf-8")
    with pytest.raises(RuleConfigError, match="state"):
        load_rules_from_yaml(path)


def _agent_yaml(tmp_path: Path, actions_section: str) -> Path:
    path = tmp_path / "agent.yaml"
    path.write_text(
        "agent: {id: agent-x, instanceIds: [inst-x]}\n"
        "publish: {endpoint: https://backend.example/telemetry/batch}\n"
        "logs: {paths: [./logs/Fix.log]}\n"
        "rules: {path: rules.yaml, reloadCheckInterval: 5s}\n" + actions_section,
        encoding="utf-8",
    )
    return path


def test_agent_config_carries_the_allowlist_and_catalogue(tmp_path: Path) -> None:
    _rules_file(tmp_path, _COMMAND, "    actions: [disk-cleanup]\n")
    cfg = load_agent_config(
        _agent_yaml(tmp_path, f"actions:\n  allowedCommands: ['{PYTHON.as_posix()}']\n")
    )
    assert cfg.allowed_commands == (PYTHON,)
    assert set(cfg.actions) == {"disk-cleanup"}
    assert cfg.rules[0].actions == ("disk-cleanup",)
    assert cfg.rules_reload_check_seconds == 5


def test_agent_config_refuses_to_start_on_an_unlisted_command(
    tmp_path: Path,
) -> None:
    _rules_file(tmp_path, _COMMAND)
    with pytest.raises(AgentConfigError, match="rules: .*allowedCommands"):
        load_agent_config(_agent_yaml(tmp_path, ""))


def test_the_shipped_example_actions_load() -> None:
    repo = Path(__file__).resolve().parents[4]
    cfg = load_agent_config(repo / "config" / "agent.yaml")
    assert cfg.actions["disk-cleanup"].dry_run is True
