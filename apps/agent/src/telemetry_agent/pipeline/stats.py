from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PipelineStats:
    """Queue depths and drop counters for heartbeat/metrics (FR-PIP-005)."""

    line_queue_depth: int
    line_queue_capacity: int
    event_queue_depth: int
    event_queue_capacity: int
    lines_dropped: int
    events_dropped: int

    def as_metrics(self) -> dict[str, int]:
        return {
            "pipeline_line_queue_depth": self.line_queue_depth,
            "pipeline_event_queue_depth": self.event_queue_depth,
            "pipeline_lines_dropped_total": self.lines_dropped,
            "pipeline_events_dropped_total": self.events_dropped,
        }
