"""UBS-104: lightweight in-process counters, shared between the Callback
Dispatcher (`FR-CBK-009`) and the Backend Publisher's own self-observability
counters (`publish.rejected`, `publish.halted`, etc.).

Moved here verbatim from `callbacks/self_metrics.py` (which now just
re-exports it) once the Publisher needed the identical counter registry --
no behavior change, see that module for the shim.
"""

from __future__ import annotations

import threading


class CounterRegistry:
    """Plain dict of named counters behind a lock -- increments happen from
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
