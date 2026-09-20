"""Backend configuration (spec 006 §3, §4; spec 010 §2).

`StreamProcessorConfig` (UBS-88/90) and `BackendHealthConfig` (UBS-69/96).

Only the settings this stage of the backend needs. Loading these from YAML +
env overrides (spec 010's full configuration system) is a separate concern;
this is the typed settings object that system will eventually populate.
"""

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
class StreamProcessorConfig:
    # FR-STM-001: the backend's canonical window grid. Every incoming
    # snapshot is aligned to this width regardless of its own bucketSeconds.
    canonical_bucket_seconds: int = 10

    # FR-ING-005 / FR-STM-005: buckets older than this are rejected
    # (`bucket_too_old`) rather than merged.
    max_bucket_age_seconds: int = 3600

    # FR-QRY-001: how long the Metric Store keeps a canonical bucket before
    # evicting it, independent of maxBucketAge.
    retention_window_seconds: int = 21600

    # FR-QRY-005: how long an instance is considered `warmingUp` after a
    # `restarted: true` bucket is merged for it.
    warmup_window_seconds: int = 120

    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE
    default_percentiles: tuple[int, ...] = field(default=DEFAULT_PERCENTILES)

    def __post_init__(self) -> None:
        # A snapshot the StreamProcessor accepts as within maxBucketAge
        # must still be resident in the store's own retention window, or
        # MetricStore.merge() would have to drop it right after accepting
        # it (FR-STM-005: dropped data must be counted, never silent —
        # refusing the invalid config outright is stronger than relying on
        # that counter to catch it).
        if self.max_bucket_age_seconds > self.retention_window_seconds:
            msg = (
                "max_bucket_age_seconds "
                f"({self.max_bucket_age_seconds}) must not exceed "
                f"retention_window_seconds ({self.retention_window_seconds})"
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
