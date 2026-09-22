import shutil
from pathlib import Path

from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.monitor_adapter import (
    MonitorPipelineAdapter,
    monitors_by_resolved_path,
)
from telemetry_agent.pipeline.supervisor import PipelineBridge


def test_monitor_to_parse_pipeline(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MAGIC_TELEMETRY_ID_HASH_KEY", "test-key")
    corpus = Path("apps/agent/testdata/fix/demo_logs.txt")
    fix_log = tmp_path / "Fix.log"
    shutil.copy(corpus, fix_log)

    registry = Registry(parsers={"fix": FixParser(hash_key=b"test-key")})
    monitor = MultiLogMonitor(
        [fix_log],
        registry_path=tmp_path / "offsets.json",
        commit_on_read=False,
    )
    bridge = PipelineBridge(
        config=PipelineConfig(line_queue_size=16, event_queue_size=16, parse_workers=1),
        registry=registry,
    )
    bridge.attach_committer(monitors_by_resolved_path(monitor.monitors))
    bridge.start()
    try:
        adapter = MonitorPipelineAdapter(
            monitor,
            bridge,
            parser_chain=["fix"],
        )
        events = list(adapter.run_until(max_lines=3, idle_rounds=2))
        assert len(events) == 3
        assert bridge.stats().lines_dropped == 0
        status = monitor.monitors["Fix.log"].get_status()
        assert status.committed_offset > 0
    finally:
        bridge.stop()
        monitor.close()
