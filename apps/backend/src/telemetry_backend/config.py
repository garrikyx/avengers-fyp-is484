"""Backend stream-processing configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

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
