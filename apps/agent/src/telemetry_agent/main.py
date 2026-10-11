"""Telemetry Agent: the one process that runs every agent component (UBS-114).

    uv run telemetry-agent --config config/agent.yaml
    uv run telemetry-agent --check-config

What runs, and on which thread:

    pipeline thread   MultiLogMonitor -> PipelineBridge (parser worker) ->
                      committer -> MetricsIngestor (UBS-112): aggregator,
                      correlator, session tracker, Health Reporter
    event loop        RuleEvaluator (UBS-113) every pipeline.evaluationInterval
                      -> AlertRouter -> BackendPublisher + CallbackDispatcher
                      Same tick, every completed publish.metricsBucketSeconds
                      bucket not yet sent: RuleEvaluator ->
                      SnapshotEmitter.emit -> BackendPublisher.enqueue_snapshot
                      (UBS-115/UBS-123)
                      BackendPublisher every publish.interval -> backend,
                      carrying the heartbeat (health/publishing.py)
                      CallbackDispatcher -> Magic callback endpoint

The pipeline thread and the loop share the metrics and health state, which is
not thread-safe; everything that touches it from the loop holds
`ingestor.lock` (the evaluator, the heartbeat provider, the drop hook).
Alerts are routed on the loop, so the dispatcher's asyncio queue is only
used from its own loop.

The parser CLI that used to live here is still `telemetry-parser`.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import signal
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx

from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import DryRunCallbackSink, HttpsCallbackSink
from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_agent.config import (
    DEFAULT_CONFIG_PATH,
    AgentConfig,
    AgentConfigError,
    load_agent_config,
)
from telemetry_agent.health.publishing import (
    connect_reporter_to_publisher,
    drop_hook,
    heartbeat_provider,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.parser.applog.parser import AppLogParser
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.pipeline.monitor_adapter import (
    MonitorPipelineAdapter,
    monitors_by_resolved_path,
)
from telemetry_agent.pipeline.supervisor import PipelineBridge
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import DryRunPublishSink, HttpsPublishSink
from telemetry_agent.publishing.snapshot_bridge import SnapshotEmitter
from telemetry_agent.rules.config_loader import SighupRuleReloader
from telemetry_agent.rules.engine import RuleEngine

logger = logging.getLogger("telemetry_agent")

APPLICATION = "Magic"
SHUTDOWN_GRACE_SECONDS = 5.0  # spec 002 s8.2

_HASH_KEY_ENV = "MAGIC_TELEMETRY_ID_HASH_KEY"
_TOKEN_ENV = "MAGIC_TELEMETRY_PUBLISH_TOKEN"
_SECRET_ENV = "MAGIC_TELEMETRY_CALLBACK_SECRET"
# Used only when every endpoint is on this machine (local development).
_DEV_HASH_KEY = "dev-only"
_DEV_TOKEN = "dev-local-token"
_DEV_SECRET = "dev-local-secret"


@dataclass
class Agent:
    config: AgentConfig
    monitor: MultiLogMonitor
    reporter: HealthReporter
    ingestor: MetricsIngestor
    bridge: PipelineBridge
    adapter: MonitorPipelineAdapter
    publisher: BackendPublisher
    publish_sink: HttpsPublishSink | DryRunPublishSink
    dispatcher: CallbackDispatcher | None
    callback_sink: HttpsCallbackSink | DryRunCallbackSink | None
    router: AlertRouter
    engine: RuleEngine
    evaluator: RuleEvaluator


def _is_local(url: str) -> bool:
    return urlparse(url).hostname in {"127.0.0.1", "localhost", "::1"}


def _secret(env: Mapping[str, str], name: str, dev_value: str, *, local: bool) -> str:
    value = env.get(name, "")
    if value:
        return value
    if local:
        logger.warning("%s not set; using a dev value (localhost only)", name)
        return dev_value
    raise RuntimeError(f"{name} is required but not set")


def build_agent(
    cfg: AgentConfig,
    *,
    publish_transport: httpx.AsyncBaseTransport | None = None,
    callback_transport: httpx.AsyncBaseTransport | None = None,
    started_at: datetime | None = None,
    env: Mapping[str, str] | None = None,
) -> Agent:
    """Wire every component from config. Transports, the engine start time
    and the environment are injectable for tests; production passes none."""
    env = os.environ if env is None else env
    local = _is_local(cfg.publish.endpoint) and (
        cfg.callbacks is None or _is_local(cfg.callbacks.endpoint)
    )

    # --- tail -> parse -> ingest (pipeline thread) -------------------------------
    cfg.logs.state_dir.mkdir(parents=True, exist_ok=True)
    for path in cfg.logs.paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
    monitor = MultiLogMonitor(
        list(cfg.logs.paths),
        registry_path=cfg.logs.state_dir / "offsets.json",
        commit_on_read=False,  # offsets move only once a line is ingested
    )
    reporter = HealthReporter(
        monitor.monitors, thresholds=cfg.thresholds, heartbeat=cfg.heartbeat
    )
    ingestor = MetricsIngestor.build_default(
        health_reporter=reporter,
        session_timeout_seconds=cfg.thresholds.session_heartbeat_timeout_seconds,
    )
    hash_key = _secret(env, _HASH_KEY_ENV, _DEV_HASH_KEY, local=local).encode()
    parsers: dict[str, FixParser | AppLogParser] = {"fix": FixParser(hash_key=hash_key)}
    chain = ["fix"]
    if cfg.logs.app_log_patterns:
        parsers["applog"] = AppLogParser(
            app_log_patterns=list(cfg.logs.app_log_patterns),
            error_signatures=list(cfg.parsing.error_signatures),
            max_dynamic_signature_labels=cfg.parsing.max_dynamic_signature_labels,
        )
        chain.append("applog")
    bridge = PipelineBridge(
        config=PipelineConfig(parse_workers=cfg.parse_workers),
        registry=Registry(parsers=parsers),
    )
    bridge.attach_committer(
        monitors_by_resolved_path(monitor.monitors), on_event=ingestor.on_event
    )
    adapter = MonitorPipelineAdapter(
        monitor, bridge, parser_chain=chain, instance_id=cfg.instance_id
    )

    # --- publish (event loop); the heartbeat rides in every batch ----------------
    publish_sink: HttpsPublishSink | DryRunPublishSink
    if cfg.publish.dry_run:
        publish_sink = DryRunPublishSink()
    else:
        publish_sink = HttpsPublishSink(
            cfg.publish.endpoint,
            _secret(env, _TOKEN_ENV, _DEV_TOKEN, local=local),
            compress_threshold=cfg.publish.compress_threshold,
            connect_timeout_seconds=cfg.publish.connect_timeout_seconds,
            total_timeout_seconds=cfg.publish.timeout_seconds,
            allow_insecure_endpoint=cfg.publish.allow_insecure_endpoint,
            transport=publish_transport,
        )
    publisher = BackendPublisher(
        publish_sink,
        cfg.publish,
        agent_id=cfg.agent_id,
        application=APPLICATION,
        heartbeat_provider=heartbeat_provider(reporter, lock=ingestor.lock),
        on_drop=drop_hook(reporter, lock=ingestor.lock),
    )
    with ingestor.lock:
        connect_reporter_to_publisher(reporter, publisher)

    # --- callbacks to Magic ---------------------------------------------------------
    dispatcher: CallbackDispatcher | None = None
    callback_sink: HttpsCallbackSink | DryRunCallbackSink | None = None
    if cfg.callbacks is not None:
        if cfg.callbacks.dry_run:
            callback_sink = DryRunCallbackSink()
        else:
            callback_sink = HttpsCallbackSink(
                cfg.callbacks.endpoint,
                connect_timeout_seconds=cfg.callbacks.connect_timeout_seconds,
                total_timeout_seconds=cfg.callbacks.timeout_seconds,
                allow_insecure_callback=cfg.callbacks.allow_insecure_callback,
                transport=callback_transport,
            )
        dispatcher = CallbackDispatcher(
            callback_sink,
            cfg.callbacks,
            _secret(env, _SECRET_ENV, _DEV_SECRET, local=local).encode(),
        )

    # --- rules (event loop, UBS-113) ---------------------------------------------
    router = AlertRouter(
        publisher, agent_id=cfg.agent_id, application=APPLICATION, dispatcher=dispatcher
    )
    engine = RuleEngine(
        cfg.rules,
        instance_id=cfg.instance_id,
        application=APPLICATION,
        agent_id=cfg.agent_id,
        started_at=started_at or datetime.now(UTC),
    )
    evaluator_counters = CounterRegistry()  # shared so shutdown logs emitter skips
    evaluator = RuleEvaluator(
        engine,
        ingestor.aggregator,
        router,
        instance_id=cfg.instance_id,
        correlator=ingestor.correlator,
        session_tracker=ingestor.session_tracker,
        publisher=publisher,
        dispatcher=dispatcher,
        reloader=SighupRuleReloader(engine, cfg.rules_path),
        interval_seconds=cfg.evaluation_interval_seconds,
        lock=ingestor.lock,
        monotonic=ingestor.monotonic,
        counters=evaluator_counters,
        snapshot_emitter=SnapshotEmitter(
            ingestor.aggregator,
            publisher,
            bucket_seconds=cfg.publish.metrics_bucket_seconds,
            agent_id=cfg.agent_id,
            application=APPLICATION,
            instance_id=cfg.instance_id,
            correlator=ingestor.correlator,
            counters=evaluator_counters,
        ),
    )
    return Agent(
        config=cfg,
        monitor=monitor,
        reporter=reporter,
        ingestor=ingestor,
        bridge=bridge,
        adapter=adapter,
        publisher=publisher,
        publish_sink=publish_sink,
        dispatcher=dispatcher,
        callback_sink=callback_sink,
        router=router,
        engine=engine,
        evaluator=evaluator,
    )


def _pump(adapter: MonitorPipelineAdapter, halt: threading.Event) -> None:
    """The pipeline thread: tail, parse and ingest until told to stop."""
    while not halt.is_set():
        adapter.poll_once(poll_interval=0.05)


async def run_agent(agent: Agent, stop: asyncio.Event) -> None:
    """Run until `stop` is set, then shut down within SHUTDOWN_GRACE_SECONDS."""
    halt = threading.Event()
    agent.bridge.start()
    pipeline = asyncio.create_task(asyncio.to_thread(_pump, agent.adapter, halt))

    def _pipeline_died(task: asyncio.Task[None]) -> None:
        if not task.cancelled() and task.exception() is not None:
            logger.error("pipeline thread stopped", exc_info=task.exception())
            stop.set()  # without the pipeline the agent would report stale data

    pipeline.add_done_callback(_pipeline_died)
    delivery = asyncio.create_task(agent.dispatcher.run()) if agent.dispatcher else None
    try:
        await asyncio.gather(agent.publisher.run(stop), agent.evaluator.run(stop))
    finally:
        await _shutdown(agent, halt, pipeline, delivery)


async def _shutdown(
    agent: Agent,
    halt: threading.Event,
    pipeline: asyncio.Task[None],
    delivery: asyncio.Task[None] | None,
) -> None:
    halt.set()
    with contextlib.suppress(Exception):
        await asyncio.wait_for(pipeline, SHUTDOWN_GRACE_SECONDS)
    agent.bridge.stop()
    with agent.ingestor.lock:
        for log_monitor in agent.monitor.monitors.values():
            log_monitor.flush_commits()
    # One last batch so the final heartbeat and any routed alerts go out.
    with contextlib.suppress(Exception):
        await asyncio.wait_for(agent.publisher.publish_once(), SHUTDOWN_GRACE_SECONDS)
    if delivery is not None:
        delivery.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await delivery
    for sink in (agent.publish_sink, agent.callback_sink):
        aclose = getattr(sink, "aclose", None)
        if aclose is not None:
            with contextlib.suppress(Exception):
                await aclose()
    agent.monitor.close()
    logger.info(
        "stopped: ingest %s, evaluator %s, publisher %s",
        agent.ingestor.stats(),
        agent.evaluator.counters.snapshot(),
        agent.publisher.counters.snapshot(),
    )


def _install_signals(
    loop: asyncio.AbstractEventLoop, agent: Agent, stop: asyncio.Event
) -> None:
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # Windows event loop
            signal.signal(sig, lambda *_: loop.call_soon_threadsafe(stop.set))
    sighup = getattr(signal, "SIGHUP", None)  # absent on Windows
    if sighup is not None:
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sighup, agent.evaluator.request_reload)


async def _main_async(cfg: AgentConfig) -> None:
    agent = build_agent(cfg)
    stop = asyncio.Event()
    _install_signals(asyncio.get_running_loop(), agent, stop)
    callbacks = (
        "off"
        if cfg.callbacks is None
        else ("dry-run" if cfg.callbacks.dry_run else cfg.callbacks.endpoint)
    )
    logger.info(
        "agent %s (%s) tailing %s -> %s; %d rules every %.0fs; callbacks %s",
        cfg.agent_id,
        cfg.instance_id,
        ", ".join(str(p) for p in cfg.logs.paths),
        "dry-run" if cfg.publish.dry_run else cfg.publish.endpoint,
        len(cfg.rules),
        cfg.evaluation_interval_seconds,
        callbacks,
    )
    await run_agent(agent, stop)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magic Telemetry Agent")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--log-level", default="info")
    parser.add_argument(
        "--check-config", action="store_true", help="validate the config and exit"
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        cfg = load_agent_config(args.config)
    except AgentConfigError as exc:
        raise SystemExit(f"config error: {exc}") from exc
    if args.check_config:
        callbacks = (
            "" if cfg.callbacks is None else f", callbacks -> {cfg.callbacks.endpoint}"
        )
        print(
            f"config ok: agent {cfg.agent_id} ({cfg.instance_id}), "
            f"{len(cfg.logs.paths)} log files, {len(cfg.rules)} rules, "
            f"publish -> {cfg.publish.endpoint}{callbacks}"
        )
        return
    try:
        asyncio.run(_main_async(cfg))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
