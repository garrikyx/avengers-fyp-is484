"""FR-PRS-010 / FR-PRS-011 classification tests."""

from __future__ import annotations

import re

from telemetry_agent.parser.fix.classify import classify_line, compile_app_log_patterns
from telemetry_agent.parser.protocol import LineClassification


def test_FR_PRS_010_fix_detected_pipe_delimited() -> None:
    line = b"8=FIX.4.2|35=D|49=SENDER|10=000|"
    assert classify_line(line) == LineClassification.FIX


def test_FR_PRS_010_fix_detected_soh_delimited() -> None:
    soh = b"\x01"
    line = soh.join([b"8=FIX.4.2", b"35=8", b"49=SENDER", b"10=000"])
    assert classify_line(line) == LineClassification.FIX


def test_FR_PRS_010_fix_detected_with_log_prefix() -> None:
    line = b"2026-01-01 INFO 8=FIX.4.2|35=D|49=X|10=000|"
    assert classify_line(line) == LineClassification.FIX


def test_FR_PRS_010_rejects_begin_string_without_delimiter_before_msg_type() -> None:
    line = b"8=FIX.4.2 junk 35=D"
    assert classify_line(line) == LineClassification.UNSUPPORTED


def test_FR_PRS_010_unsupported_garbage() -> None:
    assert classify_line(b"not a fix line") == LineClassification.UNSUPPORTED


def test_FR_PRS_011_app_log_regex_only_after_fix_fails() -> None:
    patterns = compile_app_log_patterns([r"ERROR \[Magic\]"])
    line = b"2026-01-01 ERROR [Magic] timeout"
    assert classify_line(line, app_log_patterns=patterns) == LineClassification.APP_LOG


def test_FR_PRS_011_fix_takes_priority_over_app_log_pattern() -> None:
    patterns = compile_app_log_patterns([r"ERROR"])
    line = b"ERROR 8=FIX.4.2|35=D|10=000|"
    assert classify_line(line, app_log_patterns=patterns) == LineClassification.FIX


def test_FR_PRS_010_respects_fix_detect_window() -> None:
    padding = b"x" * 300
    line = padding + b"8=FIX.4.2|35=D|10=000|"
    assert classify_line(line, fix_detect_window=256) == LineClassification.UNSUPPORTED


def test_FR_PRS_011_no_regex_on_fix_hot_path() -> None:
    """FIX detection uses substring search only — never app_log regex."""
    called: list[bool] = []

    class CountingPattern:
        def search(self, _line: bytes) -> re.Match[bytes] | None:
            called.append(True)
            return None

    line = b"8=FIX.4.2|35=D|49=SENDER|10=000|"
    classify_line(line, app_log_patterns=[CountingPattern()])  # type: ignore[list-item]
    assert called == []
