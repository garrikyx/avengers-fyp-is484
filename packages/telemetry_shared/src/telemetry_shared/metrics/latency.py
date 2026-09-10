"""Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004).

Shared by the agent (summarising its own per-window histogram) and the
backend (summarising a histogram already merged bucket-wise across every
contributing agent). Percentiles are always read off the histogram that was
merged, never averaged across per-agent percentiles.
"""

from __future__ import annotations

from collections.abc import Sequence

from telemetry_shared.metrics.histogram import DEFAULT_MIN_SAMPLE_SIZE, Histogram
from telemetry_shared.models.metrics import LatencySummary

DEFAULT_PERCENTILES: tuple[int, ...] = (50, 95, 99)


def build_latency_summary(
    histogram: Histogram,
    *,
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> LatencySummary:
    values = {
        p: histogram.percentile(p / 100, min_sample_size=min_sample_size)
        for p in percentiles
    }
    avg = float(histogram.sum_ms / histogram.count) if histogram.count > 0 else None
    p50, p95, p99 = values.get(50), values.get(95), values.get(99)
    return LatencySummary(
        p50=float(p50) if p50 is not None else None,
        p95=float(p95) if p95 is not None else None,
        p99=float(p99) if p99 is not None else None,
        avg=avg,
        count=histogram.count,
    )
