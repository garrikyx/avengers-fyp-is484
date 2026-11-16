"""Spec 002 §8.2: SIGTERM stops readers. A backlog plus stopped parser workers left
the pump retrying a full line queue forever, so the agent never exited."""

import threading
from pathlib import Path

from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.monitor_adapter import MonitorPipelineAdapter
from telemetry_agent.pipeline.supervisor import PipelineBridge


def test_poll_once_returns_on_halt_while_the_line_queue_is_full(tmp_path: Path) -> None:
    log = tmp_path / "Fix.log"
    log.write_text("".join(f"line-{i}\n" for i in range(10)), newline="\n")
    monitor = MultiLogMonitor(
        [log], registry_path=tmp_path / "offsets.json", commit_on_read=False
    )
    # Workers never start, so the one-slot queue stays full after the first line.
    bridge = PipelineBridge(config=PipelineConfig(line_queue_size=1, parse_workers=1))
    adapter = MonitorPipelineAdapter(monitor, bridge, parser_chain=["fix"])
    halt = threading.Event()
    pump = threading.Thread(
        target=adapter.poll_once, kwargs={"halt": halt}, daemon=True
    )

    pump.start()
    threading.Timer(0.1, halt.set).start()
    pump.join(timeout=5)

    assert not pump.is_alive()
    assert bridge.stats().line_queue_depth == 1
    # Nothing was ingested, so nothing is committed: a restart re-reads it all.
    [log_monitor] = monitor.monitors.values()
    assert log_monitor.get_status().committed_offset == 0
