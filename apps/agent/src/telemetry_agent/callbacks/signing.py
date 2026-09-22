"""FR-CBK-005: request signing so Magic can verify a callback originated
from this agent.

Same HMAC primitives as `parser/fix/identifiers.py`, used differently: that
module truncates to 16 hex chars to hash a correlation ID; this one needs
the full HMAC-SHA256 digest, `v1=`-prefixed, so Magic can do a
constant-time comparison against the whole signature.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Mapping

_ENV_VAR = "MAGIC_TELEMETRY_CALLBACK_SECRET"


def sign(secret: bytes, timestamp: str, body: bytes) -> str:
    """`v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)."""
    message = timestamp.encode("utf-8") + b"." + body
    digest = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return f"v1={digest}"


def load_callback_secret(env: Mapping[str, str] | None = None) -> bytes:
    """Read the callback-signing secret from the environment (`NFR-SEC-004`).

    Raises RuntimeError if unset or empty rather than falling back to an
    insecure default — call once at process startup so a missing secret
    fails the process to start, not a per-callback signing attempt.
    """
    source = env if env is not None else os.environ
    value = source.get(_ENV_VAR, "")
    if not value:
        msg = f"{_ENV_VAR} is required but not set"
        raise RuntimeError(msg)
    return value.encode("utf-8")
