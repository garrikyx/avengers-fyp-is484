"""Stream Processor / Metric Store configuration (spec 006 §3, §4; spec 010).

Only the settings this stage of the backend needs. Loading these from YAML +
env overrides (spec 010's full configuration system) is a separate concern;
this is the typed settings object that system will eventually populate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
