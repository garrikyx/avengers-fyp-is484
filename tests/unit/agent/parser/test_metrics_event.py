"""Tests for parser/metrics_event.py — the ParseResult -> ParsedMessageEvent
bridge between the Parser Engine and the Metrics Aggregator.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from telemetry_agent.metrics.counters import (
    AGENT_DIMS,
    COUNTER_DIMENSIONS,
    PARSE_ERROR_DIMS,
    SESSION_DIMS,
)
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import (
    build_parsed_message_event,
    derive_parser_counters,
    derive_session_counters,
    parser_counter_dims,
)
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


# --- UBS-73: derive_session_counters -------------------------------------
#
# SeqTracker is stateful *per FixParser instance*, so the sequence tests
# below must feed every line through one parser — a fresh parser per line
# treats each as "first message for this session" and never reports a gap.


def _session_counters(*lines: bytes, read_at: datetime | None = None) -> list[
    dict[str, Decimal]
]:
    parser = FixParser(hash_key=_KEY)
    meta = _meta(read_at=read_at) if read_at is not None else _meta()
    out: list[dict[str, Decimal]] = []
    for line in lines:
        result = parser.parse(line, meta)
        assert result.telemetry is not None
        out.append(derive_session_counters(result.telemetry))
    return out


def test_logout_derives_the_logouts_counter() -> None:
    line = b"8=FIX.4.2|35=5|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|"
    assert _session_counters(line) == [{"logouts": Decimal(1)}]


def test_logon_derives_the_logons_counter() -> None:
    line = b"8=FIX.4.2|35=A|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|"
    assert _session_counters(line) == [{"logons": Decimal(1)}]


def test_ordinary_order_derives_no_session_counters() -> None:
    line = (
        b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|"
        b"11=C1|55=AAPL|54=1|40=2|38=100|10=000|"
    )
    assert _session_counters(line) == [{}]


def test_sequence_gap_counts_the_gap_and_its_size() -> None:
    first = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|"
    jumped = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=5|52=20260101-10:00:00|10=000|"
    counters = _session_counters(first, jumped)
    # No gap can be reported on the first message of a session — there is
    # no previous sequence number to compare against.
    assert counters[0] == {}
    # Expected 2, got 5: one gap event covering three missing messages.
    assert counters[1] == {"seq_gaps": Decimal(1), "seq_gap_messages": Decimal(3)}


def test_sequence_regression_is_counted_separately_and_never_as_a_gap() -> None:
    """A backwards sequence carries gap_size=0, so counting it as seq_gaps
    would fire SeqGapDetected (> 0) on a message that skipped nothing.
    """
    first = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=5|52=20260101-10:00:00|10=000|"
    backwards = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=2|52=20260101-10:00:00|10=000|"
    counters = _session_counters(first, backwards)
    assert counters[1] == {"seq_regressions": Decimal(1)}
    assert "seq_gaps" not in counters[1]


def test_sending_time_beyond_max_skew_derives_clock_skew_events() -> None:
    # read_at is 10:00; SendingTime claims 12:00 — two hours past the
    # parser's default five-minute max_clock_skew.
    line = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=1|52=20260101-12:00:00|10=000|"
    assert _session_counters(line) == [{"clock_skew_events": Decimal(1)}]


def test_sending_time_within_max_skew_derives_nothing() -> None:
    line = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:30|10=000|"
    assert _session_counters(line) == [{}]


def test_every_derived_session_counter_is_declared_in_counter_dimensions() -> None:
    """A counter the aggregator has no dimension set for raises KeyError at
    ingest (FR-MET-030) — that must fail here, not in production.
    """
    lines = (
        b"8=FIX.4.2|35=A|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|",
        b"8=FIX.4.2|35=5|49=MAGIC|56=EXCH1|34=9|52=20260101-12:00:00|10=000|",
        b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=3|52=20260101-10:00:00|10=000|",
    )
    produced = {name for counters in _session_counters(*lines) for name in counters}
    # The three lines between them cover logon, logout, gap, gap size,
    # regression and skew — i.e. every branch derive_session_counters has.
    assert produced == {
        "logons",
        "logouts",
        "seq_gaps",
        "seq_gap_messages",
        "seq_regressions",
        "clock_skew_events",
    }
    assert produced <= set(COUNTER_DIMENSIONS)
    assert all(COUNTER_DIMENSIONS[name] == SESSION_DIMS for name in produced)


# --- UBS-18: derive_parser_counters ---------------------------------------


def _parser_counters(*lines: bytes) -> list[dict[str, Decimal]]:
    parser = FixParser(hash_key=_KEY)
    meta = _meta()
    return [derive_parser_counters(parser.parse(line, meta)) for line in lines]


def test_every_line_counts_toward_log_lines_read() -> None:
    """It is `parse_error_rate`'s denominator, so it must count lines the
    parser rejected, ignored, or never understood — not just the ones that
    became events.
    """
    counters = _parser_counters(
        b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|",
        b"2026-01-01 10:00:00 [INFO] [CoreEngine] Heartbeat active.",
        b"\x00\xff\xfe not a log line at all",
    )
    assert [c["log_lines_read"] for c in counters] == [Decimal(1)] * 3


def test_a_clean_fix_line_is_not_a_parse_error() -> None:
    line = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|"
    assert _parser_counters(line) == [{"log_lines_read": Decimal(1)}]


def test_unframeable_line_counts_a_parse_error_once_the_joiner_gives_up() -> None:
    """A FIX-looking line with no checksum is held as a possible
    continuation first (`LineJoiner`, max_join_lines=4) and only reported as
    `incomplete_message` when the joiner stops waiting. So a burst of N bad
    lines yields N//4 errors, not N — the rate reflects give-ups, not
    optimistic buffering.
    """
    bad = b"8=FIX.4.2|35=D|49=SENDER|56=T|34=2"
    counters = _parser_counters(*([bad] * 8))
    errors = [c for c in counters if "parse_errors" in c]
    assert len(errors) == 2
    assert all(c["parse_errors"] == Decimal(1) for c in errors)


@pytest.mark.parametrize(
    "line,why",
    [
        (
            b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=1|52=NOTATIME|10=000|",
            "bad_timestamp",
        ),
        (
            b"8=FIX.4.2|35=ZZ|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|",
            "unknown_msg_type",
        ),
    ],
)
def test_soft_warnings_are_not_counted_as_parse_errors(line: bytes, why: str) -> None:
    """`demo_sink.py` files these under its own `parse_errors:*` keys, which
    reads like precedent — but the line parsed. Folding them into the ratio
    would have ParseErrorRate firing on well-formed messages.
    """
    assert "parse_errors" not in _parser_counters(line)[0], why


def test_parser_counter_dims_cover_both_metrics_declared_dimensions() -> None:
    parser = FixParser(hash_key=_KEY)
    meta = _meta()
    bad = b"8=FIX.4.2|35=D|49=SENDER|56=T|34=2"
    for _ in range(3):
        parser.parse(bad, meta)
    dims = parser_counter_dims(parser.parse(bad, meta), instance_id="magic-prod-01")

    assert dims["reason"] == "incomplete_message"
    # One mapping has to satisfy both metrics: log_lines_read declares only
    # instance_id, parse_errors additionally declares reason (spec 004 §4.3).
    for metric in ("log_lines_read", "parse_errors"):
        assert set(COUNTER_DIMENSIONS[metric]) <= set(dims)
    assert COUNTER_DIMENSIONS["parse_errors"] == PARSE_ERROR_DIMS
    assert COUNTER_DIMENSIONS["log_lines_read"] == AGENT_DIMS


def test_clean_line_reports_no_reason() -> None:
    parser = FixParser(hash_key=_KEY)
    good = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|"
    dims = parser_counter_dims(parser.parse(good, _meta()), instance_id="i")
    assert dims["reason"] == "none"
