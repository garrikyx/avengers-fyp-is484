"""Identifier hashing (FR-PRS-021)."""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Mapping

_ENV_VAR = "MAGIC_TELEMETRY_ID_HASH_KEY"
_HASH_LENGTH = 16


def hash_identifier(raw: str, key: bytes) -> str:
    """HMAC-SHA256 of `raw` keyed with `key`, truncated to 16 hex chars."""
    digest = hmac.new(key, raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:_HASH_LENGTH]


def load_hash_key(env: Mapping[str, str] | None = None) -> bytes:
    """
    Read the identifier hash key from the environment (NFR-SEC-004).

    Raises RuntimeError if unset or empty rather than falling back to an
    insecure default — this MUST be called once at process startup so a
    missing secret fails the process to start, not a per-line parse.
    """
    source = env if env is not None else os.environ
    value = source.get(_ENV_VAR, "")
    if not value:
        msg = f"{_ENV_VAR} is required but not set"
        raise RuntimeError(msg)
    return value.encode("utf-8")
