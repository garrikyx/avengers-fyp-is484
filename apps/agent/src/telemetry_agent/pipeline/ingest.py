"""Feed each committed parse result into the real metrics and health state (UBS-112).

The pipeline (monitor -> parser workers -> committer) produces one
`ParsedEvent` per log line. `MetricsIngestor.ingest` is the single place that
turns that into everything downstream reads, in this order:

1. parser counters (`log_lines_read`, `parse_errors`) for every line, parsed
   or not - they are the denominator of the parse-error rate;
2. `build_parsed_message_event` - only framed FIX lines become events;
3. `LatencyCorrelator.ingest` - order -> ack/exec/cancel latency;
4. order and session counters (`derive_counters | derive_session_counters`);
5. `SessionHeartbeatTracker.observe` - "this FIX session is alive" (UBS-106);
6. `HealthReporter.record_parse_result` - the heartbeat's parse-error count
   (UBS-59).

Wire it into the committer, which calls it after the line's offset is acked:

    ingestor = MetricsIngestor.build_default(health_reporter=reporter)
    bridge.attach_committer(path_map, on_event=ingestor.on_event)

Production rules, which the demo copies of this sequence did not need:

- **Never raises.** The committer acks a line's offset before calling
  `on_event`, so an exception here would lose the rest of the drained batch.
  Failures are logged once and counted in `stats()["ingest_errors"]`.
- **Real time.** Parser counters are bucketed at `meta.read_at`; order
  counters by the message's SendingTime (falling back to `read_at`).
- **One lock.** The aggregator, correlator, tracker and reporter are not
  thread-safe. `ingest` runs on the thread that drives
  `PipelineBridge.process_commits` (the monitor adapter loop); anything that
  reads or ticks these components from another thread - the rule
  evaluator (UBS-113) - must hold `ingestor.lock` while it does.
- **Session clock.** The tracker is fed `monotonic()` seconds; whoever calls
  `tracker.timed_out(now)` must pass the same clock (`ingestor.monotonic`).
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.parser.fix.session_tracker import SessionHeartbeatTracker
from telemetry_agent.parser.metrics_event import (
    build_parsed_message_event,
    derive_parser_counters,
    derive_session_counters,
    parser_counter_dims,
)
from telemetry_agent.parser.protocol import ParseResult, SourceMeta
from telemetry_agent.pipeline.types import ParsedEvent

if TYPE_CHECKING:
    from telemetry_agent.health.reporter import HealthReporter

logger = logging.getLogger(__name__)

# spec 011 `health.sessionHeartbeatTimeout` default, used by build_default.
DEFAULT_SESSION_TIMEOUT_SECONDS = 60.0


class MetricsIngestor:
    def __init__(
        self,
        aggregator: MetricsAggregator,
        *,
        correlator: LatencyCorrelator | None = None,
        session_tracker: SessionHeartbeatTracker | None = None,
        health_reporter: HealthReporter | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        log: logging.Logger | None = None,
    ) -> None:
        self.aggregator = aggregator
        self.correlator = correlator
        self.session_tracker = session_tracker
        self.health_reporter = health_reporter
        self.monotonic = monotonic
        self.lock = threading.RLock()
        self._log = log or logger
        self._lines_ingested = 0
        self._events_built = 0
        self._ingest_errors = 0
        self._error_logged = False

    @classmethod
    def build_default(
        cls,
        *,
        health_reporter: HealthReporter | None = None,
        session_timeout_seconds: float = DEFAULT_SESSION_TIMEOUT_SECONDS,
        clock: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> MetricsIngestor:
        """The production set: an aggregator that accepts every counter and
        latency metric, a correlator on it, and a session tracker."""
        aggregator = MetricsAggregator(
            config=AggregatorConfig(
                metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
            ),
            clock=clock,
        )
        return cls(
            aggregator,
            correlator=LatencyCorrelator(aggregator, clock=clock),
            session_tracker=SessionHeartbeatTracker(
                timeout_seconds=session_timeout_seconds
            ),
            health_reporter=health_reporter,
            monotonic=monotonic,
        )

    def on_event(self, event: ParsedEvent) -> None:
        """`PipelineCommitter(on_event=...)` / `attach_committer(on_event=...)`."""
        self.ingest(event.result, event.meta)

    def ingest(self, result: ParseResult, meta: SourceMeta) -> None:
        with self.lock:
            try:
                self._ingest(result, meta)
            except Exception:
                self._ingest_errors += 1
                if not self._error_logged:
                    self._error_logged = True
                    self._log.exception(
                        "metrics ingest failed for %s @%d; counting further "
                        "failures in stats() without logging each one",
                        meta.path,
                        meta.byte_offset,
                    )
            self._lines_ingested += 1

    def _ingest(self, result: ParseResult, meta: SourceMeta) -> None:
        # 1. Every line counts towards the parse-error-rate denominator.
        self.aggregator.ingest_agent_counters(
            dims=parser_counter_dims(result, instance_id=meta.instance_id),
            counters=derive_parser_counters(result),
            at=meta.read_at,
        )
        # 2-4. Framed FIX lines become events: latency, then order + session.
        event = build_parsed_message_event(result, meta)
        if event is not None and result.telemetry is not None:
            self._events_built += 1
            if self.correlator is not None:
                self.correlator.ingest(event)
            self.aggregator.ingest_counters(
                event,
                derive_counters(event) | derive_session_counters(result.telemetry),
            )
        # 5. Any line with FIX header fields is evidence its session is alive.
        if self.session_tracker is not None and result.fields is not None:
            self.session_tracker.observe(
                msg_type=(
                    result.telemetry.normalized_msg_type if result.telemetry else None
                ),
                sender=result.fields.sender_comp_id,
                target=result.fields.target_comp_id,
                at=self.monotonic(),
            )
        # 6. The heartbeat's parse-error count (UBS-59).
        if self.health_reporter is not None:
            self.health_reporter.record_parse_result(result, now=meta.read_at)

    def stats(self) -> dict[str, int]:
        return {
            "lines_ingested": self._lines_ingested,
            "events_built": self._events_built,
            "ingest_errors": self._ingest_errors,
        }
