"""Tests for parser/metrics_event.py — the ParseResult -> ParsedMessageEvent
bridge between the Parser Engine and the Metrics Aggregator.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import build_parsed_message_event
from telemetry_agent.parser.protocol import ParseResult, SourceMeta
from telemetry_shared.models.parsed_message import (
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)

_KEY = b"unit-test-key"


def _meta(**kwargs: object) -> SourceMeta:
    defaults: dict[str, object] = {
        "instance_id": "test-instance",
        "path": "test.log",
        "log_type": "fix",
        "read_at": datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return SourceMeta(**defaults)  # type: ignore[arg-type]


def _parse(
    line: bytes, *, hash_key: bytes | None = _KEY
) -> tuple[ParseResult, SourceMeta]:
    parser = FixParser(hash_key=hash_key)
    meta = _meta()
    return parser.parse(line, meta), meta


def test_non_fix_line_produces_no_event() -> None:
    result, meta = _parse(b"not a fix message at all")
    assert build_parsed_message_event(result, meta) is None


def test_unframed_fix_line_produces_no_event() -> None:
    result, meta = _parse(b"8=FIX.4.2|35=D|49=SENDER")  # no checksum, incomplete
    assert result.framed is False
    assert build_parsed_message_event(result, meta) is None


def test_new_order_single_maps_to_new_order_event_with_normalized_enums() -> None:
    line = (
        b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|"
        b"11=C1|55=AAPL|54=1|40=2|38=100|10=000|"
    )
    result, meta = _parse(line)
    event = build_parsed_message_event(result, meta)
    assert isinstance(event, NewOrderEvent)
    assert event.instance_id == meta.instance_id
    assert event.session_id == "MAGIC->EXCH1"
    assert event.symbol == "AAPL"
    # The parser's enum table (fix/enums.py) is the canonical casing; the
    # Metrics Aggregator's contract (counters/tests/demos) matches it.
    assert event.side == "Buy"
    assert event.ord_type == "Limit"
    assert event.order_qty == Decimal(100)
    assert event.cl_ord_id_hash is not None


def test_execution_report_reject_maps_reason_code() -> None:
    line = (
        b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|"
        b"11=C3|37=O3|17=E5|55=GOOG|54=2|150=8|39=8|103=3|10=000|"
    )
    result, meta = _parse(line)
    event = build_parsed_message_event(result, meta)
    assert isinstance(event, ExecutionReportEvent)
    assert event.exec_type == "Rejected"
    assert event.ord_status == "Rejected"
    assert event.reject_reason_code == "OrderExceedsLimit"


def test_unspecified_reject_reason_becomes_none_not_the_literal_string() -> None:
    """effective_reject_reason's own "unspecified" fallback must not leak
    into reject_reason_code — the aggregator's resolvers already own that
    same fallback (default_resolve_reject_reason / ReasonNormalizer), so
    only one side should produce the label.
    """
    line = (
        b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|"
        b"11=C9|37=O9|17=E9|55=AAPL|54=1|150=4|39=4|10=000|"  # Canceled, no reason
    )
    result, meta = _parse(line)
    event = build_parsed_message_event(result, meta)
    assert event is not None
    assert event.reject_reason_code is None


def test_malformed_message_falls_back_to_base_event_instead_of_raising() -> None:
    """A NewOrderSingle missing symbol/side/ord_type/order_qty fails
    NewOrderEvent's required fields — must degrade to the base
    ParsedMessageEvent (still countable as messages_total), not raise or
    disappear.
    """
    line = b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|11=C1|10=000|"
    result, meta = _parse(line)
    event = build_parsed_message_event(result, meta)
    assert type(event) is ParsedMessageEvent
    assert event.msg_type == "NewOrderSingle"


def test_unknown_msg_type_still_produces_base_event() -> None:
    line = b"8=FIX.4.2|35=ZZ|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|"
    result, meta = _parse(line)
    event = build_parsed_message_event(result, meta)
    assert type(event) is ParsedMessageEvent
    assert event.msg_type is not None and event.msg_type.startswith("unknown_")


def test_missing_hash_key_still_builds_event_without_correlation_ids() -> None:
    line = (
        b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|"
        b"11=C1|55=AAPL|54=1|40=2|38=100|10=000|"
    )
    result, meta = _parse(line, hash_key=None)
    event = build_parsed_message_event(result, meta)
    assert type(event) is ParsedMessageEvent  # NewOrderEvent requires cl_ord_id_hash
    assert event.cl_ord_id_hash is None


def test_missing_comp_ids_fall_back_to_unknown_session_id() -> None:
    line = b"8=FIX.4.2|35=0|34=1|52=20260101-10:00:00|10=000|"
    result, meta = _parse(line)
    event = build_parsed_message_event(result, meta)
    assert event is not None
    assert event.session_id == "unknown->unknown"
