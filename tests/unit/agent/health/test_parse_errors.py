"""UBS-59: parse-error rolling count and rate in the Health Reporter."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from telemetry_agent.health.config import HealthThresholds
from telemetry_agent.health.heartbeat import heartbeat_json
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.parser.protocol import (
    LineClassification,
    ParseError,
    ParseResult,
    SourceMeta,
)
from telemetry_shared.models.health import FileReadHealth

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def ok() -> ParseResult:
    return ParseResult(classification=LineClassification.FIX, framed=True)


def bad(reason: str = "checksum_mismatch") -> ParseResult:
    return ParseResult(
        classification=LineClassification.FIX, error=ParseError(reason=reason)
    )


def make(**thresholds: float) -> tuple[HealthReporter, FakeClock]:
    clock = FakeClock()
    return HealthReporter(
        {}, thresholds=HealthThresholds(**thresholds), clock=clock
    ), clock


# --- FR-HLT-004: nothing measured => null, not 0 ---------------------------------


def test_parse_fields_are_none_until_a_producer_reports() -> None:
    reporter, _ = make()
    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))
    assert wire["parseErrorCountLast5Min"] is None
    assert reporter.snapshot().parse_error_rate is None


def test_clean_lines_give_zero_errors_and_zero_rate() -> None:
    reporter, _ = make()
    for _ in range(10):
        reporter.record_parse_result(ok())
    s = reporter.snapshot()
    assert (s.parse_error_count, s.lines_read, s.parse_error_rate) == (0, 10, 0.0)
    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))
    assert wire["parseErrorCountLast5Min"] == 0


# --- rolling count ---------------------------------------------------------------


def test_errors_counted_and_reported_in_heartbeat() -> None:
    reporter, _ = make()
    for r in (ok(), bad(), ok(), bad("line_truncated"), ok()):
        reporter.record_parse_result(r)
    assert reporter.snapshot().parse_error_count == 2
    wire = json.loads(heartbeat_json(reporter.build_heartbeat()))
    assert wire["parseErrorCountLast5Min"] == 2


def test_count_decays_as_window_slides() -> None:
    reporter, clock = make(rolling_window_seconds=300)
    reporter.record_parse_error()
    reporter.record_parse_error()
    clock.advance(200)
    reporter.record_parse_error()
    assert reporter.snapshot().parse_error_count == 3
    clock.advance(100)  # first two are now 300s old -> out
    assert reporter.snapshot().parse_error_count == 1
    clock.advance(200)
    s = reporter.snapshot()
    assert s.parse_error_count == 0
    assert s.parse_error_rate is None  # 0 lines in window: rate undefined, not 0


def test_window_is_configurable() -> None:
    reporter, clock = make(rolling_window_seconds=10)
    reporter.record_parse_error()
    clock.advance(9)
    assert reporter.snapshot().parse_error_count == 1
    clock.advance(1)
    assert reporter.snapshot().parse_error_count == 0


def test_record_lines_read_bulk_feeds_denominator_only() -> None:
    reporter, _ = make()
    reporter.record_lines_read(99)
    reporter.record_parse_error()
    s = reporter.snapshot()
    assert (s.parse_error_count, s.lines_read) == (1, 100)
    assert s.parse_error_rate == 0.01


# --- FR-HLT-002 rules (spec 011 s2: > 1% degraded, > 25% unhealthy) -------------


def test_rate_over_one_percent_is_degraded_with_reason() -> None:
    reporter, _ = make()
    reporter.record_lines_read(98)
    reporter.record_parse_error()
    reporter.record_parse_error()  # 2/100 = 2%
    hb = reporter.build_heartbeat()
    assert hb.status == "degraded"
    assert hb.status_reasons == [
        "parse error rate 2.0% (2/100 lines in last 300s) exceeds 1%"
    ]


def test_rate_over_25_percent_is_unhealthy() -> None:
    reporter, _ = make()
    reporter.record_lines_read(2)
    reporter.record_parse_error()  # 1/3 = 33%
    hb = reporter.build_heartbeat()
    assert hb.status == "unhealthy"
    assert hb.status_reasons[0].endswith("exceeds 25%")


def test_rate_exactly_at_threshold_is_not_a_breach() -> None:
    reporter, _ = make()
    reporter.record_lines_read(99)
    reporter.record_parse_error()  # exactly 1%
    assert reporter.build_heartbeat().status == "healthy"


def test_thresholds_are_configurable() -> None:
    reporter, _ = make(parse_error_rate_degraded=0.5, parse_error_rate_unhealthy=0.9)
    reporter.record_lines_read(2)
    reporter.record_parse_error()  # 33% - would be unhealthy on defaults
    assert reporter.build_heartbeat().status == "healthy"


def test_unhealthy_parse_rate_outranks_read_lag_and_keeps_both_reasons() -> None:
    reporter, _ = make()
    reporter.record_parse_error()  # 1/1 = 100%
    signals = reporter.snapshot()
    lagging = FileReadHealth(path="/l/fix.log", offset=1, read_lag_ms=9_000)
    signals = replace(signals, files={"Fix.log": lagging})
    status, reasons = reporter.derive_status(signals)
    assert status == "unhealthy"
    assert len(reasons) == 2
    assert reasons[0].startswith("parse error rate")
    assert reasons[1].startswith("Fix.log: read lag")


def test_recovery_returns_to_healthy_once_errors_age_out() -> None:
    reporter, clock = make(rolling_window_seconds=60)
    reporter.record_parse_error()
    assert reporter.build_heartbeat().status == "unhealthy"
    clock.advance(30)
    reporter.record_lines_read(100)  # storm is over, clean traffic resumes
    assert reporter.build_heartbeat().status == "healthy"  # 1/101 < 1%
    clock.advance(31)
    s = reporter.snapshot()
    assert (s.parse_error_count, s.lines_read) == (0, 100)


# --- definition of "parse error", pinned against the real FixParser -------------


def test_is_parse_error_matches_aggregator_convention() -> None:
    from telemetry_agent.health.reporter import is_parse_error
    from telemetry_agent.parser.fix.parser import FixParser

    parser = FixParser()
    meta = SourceMeta(instance_id="t", path="f", log_type="fix", read_at=T0)

    def parse(line: bytes) -> ParseResult:
        return parser.parse(line, meta)

    good = b"8=FIX.4.2|9=61|35=D|49=C|56=B|11=ORD-1|55=ABC|54=1|38=100|44=50.00|10=072|"
    unknown_type = b"8=FIX.4.2|9=61|35=ZZ|11=ORD-1|10=072|"
    assert is_parse_error(parse(good)) is False  # warnings only, not an error
    assert is_parse_error(parse(unknown_type)) is True  # telemetry.unknown_msg_type
    assert is_parse_error(parse(b"plain app log line")) is False  # unsupported
    # FR-PRS-018: the monitor flags an over-long line; the parser turns that
    # into a closed-set `line_truncated` error.
    truncated_meta = SourceMeta(
        instance_id="t", path="f", log_type="fix", read_at=T0, truncated=True
    )
    truncated = parser.parse(good, truncated_meta)
    assert truncated.error is not None and truncated.error.reason == "line_truncated"
    assert is_parse_error(truncated) is True
