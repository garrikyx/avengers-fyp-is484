"""Metrics query request/response models (spec 007 §3)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.metrics import LatencySummary


class TimeRangeAbsolute(CamelModel):
    from_utc: datetime
    to_utc: datetime


class TimeRangeRelative(CamelModel):
    last: str = Field(min_length=2)


class QueryTimeRange(CamelModel):
    """Exactly one of absolute or relative bounds."""

    from_utc: datetime | None = None
    to_utc: datetime | None = None
    last: str | None = None

    @model_validator(mode="after")
    def exactly_one_form(self) -> QueryTimeRange:
        absolute = self.from_utc is not None or self.to_utc is not None
        relative = self.last is not None
        if absolute and relative:
            raise ValueError("timeRange must not mix absolute and relative forms.")
        if not absolute and not relative:
            raise ValueError("timeRange requires either fromUtc/toUtc or last.")
        if absolute and (self.from_utc is None or self.to_utc is None):
            raise ValueError("timeRange requires both fromUtc and toUtc.")
        return self


class MetricsQueryRequest(CamelModel):
    time_range: QueryTimeRange
    filters: dict[str, str | list[str]] = Field(default_factory=dict)
    group_by: list[str] = Field(default_factory=list, max_length=3)
    metrics: list[str] = Field(min_length=1)
    percentiles: dict[str, list[int]] | None = None
    top_k: int | None = Field(default=None, ge=1)
    series: bool = False
    step: Literal["10s", "1m", "5m"] = "1m"


class EffectiveTimeRange(CamelModel):
    from_utc: datetime
    to_utc: datetime


class QueryInterpretation(CamelModel):
    metrics: list[str]
    group_by: list[str]
    filters: dict[str, str | list[str]]
    clamped: list[str] = Field(default_factory=list)


class DataCompleteness(CamelModel):
    agents_expected: int = Field(ge=0, default=0)
    agents_reporting: int = Field(ge=0, default=0)
    stale_agents: list[str] = Field(default_factory=list)
    restarted_buckets: int = Field(ge=0, default=0)
    dropped_batches_reported: int = Field(ge=0, default=0)
    confidence: Literal["complete", "partial", "degraded"] = "complete"
    failed_peers: list[str] = Field(default_factory=list)


class SeriesPoint(CamelModel):
    ts_utc: datetime
    values: dict[str, int | float | None]


class QueryGroup(CamelModel):
    dimensions: dict[str, str] = Field(default_factory=dict)
    counters: dict[str, int | float] = Field(default_factory=dict)
    indicators: dict[str, float | None] = Field(default_factory=dict)
    points: list[SeriesPoint] | None = None


class MetricsQueryResponse(CamelModel):
    query_id: str
    evaluated_at_utc: datetime
    effective_time_range: EffectiveTimeRange
    interpretation: QueryInterpretation
    totals: dict[str, int | float | None] = Field(default_factory=dict)
    latency: dict[str, LatencySummary] = Field(default_factory=dict)
    groups: list[QueryGroup] = Field(default_factory=list)
    truncated: bool = False
    data_completeness: DataCompleteness
    partial: bool = False
    timed_out: bool = False
