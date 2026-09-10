"""Shared contract: one agent metric snapshot on the wire (spec 004 §3,
`FR-MET-024`..`FR-MET-028`).

This is the Stream Processor's input (spec 006 §3): one completed bucket's
counter deltas, histograms and gauges for one `(agentId, instanceId)` pair.
Counters are deltas for that bucket, never cumulative totals — this is what
makes cross-agent, cross-bucket merge a plain sum (`FR-ING-005`).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from telemetry_shared.metrics.histogram import Histogram
from telemetry_shared.models._base import CamelModel


class HistogramPayload(CamelModel):
    """Wire shape of one histogram (`FR-MET-025`/`FR-MET-026`): fixed
    boundaries shared with `telemetry_shared.metrics.histogram.Histogram`,
    plus the exact `sum`/`min`/`max` that make averages and extremes exact
    even though percentiles are interpolated and approximate.
    """

    count: int
    sum: Decimal
    min: Decimal | None = None
    max: Decimal | None = None
    buckets: dict[str, int]

    def to_histogram(self) -> Histogram:
        """Reconstruct a mergeable `Histogram`, keyed on the canonical
        boundary set rather than trusting whatever keys the payload sent —
        an unrecognised key from a future/foreign schema version is dropped
        rather than silently corrupting percentile interpolation.
        """
        histogram = Histogram(count=self.count, sum_ms=self.sum)
        histogram.min_ms = self.min
        histogram.max_ms = self.max
        for boundary in histogram.buckets:
            histogram.buckets[boundary] = self.buckets.get(boundary, 0)
        return histogram


class SeriesEntry(CamelModel):
    """One dimension-set's counters and histograms within a snapshot. All
    counters and histograms in one entry share the same `dimensions`
    (spec 004 §3's own shape) — unlike the agent's internal per-metric
    dimension table (FR-MET-030), the wire format has already flattened
    that down to one dict per series.
    """

    dimensions: dict[str, str] = {}
    counters: dict[str, Decimal] = {}
    histograms: dict[str, HistogramPayload] = {}


class Snapshot(CamelModel):
    """One completed `bucketSeconds`-wide bucket from one agent
    (`FR-MET-024`). `restarted` marks the first snapshot after an agent
    restart (`FR-LOG-021`) so the backend can annotate — never silently
    absorb — the possible duplication from re-reading a checkpoint.
    """

    schema_version: int
    agent_id: str
    application: str
    instance_id: str
    bucket_start_utc: datetime
    bucket_seconds: int
    restarted: bool = False
    series: list[SeriesEntry] = []
    gauges: dict[str, float] = {}
