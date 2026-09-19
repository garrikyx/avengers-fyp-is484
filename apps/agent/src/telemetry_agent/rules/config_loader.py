"""RE-05: `config/rules.yaml` loading and SIGHUP reload (`FR-RUL-008`/`009`).

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
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from pydantic.alias_generators import to_camel
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import _OPERATORS, RuleEngine
from telemetry_agent.rules.types import RuleConfig, RuleKind, SeverityTier, ValueSource

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
    for_: str = Field(default="60s", alias="for")
    resolve_after: str = Field(default="300s")
    group_by: tuple[str, ...] = ()
    schedule_ref: str | None = None
    depends_on_log_activity: bool = True

    @field_validator("operator")
    @classmethod
    def _known_operator(cls, v: str) -> str:
        if v not in _OPERATORS:
            known = sorted(_OPERATORS)
            raise ValueError(f"unknown operator {v!r}, expected one of {known}")
        return v


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
        for_seconds=_parse_duration_seconds(parsed.for_),
        resolve_after_seconds=_parse_duration_seconds(parsed.resolve_after),
        group_by=parsed.group_by,
        schedule_ref=parsed.schedule_ref,
        depends_on_log_activity=parsed.depends_on_log_activity,
    )


def _rule_label(entry: Any, index: int) -> str:
    if isinstance(entry, dict):
        name = entry.get("name")
        if isinstance(name, str):
            return name
    return f"<rule #{index}>"


def load_rules_from_yaml(path: Path) -> tuple[RuleConfig, ...]:
    """Parses and validates `path` fully; raises `RuleConfigError` naming
    the offending rule on any problem. Never partially applies a file.
    """
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise RuleConfigError(f"{path}: invalid YAML: {exc}") from exc

    entries = (raw or {}).get("rules", []) if isinstance(raw, dict) else []
    if not entries:
        raise RuleConfigError(f"{path}: no rules defined")

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


class SighupRuleReloader:
    """Wires `config/rules.yaml` reloading to SIGHUP for a live
    `RuleEngine`. `install()` is the call a future agent supervisor loop
    makes once one exists — nothing in this repo runs continuously yet.
    """

    def __init__(
        self,
        engine: RuleEngine,
        path: Path,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._engine = engine
        self._path = path
        self._logger = logger or logging.getLogger(__name__)

    def reload(self, *, now: datetime | None = None) -> None:
        try:
            new_rules = load_rules(self._path)
        except RuleConfigError as exc:
            self._logger.error(
                "rules reload rejected, keeping last-known-good: %s", exc
            )
            return
        self._engine.apply_rules(new_rules, now=now or datetime.now(UTC))
        self._logger.info(
            "rules reloaded: %d rules from %s", len(new_rules), self._path
        )

    def install(self) -> None:
        signal.signal(signal.SIGHUP, lambda *_: self.reload())
