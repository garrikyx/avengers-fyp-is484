"""Live heartbeat demo (UBS-58): tail files, emit heartbeats on an interval.

    uv run telemetry-agent-heartbeat --interval 2 --log demo_logs/Fix.log
    uv run telemetry-agent-heartbeat --interval 2 --sink http://127.0.0.1:8000/telemetry/heartbeat

Heartbeats keep coming with zero log activity (FR-HLT-001). Append lines to a
tailed file and the next heartbeat's `files[]` / `readLagMs` move; stop
appending for > readLagDegraded and `status` flips to `degraded` with a
reason. Every tailed line is also run through the FIX parser (UBS-59): append
garbage and `parseErrorCountLast5Min` / the parse-error-rate reasons follow.
Pair it with `scripts/heartbeat_receiver_stub.py` to see the wire format
validated on the receiving side. With an http sink the heartbeats that fail to
send are queued (UBS-60): stop the receiver and `publishQueueDepth` rises until
the watermark reasons appear; start it again and the queue drains. Not the
production entrypoint — pipeline wiring is M1.5.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agent.health.config import HeartbeatConfig, load_health_config
from telemetry_agent.health.heartbeat import (
    BufferingHeartbeatSink,
    HeartbeatEmitter,
    HeartbeatSink,
    HttpHeartbeatSink,
    PrintHeartbeatSink,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import SourceMeta


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/agent.yaml"),
        help="agent YAML; heartbeat:/health:/agent: sections are read, rest ignored",
    )
    parser.add_argument(
        "--log",
        type=Path,
        action="append",
        default=[],
        help="file to tail (repeatable), created if missing; default demo_logs/Fix.log",
    )
    parser.add_argument(
        "--interval", type=float, help="override heartbeat interval (s)"
    )
    parser.add_argument("--agent-id", help="override agent.id")
    parser.add_argument(
        "--sink",
        default="stdout",
        help="'stdout' or an http(s) URL to POST each heartbeat to",
    )
    parser.add_argument("--state-dir", type=Path, default=Path("demo_logs/.state"))
    parser.add_argument(
        "--buffer",
        type=int,
        default=500,
        help="max heartbeats queued while the sink is failing (0 = no queue)",
    )
    return parser


def _make_sink(spec: str) -> HeartbeatSink:
    if spec == "stdout":
        return PrintHeartbeatSink()
    if spec.startswith(("http://", "https://")):
        return HttpHeartbeatSink(spec)
    raise SystemExit(f"--sink must be 'stdout' or an http(s) URL, got {spec!r}")


async def _poll_forever(
    monitors: dict[str, LogMonitor], reporter: HealthReporter, stop: asyncio.Event
) -> None:
    """Drain each tailed file every 250ms so read lag / offsets stay honest, and
    feed every line through the FIX parser into the reporter. This is the demo's
    stand-in for the pipeline bridge (M1.5)."""
    parser = FixParser()
    while not stop.is_set():
        for name, monitor in monitors.items():
            for line in monitor.poll_lines():
                meta = SourceMeta(
                    instance_id="demo",
                    path=name,
                    log_type="fix",
                    read_at=datetime.now(UTC),
                )
                # UBS-22: poll_lines() yields ReadLine (text + byte identity).
                reporter.record_parse_result(parser.parse(line.text.encode(), meta))
        try:
            await asyncio.wait_for(stop.wait(), timeout=0.25)
        except TimeoutError:
            continue


async def _main_async(args: argparse.Namespace) -> None:
    heartbeat_cfg, thresholds = load_health_config(args.config)
    if args.interval is not None and args.interval <= 0:
        raise SystemExit("--interval must be > 0")
    if args.interval is not None or args.agent_id is not None:
        heartbeat_cfg = HeartbeatConfig(
            interval_seconds=args.interval
            if args.interval is not None
            else heartbeat_cfg.interval_seconds,
            agent_id=args.agent_id or heartbeat_cfg.agent_id,
            instance_ids=heartbeat_cfg.instance_ids,
            agent_version=heartbeat_cfg.agent_version,
        )

    paths = args.log or [Path("demo_logs/Fix.log")]
    args.state_dir.mkdir(parents=True, exist_ok=True)
    tracker = OffsetTracker(registry_path=args.state_dir / "offsets.json")
    monitors: dict[str, LogMonitor] = {}
    for path in paths:
        key = str(path)
        if key in monitors:
            raise SystemExit(f"--log given twice: {key}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        # Keyed by the full path, not the basename: two Fix.log files in
        # different directories are two files.
        monitors[key] = LogMonitor(path, offset_tracker=tracker)

    reporter = HealthReporter(monitors, thresholds=thresholds, heartbeat=heartbeat_cfg)
    sink = _make_sink(args.sink)
    if args.buffer > 0:
        buffered = BufferingHeartbeatSink(sink, max_items=args.buffer)
        reporter.set_queue_depth_provider(lambda: len(buffered))
        sink = buffered
    emitter = HeartbeatEmitter(reporter, sink)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # Windows event loop
            signal.signal(sig, lambda *_: stop.set())

    logging.info(
        "heartbeat every %.1fs as %s -> %s; tailing %s",
        emitter.interval_seconds,
        heartbeat_cfg.agent_id,
        args.sink,
        ", ".join(str(p) for p in paths),
    )
    try:
        await asyncio.gather(emitter.run(stop), _poll_forever(monitors, reporter, stop))
    finally:
        for monitor in monitors.values():
            monitor.close()
        logging.info(
            "stopped: sent=%d failed=%d", emitter.sent_count, emitter.failed_count
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(_main_async(_build_parser().parse_args()))


if __name__ == "__main__":
    main()
