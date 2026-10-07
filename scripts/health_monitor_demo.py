"""Live health-monitor demo: simulator logs -> agent health path -> backend.

Runs just the health half of an agent (not the full agent runtime, which is
still to be built): tail the simulator's logs, parse them through the
pipeline, feed the Health Reporter, and publish a heartbeat-carrying batch
to a real backend every `--interval` seconds. After each publish it prints
what the backend now says about this agent.

Three terminals, all from the repo root:

    uv run telemetry-backend
    uv run python apps/simulator/src/simulator/mock_logger.py --max-bytes 50000000
    uv run python scripts/health_monitor_demo.py

(`--max-bytes` keeps the simulator from rotating: on Windows it cannot
rename a log this demo holds open.)

Then:
    curl http://127.0.0.1:8080/telemetry/health/agents
    curl http://127.0.0.1:8081/metrics
Stop this script and the agent shows `missing` about 60s later.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import tempfile
import time
from pathlib import Path

import httpx
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.publishing import (
    connect_reporter_to_publisher,
    drop_hook,
    heartbeat_provider,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.parser.applog.parser import AppLogParser
from telemetry_agent.parser.fix.identifiers import load_hash_key
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.pipeline.monitor_adapter import (
    MonitorPipelineAdapter,
    monitors_by_resolved_path,
)
from telemetry_agent.pipeline.supervisor import PipelineBridge
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink

# Matches the simulator's "Heartbeat active" Application.log lines.
_APP_LOG_PATTERN = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+ \[[A-Z]+\]"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    parser.add_argument("--backend", default="http://127.0.0.1:8080")
    parser.add_argument("--agent-id", default="magic-agent-demo")
    parser.add_argument("--interval", type=float, default=10.0)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    os.environ.setdefault("MAGIC_TELEMETRY_ID_HASH_KEY", "dev-only")
    logs = [args.log_dir / "Application.log", args.log_dir / "Fix.log"]
    for log in logs:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.touch()

    offsets = Path(tempfile.gettempdir()) / "health_monitor_demo_offsets.json"
    monitor = MultiLogMonitor(logs, registry_path=offsets, commit_on_read=False)
    reporter = HealthReporter(
        monitor.monitors,
        heartbeat=HeartbeatConfig(agent_id=args.agent_id, instance_ids=("magic-demo",)),
    )
    registry = Registry(
        parsers={
            "fix": FixParser(hash_key=load_hash_key()),
            "applog": AppLogParser(app_log_patterns=[_APP_LOG_PATTERN]),
        }
    )
    bridge = PipelineBridge(config=PipelineConfig(parse_workers=1), registry=registry)
    # UBS-112: committed lines feed the metrics aggregator and the reporter.
    ingestor = MetricsIngestor.build_default(health_reporter=reporter)
    bridge.attach_committer(
        monitors_by_resolved_path(monitor.monitors), on_event=ingestor.on_event
    )
    adapter = MonitorPipelineAdapter(
        monitor, bridge, parser_chain=["fix", "applog"], instance_id="magic-demo"
    )

    endpoint = f"{args.backend}/telemetry/batch"
    publisher = BackendPublisher(
        HttpsPublishSink(endpoint, "dev-token", allow_insecure_endpoint=True),
        parse_publish_config({"endpoint": endpoint, "allowInsecureEndpoint": True}),
        agent_id=args.agent_id,
        application="Magic",
        heartbeat_provider=heartbeat_provider(reporter),
        on_drop=drop_hook(reporter),
    )
    connect_reporter_to_publisher(reporter, publisher)

    print(f"tailing {', '.join(str(p) for p in logs)} -> {endpoint}", flush=True)
    bridge.start()
    # One loop for the whole run: the sink's HTTP client keeps connections
    # that belong to the loop it first ran on.
    loop = asyncio.new_event_loop()
    next_publish = time.monotonic()
    lines = 0
    try:
        while True:
            lines += len(adapter.poll_once())
            if time.monotonic() < next_publish:
                continue
            next_publish = time.monotonic() + args.interval
            action = loop.run_until_complete(publisher.publish_once())
            try:
                agent = httpx.get(
                    f"{args.backend}/telemetry/health/agents/{args.agent_id}",
                    timeout=3,
                ).json()
            except httpx.HTTPError as exc:
                print(f"publish={action} backend unreachable: {exc}", flush=True)
                continue
            print(
                f"lines={lines} publish={action.name if action else None} "
                f"status={agent.get('status')} "
                f"lagMs={agent.get('logReadLagMs')} "
                f"parseErrors5m={agent.get('parseErrorCountLast5Min')} "
                f"queueDepth={agent.get('publishQueueDepth')}",
                flush=True,
            )
            # UBS-112: what the metrics aggregator now holds (last minute).
            rows = ingestor.aggregator.snapshot("1m", group_by=())
            counters = rows[()].counters if () in rows else {}
            print(
                "  metrics 1m: "
                + " ".join(
                    f"{name}={counters.get(name, 0)}"
                    for name in (
                        "log_lines_read",
                        "orders_submitted",
                        "orders_acked",
                        "orders_rejected",
                        "parse_errors",
                    )
                ),
                flush=True,
            )
    except KeyboardInterrupt:
        print("\nstopped; the backend will mark this agent missing in ~60s")
    finally:
        bridge.stop()
        monitor.close()
        loop.close()


if __name__ == "__main__":
    main()
