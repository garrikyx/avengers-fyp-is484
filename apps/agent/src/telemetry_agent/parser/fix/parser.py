"""FIX parser plugin (UBS-40 wiring for classify + frame)."""

from __future__ import annotations

from re import Pattern

from telemetry_agent.parser.fix.classify import classify_line, compile_app_log_patterns
from telemetry_agent.parser.fix.frame import FrameOptions, Framer, FrameResult, LineJoiner
from telemetry_agent.parser.protocol import (
    Confidence,
    LineClassification,
    ParseError,
    ParseResult,
    SourceMeta,
)
from telemetry_agent.parser.registry import register_parser


class FixParser:

    def __init__(
        self,
        *,
        frame_options: FrameOptions | None = None,
        app_log_patterns: list[str] | None = None,
    ) -> None:
        self._frame_options = frame_options or FrameOptions()
        self._app_log_patterns: list[Pattern[bytes]] = (
            compile_app_log_patterns(app_log_patterns) if app_log_patterns else []
        )
        self._framer = Framer(self._frame_options)
        self._joiner = LineJoiner(self._framer, self._frame_options.max_join_lines)

    def name(self) -> str:
        return "fix"

    def classify(self, line: bytes) -> Confidence:
        result = classify_line(line, app_log_patterns=self._app_log_patterns)
        if result == LineClassification.FIX:
            return Confidence.HIGH
        return Confidence.NONE

    def parse(self, line: bytes, meta: SourceMeta) -> ParseResult:
        _ = meta
        try:
            if self._joiner.has_pending:
                frame_result = self._joiner.feed(line)
                if frame_result is None:
                    return ParseResult(
                        classification=LineClassification.FIX,
                        framed=False,
                    )
                return _frame_to_parse_result(
                    frame_result,
                    joined_lines=frame_result.joined_lines,
                )

            classification = classify_line(line, app_log_patterns=self._app_log_patterns)
            if classification != LineClassification.FIX:
                return ParseResult(classification=classification)

            frame_result = self._joiner.feed(line)
            if frame_result is None:
                return ParseResult(
                    classification=LineClassification.FIX,
                    framed=False,
                )

            return _frame_to_parse_result(
                frame_result,
                joined_lines=frame_result.joined_lines,
            )
        except Exception as exc:
            return ParseResult(
                classification=LineClassification.FIX,
                error=ParseError(reason="internal_error", detail=type(exc).__name__),
            )


def _frame_to_parse_result(
    frame_result: FrameResult,
    *,
    joined_lines: int,
) -> ParseResult:
    if not frame_result.ok:
        return ParseResult(
            classification=LineClassification.FIX,
            framed=False,
            warnings=list(frame_result.warnings),
            error=ParseError(reason=frame_result.error_reason),
            joined_lines=joined_lines,
        )

    message = frame_result.message
    if message is None:
        return ParseResult(
            classification=LineClassification.FIX,
            framed=False,
            error=ParseError(reason="internal_error"),
        )

    return ParseResult(
        classification=LineClassification.FIX,
        framed=True,
        msg_type=message.fields.get("35", ""),
        delimiter=message.delimiter.value,
        warnings=list(frame_result.warnings),
        joined_lines=joined_lines,
    )

register_parser(FixParser())
