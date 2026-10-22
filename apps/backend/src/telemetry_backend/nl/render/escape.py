"""Escape dynamic strings for rendered output (FR-NLQ-022)."""

from __future__ import annotations

import html


def escape_adaptive_card_text(value: str) -> str:
    """Escape text embedded in Adaptive Card TextBlock bodies."""
    return html.escape(value, quote=True)
