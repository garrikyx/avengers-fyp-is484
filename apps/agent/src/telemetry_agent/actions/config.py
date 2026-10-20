"""UBS-35: the `actions:` block of the rules file (spec 005 §5, ADR 0008).

    actions:                          # config/rules.yaml, beside `rules:`
      - name: disk-cleanup
        type: command                 # command | callback
        command: /opt/magic/bin/cleanup-disk
        args: ["--older-than", "7d"]
        timeout: 60s
        dryRun: true                  # the default (FR-CBK-017)
      - name: ops-webhook
        type: callback
        endpoint: https://ops.internal.example/hooks/telemetry

    actions:                          # config/agent.yaml
      allowedCommands: [/opt/magic/bin/cleanup-disk]

The two halves live in different files on purpose. ADR 0008 makes the command
allowlist the operator's decision, not the rule author's, so adding or
editing a rule (which reloads live) can never introduce a new executable.
`allowedCommands` only changes with an agent restart.

Rule names are cross-checked against this block by the rules loader
(`FR-CBK-013`). This module validates what each action is.
"""

from __future__ import annotations

import os
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePath
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from pydantic.alias_generators import to_camel

from telemetry_agent.callbacks.config import (
    CallbackConfigError,
    CallbacksConfig,
    parse_callbacks_config,
)
from telemetry_agent.rules.config_loader import (
    RuleConfigError,
    _parse_duration_seconds,
    read_rules_file,
)


class ActionConfigError(RuleConfigError):
    """A malformed action rejects the whole rules file, at boot and on reload,
    exactly like a malformed rule (`FR-RUL-009`)."""


class ActionType(StrEnum):
    COMMAND = "command"
    CALLBACK = "callback"


class _ActionYaml(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid"
    )

    name: str = Field(min_length=1)
    type: ActionType
    command: str | None = None
    args: tuple[str, ...] = ()
    endpoint: str | None = None
    allow_insecure_callback: bool = False
    timeout: str = "60s"
    dry_run: bool = True  # FR-CBK-017

    @model_validator(mode="after")
    def _fields_match_type(self) -> _ActionYaml:
        if self.type is ActionType.COMMAND:
            if not self.command:
                raise ValueError("a command action needs `command`")
            if self.endpoint is not None or self.allow_insecure_callback:
                raise ValueError("`endpoint` belongs on a callback action only")
        else:
            if not self.endpoint:
                raise ValueError("a callback action needs `endpoint`")
            if self.command is not None or self.args:
                raise ValueError("`command`/`args` belong on a command action only")
        return self


@dataclass(frozen=True, slots=True)
class ActionDef:
    name: str
    type: ActionType
    timeout_seconds: float
    dry_run: bool
    command: Path | None = None  # command only
    args: tuple[str, ...] = ()  # command only: fixed argv, never templated
    callbacks: CallbacksConfig | None = None  # callback only (FR-CBK-014)


ActionCatalogue = Mapping[str, ActionDef]


def _command_key(path: str | Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def _is_rooted(command: str) -> bool:
    """Absolute, or rooted at the current drive on Windows (`/opt/x`). Either
    way the OS never searches `PATH` or the working directory for it, which
    is what `FR-CBK-015`'s "absolute path" protects against."""
    return bool(PurePath(command).root)


def parse_allowed_commands(entries: Collection[str]) -> tuple[Path, ...]:
    commands: list[Path] = []
    for entry in entries:
        if not _is_rooted(entry):
            raise ActionConfigError(
                f"allowedCommands: {entry!r} must be an absolute path"
            )
        commands.append(Path(entry))
    return tuple(commands)


def _parse_action(parsed: _ActionYaml, allowed: set[str]) -> ActionDef:
    timeout = _parse_duration_seconds(parsed.timeout)
    if timeout <= 0:
        raise ActionConfigError(f"action {parsed.name!r}: timeout must be > 0")

    if parsed.type is ActionType.COMMAND:
        assert parsed.command is not None  # _fields_match_type
        if not _is_rooted(parsed.command):
            raise ActionConfigError(
                f"action {parsed.name!r}: command {parsed.command!r} must be an "
                "absolute path (no PATH lookup, FR-CBK-015)"
            )
        if _command_key(parsed.command) not in allowed:
            raise ActionConfigError(
                f"action {parsed.name!r}: command {parsed.command!r} is not in "
                "agent.yaml actions.allowedCommands (ADR 0008)"
            )
        return ActionDef(
            name=parsed.name,
            type=parsed.type,
            timeout_seconds=timeout,
            dry_run=parsed.dry_run,
            command=Path(parsed.command),
            args=parsed.args,
        )

    try:
        callbacks = parse_callbacks_config(
            {
                "endpoint": parsed.endpoint,
                "allowInsecureCallback": parsed.allow_insecure_callback,
                "dryRun": parsed.dry_run,
            }
        )
    except CallbackConfigError as exc:
        raise ActionConfigError(f"action {parsed.name!r}: {exc}") from exc
    return ActionDef(
        name=parsed.name,
        type=parsed.type,
        timeout_seconds=timeout,
        dry_run=parsed.dry_run,
        callbacks=callbacks,
    )


def parse_actions(
    entries: Any, *, allowed_commands: Collection[Path]
) -> dict[str, ActionDef]:
    """Parses an already-loaded `actions:` list. Raises `ActionConfigError`
    naming the offending action; never returns a partial catalogue."""
    if entries is None:
        return {}
    if not isinstance(entries, list):
        raise ActionConfigError("actions: must be a list")
    allowed = {_command_key(path) for path in allowed_commands}
    catalogue: dict[str, ActionDef] = {}
    for index, entry in enumerate(entries):
        label = (
            entry.get("name") if isinstance(entry, dict) else None
        ) or f"<action #{index}>"
        try:
            parsed = _ActionYaml.model_validate(entry)
        except ValidationError as exc:
            raise ActionConfigError(f"action {label!r} is invalid: {exc}") from exc
        except RuleConfigError as exc:  # a bad duration
            raise ActionConfigError(f"action {label!r}: {exc}") from exc
        if parsed.name in catalogue:
            raise ActionConfigError(f"duplicate action name {parsed.name!r}")
        try:
            catalogue[parsed.name] = _parse_action(parsed, allowed)
        except ActionConfigError:
            raise
        except RuleConfigError as exc:
            raise ActionConfigError(f"action {parsed.name!r}: {exc}") from exc
    return catalogue


def load_action_catalogue(
    path: Path, *, allowed_commands: Collection[Path]
) -> dict[str, ActionDef]:
    """The `actions:` block of the rules file at `path`; empty when the file
    doesn't exist (the agent then runs `DEFAULT_RULES`, which name none)."""
    if not path.exists():
        return {}
    return parse_actions(
        read_rules_file(path).get("actions"), allowed_commands=allowed_commands
    )
