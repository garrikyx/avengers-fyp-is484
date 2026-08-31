"""FR-PRS-012–016 framing tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from telemetry_agent.parser.fix.frame import (
    DelimiterMode,
    FrameOptions,
    Framer,
    LineJoiner,
    SOH,
    frame_message,
)
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import LineClassification, SourceMeta

CORPUS = Path(__file__).resolve().parents[3] / "apps" / "agent" / "testdata" / "fix"


def test_FR_PRS_012_pipe_delimited_framing() -> None:
    line = b"8=FIX.4.2|35=D|49=SENDER|56=TARGET|10=000|"
    result = frame_message(line)
    assert result.ok
    assert result.message is not None
    assert result.message.fields["35"] == "D"
    assert result.message.delimiter == DelimiterMode.PIPE


def test_FR_PRS_012_soh_delimited_framing() -> None:
    line = SOH.join([b"8=FIX.4.2", b"35=8", b"49=SENDER", b"10=000"])
    result = frame_message(line)
    assert result.ok
    assert result.message is not None
    assert result.message.delimiter == DelimiterMode.SOH


def test_FR_PRS_013_strips_log_prefix() -> None:
    line = b"2026-01-01 INFO 8=FIX.4.2|35=8|49=SENDER|10=000|"
    result = frame_message(line)
    assert result.ok
    assert result.message is not None
    assert result.message.fields["35"] == "8"


def test_FR_PRS_014_joins_split_message_across_lines() -> None:
    framer = Framer(FrameOptions(max_join_lines=4))
    joiner = LineJoiner(framer, max_join_lines=4)
    line1 = b"8=FIX.4.2|35=D|49=SENDER|11=SPLIT1|55=GOOG|54=1"
    line2 = b"|38=10|40=2|10=000|"
    assert joiner.feed(line1) is None
    result = joiner.feed(line2)
    assert result is not None
    assert result.ok
    assert result.joined_lines == 2
    assert result.message is not None
    assert result.message.fields["35"] == "D"


def test_FR_PRS_014_exceeds_max_join_lines() -> None:
    framer = Framer(FrameOptions(max_join_lines=2))
    joiner = LineJoiner(framer, max_join_lines=2)
    line1 = b"8=FIX.4.2|35=D|49=SENDER"
    line2 = b"|11=PART2"
    joiner.feed(line1)
    result = joiner.feed(line2)
    assert result is not None
    assert not result.ok
    assert result.error_reason == "incomplete_message"


def test_FR_PRS_015_body_length_mismatch_is_soft_warning() -> None:
    line = b"8=FIX.4.2|9=5|35=D|49=SENDER|56=TARGET|10=000|"
    result = frame_message(line)
    assert result.ok
    assert "body_length_mismatch" in result.warnings


def test_FR_PRS_016_checksum_validation_off_by_default() -> None:
    line = b"8=FIX.4.2|35=D|49=SENDER|10=999|"
    result = frame_message(line, FrameOptions(validate_checksum=False))
    assert result.ok


def test_FR_PRS_016_checksum_mismatch_when_enabled() -> None:
    line = b"8=FIX.4.2|35=D|49=SENDER|10=999|"
    result = frame_message(line, FrameOptions(validate_checksum=True))
    assert not result.ok
    assert result.error_reason == "checksum_mismatch"


def test_FR_PRS_012_corpus_files_frame_without_errors() -> None:
    parser = FixParser()
    meta = SourceMeta(
        instance_id="test",
        path="corpus",
        log_type="fix",
        read_at=datetime.now(tz=UTC),
    )
    for name in ("pipe_delimited.txt", "log_prefix.txt", "soh_clean.txt", "delimiter_auto.txt"):
        path = CORPUS / name
        for raw in path.read_bytes().splitlines():
            if not raw.strip():
                continue
            result = parser.parse(raw, meta)
            assert result.classification == LineClassification.FIX, name
            assert result.framed, f"{name}: {raw!r}"
            assert result.error is None


@pytest.mark.parametrize(
    "garbage",
    [
        b"",
        b"\x00\xff\xfe",
        b"x" * 10_000,
        b"8=FIX.4.2|35=\x00|10=000|",
    ],
)
def test_FR_PRS_019_no_panic_on_garbage_bytes(garbage: bytes) -> None:
    parser = FixParser()
    meta = SourceMeta(
        instance_id="test",
        path="corpus",
        log_type="fix",
        read_at=datetime.now(tz=UTC),
    )
    result = parser.parse(garbage, meta)
    assert isinstance(result.classification, LineClassification)
