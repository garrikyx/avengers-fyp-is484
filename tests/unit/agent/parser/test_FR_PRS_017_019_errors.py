"""FR-PRS-017/018/019 validation and resilience tests."""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import LineClassification, SourceMeta


def _meta(**kwargs: object) -> SourceMeta:
    defaults = {
        "instance_id": "test",
        "path": "test.log",
        "log_type": "fix",
        "read_at": datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return SourceMeta(**defaults)  # type: ignore[arg-type]


def test_FR_PRS_017_unknown_msg_type_still_framed() -> None:
    parser = FixParser(hash_key=b"test-key")
    line = b"8=FIX.4.2|35=ZZ|49=SENDER|56=TARGET|34=1|52=20260101-10:00:00|10=000|"
    result = parser.parse(line, _meta())
    assert result.framed is True
    assert result.telemetry is not None
    assert result.telemetry.unknown_msg_type is True
    assert "unknown_msg_type" in result.warnings


def test_FR_PRS_018_line_truncated() -> None:
    parser = FixParser(hash_key=b"test-key")
    line = b"8=FIX.4.2|35=D|49=SENDER|56=TARGET|34=1|10=000|"
    result = parser.parse(line, _meta(truncated=True))
    assert result.error is not None
    assert result.error.reason == "line_truncated"


def test_FR_PRS_019_no_panic_on_arbitrary_bytes() -> None:
    parser = FixParser(hash_key=b"test-key")
    for i in range(200):
        payload = bytes([i % 256]) * (i % 64)
        result = parser.parse(payload, _meta())
        assert result.classification in (
            LineClassification.FIX,
            LineClassification.APP_LOG,
            LineClassification.UNSUPPORTED,
        )
