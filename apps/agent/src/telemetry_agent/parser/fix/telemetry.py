from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SeqGapEvent:
    session_key: str
    expected: int
    actual: int
    gap_size: int
    is_regression: bool


@dataclass(frozen=True, slots=True)
class FixTelemetry:
    """Sanitized telemetry derived from a framed FIX message."""

    normalized_msg_type: str | None = None
    normalized_exec_type: str | None = None
    normalized_ord_status: str | None = None
    normalized_ord_rej_reason: str | None = None
    normalized_session_reject_reason: str | None = None
    normalized_side: str | None = None
    normalized_ord_type: str | None = None
    reject_reason_label: str | None = None
    effective_reject_reason: str | None = None
    unknown_enums: tuple[str, ...] = ()
    unclassified_reject_text: bool = False
    event_time_utc: datetime | None = None
    time_source: str = "fix"
    bad_timestamp: bool = False
    clock_skew: bool = False
    unknown_msg_type: bool = False
    seq_gap: SeqGapEvent | None = None
