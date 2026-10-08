"""Agent configuration: `config/agent.yaml` loaded once (UBS-114).

Each section is parsed by the loader its component already owns; this module
only reads the file once, hands every section to the right loader and adds
the two sections nothing else reads yet (`logs:`, `pipeline:`):

    agent: / heartbeat: / health:   -> health.config.load_health_config
    publish:                        -> publishing.config.parse_publish_config
    callbacks:                      -> callbacks.config.parse_callbacks_config
    rules: {path: rules.yaml}       -> rules.config_loader.load_rules
    logs: {paths, stateDir, appLogPatterns}
    parsing: {errorSignatures, maxDynamicSignatureLabels}
    pipeline: {parseWorkers, evaluationInterval}

Log paths and the state dir resolve against the directory the agent is
started from (the simulator writes `./logs/*.log` relative to its own working
directory); the rules file resolves next to the config file.

Secrets never live here: the publish token, callback secret and identifier
hash key come from the environment (see `.env.example`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel

from telemetry_agent.callbacks.config import CallbacksConfig, parse_callbacks_config
from telemetry_agent.health.config import (
    HealthThresholds,
    HeartbeatConfig,
    load_health_config,
    parse_duration_seconds,
)
from telemetry_agent.publishing.config import PublishConfig, parse_publish_config
from telemetry_agent.rules.config_loader import load_rules
from telemetry_agent.rules.types import RuleConfig

DEFAULT_CONFIG_PATH = Path("config/agent.yaml")


class AgentConfigError(Exception):
    """`agent.yaml` is missing or a section is invalid; the message names it."""


class _Section(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid"
    )


class _LogsYaml(_Section):
    paths: list[str]
    state_dir: str = ".agent-state"
    app_log_patterns: list[str] = []


class _SignatureYaml(_Section):
    label: str
    match: str


class _ParsingYaml(_Section):
    # spec 010 `parsing:` — only the app-log signature keys are read here;
    # the FIX parser's own keys aren't wired into the agent yet.
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="ignore"
    )
    error_signatures: list[_SignatureYaml] = []
    max_dynamic_signature_labels: int = 50


class _PipelineYaml(_Section):
    parse_workers: int = 1
    evaluation_interval: str | float = "10s"


class _RulesYaml(_Section):
    path: str = "rules.yaml"


@dataclass(frozen=True, slots=True)
class LogsConfig:
    paths: tuple[Path, ...]
    state_dir: Path
    app_log_patterns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParsingConfig:
    error_signatures: tuple[tuple[str, str], ...]  # (label, match) pairs
    max_dynamic_signature_labels: int


@dataclass(frozen=True, slots=True)
class AgentConfig:
    source: Path
    heartbeat: HeartbeatConfig
    thresholds: HealthThresholds
    publish: PublishConfig
    callbacks: CallbacksConfig | None  # None when absent or `enabled: false`
    rules: tuple[RuleConfig, ...]
    rules_path: Path
    logs: LogsConfig
    parsing: ParsingConfig
    parse_workers: int
    evaluation_interval_seconds: float

    @property
    def agent_id(self) -> str:
        return self.heartbeat.agent_id

    @property
    def instance_id(self) -> str:
        return self.heartbeat.instance_ids[0]


def _section(raw: dict[str, Any], name: str, model: type[_Section]) -> Any:
    try:
        return model.model_validate(raw.get(name) or {})
    except ValidationError as exc:
        raise AgentConfigError(f"{name}: {exc}") from exc


def load_agent_config(path: Path | str = DEFAULT_CONFIG_PATH) -> AgentConfig:
    file = Path(path)
    if not file.is_file():
        raise AgentConfigError(f"config file not found: {file}")
    try:
        raw = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise AgentConfigError(f"{file}: invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise AgentConfigError(f"{file}: top level must be a mapping")

    try:
        heartbeat, thresholds = load_health_config(file)
    except Exception as exc:  # HealthConfigError carries the detail
        raise AgentConfigError(f"agent/heartbeat/health: {exc}") from exc

    if "publish" not in raw:
        raise AgentConfigError("publish: section is required")
    try:
        publish = parse_publish_config(raw["publish"])
    except Exception as exc:
        raise AgentConfigError(f"publish: {exc}") from exc

    callbacks: CallbacksConfig | None = None
    if raw.get("callbacks"):
        try:
            parsed_callbacks = parse_callbacks_config(raw["callbacks"])
        except Exception as exc:
            raise AgentConfigError(f"callbacks: {exc}") from exc
        callbacks = parsed_callbacks if parsed_callbacks.enabled else None

    rules_section: _RulesYaml = _section(raw, "rules", _RulesYaml)
    rules_path = (file.parent / rules_section.path).resolve()
    try:
        rules = load_rules(rules_path)
    except Exception as exc:
        raise AgentConfigError(f"rules: {exc}") from exc

    if "logs" not in raw:
        raise AgentConfigError("logs: section is required (paths to tail)")
    logs_section: _LogsYaml = _section(raw, "logs", _LogsYaml)
    if not logs_section.paths:
        raise AgentConfigError("logs: paths must list at least one file")

    parsing: _ParsingYaml = _section(raw, "parsing", _ParsingYaml)
    for signature in parsing.error_signatures:
        try:
            re.compile(signature.match)
        except re.error as exc:
            raise AgentConfigError(
                f"parsing: errorSignatures {signature.label!r}: invalid match: {exc}"
            ) from exc
    if parsing.max_dynamic_signature_labels < 1:
        raise AgentConfigError("parsing: maxDynamicSignatureLabels must be >= 1")

    pipeline: _PipelineYaml = _section(raw, "pipeline", _PipelineYaml)
    if pipeline.parse_workers < 1:
        raise AgentConfigError("pipeline: parseWorkers must be >= 1")
    try:
        interval = parse_duration_seconds(pipeline.evaluation_interval)
    except Exception as exc:
        raise AgentConfigError(f"pipeline: evaluationInterval: {exc}") from exc
    if interval <= 0:
        raise AgentConfigError("pipeline: evaluationInterval must be > 0")

    return AgentConfig(
        source=file,
        heartbeat=heartbeat,
        thresholds=thresholds,
        publish=publish,
        callbacks=callbacks,
        rules=rules,
        rules_path=rules_path,
        logs=LogsConfig(
            paths=tuple(Path(p) for p in logs_section.paths),
            state_dir=Path(logs_section.state_dir),
            app_log_patterns=tuple(logs_section.app_log_patterns),
        ),
        parsing=ParsingConfig(
            error_signatures=tuple(
                (sig.label, sig.match) for sig in parsing.error_signatures
            ),
            max_dynamic_signature_labels=parsing.max_dynamic_signature_labels,
        ),
        parse_workers=pipeline.parse_workers,
        evaluation_interval_seconds=interval,
    )
