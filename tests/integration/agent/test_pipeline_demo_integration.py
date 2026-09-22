import shutil
from pathlib import Path

import pipeline_demo
import pytest
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


# `make pipeline-demo` once died on a NameError in `run_happy_path` that no
# test caught, because the test above reimplements the pipeline rather than
# calling the demo's own entry points. These two invoke them directly, so a
# demo that no longer runs fails the suite instead of failing in front of an
# audience. They assert on reaching the end, not on exact output — the demo's
# narration is meant to be editable without breaking tests.
@pytest.mark.parametrize(
    "scenario",
    [pipeline_demo.run_happy_path, pipeline_demo.run_slow_parser_backpressure],
    ids=["happy_path", "slow_parser_backpressure"],
)
def test_demo_scenarios_run_to_completion(
    scenario, tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("MAGIC_TELEMETRY_ID_HASH_KEY", "test-key")
    corpus = tmp_path / "demo_logs.txt"
    shutil.copy(Path("apps/agent/testdata/fix/demo_logs.txt"), corpus)

    scenario(corpus, pipeline_demo._load_config(None))

    # `[STATS]` is the last line each scenario prints, so reaching it means
    # the whole scenario ran. (Only the happy path prints `[PARSE]` — the
    # backpressure one narrates queue depth instead.)
    assert "[STATS]" in capsys.readouterr().out
