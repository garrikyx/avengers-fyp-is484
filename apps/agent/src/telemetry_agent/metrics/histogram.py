"""Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012).

Agent-internal — plain dataclass, not a telemetry_shared contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

# Shared boundary set with spec 004 §3, milliseconds. Bucket "5" holds values
# in (1, 5], "+Inf" holds everything above 5000 — buckets are exclusive per
# value (each sample falls into exactly one), not cumulative.
BOUNDARIES_MS: tuple[int, ...] = (1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000)
OVERFLOW_BUCKET = "+Inf"

DEFAULT_MIN_SAMPLE_SIZE = 20


@dataclass(slots=True)
class Histogram:
    """Constant memory per series regardless of sample count (MA-03 AC)."""

    count: int = 0
    sum_ms: Decimal = field(default_factory=lambda: Decimal(0))
    min_ms: Decimal | None = None
    max_ms: Decimal | None = None
    buckets: dict[str, int] = field(
        default_factory=lambda: {str(b): 0 for b in (*BOUNDARIES_MS, OVERFLOW_BUCKET)}
    )

    def record(self, value_ms: Decimal) -> None:
        self.count += 1
        self.sum_ms += value_ms
        self.min_ms = value_ms if self.min_ms is None else min(self.min_ms, value_ms)
        self.max_ms = value_ms if self.max_ms is None else max(self.max_ms, value_ms)
        for boundary in BOUNDARIES_MS:
            if value_ms <= boundary:
                self.buckets[str(boundary)] += 1
                return
        self.buckets[OVERFLOW_BUCKET] += 1

    def merge(self, other: Histogram) -> None:
        """Bucket-wise addition (FR-ING-005) — used when a window snapshot
        combines several ring-buffer buckets' histograms for one series.
        """
        self.count += other.count
        self.sum_ms += other.sum_ms
        if other.min_ms is not None:
            self.min_ms = (
                other.min_ms if self.min_ms is None else min(self.min_ms, other.min_ms)
            )
        if other.max_ms is not None:
            self.max_ms = (
                other.max_ms if self.max_ms is None else max(self.max_ms, other.max_ms)
            )
        for key, value in other.buckets.items():
            self.buckets[key] = self.buckets.get(key, 0) + value

    def percentile(
        self, p: float, *, min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE
    ) -> Decimal | None:
        """Interpolated, approximate (FR-QRY-012). None below min_sample_size
        (FR-QRY-007) rather than a misleadingly precise number from too few
        samples.
        """
        if self.count < min_sample_size:
            return None

        target_rank = Decimal(str(p)) * self.count
        cumulative = 0
        lower_boundary = Decimal(0)
        for boundary in (*BOUNDARIES_MS, None):
            key = str(boundary) if boundary is not None else OVERFLOW_BUCKET
            bucket_count = self.buckets[key]
            upper_boundary = (
                Decimal(boundary)
                if boundary is not None
                else (self.max_ms or lower_boundary)
            )

            if cumulative + bucket_count >= target_rank:
                if bucket_count == 0:
                    return upper_boundary
                fraction = (target_rank - cumulative) / Decimal(bucket_count)
                return lower_boundary + fraction * (upper_boundary - lower_boundary)

            cumulative += bucket_count
            lower_boundary = upper_boundary

        return self.max_ms
