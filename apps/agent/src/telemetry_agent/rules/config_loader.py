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
from telemetry_agent.metrics.aggregator import DEFAULT_WINDOWS
from telemetry_agent.rules.baseline import ANOMALY_METRICS
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import _OPERATORS, RuleEngine
from telemetry_agent.rules.types import (
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
    def _not_anomaly(self) -> _RuleYaml:
        if self.kind is RuleKind.ANOMALY:
            raise ValueError(
                "kind: anomaly rules are configured in anomaly.yaml, not rules.yaml"
            )
        return self

    @model_validator(mode="after")
    def _signature_matches_kind(self) -> _RuleYaml:
        # A signature rule with no label would silently read nothing; a
        # label on any other kind would be ignored. Both are config mistakes.
        if (self.kind is RuleKind.SIGNATURE) != (self.signature is not None):
            raise ValueError("`signature` is required on, and only on, kind: signature")
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


# --- anomaly.yaml (D2: UBS-25/26/28/29) ------------------------------------
#
# One top-level key per metric in `baseline.ANOMALY_METRICS`; each enabled
# entry becomes one `kind: anomaly` rule, so the Rule Engine's lifecycle,
# routing, silences and reload apply to it unchanged.

ANOMALY_RULE_NAMES: dict[str, str] = {
    "reject_rate": "AbnormalRejectRate",
    "ack_latency_ms": "AbnormalProcessingLatency",
    "execution_issue_rate": "AbnormalExecutionIssueRate",
    "parser_failure_rate": "AbnormalParserFailureRate",
}

# A p95 over fewer observations than this is mostly one slow order.
_DEFAULT_WINDOW_MIN_SAMPLES = {"ack_latency_ms": 50}
_DEFAULT_ANOMALY_TIER = _TierYaml(severity="warning", threshold=Decimal("0.5"))


_ANOMALY_WINDOW_MINUTES = frozenset(
    seconds // 60 for seconds in DEFAULT_WINDOWS.values()
)


class _AnomalyYaml(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    enabled: bool = True
    window_minutes: int = Field(default=5, ge=1)
    baseline_window_minutes: int = Field(default=60, ge=1)
    # Pooled events (denominator, or latency observations) the baseline needs.
    minimum_samples: int = Field(default=100, ge=1)
    # Events the current window needs before it is judged; the metric's own
    # default applies when omitted.
    window_minimum_samples: int | None = Field(default=None, ge=1)
    # Deviation tiers: 0.5 = +50% over baseline (1.5x), ordered least->most severe.
    tiers: tuple[_TierYaml, ...] = Field(default=(_DEFAULT_ANOMALY_TIER,), min_length=1)
    for_: str = Field(default="2m", alias="for")
    resolve_after: str = "5m"
    actions: tuple[str, ...] = ()
    state: RuleState = RuleState.ACTIVE

    @model_validator(mode="after")
    def _window_exists(self) -> _AnomalyYaml:
        # The snapshot is built per aggregator window; any other length would
        # raise on every evaluation tick, for every rule.
        if self.window_minutes not in _ANOMALY_WINDOW_MINUTES:
            raise ValueError(
                f"window_minutes must be one of {sorted(_ANOMALY_WINDOW_MINUTES)}"
            )
        return self

    @model_validator(mode="after")
    def _baseline_covers_windows(self) -> _AnomalyYaml:
        # MIN_BASELINE_WINDOWS non-overlapping windows must fit in the baseline.
        if self.baseline_window_minutes < 3 * self.window_minutes:
            raise ValueError(
                "baseline_window_minutes must be at least 3x window_minutes"
            )
        return self


def anomaly_path_for(rules_path: Path) -> Path:
    """`anomaly.yaml` lives beside `rules.yaml` (both under `config/`)."""
    return rules_path.with_name("anomaly.yaml")


def load_anomaly_rules(path: Path) -> tuple[RuleConfig, ...]:
    """Anomaly rules from `path`; none if the file is absent or empty.
    Raises `RuleConfigError` naming the offending metric on any problem."""
    if not path.exists():
        return ()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuleConfigError(f"{path}: invalid YAML: {exc}") from exc
    if raw is None:
        return ()
    if not isinstance(raw, dict):
        raise RuleConfigError(f"{path}: expected one entry per metric")

    rules: list[RuleConfig] = []
    for metric, entry in raw.items():
        if metric not in ANOMALY_METRICS:
            raise RuleConfigError(
                f"{path}: unknown anomaly metric {metric!r}, "
                f"expected one of {sorted(ANOMALY_METRICS)}"
            )
        try:
            parsed = _AnomalyYaml.model_validate(entry or {})
        except ValidationError as exc:
            raise RuleConfigError(f"anomaly {metric!r} is invalid: {exc}") from exc
        if not parsed.enabled:
            continue
        kind = ANOMALY_METRICS[metric].kind
        rules.append(
            RuleConfig(
                name=ANOMALY_RULE_NAMES[metric],
                kind=RuleKind.ANOMALY,
                source=(
                    ValueSource.LATENCY_P95
                    if kind == "latency"
                    else ValueSource.INDICATOR
                ),
                metric=metric,
                operator=">",
                tiers=tuple(
                    SeverityTier(severity=t.severity, threshold=t.threshold)
                    for t in parsed.tiers
                ),
                window=f"{parsed.window_minutes}m",
                min_samples=parsed.window_minimum_samples
                or _DEFAULT_WINDOW_MIN_SAMPLES.get(metric, 20),
                for_seconds=_parse_duration_seconds(parsed.for_),
                resolve_after_seconds=_parse_duration_seconds(parsed.resolve_after),
                actions=parsed.actions,
                state=parsed.state,
                baseline_seconds=parsed.baseline_window_minutes * 60,
                baseline_min_samples=parsed.minimum_samples,
            )
        )
    return tuple(rules)


def load_rules(path: Path) -> tuple[RuleConfig, ...]:
    """`DEFAULT_RULES` if `path` doesn't exist; otherwise the parsed file
    (raising `RuleConfigError` if it exists but is malformed — a present-
    but-broken file never silently falls back to defaults). The sibling
    `anomaly.yaml`'s rules are appended either way.
    """
    base = DEFAULT_RULES if not path.exists() else load_rules_from_yaml(path)
    anomaly = load_anomaly_rules(anomaly_path_for(path))
    clash = {r.name for r in base} & {r.name for r in anomaly}
    if clash:
        raise RuleConfigError(f"duplicate rule name(s) {sorted(clash)}")
    return (*base, *anomaly)


# Stage the non-rule parts of a reload (the action catalogue) before the new
# rules are applied: called with the rules file path, it raises
# `RuleConfigError` to reject the whole reload, or returns the step that
# commits them once the rules are in.
ReloadStage = Callable[[Path], Callable[[], None]]


def _mtime_or_none(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


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

    def _read_mtime(self) -> tuple[float | None, float | None]:
        """(rules.yaml, anomaly.yaml) modification times."""
        return (
            _mtime_or_none(self._path),
            _mtime_or_none(anomaly_path_for(self._path)),
        )

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
