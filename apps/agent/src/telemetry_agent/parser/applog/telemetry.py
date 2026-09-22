from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppLogTelemetry:
    """Structured fields extracted from Magic-style application log lines."""

    timestamp: str
    thread_id: str
    level: str
    component: str
    message: str
    error_signature: str | None = None
