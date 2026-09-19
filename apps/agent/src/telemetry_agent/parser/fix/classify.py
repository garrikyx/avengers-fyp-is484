"""Line classification (FR-PRS-010, FR-PRS-011)."""

from __future__ import annotations

import re
from re import Pattern

from telemetry_agent.parser.protocol import LineClassification

_FIX_BEGIN = (b"8=FIX", b"8=FIXT")
_FIELD_DELIMITERS = (b"\x01", b"|", b";", b"^A")
_DEFAULT_WINDOW = 256


def classify_line(
    line: bytes,
    *,
    fix_detect_window: int = _DEFAULT_WINDOW,
    app_log_patterns: list[Pattern[bytes]] | None = None,
) -> LineClassification:
    """
    Classify a log line before parsing (FR-PRS-010).

    Order: fix → app_log → unsupported. Uses substring search on the hot path;
    regex only for configured app_log patterns (FR-PRS-011).
    """
    window = line[:fix_detect_window]
    if _looks_like_fix(window):
        return LineClassification.FIX

    if app_log_patterns:
        for pattern in app_log_patterns:
            if pattern.search(line):
                return LineClassification.APP_LOG

    return LineClassification.UNSUPPORTED


def _looks_like_fix(window: bytes) -> bool:
    """
    True when 8=FIX/8=FIXT is followed by a delimiter and 35= within the window.

    FR-PRS-010 requires a delimiter between the begin string and MsgType tag.
    """
    fix_start = -1
    for token in _FIX_BEGIN:
        idx = window.find(token)
        if idx >= 0 and (fix_start < 0 or idx < fix_start):
            fix_start = idx

    if fix_start < 0:
        return False

    msg_type_idx = window.find(b"35=", fix_start)
    if msg_type_idx < 0:
        return False

    between = window[fix_start:msg_type_idx]
    return any(delim in between for delim in _FIELD_DELIMITERS)


def compile_app_log_patterns(patterns: list[str]) -> list[Pattern[bytes]]:
    """Compile configured app-log regexes for use after FIX detection fails."""
    return [re.compile(pat.encode("utf-8")) for pat in patterns]
