"""UBS-112 integration: a tailed log file -> MultiLogMonitor -> PipelineBridge
(parser worker thread) -> committer -> MetricsIngestor -> the real
MetricsAggregator, LatencyCorrelator, SessionHeartbeatTracker and
HealthReporter.

Lines carry the current SendingTime, as production lines do: the aggregator
runs on the real clock, so lines stamped long ago would fall outside its
buckets and be dropped silently.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.pipeline.monitor_adapter import (
    MonitorPipelineAdapter,
    monitors_by_resolved_path,
)
from telemetry_agent.pipeline.supervisor import PipelineBridge

INSTANCE = "magic-prod-01"
HASH_KEY = b"ubs-112-integration-key"

# Three orders (two acked and filled, one rejected) plus one hard parse error.
# {ts} is replaced with the current SendingTime when the file is written.
_TEMPLATES = [
    "8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=1|52={ts}|11=C1|55=AAPL|54=1|40=2|38=100|10=000|",
    "8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=2|52={ts}|11=C1|37=O1|17=E1|55=AAPL|54=1"
    "|150=0|39=0|10=000|",
    "8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=3|52={ts}|11=C1|37=O1|17=E2|55=AAPL|54=1"
    "|150=F|39=2|32=100|151=0|10=000|",
    "8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=4|52={ts}|11=C2|55=MSFT|54=1|40=2|38=50|10=000|",
    "8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=5|52={ts}|11=C2|37=O2|17=E3|55=MSFT|54=1"
    "|150=0|39=0|10=000|",
    "8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=6|52={ts}|11=C2|37=O2|17=E4|55=MSFT|54=1"
    "|150=F|39=2|32=50|151=0|10=000|",
    "8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=7|52={ts}|11=C3|55=GOOG|54=2|40=1|38=200|10=000|",
    "8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=8|52={ts}|11=C3|37=O3|17=E5|55=GOOG|54=2"
    "|150=8|39=8|103=3|10=000|",
    "8=FIX.4.2|35=|49=MAGIC|56=EXCH1|10=000|",
]


def _now_sending_time() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]


def test_tailed_fix_lines_reach_the_real_aggregator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAGIC_TELEMETRY_ID_HASH_KEY", HASH_KEY.decode())
    fix_log = tmp_path / "Fix.log"
    ts = _now_sending_time()
    with fix_log.open("w", encoding="utf-8", newline="\n") as f:
        for template in _TEMPLATES:
            f.write(template.format(ts=ts) + "\n")

    monitor = MultiLogMonitor(
        [fix_log], registry_path=tmp_path / "offsets.json", commit_on_read=False
    )
    reporter = HealthReporter(
        monitor.monitors, heartbeat=HeartbeatConfig(agent_id="agent-112")
    )
    ingestor = MetricsIngestor.build_default(health_reporter=reporter)
    bridge = PipelineBridge(
        config=PipelineConfig(parse_workers=1),
        registry=Registry(parsers={"fix": FixParser(hash_key=HASH_KEY)}),
    )
    bridge.attach_committer(
        monitors_by_resolved_path(monitor.monitors), on_event=ingestor.on_event
    )
    bridge.start()
    try:
        adapter = MonitorPipelineAdapter(
            monitor, bridge, parser_chain=["fix"], instance_id=INSTANCE
        )
        committed = sum(1 for _ in adapter.run_until(max_lines=100, idle_rounds=3))
    finally:
        bridge.stop()

    assert committed == len(_TEMPLATES)

    # --- the aggregator got every line, through the real pipeline -----------------
    row = ingestor.aggregator.snapshot("1m", group_by=())[()]
    assert row.counters["log_lines_read"] == 9
    assert row.counters["parse_errors"] == 1
    assert row.counters["orders_submitted"] == 3
    assert row.counters["orders_acked"] == 2
    assert row.counters["orders_rejected"] == 1
    assert row.counters["fills_full"] == 2
    assert "ack_latency_ms" in row.histograms  # via the correlator

    by_instance = ingestor.aggregator.snapshot("1m", group_by=("instance_id",))
    assert (INSTANCE,) in by_instance  # SourceMeta.instance_id carried through

    # --- the session tracker saw the MAGIC -> EXCH1 session -----------------------
    assert ingestor.session_tracker is not None
    assert len(ingestor.session_tracker.tracked_sessions()) == 1

    # --- the Health Reporter counted each line exactly once -----------------------
    signals = reporter.snapshot()
    assert signals.lines_read == 9
    assert signals.parse_error_count == 1

    # --- nothing failed, and offsets committed to the end of the file -------------
    assert ingestor.stats() == {
        "lines_ingested": 9,
        "events_built": 8,
        "ingest_errors": 0,
    }
    for log_monitor in monitor.monitors.values():
        log_monitor.flush_commits()
    entries = json.loads((tmp_path / "offsets.json").read_text())
    assert entries[0]["offset"] == fix_log.stat().st_size
    monitor.close()
