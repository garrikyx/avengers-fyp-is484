from __future__ import annotations

import re
from re import Pattern

from telemetry_agent.parser.applog.signatures import (
    SignatureMatcher,
    compile_signature_rules,
)
from telemetry_agent.parser.applog.telemetry import AppLogTelemetry
from telemetry_agent.parser.fix.classify import compile_app_log_patterns
from telemetry_agent.parser.protocol import (
    Confidence,
    LineClassification,
    ParseResult,
    SourceMeta,
)

_MAGIC_LINE = re.compile(
    rb"^(\d{2}:\d{2}:\d{2}\.\d+) <(\d+)> \[([NWEIF]+)\] ([^:]+): (.*)$"
)


class AppLogParser:
    """Parser plugin for configured application log patterns (Magic format)."""

    def __init__(
        self,
        *,
        app_log_patterns: list[str] | None = None,
        error_signatures: list[tuple[str, str]] | None = None,
        max_dynamic_signature_labels: int = 50,
    ) -> None:
        self._patterns: list[Pattern[bytes]] = (
            compile_app_log_patterns(app_log_patterns) if app_log_patterns else []
        )
        self._signature_matcher = SignatureMatcher(
            compile_signature_rules(error_signatures or []),
            max_dynamic_labels=max_dynamic_signature_labels,
        )

    def name(self) -> str:
        return "applog"

    def classify(self, line: bytes) -> Confidence:
        for pattern in self._patterns:
            if pattern.search(line):
                return Confidence.HIGH
        return Confidence.NONE

    def parse(self, line: bytes, meta: SourceMeta) -> ParseResult:
        telemetry = self._extract_fields(line)
        if telemetry is not None:
            signature = self._signature_matcher.match(line)
            if signature is not None:
                telemetry = AppLogTelemetry(
                    timestamp=telemetry.timestamp,
                    thread_id=telemetry.thread_id,
                    level=telemetry.level,
                    component=telemetry.component,
                    message=telemetry.message,
                    error_signature=signature,
                )
            return ParseResult(
                classification=LineClassification.APP_LOG,
                app_log_telemetry=telemetry,
            )

        return ParseResult(classification=LineClassification.APP_LOG)

    def _extract_fields(self, line: bytes) -> AppLogTelemetry | None:
        match = _MAGIC_LINE.match(line)
        if match is None:
            return None
        timestamp, thread_id, level, component, message = match.groups()
        return AppLogTelemetry(
            timestamp=timestamp.decode("ascii"),
            thread_id=thread_id.decode("ascii"),
            level=level.decode("ascii"),
            component=component.decode("ascii"),
            message=message.decode("utf-8", errors="replace"),
        )
