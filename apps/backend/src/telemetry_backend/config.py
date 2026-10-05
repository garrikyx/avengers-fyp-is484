"""Backend stream-processing configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

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
