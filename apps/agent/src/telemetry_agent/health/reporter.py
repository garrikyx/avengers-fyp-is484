"""Health Reporter (UBS-30): aggregates per-file read lag. See docs/plan/ubs30-notes.md."""

from collections.abc import Iterable
from datetime import UTC, datetime

from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_shared.models.health import FileReadHealth

# spec 011 §1.1: "Log read lag | log_read_lag_ms | < 1s | > 5s sustained"
DEFAULT_DEGRADED_THRESHOLD_MS = 5_000.0


class HealthReporter:
    """Read-lag health for a set of monitored log files, keyed by name."""

    def __init__(
        self,
        monitors: dict[str, LogMonitor],
        degraded_threshold_ms: float = DEFAULT_DEGRADED_THRESHOLD_MS,
    ) -> None:
        self.monitors = monitors
        self.degraded_threshold_ms = degraded_threshold_ms

    def file_statuses(self, now: datetime | None = None) -> dict[str, FileReadHealth]:
        """Per-file read health, keyed by the same name `monitors` was built with."""
        now = now or datetime.now(UTC)
        statuses: dict[str, FileReadHealth] = {}
        for name, monitor in self.monitors.items():
            status = monitor.get_status(now=now)
            statuses[name] = FileReadHealth(
                path=status.path,
                offset=status.offset,
                size=status.size,
                last_read_at=status.last_read_at,
                read_lag_ms=status.read_lag_ms,
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

    def degraded_reasons(self, statuses: dict[str, FileReadHealth] | None = None) -> list[str]:
        """Files whose lag exceeds the threshold. Unread files are never flagged."""
        if statuses is None:
            statuses = self.file_statuses()
        reasons = []
        for name, status in statuses.items():
            if status.read_lag_ms is not None and status.read_lag_ms > self.degraded_threshold_ms:
                reasons.append(
                    f"{name}: read lag {status.read_lag_ms:.0f}ms exceeds "
                    f"{self.degraded_threshold_ms:.0f}ms threshold"
                )
        return reasons

    def is_degraded(self, statuses: dict[str, FileReadHealth] | None = None) -> bool:
        return len(self.degraded_reasons(statuses)) > 0
