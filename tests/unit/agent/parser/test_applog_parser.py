from __future__ import annotations

from datetime import UTC, datetime

from telemetry_agent.parser.applog.parser import AppLogParser
from telemetry_agent.parser.protocol import Confidence, LineClassification, SourceMeta

_MAGIC_PATTERN = r"^\d{2}:\d{2}:\d{2}\.\d+ <\d+> \[[NWEIF]+\]"
_SIGNATURES = [
    ("%_connection_disconnected", r"(\w+) connection disconnected"),
]


def _meta() -> SourceMeta:
    return SourceMeta(
        instance_id="demo",
        path="Application.log",
        log_type="app",
        read_at=datetime.now(tz=UTC),
    )


def test_applog_parser_classifies_and_parses_magic_line() -> None:
    parser = AppLogParser(
        app_log_patterns=[_MAGIC_PATTERN],
        error_signatures=_SIGNATURES,
    )
    line = b"07:52:15.027292 <413010> [F] VS_788: GR connection disconnected"

    assert parser.classify(line) == Confidence.HIGH

    result = parser.parse(line, _meta())
    assert result.classification == LineClassification.APP_LOG
    tel = result.app_log_telemetry
    assert tel is not None
    assert tel.timestamp == "07:52:15.027292"
    assert tel.thread_id == "413010"
    assert tel.level == "F"
    assert tel.component == "VS_788"
    assert tel.message == "GR connection disconnected"
    assert tel.error_signature == "gr_connection_disconnected"


def test_applog_parser_returns_none_confidence_for_fix_line() -> None:
    parser = AppLogParser(app_log_patterns=[_MAGIC_PATTERN])
    line = b"8=FIX.4.4|35=D|11=ORD-1|"

    assert parser.classify(line) == Confidence.NONE
