"""Magic binary frame detection (FR-PRS-010, FR-PRS-011, FR-PRS-041)."""

from __future__ import annotations

from telemetry_agent.parser.fix.classify import classify_line
from telemetry_agent.parser.protocol import LineClassification

DEFAULT_BINARY_DETECT_WINDOW = 64


def looks_like_magic_binary(
    line: bytes,
    magic: bytes,
    *,
    window: int = DEFAULT_BINARY_DETECT_WINDOW,
) -> bool:
    """
    True when the configured magic prefix occurs within the first `window` bytes.

    Bounded substring search only, no regex (FR-PRS-011). An empty `magic`
    never claims anything: the real Magic prefix is TBD(vendor) until sanitised
    sample frames are available (FR-PRS-040). Lines FIX classification claims are
    never binary.
    """
    if not magic:
        return False
    head = line[:window]
    if magic not in head:
        return False
    return classify_line(head) != LineClassification.FIX
