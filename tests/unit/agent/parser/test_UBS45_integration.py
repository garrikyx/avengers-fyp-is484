"""Integration-style parser tests for UBS-45 enrich path."""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_agent.parser.corpus import demo_log_lines
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import SourceMeta


def _meta() -> SourceMeta:
    return SourceMeta(
        instance_id="test",
        path="reject_text.txt",
        log_type="fix",
        read_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
    )


def test_reject_text_maps_to_label() -> None:
    parser = FixParser(hash_key=b"test-key")
    line = (
        b"8=FIX.4.2|35=8|49=SENDER|56=TARGET|34=1|52=20260101-10:00:00|"
        b"150=8|39=8|103=3|58=Price exceeds limit for symbol ABC|10=000|"
    )
    result = parser.parse(line, _meta())
    assert result.telemetry is not None
    assert result.telemetry.reject_reason_label == "price_exceeds_limit"
    assert result.telemetry.effective_reject_reason == "OrderExceedsLimit"
    assert result.fields is not None
    assert result.fields.text is None


def test_seq_gap_from_corpus() -> None:
    parser = FixParser(hash_key=b"test-key")
    gaps = []
    for line, _ in demo_log_lines(source="seq_gap.txt"):
        result = parser.parse(line, _meta())
        if result.telemetry and result.telemetry.seq_gap:
            gaps.append(result.telemetry.seq_gap)
    assert len(gaps) == 1
    assert gaps[0].gap_size == 1
