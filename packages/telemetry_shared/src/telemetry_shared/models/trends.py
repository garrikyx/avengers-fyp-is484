"""Reject-reason trend request/response (UBS-27).

Compares each reject reason's occurrence count in the latest window with the
preceding window of equal length, so a rise is a like-for-like comparison.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from telemetry_shared.models._base import CamelModel

TrendDirection = Literal["emerging", "increasing", "steady", "decreasing"]


class RejectReasonTrendsRequest(CamelModel):
    # Relative length of each compared window, e.g. "15m" (`s`/`m`/`h`).
    window: str = Field(default="15m", min_length=2)
    # Relative increase that counts as a trend: 0.5 = more than +50%.
    threshold: float = Field(default=0.5, gt=0)
    # A reason needs at least this many occurrences in the latest window
    # before it can be called a trend; 1 -> 3 rejects is noise, not a cause.
    min_occurrences: int = Field(default=5, ge=1)
    filters: dict[str, str | list[str]] = Field(default_factory=dict)


class ReasonTrend(CamelModel):
    reject_reason: str
    current_count: int
    previous_count: int
    # (current - previous) / previous; None when previous is 0.
    change_ratio: float | None = None
    trend: TrendDirection


class RejectReasonTrendsResponse(CamelModel):
    evaluated_at_utc: datetime
    window: str
    threshold: float
    min_occurrences: int
    current_from_utc: datetime
    current_to_utc: datetime
    previous_from_utc: datetime
    previous_to_utc: datetime
    # False when the store does not yet cover the whole preceding window; no
    # reason is flagged then, because "up from nothing" would be an artefact.
    previous_window_complete: bool
    # Reasons that are `emerging` (absent before) or `increasing`, largest
    # rise first.
    increasing: list[ReasonTrend] = Field(default_factory=list)
    reasons: list[ReasonTrend] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
