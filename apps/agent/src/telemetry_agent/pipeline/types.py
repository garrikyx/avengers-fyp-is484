from __future__ import annotations

from dataclasses import dataclass

from telemetry_agent.parser.protocol import ParseResult, SourceMeta


@dataclass(frozen=True, slots=True)
class QueuedLine:
    """One complete log line waiting for a parser worker."""

    line: bytes
    meta: SourceMeta
    parser_chain: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParsedEvent:
    """ParseResult plus the monitor metadata that produced it."""

    meta: SourceMeta
    result: ParseResult
    line: bytes = b""
