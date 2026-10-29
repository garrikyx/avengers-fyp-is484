"""RE-05: `config/rules.yaml` loading and live reload (`FR-RUL-008`/`009`).

`config/rules.yaml` is the live source of rules; `defaults.DEFAULT_RULES`
is the fallback used only when that file doesn't exist. A malformed
*existing* file always raises `RuleConfigError` rather than silently
falling back — `FR-RUL-009`'s "refuse to start" applies to initial load.

`SighupRuleReloader` extends that same loader to a live `RuleEngine`: a
malformed reload is rejected (logged, last-known-good rules kept, process
stays up) rather than crashing an already-running agent over an operator's
YAML typo — reload safety is deliberately looser than boot safety.
"""

from __future__ import annotations

import logging
import re
import signal
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import _OPERATORS, RuleEngine
from telemetry_agent.rules.types import (
    APP_LOG_LEVELS,
    LEVEL_DIMENSION,
    RuleConfig,
    RuleKind,
    RuleState,
    SeverityTier,
    ValueSource,
)
from telemetry_shared.models.alerts import AlertEvent

_DURATION_RE = re.compile(r"^(\d+)([smh])$")
_DURATION_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600}


class RuleConfigError(Exception):
    """Raised at load or reload time, naming the offending rule."""


def _parse_duration_seconds(text: str) -> int:
    match = _DURATION_RE.match(text.strip())
    if match is None:
        raise RuleConfigError(
            f"invalid duration {text!r}: expected e.g. '30s', '2m', '1h'"
        )
    value, unit = match.groups()
    return int(value) * _DURATION_UNIT_SECONDS[unit]


class _TierYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    threshold: Decimal


class _RuleYaml(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid"
    )

    name: str
    kind: RuleKind
    source: ValueSource
    metric: str
    operator: str
    tiers: tuple[_TierYaml, ...] = Field(min_length=1)

    window: str | None = None
    min_samples: int | None = None
    guard_metric: str | None = None
    extra_counters: tuple[str, ...] = ()
    signature: str | None = None
    level: str | None = None
    for_: str = Field(default="60s", alias="for")
    resolve_after: str = Field(default="300s")
    group_by: tuple[str, ...] = ()
    schedule_ref: str | None = None
    depends_on_log_activity: bool = True
    actions: tuple[str, ...] = ()
    state: RuleState = RuleState.ACTIVE

    @field_validator("operator")
    @classmethod
    def _known_operator(cls, v: str) -> str:
        if v not in _OPERATORS:
            known = sorted(_OPERATORS)
            raise ValueError(f"unknown operator {v!r}, expected one of {known}")
        return v

    @model_validator(mode="after")
    def _signature_matches_kind(self) -> _RuleYaml:
        # A signature rule with no label would silently read nothing; a
        # label on any other kind would be ignored. Both are config mistakes.
        if (self.kind is RuleKind.SIGNATURE) != (self.signature is not None):
            raise ValueError("`signature` is required on, and only on, kind: signature")
        return self

    @model_validator(mode="after")
    def _level_selects_a_level_dimension(self) -> _RuleYaml:
        # FR-RUL-023: `level:` reads a snapshot grouped by `level`, so it is
        # meaningful only on a counter that carries that dimension. Anything
        # else would silently read nothing, so reject it at load (FR-RUL-009).
        if self.level is None:
            return self
        if self.kind is not RuleKind.THRESHOLD:
            raise ValueError("`level` is valid only on kind: threshold")
        if LEVEL_DIMENSION not in COUNTER_DIMENSIONS.get(self.metric, ()):
            raise ValueError(
                f"`level` requires a metric with a `level` dimension; "
                f"{self.metric!r} has none"
            )
        if self.level not in APP_LOG_LEVELS:
            raise ValueError(
                f"`level` must be one of {sorted(APP_LOG_LEVELS)}, got {self.level!r}"
            )
        return self


def _to_rule_config(parsed: _RuleYaml) -> RuleConfig:
    return RuleConfig(
        name=parsed.name,
        kind=parsed.kind,
        source=parsed.source,
        metric=parsed.metric,
        operator=parsed.operator,
        tiers=tuple(
            SeverityTier(severity=t.severity, threshold=t.threshold)
            for t in parsed.tiers
        ),
        window=parsed.window,
        min_samples=parsed.min_samples,
        guard_metric=parsed.guard_metric,
        extra_counters=parsed.extra_counters,
        signature=parsed.signature,
        level=parsed.level,
        for_seconds=_parse_duration_seconds(parsed.for_),
        resolve_after_seconds=_parse_duration_seconds(parsed.resolve_after),
        group_by=parsed.group_by,
        schedule_ref=parsed.schedule_ref,
        depends_on_log_activity=parsed.depends_on_log_activity,
        actions=parsed.actions,
        state=parsed.state,
    )


def _rule_label(entry: Any, index: int) -> str:
    if isinstance(entry, dict):
        name = entry.get("name")
        if isinstance(name, str):
            return name
    return f"<rule #{index}>"


def read_rules_file(path: Path) -> dict[str, Any]:
    """The parsed top level of a rules file: `rules:` plus, optionally, the
    `actions:` block (spec 005 §5) that `telemetry_agent.actions.config`
    validates in full."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuleConfigError(f"{path}: invalid YAML: {exc}") from exc
    return raw if isinstance(raw, dict) else {}


def _defined_action_names(raw: dict[str, Any]) -> set[str]:
    entries = raw.get("actions") or []
    if not isinstance(entries, list):
        return set()
    return {
        entry["name"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def load_rules_from_yaml(path: Path) -> tuple[RuleConfig, ...]:
    """Parses and validates `path` fully; raises `RuleConfigError` naming
    the offending rule on any problem. Never partially applies a file.

    `FR-CBK-013`: every name in a rule's `actions` must be defined in the
    same file's `actions:` block. Only names are checked here; what each
    action is (and whether its command is allowlisted) is checked by
    `telemetry_agent.actions.config.load_action_catalogue`.
    """
    raw = read_rules_file(path)
    entries = raw.get("rules", [])
    if not entries:
        raise RuleConfigError(f"{path}: no rules defined")
    action_names = _defined_action_names(raw)

    rules: list[RuleConfig] = []
    seen_names: set[str] = set()
    for index, entry in enumerate(entries):
        label = _rule_label(entry, index)
        try:
            parsed = _RuleYaml.model_validate(entry)
        except ValidationError as exc:
            raise RuleConfigError(f"rule {label!r} is invalid: {exc}") from exc
        if parsed.name in seen_names:
            raise RuleConfigError(f"duplicate rule name {parsed.name!r}")
        seen_names.add(parsed.name)
        unknown = [name for name in parsed.actions if name not in action_names]
        if unknown:
            raise RuleConfigError(
                f"rule {parsed.name!r} references undefined action(s) {unknown}; "
                f"defined actions: {sorted(action_names)}"
            )
        rules.append(_to_rule_config(parsed))

    return tuple(rules)


def load_rules(path: Path) -> tuple[RuleConfig, ...]:
    """`DEFAULT_RULES` if `path` doesn't exist; otherwise the parsed file
    (raising `RuleConfigError` if it exists but is malformed — a present-
    but-broken file never silently falls back to defaults).
    """
    if not path.exists():
        return DEFAULT_RULES
    return load_rules_from_yaml(path)


# Stage the non-rule parts of a reload (the action catalogue) before the new
# rules are applied: called with the rules file path, it raises
# `RuleConfigError` to reject the whole reload, or returns the step that
# commits them once the rules are in.
ReloadStage = Callable[[Path], Callable[[], None]]


class SighupRuleReloader:
    """Reloads `config/rules.yaml` into a live `RuleEngine`, on SIGHUP or
    (UBS-35, so Windows has a trigger too) when `changed_on_disk()` sees a
    new modification time. A rejected reload keeps every last-known-good
    piece: rules and, through `stage`, the action catalogue.
    """

    def __init__(
        self,
        engine: RuleEngine,
        path: Path,
        *,
        stage: ReloadStage | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._engine = engine
        self._path = path
        self._stage = stage
        self._logger = logger or logging.getLogger(__name__)
        self._mtime = self._read_mtime()

    def _read_mtime(self) -> float | None:
        try:
            return self._path.stat().st_mtime
        except OSError:
            return None

    def changed_on_disk(self) -> bool:
        """True when the file's mtime differs from the one last loaded (or
        last rejected, so a broken file isn't re-parsed every tick)."""
        return self._read_mtime() != self._mtime

    def reload(self, *, now: datetime | None = None) -> list[AlertEvent]:
        """Returns the `resolved` events `apply_rules()` emits for alerts
        whose rule was removed, so a caller can route them (UBS-113). Empty
        when the new file is rejected and the last-known-good set stays.
        """
        self._mtime = self._read_mtime()
        try:
            new_rules = load_rules(self._path)
            commit = self._stage(self._path) if self._stage is not None else None
        except RuleConfigError as exc:
            self._logger.error(
                "rules reload rejected, keeping last-known-good: %s", exc
            )
            return []
        resolved = self._engine.apply_rules(new_rules, now=now or datetime.now(UTC))
        if commit is not None:
            commit()
        self._logger.info(
            "rules reloaded: %d rules from %s", len(new_rules), self._path
        )
        return resolved

    def install(self) -> None:
        """Standalone use only: this reloads inside the signal handler and
        drops the returned `resolved` events. A running agent should
        instead register `RuleEvaluator.request_reload` with
        `loop.add_signal_handler(SIGHUP, ...)`, which defers the reload to
        the next evaluation tick and routes those events (UBS-113)."""
        signal.signal(signal.SIGHUP, lambda *_: self.reload())
