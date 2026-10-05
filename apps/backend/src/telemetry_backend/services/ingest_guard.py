"""Batch dedupe and per-agent rate limiting (UBS-85; FR-ING-004, FR-ING-008).

Agents retry a batch with the same `batchId` after a timeout or a 5xx
(FR-PUB-003), so a batch the backend already accepted can arrive again.
The guard answers each `POST /telemetry/batch` with one of three verdicts:

- `Duplicate`: this agent's `batchId` was accepted within `dedupeTtl`.
  The route answers 202 with `duplicate: true` and does not enqueue it again.
- `RateLimited`: the agent already had `maxBatchesPerMinutePerAgent`
  batches accepted in the last 60s. The route answers 429 with `Retry-After`.
- `Accept`: go ahead and enqueue.

Dedupe is checked first, so an agent re-sending a batch we already hold
never spends rate-limit quota on it.

`check()` does not record anything; `commit()` does, and the route calls it
only after the batch is actually on the ingest queue. A batch refused with
503 `queue_full` therefore isn't remembered, and the agent's retry of it is
accepted instead of being treated as a duplicate of data we never kept.

State is per replica and in memory (ADR 0005). With several replicas,
dedupe is best-effort across them; consistent-hash routing on the agent
(spec 001) keeps one agent on one replica in the normal case.
"""

from __future__ import annotations

import math
import threading
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from telemetry_backend.config import IngestGuardConfig

Clock = Callable[[], datetime]

_RATE_WINDOW = timedelta(seconds=60)


@dataclass(slots=True, frozen=True)
class Accept:
    pass


@dataclass(slots=True, frozen=True)
class Duplicate:
    pass


@dataclass(slots=True, frozen=True)
class RateLimited:
    retry_after_seconds: int


Verdict = Accept | Duplicate | RateLimited


def _utc_now() -> datetime:
    return datetime.now(UTC)


class IngestGuard:
    def __init__(
        self, config: IngestGuardConfig | None = None, clock: Clock | None = None
    ) -> None:
        self._config = config or IngestGuardConfig()
        self._clock = clock or _utc_now
        self._ttl = timedelta(seconds=self._config.dedupe_ttl_seconds)
        self._lock = threading.Lock()
        # agent_id -> batch_id -> accepted_at, oldest first (LRU order).
        self._seen: dict[str, OrderedDict[str, datetime]] = {}
        # agent_id -> accept times inside the last minute, oldest first.
        self._accepted: dict[str, deque[datetime]] = {}

    def check(self, agent_id: str, batch_id: str) -> Verdict:
        now = self._clock()
        with self._lock:
            seen = self._seen.get(agent_id)
            if seen is not None:
                self._expire(seen, now)
                if batch_id in seen:
                    return Duplicate()
            times = self._accepted.get(agent_id)
            if times is not None:
                self._slide(times, now)
                if len(times) >= self._config.max_batches_per_minute_per_agent:
                    wait = (times[0] + _RATE_WINDOW - now).total_seconds()
                    return RateLimited(retry_after_seconds=max(1, math.ceil(wait)))
            return Accept()

    def commit(self, agent_id: str, batch_id: str) -> None:
        """Record a batch that is now on the ingest queue."""
        now = self._clock()
        with self._lock:
            seen = self._seen.setdefault(agent_id, OrderedDict())
            seen[batch_id] = now
            seen.move_to_end(batch_id)
            while len(seen) > self._config.dedupe_cache_size:
                seen.popitem(last=False)
            times = self._accepted.setdefault(agent_id, deque())
            self._slide(times, now)
            times.append(now)

    def _expire(self, seen: OrderedDict[str, datetime], now: datetime) -> None:
        while seen:
            oldest_id, accepted_at = next(iter(seen.items()))
            if now - accepted_at < self._ttl:
                return
            del seen[oldest_id]

    @staticmethod
    def _slide(times: deque[datetime], now: datetime) -> None:
        while times and now - times[0] >= _RATE_WINDOW:
            times.popleft()
