"""FR-PRS-010/011/031/041/046: Magic binary frame classification (UBS-50).

All fixtures are synthetic: `MAGIC` is an invented prefix, not the real Magic
frame header (TBD(vendor), FR-PRS-040).
"""

from datetime import UTC, datetime

import pytest
from telemetry_agent.metrics.demo_sink import DemoMetricsSink
from telemetry_agent.parser.binary.classify import looks_like_magic_binary
from telemetry_agent.parser.binary.parser import MagicBinaryParser
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import (
    Confidence,
    LineClassification,
    SourceMeta,
)
from telemetry_agent.parser.registry import Registry

MAGIC = bytes.fromhex("4d414731")
FRAME = MAGIC + b"\x01\x00\x10" + b"\x00" * 13
FIX_LINE = (
    b"2024-01-01 10:00:00.000 "
    b"8=FIX.4.2|9=000|35=D|49=SESS|56=CL|34=1|52=20240101-10:00:00|"
    b"11=ORD-1|55=IBM|54=1|38=100|40=2|10=000|"
)


def _meta() -> SourceMeta:
    return SourceMeta(
        instance_id="demo",
        path="/tmp/Magic.bin",
        log_type="binary",
        read_at=datetime.now(tz=UTC),
    )


def test_frame_at_line_start_is_high_confidence() -> None:
    assert MagicBinaryParser(magic=MAGIC).classify(FRAME) == Confidence.HIGH


def test_frame_after_text_prefix_inside_window_is_recognised() -> None:
    line = b"10:00:00.000 <1> " + FRAME
    assert looks_like_magic_binary(line, MAGIC, window=64)


def test_magic_beyond_the_window_is_not_claimed() -> None:
    line = b"x" * 64 + FRAME
    assert not looks_like_magic_binary(line, MAGIC, window=64)
    assert looks_like_magic_binary(line, MAGIC, window=128)


def test_fix_line_is_not_claimed_even_if_it_contains_the_magic() -> None:
    parser = MagicBinaryParser(magic=b"8=FIX")
    assert parser.classify(FIX_LINE) == Confidence.NONE


def test_fix_text_line_is_not_claimed() -> None:
    assert MagicBinaryParser(magic=MAGIC).classify(FIX_LINE) == Confidence.NONE


@pytest.mark.parametrize(
    "line",
    [b"", b"hello world", bytes(range(32)), b"\xff\xfe\x00\x01" * 8],
)
def test_garbage_is_not_claimed(line: bytes) -> None:
    assert MagicBinaryParser(magic=MAGIC).classify(line) == Confidence.NONE


def test_empty_magic_never_claims_anything() -> None:
    parser = MagicBinaryParser()
    assert parser.classify(FRAME) == Confidence.NONE
    assert parser.classify(b"") == Confidence.NONE


def test_parse_reports_binary_without_echoing_bytes() -> None:
    result = MagicBinaryParser(magic=MAGIC).parse(FRAME, _meta())

    assert result.classification == LineClassification.BINARY
    assert not result.framed
    assert result.fields is None
    assert result.telemetry is None
    assert all(MAGIC.hex() not in w for w in result.warnings)


def test_chain_order_decides_the_winner() -> None:
    registry = Registry(
        parsers={
            "fix": FixParser(hash_key=b"test-key"),
            "magic-binary": MagicBinaryParser(magic=MAGIC),
        }
    )
    chain = ["fix", "magic-binary"]

    parser, _ = registry.select(chain, FRAME)
    assert parser is not None and parser.name() == "magic-binary"

    parser, _ = registry.select(chain, FIX_LINE)
    assert parser is not None and parser.name() == "fix"

    parser, _ = registry.select(chain, b"garbage")
    assert parser is None


def test_binary_lines_are_counted_separately_from_unsupported() -> None:
    sink = DemoMetricsSink()
    result = MagicBinaryParser(magic=MAGIC).parse(FRAME, _meta())

    sink.record_parse_result(result)

    assert sink.counters["binary_lines"] == 1
    assert sink.counters["unsupported_lines"] == 0
