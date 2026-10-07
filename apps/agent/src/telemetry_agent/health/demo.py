"""Live heartbeat demo (UBS-58): tail files, report health on an interval.

    uv run telemetry-agent-heartbeat --interval 2 --log demo_logs/Fix.log
    uv run telemetry-agent-heartbeat --interval 2 --sink http://127.0.0.1:8080/telemetry/batch

Heartbeats keep coming with zero log activity (FR-HLT-001). Append lines to a
tailed file and the next heartbeat's `files[]` / `readLagMs` move; stop
appending for > readLagDegraded and `status` flips to `degraded` with a
reason. Every tailed line is also run through the FIX parser (UBS-59): append
garbage and `parseErrorCountLast5Min` / the parse-error-rate reasons follow.

`--sink stdout` prints each heartbeat locally. With an http(s) URL the
heartbeat goes the production way: the Backend Publisher carries it in the
`heartbeat` slot of a `TelemetryBatch` to `POST /telemetry/batch`
(`health/publishing.py`), never straight to the backend. Stop the backend and
the publisher's outbox fills, so `publishQueueDepth` rises (UBS-60); start it
again and the queue drains. Set MAGIC_TELEMETRY_PUBLISH_TOKEN for an https
backend; a plain-http local backend gets a dev token. Not the production
entrypoint (that is the agent composition root, UBS-114).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import math
import os
import signal
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from telemetry_agent.health.config import HeartbeatConfig, load_health_config
from telemetry_agent.health.heartbeat import HeartbeatEmitter, PrintHeartbeatSink
from telemetry_agent.health.publishing import (
    connect_reporter_to_publisher,
    drop_hook,
    heartbeat_provider,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.fix.session_tracker import SessionHeartbeatTracker
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.publishing.config import load_publish_token, parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink

_DEV_TOKEN = "dev-local-token"


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
        help="'stdout', or the backend batch URL "
        "(e.g. http://127.0.0.1:8080/telemetry/batch) to publish through",
    )
    parser.add_argument("--state-dir", type=Path, default=Path("demo_logs/.state"))
    return parser


def _make_publisher(
    endpoint: str, reporter: HealthReporter, cfg: HeartbeatConfig
) -> BackendPublisher:
    """The production route: reporter -> Backend Publisher -> backend."""
    insecure = endpoint.startswith("http://")
    if insecure:
        token = os.environ.get("MAGIC_TELEMETRY_PUBLISH_TOKEN") or _DEV_TOKEN
    else:
        token = load_publish_token()
    # The publisher ticks on whole seconds; the heartbeat rides on each tick.
    interval = max(1, math.ceil(cfg.interval_seconds))
    publish_cfg = parse_publish_config(
        {
            "endpoint": endpoint,
            "allowInsecureEndpoint": insecure,
            "interval": f"{interval}s",
        }
    )
    publisher = BackendPublisher(
        HttpsPublishSink(endpoint, token, allow_insecure_endpoint=insecure),
        publish_cfg,
        agent_id=cfg.agent_id,
        application="Magic",
        heartbeat_provider=heartbeat_provider(reporter),
        on_drop=drop_hook(reporter),
    )
    connect_reporter_to_publisher(reporter, publisher)
    return publisher


async def _poll_forever(
    monitors: dict[str, LogMonitor],
    reporter: HealthReporter,
    stop: asyncio.Event,
    sessions: SessionHeartbeatTracker | None = None,
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
                result = parser.parse(line.text.encode(), meta)
                reporter.record_parse_result(result)
                # UBS-106: every line is evidence its session is alive. The
                # tick in `_detect_session_timeouts` notices when they stop.
                if sessions is not None and result.fields is not None:
                    sessions.observe(
                        msg_type=(
                            result.telemetry.normalized_msg_type
                            if result.telemetry
                            else None
                        ),
                        sender=result.fields.sender_comp_id,
                        target=result.fields.target_comp_id,
                        at=monotonic(),
                    )
        try:
            await asyncio.wait_for(stop.wait(), timeout=0.25)
        except TimeoutError:
            continue


async def _detect_session_timeouts(
    sessions: SessionHeartbeatTracker, stop: asyncio.Event, interval_seconds: float
) -> None:
    """UBS-106: the periodic half of heartbeat-timeout detection.

    A timeout is the absence of a message, so it can only be noticed by a
    clock, not by parsing. This logs what it finds rather than ingesting it:
    this demo carries a `HealthReporter`, not a `MetricsAggregator`, and
    threading a metrics + rule-engine stack through a health demo to post one
    counter would be a far bigger change than the signal is worth. The
    aggregator wiring lives in `rules/demo_quickstart.py`'s act 18, where an
    aggregator already exists; here you can watch real detection against a
    real tailed log by stopping the simulator and waiting.
    """
    while not stop.is_set():
        for timeout in sessions.timed_out(monotonic()):
            logging.warning(
                "heartbeat timeout: session %s silent for %.0fs "
                "(heartbeat_timeouts +1; FixSessionDown reads this)",
                timeout.session_id,
                timeout.silent_seconds,
            )
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
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
    publisher: BackendPublisher | None = None
    emitter: HeartbeatEmitter | None = None
    if args.sink == "stdout":
        emitter = HeartbeatEmitter(reporter, PrintHeartbeatSink())
    elif args.sink.startswith(("http://", "https://")):
        publisher = _make_publisher(args.sink, reporter, heartbeat_cfg)
    else:
        raise SystemExit(
            f"--sink must be 'stdout' or an http(s) URL, got {args.sink!r}"
        )
    # UBS-106: one tracker for the process, driven by the two loops below.
    sessions = SessionHeartbeatTracker(
        timeout_seconds=thresholds.session_heartbeat_timeout_seconds
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # Windows event loop
            signal.signal(sig, lambda *_: stop.set())

    interval = heartbeat_cfg.interval_seconds
    logging.info(
        "heartbeat every %.1fs as %s -> %s; tailing %s",
        interval,
        heartbeat_cfg.agent_id,
        args.sink,
        ", ".join(str(p) for p in paths),
    )
    reporting = publisher.run(stop) if publisher is not None else None
    if emitter is not None:
        reporting = emitter.run(stop)
    if reporting is None:
        raise SystemExit("no heartbeat route configured")
    try:
        await asyncio.gather(
            reporting,
            _poll_forever(monitors, reporter, stop, sessions),
            _detect_session_timeouts(sessions, stop, interval),
        )
    finally:
        for monitor in monitors.values():
            monitor.close()
        if emitter is not None:
            logging.info(
                "stopped: sent=%d failed=%d", emitter.sent_count, emitter.failed_count
            )
        if publisher is not None:
            logging.info("stopped: publisher %s", publisher.counters.snapshot())


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(_main_async(_build_parser().parse_args()))


if __name__ == "__main__":
    main()
