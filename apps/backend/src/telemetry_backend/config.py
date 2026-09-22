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
