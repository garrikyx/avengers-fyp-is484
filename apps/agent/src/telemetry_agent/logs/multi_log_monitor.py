"""LOCAL STOPGAP - NOT COMMITTED, NOT UBS-22.

run_streamer.py and demo_suite.py (both from Mitch's UBS-22 branch) import a
MultiLogMonitor class that was never actually committed anywhere in the repo's
history (checked across every branch, by filename and by class name). This file
exists purely so we can run those two scripts locally to test UBS-30's
HealthReporter against realistic multi-file tailing, while we wait for Mitch to
push his real implementation.

It is deliberately minimal: sequential round-robin polling, not the concurrent,
non-blocking tailing FR-LOG-002/UBS-22 actually calls for. Delete this file (or
replace it wholesale) once the real UBS-22 multi-file monitor is pushed - do not
let this become the merged version.
"""

import time
from collections.abc import Generator, Iterable
from datetime import datetime
from pathlib import Path

from telemetry_agent.logs.log_monitor import FileReadStatus, LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker


class MultiLogMonitor:
    """Round-robin wrapper over one LogMonitor per file, sharing one OffsetTracker."""

    def __init__(self, log_paths: Iterable[Path], registry_path: Path = Path("offsets.json")):
        self.registry_path = Path(registry_path)
        self._offset_tracker = OffsetTracker(registry_path=self.registry_path)
        self._monitors: dict[str, LogMonitor] = {
            Path(p).name: LogMonitor(Path(p), offset_tracker=self._offset_tracker)
            for p in log_paths
        }

    @property
    def monitors(self) -> dict[str, LogMonitor]:
        """Exposes the underlying per-file LogMonitors, e.g. for HealthReporter."""
        return self._monitors

    def stream_lines(self, poll_interval: float = 1.0) -> Generator[tuple[str, str], None, None]:
        """Round-robin polls every monitored file, yielding (source_name, line)."""
        while True:
            any_line = False
            for name, monitor in self._monitors.items():
                for line in monitor.poll_lines():
                    any_line = True
                    yield name, line
            if not any_line:
                time.sleep(poll_interval)

    def get_statuses(self, now: datetime | None = None) -> dict[str, FileReadStatus]:
        return {name: monitor.get_status(now=now) for name, monitor in self._monitors.items()}

    def close(self) -> None:
        for monitor in self._monitors.values():
            monitor.close()
