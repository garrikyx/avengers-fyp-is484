"""Magic applog classification tests."""

from __future__ import annotations

from telemetry_agent.parser.fix.classify import classify_line, compile_app_log_patterns

_MAGIC_PATTERN = r"^\d{2}:\d{2}:\d{2}\.\d+ <\d+> \[[NWEIF]\]"


def test_FR_PRS_010_magic_venue_lines_classify_as_app_log() -> None:
    patterns = compile_app_log_patterns([_MAGIC_PATTERN])
    samples = [
        b"07:51:15.000114 <413013> [N] VS_788: VS <BSE|788@BSE|status Connecting",
        b"07:51:45.000090 <413020> [E] VS_788: timed out after 00:00:30",
        b"07:52:15.027292 <413010> [F] VS_788: GR connection disconnected",
    ]
    for line in samples:
        assert classify_line(line, app_log_patterns=patterns).name == "APP_LOG"
