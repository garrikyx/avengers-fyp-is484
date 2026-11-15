"""NFR-REL-004 / FR-PIP-006: stopping cannot strand a blocked log pump."""

import threading
from pathlib import Path

from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.monitor_adapter import MonitorPipelineAdapter
from telemetry_agent.pipeline.supervisor import PipelineBridge


def test_stop_interrupts_full_queue_without_committing_unparsed_lines(
    tmp_path: Path,
) -> None:
    log = tmp_path / "Fix.log"
    log.write_text("first\nsecond\nthird\n", encoding="utf-8")
    monitor = MultiLogMonitor(
        [log], registry_path=tmp_path / "offsets.json", commit_on_read=False
    )
    bridge = PipelineBridge(
        config=PipelineConfig(line_queue_size=1, put_timeout_seconds=0.01)
    )
    adapter = MonitorPipelineAdapter(monitor, bridge, parser_chain=[])
    stop = threading.Event()
    entered_retry = threading.Event()
    checks = 0

    def should_stop() -> bool:
        nonlocal checks
        checks += 1
        # First and second checks precede each read line; the third is
        # after a timed-out enqueue of the second line into the full queue.
        if checks >= 3:
            entered_retry.set()
        return stop.is_set()

    # No workers: one line queues, then the monitor blocks on the next line.
    thread = threading.Thread(
        target=lambda: adapter.poll_once(should_stop=should_stop), daemon=True
    )
    thread.start()
    try:
        assert entered_retry.wait(2)
        stop.set()
        thread.join(timeout=2)
        assert not thread.is_alive(), "shutdown left a producer retrying a full queue"
        assert bridge.line_queue.depth == 1
        assert bridge.stats().lines_dropped == 0
        # No parser/ingestor ran, so no offset may acknowledge this read-ahead.
        assert not (tmp_path / "offsets.json").exists()
    finally:
        stop.set()
        thread.join(timeout=2)
        monitor.close()
