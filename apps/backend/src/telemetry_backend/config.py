"""Backend stream-processing configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel
from telemetry_shared.metrics import DEFAULT_MIN_SAMPLE_SIZE, DEFAULT_PERCENTILES


@dataclass(slots=True, frozen=True)
class IngestionConfig:
    """Configuration for the bounded ingestion hand-off."""

    queue_size: int = 10_000

    def __post_init__(self) -> None:
        if self.queue_size < 1:
            raise ValueError("queue_size must be at least 1")


@dataclass(slots=True, frozen=True)
class StreamProcessorConfig:
    canonical_bucket_seconds: int = 10

    max_bucket_age_seconds: int = 3600

    retention_window_seconds: int = 21600

    warmup_window_seconds: int = 120

    # FR-MET-030-equivalent cap, applied here against cross-agent
    # cardinality within one canonical bucket rather than one agent's own
    # buckets — same default as the agent's own AggregatorConfig for
    # consistency, since both guard the same underlying series-count risk.
    max_series_per_bucket: int = 2000

    # FR-QRY-003: the memory budget MetricStore.estimated_memory_bytes()
    # checks itself against, and the warn/shed thresholds of that budget.
    memory_limit_mb: int = 4096
    memory_warn_percent: float = 75.0
    memory_shed_percent: float = 90.0

    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE
    default_percentiles: tuple[int, ...] = field(default=DEFAULT_PERCENTILES)

    def __post_init__(self) -> None:
        if self.max_bucket_age_seconds > self.retention_window_seconds:
            msg = (
                "max_bucket_age_seconds "
                f"({self.max_bucket_age_seconds}) must not exceed "
                f"retention_window_seconds ({self.retention_window_seconds})"
            )
            raise ValueError(msg)
        if self.max_series_per_bucket < 1:
            msg = (
                f"max_series_per_bucket ({self.max_series_per_bucket}) must be "
                "at least 1, or every series would be dropped as over-cap"
            )
            raise ValueError(msg)
        if self.memory_limit_mb <= 0:
            msg = f"memory_limit_mb ({self.memory_limit_mb}) must be positive"
            raise ValueError(msg)
        if not (0 < self.memory_warn_percent < self.memory_shed_percent <= 100):
            msg = (
                "memory_warn_percent "
                f"({self.memory_warn_percent}) must be greater than 0 and less "
                f"than memory_shed_percent ({self.memory_shed_percent}), which "
                "must itself be at most 100"
            )
            raise ValueError(msg)


# --- Backend health / registry settings (UBS-69, UBS-96) ----------------------------
#
# Loaded from `config/backend.yaml` (spec 010 s2): `backend.listen`,
# `backend.internalListen`, `store.warmupWindow`, `alerting.missingHeartbeatThreshold`.
# Same policy as the agent's health config: a missing file yields defaults, a
# malformed one is refused at boot.

_DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)(ms|s|m|h)$")
_DURATION_UNIT_SECONDS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


class BackendConfigError(Exception):
    """Raised when `config/backend.yaml` exists but is invalid."""


def parse_duration_seconds(value: str | int | float) -> float:
    if isinstance(value, int | float):
        return float(value)
    match = _DURATION_RE.match(value.strip())
    if match is None:
        raise BackendConfigError(
            f"invalid duration {value!r}: expected e.g. '250ms', '60s', '2m', '1h'"
        )
    number, unit = match.groups()
    return float(number) * _DURATION_UNIT_SECONDS[unit]


@dataclass(slots=True, frozen=True)
class BackendHealthConfig:
    # FR-RUL-030 / spec 005: an agent with no heartbeat for this long is `missing`.
    missing_heartbeat_threshold_seconds: float = 60.0
    # FR-QRY-005: /readyz reports `warming` until this much data exists.
    warmup_window_seconds: float = 120.0
    # FR-HLT-012: public API vs internal-only listener (/healthz /readyz /metrics).
    listen: str = "0.0.0.0:8080"
    internal_listen: str = "127.0.0.1:8081"

    def __post_init__(self) -> None:
        if self.missing_heartbeat_threshold_seconds <= 0:
            raise BackendConfigError("alerting.missingHeartbeatThreshold must be > 0")
        if self.warmup_window_seconds < 0:
            raise BackendConfigError("store.warmupWindow must be >= 0")
        for name, value in (
            ("listen", self.listen),
            ("internalListen", self.internal_listen),
        ):
            if ":" not in value or not value.rsplit(":", 1)[1].isdigit():
                raise BackendConfigError(
                    f"backend.{name} must be host:port, got {value!r}"
                )

    def _split(self, value: str) -> tuple[str, int]:
        host, port = value.rsplit(":", 1)
        return host, int(port)

    @property
    def listen_host_port(self) -> tuple[str, int]:
        return self._split(self.listen)

    @property
    def internal_listen_host_port(self) -> tuple[str, int]:
        return self._split(self.internal_listen)


class _Lenient(BaseModel):
    # spec 010's `backend:` / `store:` / `alerting:` sections also carry keys
    # owned by other components (workers, retentionWindow, ...), so unknown
    # keys are tolerated here - unlike the agent's health sections, which
    # are ours alone and refuse typos. A misspelt key of *ours* therefore
    # silently keeps its default; `--check-config` prints the effective values.
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="allow"
    )


class _BackendYaml(_Lenient):
    listen: str | None = None
    internal_listen: str | None = None


class _StoreYaml(_Lenient):
    warmup_window: str | int | float | None = None


class _AlertingYaml(_Lenient):
    missing_heartbeat_threshold: str | int | float | None = None


class _BackendConfigYaml(BaseModel):
    # Sibling sections (ingest:, query:, nl:, ...) belong to other components.
    model_config = ConfigDict(extra="allow")

    backend: _BackendYaml | None = None
    store: _StoreYaml | None = None
    alerting: _AlertingYaml | None = None


def _drop_none(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


def load_backend_health_config(path: Path | str | None) -> BackendHealthConfig:
    if path is None:
        return BackendHealthConfig()
    file = Path(path)
    if not file.exists():
        return BackendHealthConfig()
    try:
        raw = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise BackendConfigError(f"{file}: invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise BackendConfigError(f"{file}: top level must be a mapping")
    try:
        parsed = _BackendConfigYaml.model_validate(raw)
    except ValidationError as exc:
        raise BackendConfigError(f"{file}: {exc}") from exc

    backend = parsed.backend or _BackendYaml()
    store = parsed.store or _StoreYaml()
    alerting = parsed.alerting or _AlertingYaml()
    return BackendHealthConfig(
        **_drop_none(
            missing_heartbeat_threshold_seconds=(
                parse_duration_seconds(alerting.missing_heartbeat_threshold)
                if alerting.missing_heartbeat_threshold is not None
                else None
            ),
            warmup_window_seconds=(
                parse_duration_seconds(store.warmup_window)
                if store.warmup_window is not None
                else None
            ),
            listen=backend.listen,
            internal_listen=backend.internal_listen,
        )
    )
