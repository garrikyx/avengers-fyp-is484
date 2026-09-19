"""Health Reporter: per-file read lag (UBS-30) + status rollup and heartbeat
payload (UBS-58, FR-HLT-001..004).

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

from telemetry_agent.callbacks.status import DeliveryStatus, DeliveryTracker
from telemetry_agent.health.config import HealthThresholds, HeartbeatConfig
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_shared.models.health import AgentHeartbeat, AgentStatus, FileReadHealth

# spec 011 §1.1: "Log read lag | log_read_lag_ms | < 1s | > 5s sustained"
DEFAULT_DEGRADED_THRESHOLD_MS = HealthThresholds().read_lag_degraded_ms

Clock = Callable[[], datetime]


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
    callback_failures: int | None = None
    dropped_events: int | None = None


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

    # --- UBS-58: rollup + heartbeat ------------------------------------------

    def snapshot(self, now: datetime | None = None) -> HealthSignals:
        """Sample every signal this reporter currently has a producer for."""
        now = now or self._clock()
        statuses = self.file_statuses(now=now)
        return HealthSignals(
            sampled_at=now,
            files=statuses,
            read_lag_ms=self.overall_read_lag_ms(statuses.values()),
        )

    def derive_status(self, signals: HealthSignals) -> tuple[AgentStatus, list[str]]:
        """FR-HLT-002 rollup for the signals that exist; FR-HLT-003 reasons.

        Each rule only fires on a non-None signal. The parse-error and
        publish-queue rules are added by UBS-59 / UBS-60.
        """
        unhealthy: list[str] = []
        degraded: list[str] = self._read_lag_reasons(signals.files)

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
            dropped_events_last5_min=signals.dropped_events,
        )

    # --- rules ---------------------------------------------------------------

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
