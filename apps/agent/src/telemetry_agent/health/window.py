"""Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min` fields.

Per-bucket integers rather than a list of timestamps, so memory is fixed by
`window_seconds / bucket_seconds` and independent of event rate — a parser
storm of 100k errors/s costs the same 300 ints as an idle window. Expiry runs
on every access, so the bucket map can never hold more than `capacity` keys.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

Clock = Callable[[], datetime]


class SlidingWindowCounter:
    def __init__(
        self,
        window_seconds: float = 300.0,
        bucket_seconds: float = 1.0,
        clock: Clock | None = None,
    ) -> None:
        if window_seconds <= 0 or bucket_seconds <= 0:
            raise ValueError("window_seconds and bucket_seconds must be > 0")
        if bucket_seconds > window_seconds:
            raise ValueError("bucket_seconds must not exceed window_seconds")
        self.window_seconds = window_seconds
        self.bucket_seconds = bucket_seconds
        # round(), not //: 300 // 0.1 is 2999.999... -> 2999 in float math.
        self.capacity = max(1, round(window_seconds / bucket_seconds))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._buckets: dict[int, int] = {}

    def _bucket_index(self, now: datetime) -> int:
        return int(now.timestamp() // self.bucket_seconds)

    def _expire(self, now_idx: int) -> None:
        oldest_live = now_idx - self.capacity + 1
        for idx in [i for i in self._buckets if i < oldest_live]:
            del self._buckets[idx]

    def record(self, now: datetime | None = None, n: int = 1) -> None:
        """Count `n` events at `now`. A late timestamp still inside the window
        lands in its own bucket; one older than the window is dropped (it could
        never be observed again). Callers pass the reporter's clock, so `now`
        is monotonic in practice."""
        idx = self._bucket_index(now or self._clock())
        self._expire(idx)
        self._buckets[idx] = self._buckets.get(idx, 0) + n

    def count(self, now: datetime | None = None) -> int:
        """Events inside the window ending at `now`; decays as the window slides."""
        idx = self._bucket_index(now or self._clock())
        self._expire(idx)
        return sum(c for i, c in self._buckets.items() if i <= idx)

    def __len__(self) -> int:
        """Live buckets (never exceeds `capacity`)."""
        return len(self._buckets)
