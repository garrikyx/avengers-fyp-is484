"""Health Reporter (UBS-30).

Aggregates per-file read status from one or more `LogMonitor`s into the read-lag
signal spec 011 §1.1 defines: `log_read_lag_ms`, healthy under 1s, "investigate" past
5s sustained. Spec 002 `FR-LOG-010` and `FR-HLT-001` require this to be reported on
every heartbeat, keyed per file, alongside offset progress.

Scope note: spec 011 `FR-HLT-002` derives a single `healthy`/`degraded`/`unhealthy`
status from read lag *and* parse error rate *and* publish buffer *and* RSS. Only read
lag exists today (M1) — the Parser Engine (M2), Metrics/Publisher (M3/M4) and their
counters don't. `degraded_reasons` below is the read-lag slice of that rollup only;
whoever wires up M2+ should fold this in rather than replace it.
"""

from collections.abc import Iterable
from datetime import UTC, datetime

from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_shared.models.health import FileReadHealth

# spec 011 §1.1: "Log read lag | log_read_lag_ms | < 1s | > 5s sustained"
DEFAULT_DEGRADED_THRESHOLD_MS = 5_000.0


class HealthReporter:
    """Computes read-lag health for a set of monitored log files.

    `monitors` is keyed by a human-readable name (e.g. `"Fix.log"`) purely so status
    output and `degraded_reasons` are legible; the Health Reporter never inspects log
    content or file identity itself, only what each `LogMonitor` reports.
    """

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
        """The gauge value for the heartbeat/metric snapshot (spec 004 `gauges.read_lag_ms`).

        Reported as the worst (highest) lag across files still awaiting their first
        line contribute `None`, since a file that has never been read has no lag
        value to compare, not a lag of zero (`FR-HLT-004`); if every file is in that
        state the overall gauge is `None` too, rather than misreporting the agent as
        perfectly caught up.
        """
        if statuses is None:
            statuses = self.file_statuses().values()
        known_lags = [s.read_lag_ms for s in statuses if s.read_lag_ms is not None]
        if not known_lags:
            return None
        return max(known_lags)

    def degraded_reasons(self, statuses: dict[str, FileReadHealth] | None = None) -> list[str]:
        """Human-readable reasons this reporter's slice of `FR-HLT-002`/`FR-HLT-003` is degraded.

        Empty when every file with a known lag is under threshold. A file with no
        reads yet is not reported as degraded — it has no signal either way — but it
        also is not reported as healthy; see `overall_read_lag_ms`.
        """
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
