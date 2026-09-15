"""Lightweight in-process counters for callback self-observability
(`FR-CBK-009`): delivery outcomes, failures. Not the FIX business metrics
in `metrics/counters.py` — this is the dispatcher's own health surface.
"""

from __future__ import annotations

import threading


class CounterRegistry:
    """Plain dict of named counters behind a lock — increments happen from
    both async worker tasks and sync call sites, so a `threading.Lock`
    (not an `asyncio.Lock`) is correct here.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counters)
