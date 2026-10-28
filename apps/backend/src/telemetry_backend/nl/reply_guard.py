"""Guard for the LLM's conversational reply (FR-NLQ-030, FR-NLQ-009).

The reply is untrusted model output shown to the user. It may only be a short
pleasantry: anything with a digit could be a fabricated number, and links or markup
could be injected, so those replies are dropped for a templated one instead. A reply
must also steer back to telemetry: one that never mentions it (such as "I can help
with the weather") would promise something the bot cannot do.
"""

from __future__ import annotations

import re

MAX_REPLY_CHARS = 300

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")
_FORBIDDEN = re.compile(r"\d|https?:|www\.|[<>`\[\]{}|]", re.IGNORECASE)


def guard_reply(reply: str | None, *, application: str = "Magic") -> str | None:
    """The cleaned reply, or None when it must not be shown."""
    if reply is None:
        return None
    text = _WHITESPACE.sub(" ", _CONTROL_CHARS.sub(" ", reply)).strip()
    if not text or len(text) > MAX_REPLY_CHARS or _FORBIDDEN.search(text):
        return None
    lowered = text.lower()
    if "telemetry" not in lowered and application.lower() not in lowered:
        return None
    return text
