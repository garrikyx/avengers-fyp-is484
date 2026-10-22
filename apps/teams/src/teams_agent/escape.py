"""Escaping for text placed in Adaptive Card TextBlocks (FR-NLQ-022).

Teams renders a Markdown subset in TextBlocks, so any backend- or user-derived
string is backslash-escaped before it is interpolated. Inline markup characters are
escaped everywhere; list markers only where they would start a list item.
"""

from __future__ import annotations

import re

_MARKDOWN_SPECIALS = frozenset("\\`*_~[]()<>#|&!")
_LIST_MARKER = re.compile(r"(?m)^([ \t]*)([-+]|\d+\.)(?=[ \t])")


def escape_card_text(value: object) -> str:
    escaped = "".join(
        f"\\{ch}" if ch in _MARKDOWN_SPECIALS else ch for ch in str(value)
    )
    return _LIST_MARKER.sub(_escape_list_marker, escaped)


def _escape_list_marker(match: re.Match[str]) -> str:
    indent, marker = match.groups()
    if marker.endswith("."):
        return f"{indent}{marker[:-1]}\\."
    return f"{indent}\\{marker}"
