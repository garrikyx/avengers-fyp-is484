from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable


class Confidence(str, Enum):
    """How strongly a parser claims an input line."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LineClassification(str, Enum):
    """FR-PRS-010 classification outcome."""

    FIX = "fix"
    APP_LOG = "app_log"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class SourceMeta:
    """Metadata attached to each log line by the monitor."""

    instance_id: str
    path: str
    log_type: str
    read_at: datetime
    truncated: bool = False
    file_set: str = ""


@dataclass(frozen=True, slots=True)
class ParseError:
    """Closed-set parse failure (FR-PRS-018 subset for framing stage)."""

    reason: str
    detail: str = ""


@dataclass(slots=True)
class ParseResult:
    """Outcome of parsing one logical input unit."""

    classification: LineClassification
    framed: bool = False
    msg_type: str = ""
    delimiter: str = ""
    warnings: list[str] = field(default_factory=list)
    error: ParseError | None = None
    joined_lines: int = 1


@runtime_checkable
class Parser(Protocol):
    """FR-PRS-030: pluggable parser interface."""

    def name(self) -> str:
        """Configuration name, e.g. 'fix' or 'applog'."""

    def classify(self, line: bytes) -> Confidence:
        """Report whether this parser claims the input."""

    def parse(self, line: bytes, meta: SourceMeta) -> ParseResult:
        """Parse one line; must not raise and must not return raw input in fields."""
