"""Per-user NL question rate limit (UBS-135; FR-NLQ-021).

A sliding 60s window per caller key, same shape as the per-agent batch limit
in `ingest_guard`. The route answers a refusal with 429 and `Retry-After`.

State is per replica and in memory (ADR 0005).
"""

from __future__ import annotations

import math
import threading
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

Clock = Callable[[], datetime]

_RATE_WINDOW = timedelta(seconds=60)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class QuestionLimiter:
    def __init__(self, per_minute: int, clock: Clock | None = None) -> None:
        self._per_minute = per_minute
        self._clock = clock or _utc_now
        self._lock = threading.Lock()
        # key -> accepted question times inside the last minute, oldest first.
        self._asked: dict[str, deque[datetime]] = {}

    def acquire(self, key: str) -> int | None:
        """Record a question for `key`; return `Retry-After` seconds if refused."""
        now = self._clock()
        with self._lock:
            times = self._asked.setdefault(key, deque())
            while times and now - times[0] >= _RATE_WINDOW:
                times.popleft()
            if len(times) >= self._per_minute:
                wait = (times[0] + _RATE_WINDOW - now).total_seconds()
                return max(1, math.ceil(wait))
            times.append(now)
            return None
