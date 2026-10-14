from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def session_id_for(sender: str | None, target: str | None) -> str:
    """The canonical `session_id` *dimension* value (`FR-MET-030`).

    Deliberately distinct from `SeqTracker.session_key` /
    `SessionHeartbeatTracker.session_key`, which are internal tracking keys:
    those carry a `:direction` suffix and fall back to `"?"`, because
    inbound and outbound are separate sequence/heartbeat streams. This is
    the label the aggregator groups by, so every session counter
    (`logouts`, `seq_gaps`, `clock_skew_events`, `heartbeat_timeouts`) must
    produce it identically — two formats would split one session into two
    rows of the shared dimension table, and `FixSessionDown` would read a
    logout and a heartbeat timeout as unrelated sessions.
    """
    return f"{sender or 'unknown'}->{target or 'unknown'}"


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
