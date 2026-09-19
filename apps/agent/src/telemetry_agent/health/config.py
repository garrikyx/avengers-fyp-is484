"""Health Reporter / heartbeat settings (spec 010 `heartbeat:`, spec 011 §1.1, §2).

Typed settings plus a loader for the `heartbeat:` and `health:` sections of
`config/agent.yaml`. Same shape as `telemetry_backend.config`: frozen
dataclasses hold the values, YAML is parsed through a strict pydantic model so
an operator typo is refused rather than silently ignored. Rationale and
ticket-vs-spec decisions: docs/plan/ubs58-notes.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel

_DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)(ms|s|m|h)$")
_DURATION_UNIT_SECONDS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


class HealthConfigError(Exception):
    """Raised when `config/agent.yaml` exists but its health sections are invalid."""


def parse_duration_seconds(value: str | int | float) -> float:
    """`"10s"` / `"250ms"` / `"5m"` / bare number of seconds -> float seconds."""
    if isinstance(value, int | float):
        return float(value)
    match = _DURATION_RE.match(value.strip())
    if match is None:
        raise HealthConfigError(
            f"invalid duration {value!r}: expected e.g. '250ms', '10s', '5m', '1h'"
        )
    number, unit = match.groups()
    return float(number) * _DURATION_UNIT_SECONDS[unit]


@dataclass(slots=True, frozen=True)
class HeartbeatConfig:
    # FR-HLT-001 / spec 010 `heartbeat.interval`: default 10s. The UBS-58
    # ticket text says 30s; spec wins (see docs/plan/ubs58-notes.md).
    interval_seconds: float = 10.0
    agent_id: str = "magic-agent-local"
    instance_ids: tuple[str, ...] = ("magic-local",)
    agent_version: str = "0.1.0"

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise HealthConfigError("heartbeat.interval must be > 0")
        if not self.agent_id:
            raise HealthConfigError("agent.id must be non-empty")


@dataclass(slots=True, frozen=True)
class HealthThresholds:
    """FR-HLT-002 thresholds. Only the read-lag one has a producer on UBS-58;
    the rest are declared here so 59/60 add a signal, not a config shape."""

    # spec 011 §1.1: read lag > 5s sustained => degraded
    read_lag_degraded_ms: float = 5_000.0
    # spec 011 §2 / spec 005: parse error rate > 1% degraded, > 25% unhealthy
    parse_error_rate_degraded: float = 0.01
    parse_error_rate_unhealthy: float = 0.25
    # spec 004 §6 `...Last5Min` fields
    rolling_window_seconds: float = 300.0
    # spec 011 §1.1: publish queue depth "< 10" healthy; second tier is a
    # placeholder pending team review (UBS-60).
    publish_queue_high_watermark: int = 10
    publish_queue_critical_watermark: int = 100
    # spec 011 §2: callback failures > 0 in last 5 minutes => degraded
    callback_failures_degraded: int = 1

    def __post_init__(self) -> None:
        if self.parse_error_rate_degraded >= self.parse_error_rate_unhealthy:
            raise HealthConfigError(
                "health.parseErrorRateDegraded must be below parseErrorRateUnhealthy"
            )
        if self.publish_queue_high_watermark >= self.publish_queue_critical_watermark:
            raise HealthConfigError(
                "health.publishQueueHighWatermark must be below "
                "publishQueueCriticalWatermark"
            )
        if self.rolling_window_seconds <= 0:
            raise HealthConfigError("health.rollingWindow must be > 0")


# --- YAML shape -------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid"
    )


class _AgentYaml(_Strict):
    id: str | None = None
    instance_ids: list[str] | None = None
    instance_id: str | None = None  # accepted alias for a single instance
    version: str | None = None


class _HeartbeatYaml(_Strict):
    interval: str | int | float | None = None


class _HealthYaml(_Strict):
    read_lag_degraded: str | int | float | None = None
    parse_error_rate_degraded: float | None = None
    parse_error_rate_unhealthy: float | None = None
    rolling_window: str | int | float | None = None
    publish_queue_high_watermark: int | None = None
    publish_queue_critical_watermark: int | None = None
    callback_failures_degraded: int | None = None


class _AgentConfigYaml(BaseModel):
    # Only the sections this module owns are validated; siblings (log:,
    # backend:, ...) belong to other components and are passed through.
    model_config = ConfigDict(extra="allow")

    agent: _AgentYaml | None = None
    heartbeat: _HeartbeatYaml | None = None
    health: _HealthYaml | None = None


def _drop_none(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


def load_health_config(
    path: Path | str | None,
) -> tuple[HeartbeatConfig, HealthThresholds]:
    """Load `heartbeat:` / `health:` / `agent:` from an agent YAML file.

    A missing file (or `None`) yields defaults; a present-but-malformed file
    raises `HealthConfigError` (refuse to start, same policy as rules RE-05).
    """
    if path is None:
        return HeartbeatConfig(), HealthThresholds()
    file = Path(path)
    if not file.exists():
        return HeartbeatConfig(), HealthThresholds()

    try:
        raw = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise HealthConfigError(f"{file}: invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise HealthConfigError(f"{file}: top level must be a mapping")

    try:
        parsed = _AgentConfigYaml.model_validate(raw)
    except ValidationError as exc:
        raise HealthConfigError(f"{file}: {exc}") from exc

    agent = parsed.agent or _AgentYaml()
    heartbeat = parsed.heartbeat or _HeartbeatYaml()
    health = parsed.health or _HealthYaml()

    instance_ids: tuple[str, ...] | None = None
    if agent.instance_ids is not None:
        instance_ids = tuple(agent.instance_ids)
    elif agent.instance_id is not None:
        instance_ids = (agent.instance_id,)

    hb = HeartbeatConfig(
        **_drop_none(
            interval_seconds=(
                parse_duration_seconds(heartbeat.interval)
                if heartbeat.interval is not None
                else None
            ),
            agent_id=agent.id,
            instance_ids=instance_ids,
            agent_version=agent.version,
        )
    )
    thresholds = HealthThresholds(
        **_drop_none(
            read_lag_degraded_ms=(
                parse_duration_seconds(health.read_lag_degraded) * 1000
                if health.read_lag_degraded is not None
                else None
            ),
            parse_error_rate_degraded=health.parse_error_rate_degraded,
            parse_error_rate_unhealthy=health.parse_error_rate_unhealthy,
            rolling_window_seconds=(
                parse_duration_seconds(health.rolling_window)
                if health.rolling_window is not None
                else None
            ),
            publish_queue_high_watermark=health.publish_queue_high_watermark,
            publish_queue_critical_watermark=health.publish_queue_critical_watermark,
            callback_failures_degraded=health.callback_failures_degraded,
        )
    )
    return hb, thresholds
