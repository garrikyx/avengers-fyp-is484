"""Idempotent ingest dedupe by file byte position (FR-PIP-007)."""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass

from telemetry_agent.parser.protocol import SourceMeta


@dataclass(frozen=True, slots=True)
class LinePosition:
    dev: int
    inode: int
    byte_offset: int


class ProcessedLineDeduper:
    """Bounded LRU cache suppressing double-count on re-read."""

    def __init__(self, capacity: int = 100_000, ttl_seconds: float = 3600.0) -> None:
        self._capacity = capacity
        self._ttl_seconds = ttl_seconds
        self._seen: OrderedDict[LinePosition, float] = OrderedDict()
        self._duplicates_suppressed = 0

    @property
    def duplicates_suppressed(self) -> int:
        return self._duplicates_suppressed

    def _position(self, meta: SourceMeta) -> LinePosition:
        return LinePosition(
            dev=meta.dev,
            inode=meta.inode,
            byte_offset=meta.byte_offset,
        )

    def _evict_expired(self, now: float) -> None:
        cutoff = now - self._ttl_seconds
        while self._seen:
            oldest_key, oldest_at = next(iter(self._seen.items()))
            if oldest_at >= cutoff:
                break
            self._seen.pop(oldest_key)

    def is_duplicate(self, meta: SourceMeta, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        self._evict_expired(now)
        key = self._position(meta)
        if key not in self._seen:
            return False
        self._duplicates_suppressed += 1
        self._seen.move_to_end(key)
        return True

    def mark_processed(self, meta: SourceMeta, now: float | None = None) -> None:
        now = now if now is not None else time.monotonic()
        self._evict_expired(now)
        key = self._position(meta)
        self._seen[key] = now
        self._seen.move_to_end(key)
        while len(self._seen) > self._capacity:
            self._seen.popitem(last=False)
