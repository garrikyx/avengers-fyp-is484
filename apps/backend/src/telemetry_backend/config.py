"""Backend stream-processing configuration."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel
from telemetry_shared.metrics import DEFAULT_MIN_SAMPLE_SIZE, DEFAULT_PERCENTILES


@dataclass(slots=True, frozen=True)
class AlertStoreConfig:
    """Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)."""

    recent_alert_limit: int = 500
    max_transitions: int = 50

    def __post_init__(self) -> None:
        if self.recent_alert_limit < 1:
            raise ValueError("recent_alert_limit must be at least 1")
        if self.max_transitions < 1:
            raise ValueError("max_transitions must be at least 1")


@dataclass(slots=True, frozen=True)
class EventStoreConfig:
    """Event store retention (UBS-118; spec 010 `store.recentAlertLimit` default)."""

    recent_event_limit: int = 500

    def __post_init__(self) -> None:
        if self.recent_event_limit < 1:
            raise ValueError("recent_event_limit must be at least 1")


@dataclass(slots=True, frozen=True)
class AlertingConfig:
    """Backend-owned alerting rules (spec 005 `FR-RUL-030`)."""

    missing_heartbeat_threshold_seconds: int = 60
    monitor_interval_seconds: int = 10

    def __post_init__(self) -> None:
        if self.missing_heartbeat_threshold_seconds < 1:
            raise ValueError("missing_heartbeat_threshold_seconds must be at least 1")
        if self.monitor_interval_seconds < 1:
            raise ValueError("monitor_interval_seconds must be at least 1")


@dataclass(slots=True, frozen=True)
class IngestionConfig:
    """Configuration for the bounded ingestion hand-off."""

    queue_size: int = 10_000

    def __post_init__(self) -> None:
        if self.queue_size < 1:
            raise ValueError("queue_size must be at least 1")


@dataclass(slots=True, frozen=True)
class QueryConfig:
    """Query engine limits (spec 006 §5, spec 010 `query.*`)."""

    query_timeout_seconds: float = 3.0
    max_range_seconds: int = 21600
    max_groups: int = 500
    max_series_points: int = 1500
    query_mode: Literal["fanout", "colocated"] = "colocated"
    replica_registry: tuple[str, ...] = ()
    fanout_timeout_seconds: float = 1.5
    missing_heartbeat_threshold_seconds: int = 60

    def __post_init__(self) -> None:
        if self.query_timeout_seconds <= 0:
            raise ValueError("query_timeout_seconds must be positive")
        if self.max_range_seconds < 1:
            raise ValueError("max_range_seconds must be at least 1")
        if self.max_groups < 1:
            raise ValueError("max_groups must be at least 1")
        if self.max_series_points < 1:
            raise ValueError("max_series_points must be at least 1")
        if self.fanout_timeout_seconds <= 0:
            raise ValueError("fanout_timeout_seconds must be positive")
        if self.missing_heartbeat_threshold_seconds < 1:
            raise ValueError("missing_heartbeat_threshold_seconds must be at least 1")


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
# `backend.internalListen`, `store.warmupWindow`, `alerting.missingHeartbeatThreshold`
# and the UBS-85 keys of `ingest:`.
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


OSS_LLM_PROVIDERS: frozenset[str] = frozenset(
    {"openai-compatible", "ollama", "vllm"}
)
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_VLLM_BASE_URL = "http://127.0.0.1:8000/v1"
OSS_LLM_DEFAULT_TIMEOUT_SECONDS = 25.0
AZURE_LLM_DEFAULT_TIMEOUT_SECONDS = 2.0


@dataclass(slots=True, frozen=True)
class LlmConfig:
    provider: str = "openai-compatible"
    model: str = "llama3.2"
    base_url: str | None = DEFAULT_OLLAMA_BASE_URL
    deployment: str = "gpt-4o-mini"
    endpoint: str | None = None
    api_version: str = "2024-08-01-preview"
    timeout_seconds: float = OSS_LLM_DEFAULT_TIMEOUT_SECONDS
    max_retries: int = 1
    structured_output: bool = True
    require_api_key: bool = False

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise BackendConfigError("nl.llm.timeout must be > 0")
        if self.max_retries < 0:
            raise BackendConfigError("nl.llm.maxRetries must be >= 0")


def resolve_llm_config(
    config: LlmConfig, *, timeout_from_yaml: bool
) -> LlmConfig:
    """Apply provider-specific defaults after YAML merge."""
    provider = config.provider
    if provider not in OSS_LLM_PROVIDERS | {"azure-openai", "mock"}:
        raise BackendConfigError(f"unsupported nl.llm.provider {provider!r}")

    timeout = config.timeout_seconds
    if not timeout_from_yaml:
        if provider == "azure-openai":
            timeout = AZURE_LLM_DEFAULT_TIMEOUT_SECONDS
        elif provider in OSS_LLM_PROVIDERS:
            timeout = OSS_LLM_DEFAULT_TIMEOUT_SECONDS

    if provider in OSS_LLM_PROVIDERS:
        base_url = config.base_url
        if base_url is None:
            base_url = (
                DEFAULT_VLLM_BASE_URL
                if provider == "vllm"
                else DEFAULT_OLLAMA_BASE_URL
            )
        return replace(config, base_url=base_url, timeout_seconds=timeout)

    if provider == "azure-openai":
        return replace(config, timeout_seconds=timeout)

    return replace(config, timeout_seconds=timeout)


@dataclass(slots=True, frozen=True)
class NlConfig:
    enabled: bool = False
    max_question_chars: int = 500
    per_user_rate_limit_per_minute: int = 20
    default_timezone: str = "Asia/Singapore"
    default_time_range: str = "30m"
    llm: LlmConfig = field(default_factory=LlmConfig)

    def __post_init__(self) -> None:
        if self.max_question_chars < 1:
            raise BackendConfigError("nl.maxQuestionChars must be >= 1")
        if self.per_user_rate_limit_per_minute < 1:
            raise BackendConfigError("nl.perUserRateLimitPerMinute must be >= 1")


def ensure_nl_llm_credentials(config: NlConfig) -> None:
    if not config.enabled:
        return
    provider = config.llm.provider
    needs_key = provider == "azure-openai" or (
        provider in OSS_LLM_PROVIDERS and config.llm.require_api_key
    )
    if not needs_key:
        return
    if not os.environ.get("MAGIC_TELEMETRY_LLM_API_KEY"):
        raise BackendConfigError(
            "MAGIC_TELEMETRY_LLM_API_KEY is required when nl is enabled "
            f"with {provider} (NFR-SEC-004)"
        )


@dataclass(slots=True, frozen=True)
class IngestGuardConfig:
    """UBS-85: batch dedupe (FR-ING-004) and per-agent rate limiting
    (FR-ING-008). Defaults are spec 010's `ingest:` section."""

    max_batches_per_minute_per_agent: int = 30
    dedupe_cache_size: int = 10_000
    dedupe_ttl_seconds: float = 1800.0

    def __post_init__(self) -> None:
        if self.max_batches_per_minute_per_agent < 1:
            raise BackendConfigError("ingest.maxBatchesPerMinutePerAgent must be >= 1")
        if self.dedupe_cache_size < 1:
            raise BackendConfigError("ingest.dedupeCacheSize must be >= 1")
        if self.dedupe_ttl_seconds <= 0:
            raise BackendConfigError("ingest.dedupeTtl must be > 0")


@dataclass(slots=True, frozen=True)
class BackendHealthConfig:
    # FR-RUL-030 / spec 005: an agent with no heartbeat for this long is `missing`.
    missing_heartbeat_threshold_seconds: float = 60.0
    # FR-QRY-005: /readyz reports `warming` until this much data exists.
    warmup_window_seconds: float = 120.0
    # FR-HLT-012: public API vs internal-only listener (/healthz /readyz /metrics).
    listen: str = "0.0.0.0:8080"
    internal_listen: str = "127.0.0.1:8081"
    ingest: IngestGuardConfig = field(default_factory=IngestGuardConfig)

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


class _LlmYaml(_Lenient):
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    deployment: str | None = None
    endpoint: str | None = None
    api_version: str | None = None
    timeout: str | int | float | None = None
    max_retries: int | None = None
    structured_output: bool | None = None
    require_api_key: bool | None = None


class _NlYaml(_Lenient):
    enabled: bool | None = None
    max_question_chars: int | None = None
    per_user_rate_limit_per_minute: int | None = None
    default_timezone: str | None = None
    default_time_range: str | None = None
    llm: _LlmYaml | None = None


class _IngestYaml(_Lenient):
    # `maxBodyBytes` and `queueSize` live in this section too but are read
    # elsewhere (or not yet); `extra="allow"` keeps them legal.
    max_batches_per_minute_per_agent: int | None = None
    dedupe_cache_size: int | None = None
    dedupe_ttl: str | int | float | None = None


class _BackendConfigYaml(BaseModel):
    # Sibling sections (query:, nl:, ...) belong to other components.
    model_config = ConfigDict(extra="allow")

    backend: _BackendYaml | None = None
    store: _StoreYaml | None = None
    alerting: _AlertingYaml | None = None
    ingest: _IngestYaml | None = None
    nl: _NlYaml | None = None


def _drop_none(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


def _load_backend_yaml(path: Path | str | None) -> _BackendConfigYaml:
    if path is None:
        return _BackendConfigYaml()
    file = Path(path)
    if not file.exists():
        return _BackendConfigYaml()
    try:
        raw = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise BackendConfigError(f"{file}: invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise BackendConfigError(f"{file}: top level must be a mapping")
    try:
        return _BackendConfigYaml.model_validate(raw)
    except ValidationError as exc:
        raise BackendConfigError(f"{file}: {exc}") from exc


def load_nl_config(path: Path | str | None) -> NlConfig:
    parsed = _load_backend_yaml(path)
    nl = parsed.nl or _NlYaml()
    llm = nl.llm or _LlmYaml()
    timeout_from_yaml = llm.timeout is not None
    raw_llm = LlmConfig(
        **_drop_none(
            provider=llm.provider,
            model=llm.model,
            base_url=llm.base_url,
            deployment=llm.deployment,
            endpoint=llm.endpoint,
            api_version=llm.api_version,
            timeout_seconds=(
                parse_duration_seconds(llm.timeout)
                if llm.timeout is not None
                else None
            ),
            max_retries=llm.max_retries,
            structured_output=llm.structured_output,
            require_api_key=llm.require_api_key,
        )
    )
    return NlConfig(
        **_drop_none(
            enabled=nl.enabled,
            max_question_chars=nl.max_question_chars,
            per_user_rate_limit_per_minute=nl.per_user_rate_limit_per_minute,
            default_timezone=nl.default_timezone,
            default_time_range=nl.default_time_range,
            llm=resolve_llm_config(raw_llm, timeout_from_yaml=timeout_from_yaml),
        )
    )


def load_backend_health_config(path: Path | str | None) -> BackendHealthConfig:
    parsed = _load_backend_yaml(path)

    backend = parsed.backend or _BackendYaml()
    store = parsed.store or _StoreYaml()
    alerting = parsed.alerting or _AlertingYaml()
    ingest = parsed.ingest or _IngestYaml()
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
            ingest=IngestGuardConfig(
                **_drop_none(
                    max_batches_per_minute_per_agent=(
                        ingest.max_batches_per_minute_per_agent
                    ),
                    dedupe_cache_size=ingest.dedupe_cache_size,
                    dedupe_ttl_seconds=(
                        parse_duration_seconds(ingest.dedupe_ttl)
                        if ingest.dedupe_ttl is not None
                        else None
                    ),
                )
            ),
        )
    )
