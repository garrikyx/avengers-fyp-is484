from __future__ import annotations

from datetime import timedelta

from telemetry_agent.parser.fix.enums import (
    normalize_exec_type,
    normalize_msg_type,
    normalize_ord_rej_reason,
    normalize_ord_status,
    normalize_ord_type,
    normalize_session_reject_reason,
    normalize_side,
)
from telemetry_agent.parser.fix.fields import FixFields
from telemetry_agent.parser.fix.normalize import RejectPattern, match_reject_label
from telemetry_agent.parser.fix.rejection import effective_reject_reason
from telemetry_agent.parser.fix.seq_tracker import SeqTracker
from telemetry_agent.parser.fix.telemetry import FixTelemetry
from telemetry_agent.parser.fix.timestamps import parse_fix_timestamp
from telemetry_agent.parser.protocol import SourceMeta


def build_fix_telemetry(
    fields: FixFields,
    *,
    meta: SourceMeta,
    reject_patterns: list[RejectPattern],
    max_reject_labels: int,
    seen_reject_labels: set[str],
    seq_tracker: SeqTracker,
    max_clock_skew: timedelta = timedelta(minutes=5),
) -> FixTelemetry:
    unknown: list[str] = []

    msg_type, unk = normalize_msg_type(fields.msg_type)
    if unk:
        unknown.append(unk)

    exec_type, unk = normalize_exec_type(fields.exec_type)
    if unk:
        unknown.append(unk)

    ord_status, unk = normalize_ord_status(fields.ord_status)
    if unk:
        unknown.append(unk)

    ord_rej, unk = normalize_ord_rej_reason(fields.ord_rej_reason)
    if unk:
        unknown.append(unk)

    session_rej, unk = normalize_session_reject_reason(fields.session_reject_reason)
    if unk:
        unknown.append(unk)

    side, unk = normalize_side(fields.side)
    if unk:
        unknown.append(unk)

    ord_type_val, unk = normalize_ord_type(fields.ord_type)
    if unk:
        unknown.append(unk)

    reject_label, unclassified = match_reject_label(
        fields.text,
        reject_patterns,
        max_labels=max_reject_labels,
        seen_labels=seen_reject_labels,
    )

    ts_raw = fields.sending_time or fields.transact_time
    ts = parse_fix_timestamp(ts_raw, wall=meta.read_at, max_skew=max_clock_skew)

    seq_gap = seq_tracker.observe(
        msg_type=msg_type or fields.msg_type,
        seq_num=fields.seq_num,
        sender=fields.sender_comp_id,
        target=fields.target_comp_id,
    )

    eff_reject = effective_reject_reason(
        ord_rej_reason=ord_rej,
        reject_reason_label=reject_label,
        session_reject_reason=session_rej,
        msg_type=msg_type,
    )

    unknown_msg = msg_type is not None and msg_type.startswith("unknown_")

    return FixTelemetry(
        normalized_msg_type=msg_type,
        normalized_exec_type=exec_type,
        normalized_ord_status=ord_status,
        normalized_ord_rej_reason=ord_rej,
        normalized_session_reject_reason=session_rej,
        normalized_side=side,
        normalized_ord_type=ord_type_val,
        reject_reason_label=reject_label,
        effective_reject_reason=eff_reject,
        unknown_enums=tuple(unknown),
        unclassified_reject_text=unclassified,
        event_time_utc=ts.event_time,
        time_source=ts.time_source,
        bad_timestamp=ts.bad_timestamp,
        clock_skew=ts.clock_skew,
        unknown_msg_type=unknown_msg,
        seq_gap=seq_gap,
    )
