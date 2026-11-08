from __future__ import annotations

from telemetry_agent.parser.binary.classify import (
    DEFAULT_BINARY_DETECT_WINDOW,
    looks_like_magic_binary,
)
from telemetry_agent.parser.protocol import (
    Confidence,
    LineClassification,
    ParseResult,
    SourceMeta,
)


class MagicBinaryParser:
    """Parser plugin that recognises Magic binary frames (FR-PRS-030, UBS-50).

    Classification only. Framing and field decoding are UBS-51, so `parse()`
    reports the line as binary without extracting anything or echoing bytes.
    """

    def __init__(
        self,
        *,
        magic: bytes = b"",
        detect_window: int = DEFAULT_BINARY_DETECT_WINDOW,
    ) -> None:
        self._magic = magic
        self._detect_window = detect_window

    def name(self) -> str:
        return "magic-binary"

    def classify(self, line: bytes) -> Confidence:
        if looks_like_magic_binary(line, self._magic, window=self._detect_window):
            return Confidence.HIGH
        return Confidence.NONE

    def parse(self, line: bytes, meta: SourceMeta) -> ParseResult:
        return ParseResult(
            classification=LineClassification.BINARY,
            warnings=["binary_decoding_not_implemented"],
        )
