from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

OverflowPolicy = Literal["block", "drop_oldest"]


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Pipeline bridge sizing (spec 010 §pipeline, FR-PIP-002–004)."""

    line_queue_size: int = 2048
    event_queue_size: int = 256
    parse_workers: int = 0
    overflow_policy: OverflowPolicy = "block"
    dedupe_capacity: int = 100_000
    dedupe_ttl_seconds: float = 3600.0
    put_timeout_seconds: float = 0.5

    def resolved_worker_count(self) -> int:
        if self.parse_workers > 0:
            return self.parse_workers
        return min(2, os.cpu_count() or 1)
