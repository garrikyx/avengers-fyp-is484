"""Bridges the Parser Engine's `ParseResult` to the Metrics Aggregator's
contract type, `telemetry_shared.models.parsed_message.ParsedMessageEvent`.

Nothing upstream of this module builds a `ParsedMessageEvent` from parsed FIX
output today — every demo and test constructs one by hand instead (see
docs/plan/ma-epic-implementation-summary.md: "Nothing upstream of the agent's
own snapshot... is in scope" for the MA epic). This is that missing seam,
kept as a single pure function so both the CLI demo and the future
`pipeline/` worker (spec 002 §1.1) can call it without duplicating the
field-by-field translation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import ValidationError
from telemetry_shared.models.parsed_message import (
    EVENT_CLASS_BY_MSG_TYPE,
    ParsedMessageEvent,
)

from telemetry_agent.parser.fix.fields import FixFields
from telemetry_agent.parser.fix.telemetry import FixTelemetry
from telemetry_agent.parser.fix.timestamps import parse_fix_timestamp
from telemetry_agent.parser.protocol import LineClassification, ParseResult, SourceMeta

_UNSPECIFIED = "unspecified"


def build_parsed_message_event(
    result: ParseResult, meta: SourceMeta
) -> ParsedMessageEvent | None:
    """Construct the Metrics Aggregator's event from one framed FIX line.

    Returns None for anything the aggregator has nothing to count: non-FIX
    lines, unframed lines, and internal parser errors. A known-FIX line with
    an unrecognised msg_type still produces a base `ParsedMessageEvent`
    (msg_type outside `KNOWN_MSG_TYPES` becomes `unclassified_messages` on
    the aggregator side, per counters.derive_counters) — that is a valid,
    countable outcome, not a failure.
    """
    if (
        result.classification != LineClassification.FIX
        or not result.framed
        or result.internal_error
        or result.fields is None
        or result.telemetry is None
    ):
        return None

    fields = result.fields
    telemetry = result.telemetry
    msg_type = telemetry.normalized_msg_type or result.msg_type or "unspecified"
    event_class = EVENT_CLASS_BY_MSG_TYPE.get(msg_type, ParsedMessageEvent)

    kwargs: dict[str, Any] = {
        "event_time_utc": telemetry.event_time_utc or meta.read_at,
        "instance_id": meta.instance_id,
        "session_id": _session_id(fields),
        "msg_type": msg_type,
        "transact_time_utc": _parse_transact_time(fields, telemetry),
        "cl_ord_id_hash": fields.cl_ord_id_hash,
        "orig_cl_ord_id_hash": fields.orig_cl_ord_id_hash,
        "order_id_hash": fields.order_id_hash,
        "exec_id_hash": fields.exec_id_hash,
        "symbol": fields.symbol,
        "side": telemetry.normalized_side,
        "ord_type": telemetry.normalized_ord_type,
        "ord_status": telemetry.normalized_ord_status,
        "exec_type": telemetry.normalized_exec_type,
        "order_qty": _to_decimal(fields.order_qty),
        "last_qty": _to_decimal(fields.last_qty),
        "cum_qty": _to_decimal(fields.cum_qty),
        "leaves_qty": _to_decimal(fields.leaves_qty),
        # effective_reject_reason's own "unspecified" fallback would otherwise
        # double up with the aggregator's identical fallback
        # (default_resolve_reject_reason / ReasonNormalizer.resolve) — only
        # one side should own that default, so it is normalised back to None
        # here and left to the aggregator.
        "reject_reason_code": (
            None
            if telemetry.effective_reject_reason in (None, _UNSPECIFIED)
            else telemetry.effective_reject_reason
        ),
        # Raw tag 58 text never reaches this point (FR-PRS-022 strips it at
        # the parser boundary); reject_reason_code/effective_reject_reason
        # is the safe replacement, so this stays unset.
        "reject_reason_text": None,
    }

    try:
        return event_class(**kwargs)
    except ValidationError:
        # A malformed/partial message that fails the subclass's own required
        # fields (e.g. an ExecutionReport missing symbol) still has a valid,
        # countable base event — fall back rather than dropping it.
        return ParsedMessageEvent(**kwargs)


def derive_session_counters(telemetry: FixTelemetry) -> dict[str, Decimal]:
    """UBS-73: the session/parser-health counters (spec 004 §4.1) that
    `FixSessionDown`, `SeqGapDetected` and `ClockSkew` read.

    Separate from `counters.derive_counters` because these come off the
    parser's own `FixTelemetry`, not off the `ParsedMessageEvent` — the
    shared contract carries no seq-gap or clock-skew field, and shouldn't:
    they describe the FIX session's health, not the message's content. The
    caller merges both dicts into one `ingest_counters` call; the metric
    names are declared on `counters.SESSION_DIMS`.

    `heartbeat_timeouts` is not derived here. A timeout is the *absence* of
    a message, which no per-message function can observe — it belongs to
    the Health Reporter's periodic tick. `FixSessionDown` still fires on
    `logouts` alone, since `RuleEngine._read_counter_sum` defaults a
    missing `extra_counter` to 0.
    """
    counters: dict[str, Decimal] = {}

    if telemetry.normalized_msg_type == "Logout":
        counters["logouts"] = Decimal(1)
    elif telemetry.normalized_msg_type == "Logon":
        counters["logons"] = Decimal(1)

    if telemetry.clock_skew:
        counters["clock_skew_events"] = Decimal(1)

    if telemetry.seq_gap is not None:
        if telemetry.seq_gap.is_regression:
            # A sequence that went *backwards* is not a gap: SeqTracker
            # reports gap_size=0 for it, so counting it as seq_gaps would
            # trip SeqGapDetected (> 0) on a message that skipped nothing.
            counters["seq_regressions"] = Decimal(1)
        else:
            counters["seq_gaps"] = Decimal(1)
            counters["seq_gap_messages"] = Decimal(telemetry.seq_gap.gap_size)

    return counters


def derive_parser_counters(result: ParseResult) -> dict[str, Decimal]:
    """UBS-18: the two counters `ParseErrorRate` reads.

    `parse_error_rate` is `parse_errors / log_lines_read` (spec 004 §4.5), so
    these are a ratio's numerator and denominator and have to be counted
    together, on every line — including lines that produced no
    `ParsedMessageEvent` at all. That's why they carry `AGENT_DIMS` and go in
    through `MetricsAggregator.ingest_agent_counters`: a line that failed to
    parse has no event to read dimensions off.

    Only *hard* failures count as errors. `FixTelemetry.bad_timestamp` and
    `unknown_msg_type` are soft warnings on a line that otherwise parsed
    fine; `metrics/demo_sink.py` files them under its own `parse_errors:*`
    sub-keys, but folding them into this ratio would have `ParseErrorRate`
    firing on well-formed messages.
    """
    counters: dict[str, Decimal] = {"log_lines_read": Decimal(1)}
    if _parse_error_reason(result) is not None:
        counters["parse_errors"] = Decimal(1)
    return counters


def parser_counter_dims(result: ParseResult, *, instance_id: str) -> dict[str, str]:
    """Dimension values for `derive_parser_counters`' output.

    Supplies both `instance_id` (which `log_lines_read` declares) and
    `reason` (which `parse_errors` additionally declares, per spec 004 §4.3),
    so one mapping covers both metrics —
    `MetricsAggregator.ingest_agent_counters` picks the subset each metric
    actually declares.
    """
    return {
        "instance_id": instance_id,
        "reason": _parse_error_reason(result) or "none",
    }


def _parse_error_reason(result: ParseResult) -> str | None:
    """The closed-set reason this line failed to parse, or None if it
    didn't. `internal_error` is the parser defending itself against an
    unexpected exception (FR-PRS-019) — a failure with no closed-set reason
    of its own, so it gets its own label.
    """
    if result.error is not None:
        return result.error.reason
    if result.internal_error:
        return "internal_error"
    return None


def _session_id(fields: FixFields) -> str:
    sender = fields.sender_comp_id or "unknown"
    target = fields.target_comp_id or "unknown"
    return f"{sender}->{target}"


def _to_decimal(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def _parse_transact_time(
    fields: FixFields, telemetry: FixTelemetry
) -> datetime | None:
    if not fields.transact_time or telemetry.event_time_utc is None:
        return None
    ts = parse_fix_timestamp(fields.transact_time, wall=telemetry.event_time_utc)
    return None if ts.bad_timestamp else ts.event_time
