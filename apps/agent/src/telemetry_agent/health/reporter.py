"""Health Reporter: per-file read lag (UBS-30), status rollup and heartbeat
payload (UBS-58, FR-HLT-001..004), rolling parse-error window (UBS-59),
publish queue depth (UBS-60), publish buffer bytes and dropped-event rate
(UBS-104).

See docs/plan/ubs30-notes.md and docs/plan/ubs58-60-notes.md. UBS-33/34
additionally surface callback delivery failures here (`failed_deliveries`),
per the "surfaced via the Health Reporter" AC — this takes a
`DeliveryTracker` as a parameter rather than constructing one, so
`HealthReporter` stays decoupled from owning the Callback Dispatcher's
state, the same way it stays decoupled from owning `LogMonitor`
construction.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Literal

from telemetry_agent.callbacks.status import DeliveryStatus, DeliveryTracker
from telemetry_agent.health.config import HealthThresholds, HeartbeatConfig
from telemetry_agent.health.window import SlidingWindowCounter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.parser.protocol import ParseResult
from telemetry_shared.models.health import AgentHeartbeat, AgentStatus, FileReadHealth

# spec 011 §1.1: "Log read lag | log_read_lag_ms | < 1s | > 5s sustained"
DEFAULT_DEGRADED_THRESHOLD_MS = HealthThresholds().read_lag_degraded_ms

Clock = Callable[[], datetime]
# UBS-60: whatever owns the publish queue answers "how deep is it right now".
QueueDepthProvider = Callable[[], int]
QueueTrend = Literal["rising", "draining", "flat"]
# UBS-104: whatever owns the publish buffer answers "how many bytes right now".
BufferBytesProvider = Callable[[], int]


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True, frozen=True)
class HealthSignals:
    """Everything `derive_status` looks at, sampled at one instant.

    `None` means the signal has no producer yet (FR-HLT-004) — it is skipped
    by the rollup, never treated as zero. Fields beyond the read-lag ones are
    populated by UBS-59 (parse errors) and UBS-60 (publish queue).
    """

    sampled_at: datetime
    files: dict[str, FileReadHealth] = field(default_factory=dict)
    read_lag_ms: float | None = None
    parse_error_count: int | None = None
    lines_read: int | None = None
    parse_error_rate: float | None = None
    publish_queue_depth: int | None = None
    # Direction since the previous snapshot; None on the first sample.
    publish_queue_trend: QueueTrend | None = None
    publish_buffer_bytes: int | None = None
    callback_failures: int | None = None
    dropped_events: int | None = None


def is_parse_error(result: ParseResult) -> bool:
    """What the heartbeat counts as a parse error (UBS-59).

    Same definition as the Metrics Aggregator's `parse_errors` counter
    (`metrics/demo_sink.py`), so `parseErrorCountLast5Min` and
    `parseErrorRate` agree: a closed-set `ParseResult.error`, or a framed
    message whose timestamp or MsgType could not be interpreted. Warnings
    (`body_length_mismatch`, `malformed_field`) are not errors — the line
    still yielded usable telemetry.
    """
    if result.error is not None:
        return True
    tel = result.telemetry
    return tel is not None and bool(tel.bad_timestamp or tel.unknown_msg_type)


class HealthReporter:
    """Aggregates agent health signals and derives spec 011 §2 status."""

    def __init__(
        self,
        monitors: dict[str, LogMonitor],
        degraded_threshold_ms: float | None = None,
        *,
        thresholds: HealthThresholds | None = None,
        heartbeat: HeartbeatConfig | None = None,
        clock: Clock | None = None,
        queue_depth_provider: QueueDepthProvider | None = None,
        buffer_bytes_provider: BufferBytesProvider | None = None,
    ) -> None:
        self.monitors = monitors
        base = thresholds or HealthThresholds()
        # `degraded_threshold_ms` predates `thresholds` (UBS-30 callers); an
        # explicit value still wins so those call sites keep their meaning.
        if degraded_threshold_ms is not None:
            base = replace(base, read_lag_degraded_ms=degraded_threshold_ms)
        self.thresholds = base
        self.heartbeat_config = heartbeat or HeartbeatConfig()
        self._clock = clock or _utc_now
        self.started_at = self._clock()
        # UBS-59: bounded rolling windows behind the `...Last5Min` fields.
        # `_lines_read` is the denominator for parse_error_rate (spec 004 s4.5
        # `parse_errors / log_lines_read`), sampled over the same window.
        window = self.thresholds.rolling_window_seconds
        self._parse_errors = SlidingWindowCounter(window, clock=self._clock)
        self._lines_read = SlidingWindowCounter(window, clock=self._clock)
        self._parse_signal_seen = False
        # UBS-60/104: until a Publisher registers itself, the queue/buffer/
        # drop fields stay None on the wire (FR-HLT-004) rather than a
        # fabricated zero.
        self._queue_depth_provider = queue_depth_provider
        self._last_queue_depth: int | None = None
        self._buffer_bytes_provider = buffer_bytes_provider
        self._dropped_events = SlidingWindowCounter(window, clock=self._clock)
        self._dropped_signal_seen = False

    @property
    def degraded_threshold_ms(self) -> float:
        return self.thresholds.read_lag_degraded_ms

    # --- UBS-30: read lag ---------------------------------------------------

    def file_statuses(self, now: datetime | None = None) -> dict[str, FileReadHealth]:
        """Per-file read health, keyed by the same name `monitors` was built with."""
        now = now or self._clock()
        statuses: dict[str, FileReadHealth] = {}
        for name, monitor in self.monitors.items():
            status = monitor.get_status(now=now)
            statuses[name] = FileReadHealth(
                path=status.path,
                offset=status.offset,
                size=status.size,
                last_line_at_utc=status.last_read_at,
                read_lag_ms=status.read_lag_ms,
                # LogMonitor exposes no rotation count or error state yet;
                # "reading" vs "waiting" is all that can be said honestly.
                state="reading" if status.has_read_any_line else "waiting",
            )
        return statuses

    def overall_read_lag_ms(
        self, statuses: Iterable[FileReadHealth] | None = None
    ) -> float | None:
        """Worst-case lag across files (heartbeat gauge). None if none have read yet."""
        if statuses is None:
            statuses = self.file_statuses().values()
        known_lags = [s.read_lag_ms for s in statuses if s.read_lag_ms is not None]
        if not known_lags:
            return None
        return max(known_lags)

    def degraded_reasons(
        self, statuses: dict[str, FileReadHealth] | None = None
    ) -> list[str]:
        """Files whose lag exceeds the threshold. Unread files are never flagged."""
        if statuses is None:
            statuses = self.file_statuses()
        return self._read_lag_reasons(statuses)

    def is_degraded(self, statuses: dict[str, FileReadHealth] | None = None) -> bool:
        return len(self.degraded_reasons(statuses)) > 0

    # --- UBS-59: parse-error intake ---------------------------------------------
    #
    # There is no event bus yet (pipeline bridge is M1.5); whoever drives the
    # parser calls one of these per line. Until the first call the parse
    # signals stay None on the wire (FR-HLT-004): "nobody is measuring" must
    # not read as "no errors".

    def record_parse_result(
        self, result: ParseResult, now: datetime | None = None
    ) -> None:
        """Count one parsed line, and a parse error if `is_parse_error(result)`."""
        now = now or self._clock()
        self._parse_signal_seen = True
        self._lines_read.record(now)
        if is_parse_error(result):
            self._parse_errors.record(now)

    def record_parse_error(self, now: datetime | None = None) -> None:
        """Count a parse error from a producer that does not hand over a
        `ParseResult` (still counts the line so the rate stays honest)."""
        now = now or self._clock()
        self._parse_signal_seen = True
        self._lines_read.record(now)
        self._parse_errors.record(now)

    def record_lines_read(self, n: int = 1, now: datetime | None = None) -> None:
        """Count successfully parsed lines in bulk (denominator only)."""
        self._parse_signal_seen = True
        self._lines_read.record(now or self._clock(), n)

    # --- UBS-60: publish queue depth ---------------------------------------------

    def set_queue_depth_provider(self, provider: QueueDepthProvider | None) -> None:
        """Register (or remove) the Publisher's queue-depth callback."""
        self._queue_depth_provider = provider
        self._last_queue_depth = None

    # --- UBS-104: publish buffer bytes and dropped-event rate -------------------

    def set_buffer_bytes_provider(self, provider: BufferBytesProvider | None) -> None:
        """Register (or remove) the Publisher's buffer-bytes callback
        (`publishBufferBytes`, spec 004 §6) -- same parameter-injected shape
        as `set_queue_depth_provider`, so `HealthReporter` never owns or
        constructs the Publisher's buffer.
        """
        self._buffer_bytes_provider = provider

    def record_dropped_events(self, n: int = 1, now: datetime | None = None) -> None:
        """Count `n` buffer-eviction drops (`droppedEventsLast5Min`,
        `FR-PUB-004`) at `now`. The Publisher's buffer calls this once per
        evicted item.

        Calling this even with `n=0` at wiring time is enough to mark the
        signal as "has a producer" (`FR-HLT-004`) -- otherwise a healthy
        Publisher that has never actually dropped anything would report
        `None` forever instead of a genuine `0`, indistinguishable from no
        Publisher being wired in at all.
        """
        now = now or self._clock()
        self._dropped_signal_seen = True
        self._dropped_events.record(now, n)

    def _queue_signals(self) -> tuple[int | None, QueueTrend | None]:
        """(depth, trend) sampled now; trend compares with the previous sample
        so consecutive heartbeats show rising vs draining (spec 011 s1.1
        "growing monotonically" is the warning sign, not the level alone)."""
        if self._queue_depth_provider is None:
            return None, None
        depth = max(0, int(self._queue_depth_provider()))
        previous, self._last_queue_depth = self._last_queue_depth, depth
        if previous is None:
            return depth, None
        if depth > previous:
            return depth, "rising"
        if depth < previous:
            return depth, "draining"
        return depth, "flat"

    # --- UBS-58: rollup + heartbeat ------------------------------------------

    def snapshot(self, now: datetime | None = None) -> HealthSignals:
        """Sample every signal this reporter currently has a producer for."""
        now = now or self._clock()
        statuses = self.file_statuses(now=now)
        errors, lines, rate = self._parse_signals(now)
        queue_depth, queue_trend = self._queue_signals()
        buffer_bytes = (
            self._buffer_bytes_provider() if self._buffer_bytes_provider else None
        )
        dropped = self._dropped_events.count(now) if self._dropped_signal_seen else None
        return HealthSignals(
            sampled_at=now,
            files=statuses,
            read_lag_ms=self.overall_read_lag_ms(statuses.values()),
            parse_error_count=errors,
            lines_read=lines,
            parse_error_rate=rate,
            publish_queue_depth=queue_depth,
            publish_queue_trend=queue_trend,
            publish_buffer_bytes=buffer_bytes,
            dropped_events=dropped,
        )

    def _parse_signals(
        self, now: datetime
    ) -> tuple[int | None, int | None, float | None]:
        """(errors, lines, rate) over the rolling window; all None until a
        producer has reported at least once."""
        if not self._parse_signal_seen:
            return None, None, None
        errors = self._parse_errors.count(now)
        lines = self._lines_read.count(now)
        # spec 004 s4.5: a ratio with no denominator is null, not 0.
        return errors, lines, (errors / lines if lines > 0 else None)

    def derive_status(self, signals: HealthSignals) -> tuple[AgentStatus, list[str]]:
        """FR-HLT-002 rollup for the signals that exist; FR-HLT-003 reasons.

        Each rule only fires on a non-None signal.
        """
        unhealthy: list[str] = []
        degraded: list[str] = self._read_lag_reasons(signals.files)
        self._parse_error_reasons(signals, unhealthy, degraded)
        self._queue_depth_reasons(signals, unhealthy, degraded)

        if unhealthy:
            return "unhealthy", unhealthy + degraded
        if degraded:
            return "degraded", degraded
        return "healthy", []

    def build_heartbeat(self, now: datetime | None = None) -> AgentHeartbeat:
        """Assemble the spec 004 §6 payload from a fresh snapshot."""
        signals = self.snapshot(now=now)
        status, reasons = self.derive_status(signals)
        cfg = self.heartbeat_config
        return AgentHeartbeat(
            agent_id=cfg.agent_id,
            instance_ids=list(cfg.instance_ids),
            sent_at_utc=signals.sampled_at,
            agent_version=cfg.agent_version,
            uptime_seconds=max(
                0.0, (signals.sampled_at - self.started_at).total_seconds()
            ),
            status=status,
            status_reasons=reasons,
            files=list(signals.files.values()),
            read_lag_ms=signals.read_lag_ms,
            parse_error_count_last5_min=signals.parse_error_count,
            callback_failures_last5_min=signals.callback_failures,
            publish_queue_depth=signals.publish_queue_depth,
            publish_buffer_bytes=signals.publish_buffer_bytes,
            dropped_events_last5_min=signals.dropped_events,
        )

    # --- rules ---------------------------------------------------------------

    def _queue_depth_reasons(
        self, signals: HealthSignals, unhealthy: list[str], degraded: list[str]
    ) -> None:
        """spec 011 s1.1: publish queue depth >= critical watermark unhealthy,
        >= high watermark degraded. Trend is appended so an operator can tell
        a draining backlog from a stalled Publisher without a second query."""
        depth = signals.publish_queue_depth
        if depth is None:
            return
        trend = (
            f", {signals.publish_queue_trend}" if signals.publish_queue_trend else ""
        )
        if depth >= self.thresholds.publish_queue_critical_watermark:
            unhealthy.append(
                f"publish queue depth {depth}{trend} at or above critical "
                f"watermark {self.thresholds.publish_queue_critical_watermark}"
            )
        elif depth >= self.thresholds.publish_queue_high_watermark:
            degraded.append(
                f"publish queue depth {depth}{trend} at or above high "
                f"watermark {self.thresholds.publish_queue_high_watermark}"
            )

    def _parse_error_reasons(
        self, signals: HealthSignals, unhealthy: list[str], degraded: list[str]
    ) -> None:
        """spec 011 s2: parse error rate > 25% unhealthy, > 1% degraded."""
        rate = signals.parse_error_rate
        if rate is None:
            return
        window = self.thresholds.rolling_window_seconds
        detail = (
            f"parse error rate {rate:.1%} ({signals.parse_error_count}/"
            f"{signals.lines_read} lines in last {window:.0f}s)"
        )
        if rate > self.thresholds.parse_error_rate_unhealthy:
            unhealthy.append(
                f"{detail} exceeds {self.thresholds.parse_error_rate_unhealthy:.0%}"
            )
        elif rate > self.thresholds.parse_error_rate_degraded:
            degraded.append(
                f"{detail} exceeds {self.thresholds.parse_error_rate_degraded:.0%}"
            )

    def _read_lag_reasons(self, statuses: dict[str, FileReadHealth]) -> list[str]:
        threshold = self.thresholds.read_lag_degraded_ms
        reasons = []
        for name, status in statuses.items():
            over_threshold = (
                status.read_lag_ms is not None and status.read_lag_ms > threshold
            )
            if over_threshold:
                reasons.append(
                    f"{name}: read lag {status.read_lag_ms:.0f}ms exceeds "
                    f"{threshold:.0f}ms threshold"
                )
        return reasons

    def failed_deliveries(self, tracker: DeliveryTracker) -> list[str]:
        """Alert IDs whose callback delivery is currently `FAILED`
        (UBS-33's "surfaced via the Health Reporter" AC), following the
        same shape as `degraded_reasons` above.
        """
        return [
            alert_id
            for alert_id, record in tracker.snapshot().items()
            if record.status is DeliveryStatus.FAILED
        ]
