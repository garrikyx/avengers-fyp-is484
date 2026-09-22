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
