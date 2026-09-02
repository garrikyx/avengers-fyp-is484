from __future__ import annotations

import pytest

from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import Confidence, LineClassification, ParseResult, SourceMeta
from telemetry_agent.parser.registry import Registry, get_parser, register_parser, registered_names


class StubParser:
    def __init__(self, parser_name: str, confidence: Confidence) -> None:
        self._name = parser_name
        self._confidence = confidence

    def name(self) -> str:
        return self._name

    def classify(self, line: bytes) -> Confidence:
        _ = line
        return self._confidence

    def parse(self, line: bytes, meta: SourceMeta) -> ParseResult:
        _ = line, meta
        return ParseResult(classification=LineClassification.UNSUPPORTED)


def test_FR_PRS_032_register_parser_at_import_time() -> None:
    assert "fix" in registered_names()
    parser = get_parser("fix")
    assert parser.name() == "fix"


def test_FR_PRS_032_duplicate_registration_raises() -> None:
    with pytest.raises(ValueError, match="already registered"):
        register_parser(FixParser())


def test_FR_PRS_031_chain_selects_first_high_confidence() -> None:
    parsers = {
        "applog": StubParser("applog", Confidence.HIGH),
        "fix": StubParser("fix", Confidence.HIGH),
    }
    registry = Registry(parsers)
    line = b"8=FIX.4.2|35=D|10=000|"
    selected, confidence = registry.select(["applog", "fix"], line)
    assert selected is not None
    assert selected.name() == "applog"
    assert confidence == Confidence.HIGH


def test_FR_PRS_031_skips_low_confidence_parser() -> None:
    parsers = {
        "applog": StubParser("applog", Confidence.NONE),
        "fix": StubParser("fix", Confidence.HIGH),
    }
    registry = Registry(parsers)
    line = b"8=FIX.4.2|35=D|10=000|"
    selected, confidence = registry.select(["applog", "fix"], line)
    assert selected is not None
    assert selected.name() == "fix"
    assert confidence == Confidence.HIGH


def test_FR_PRS_031_validate_chain_reports_unknown_parsers() -> None:
    registry = Registry({"fix": get_parser("fix")})
    unknown = registry.validate_chain(["fix", "magic-binary"])
    assert unknown == ["magic-binary"]


def test_FR_PRS_030_fix_parser_classify_high_for_fix_line() -> None:
    parser = FixParser()
    line = b"8=FIX.4.2|35=D|49=SENDER|10=000|"
    assert parser.classify(line) == Confidence.HIGH


def test_FR_PRS_030_fix_parser_classify_none_for_garbage() -> None:
    parser = FixParser()
    assert parser.classify(b"not fix") == Confidence.NONE
