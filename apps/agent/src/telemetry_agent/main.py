"""Telemetry Agent: the one process that runs every agent component (UBS-114).

    uv run telemetry-agent --config config/agent.yaml
    uv run telemetry-agent --check-config
    uv run telemetry-agent --test-rule HighRejectRate --replay logs/Fix.log

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
                      ActionRunner -> a rule's actions on pending->firing,
                      one at a time (UBS-35, spec 005 s5)

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
import json
import logging
import os
import signal
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

import httpx
from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.actions.config import (
    ActionCatalogue,
    ActionConfigError,
    ActionType,
    load_action_catalogue,
)
from telemetry_agent.actions.runner import ActionRunner
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
from telemetry_agent.pipeline.backtest import ReplayParsers, backtest
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.pipeline.monitor_adapter import (
    MonitorPipelineAdapter,
    monitors_by_resolved_path,
)
from telemetry_agent.pipeline.supervisor import PipelineBridge
from telemetry_agent.publishing.events import EventEmitter
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
    actions: ActionRunner


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
        log_stall_threshold=cfg.logs.log_stall_threshold_seconds,
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
    events = EventEmitter(
        publisher,
        agent_id=cfg.agent_id,
        application=APPLICATION,
        instance_id=cfg.instance_id,
        max_events_per_minute=cfg.publish.max_events_per_minute,
        execution_sample_every=cfg.publish.execution_sample_every,
        bucket_seconds=cfg.publish.metrics_bucket_seconds,
        on_drop=drop_hook(reporter, lock=ingestor.lock),
    )
    ingestor.event_emitter = events

    def log_event(event_type: str, source_index: int) -> None:
        with ingestor.lock:
            events.log_lifecycle(event_type, source_index)

    for source_index, file_monitor in enumerate(monitor.monitors.values()):
        file_monitor.on_event = partial(log_event, source_index=source_index)

    def callback_failed(
        alert: AlertEvent, reason: str, attempts: int, status: int | None
    ) -> None:
        with ingestor.lock:
            events.callback_failed(alert, reason, attempts, status)

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
            on_delivery_settled=publisher.enqueue_alert,
            on_failure=callback_failed,
        )

    # --- rules (event loop, UBS-113) ---------------------------------------------
    engine = RuleEngine(
        cfg.rules,
        instance_id=cfg.instance_id,
        application=APPLICATION,
        agent_id=cfg.agent_id,
        started_at=started_at or datetime.now(UTC),
    )

    # --- rule actions (UBS-35); reloaded with the rules file ---------------------
    env_secret = env.get(_SECRET_ENV, "")

    def check_action_secret(catalogue: ActionCatalogue) -> None:
        """A callback action is signed like the Magic callback. The dev
        secret is only acceptable when every callback endpoint is local."""
        endpoints = [
            a.callbacks.endpoint
            for a in catalogue.values()
            if a.type is ActionType.CALLBACK and a.callbacks is not None
        ]
        if env_secret or not endpoints:
            return
        if local and all(_is_local(url) for url in endpoints):
            logger.warning(
                "%s not set; using a dev value (localhost only)", _SECRET_ENV
            )
            return
        raise ActionConfigError(f"{_SECRET_ENV} is required for callback actions")

    try:
        check_action_secret(cfg.actions)
    except ActionConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    def rule_actions(rule_name: str) -> tuple[str, ...]:
        rule = next((r for r in engine.rules if r.name == rule_name), None)
        return rule.actions if rule is not None else ()

    actions = ActionRunner(
        cfg.actions,
        rule_actions,
        secret=(env_secret or _DEV_SECRET).encode(),
        callback_transport=callback_transport,
    )

    def stage_actions(path: Path) -> Callable[[], None]:
        catalogue = load_action_catalogue(path, allowed_commands=cfg.allowed_commands)
        check_action_secret(catalogue)
        return lambda: actions.replace_catalogue(catalogue)

    router = AlertRouter(
        publisher,
        agent_id=cfg.agent_id,
        application=APPLICATION,
        dispatcher=dispatcher,
        actions=actions,
        on_event=ingestor.emit_alert,
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
        reloader=SighupRuleReloader(engine, cfg.rules_path, stage=stage_actions),
        interval_seconds=cfg.evaluation_interval_seconds,
        reload_check_seconds=cfg.rules_reload_check_seconds,
        lock=ingestor.lock,
        monotonic=ingestor.monotonic,
        counters=evaluator_counters,
        event_emitter=events,
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
        actions=actions,
    )


def _pump(adapter: MonitorPipelineAdapter, halt: threading.Event) -> None:
    """The pipeline thread: tail, parse and ingest until told to stop."""
    while not halt.is_set():
        adapter.poll_once(poll_interval=0.05)


async def run_agent(agent: Agent, stop: asyncio.Event) -> None:
    """Run until `stop` is set, then shut down within SHUTDOWN_GRACE_SECONDS."""
    halt = threading.Event()
    agent.bridge.start()
    with agent.ingestor.lock:
        if agent.ingestor.event_emitter is not None:
            agent.ingestor.event_emitter.emit("agent.started", at=datetime.now(UTC))
            if agent.monitor.state_reset_reason is not None:
                agent.ingestor.event_emitter.state_reset(
                    agent.monitor.state_reset_reason
                )
    pipeline = asyncio.create_task(asyncio.to_thread(_pump, agent.adapter, halt))

    def _pipeline_died(task: asyncio.Task[None]) -> None:
        if not task.cancelled() and task.exception() is not None:
            logger.error("pipeline thread stopped", exc_info=task.exception())
            stop.set()  # without the pipeline the agent would report stale data

    pipeline.add_done_callback(_pipeline_died)
    delivery = asyncio.create_task(agent.dispatcher.run()) if agent.dispatcher else None
    action_runs = asyncio.create_task(agent.actions.run())
    try:
        await asyncio.gather(agent.publisher.run(stop), agent.evaluator.run(stop))
    finally:
        await _shutdown(agent, halt, pipeline, delivery, action_runs)


async def _shutdown(
    agent: Agent,
    halt: threading.Event,
    pipeline: asyncio.Task[None],
    delivery: asyncio.Task[None] | None,
    action_runs: asyncio.Task[None] | None = None,
) -> None:
    halt.set()
    with contextlib.suppress(Exception):
        await asyncio.wait_for(pipeline, SHUTDOWN_GRACE_SECONDS)
    agent.bridge.stop()
    with agent.ingestor.lock:
        if agent.ingestor.event_emitter is not None:
            now = datetime.now(UTC)
            agent.ingestor.event_emitter.flush(now, force=True)
            agent.ingestor.event_emitter.emit("agent.stopping", at=now)
        for log_monitor in agent.monitor.monitors.values():
            log_monitor.flush_commits()
    # One last batch so the final heartbeat and any routed alerts go out.
    with contextlib.suppress(Exception):
        await asyncio.wait_for(agent.publisher.publish_once(), SHUTDOWN_GRACE_SECONDS)
    for task in (delivery, action_runs):
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
    with contextlib.suppress(Exception):
        await agent.actions.aclose()
    for sink in (agent.publish_sink, agent.callback_sink):
        aclose = getattr(sink, "aclose", None)
        if aclose is not None:
            with contextlib.suppress(Exception):
                await aclose()
    agent.monitor.close()
    logger.info(
        "stopped: ingest %s, evaluator %s, publisher %s, events %s",
        agent.ingestor.stats(),
        agent.evaluator.counters.snapshot(),
        agent.publisher.counters.snapshot(),
        agent.ingestor.event_emitter.counters.snapshot()
        if agent.ingestor.event_emitter is not None
        else {},
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
        "agent %s (%s) tailing %s -> %s; %d rules every %.0fs; callbacks %s; "
        "%d actions",
        cfg.agent_id,
        cfg.instance_id,
        ", ".join(str(p) for p in cfg.logs.paths),
        "dry-run" if cfg.publish.dry_run else cfg.publish.endpoint,
        len(cfg.rules),
        cfg.evaluation_interval_seconds,
        callbacks,
        len(cfg.actions),
    )
    await run_agent(agent, stop)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magic Telemetry Agent")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--log-level", default="info")
    parser.add_argument(
        "--check-config", action="store_true", help="validate the config and exit"
    )
    test = parser.add_argument_group(
        "test mode (UBS-36)",
        "replay log files through one rule, draft or active, and report when it "
        "would have fired; nothing is published, called back or run",
    )
    test.add_argument("--test-rule", metavar="NAME", help="the rule to test")
    test.add_argument(
        "--replay", nargs="+", type=Path, metavar="LOG", help="log files to replay"
    )
    test.add_argument(
        "--replay-date",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="date for Application.log times when no FIX line carries one",
    )
    test.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def _test_rule(cfg: AgentConfig, args: argparse.Namespace) -> None:
    rule = next((r for r in cfg.rules if r.name == args.test_rule), None)
    if rule is None:
        names = ", ".join(r.name for r in cfg.rules)
        raise SystemExit(f"unknown rule {args.test_rule!r}; rules: {names}")
    if not args.replay:
        raise SystemExit("--test-rule needs --replay LOG [LOG ...]")
    missing = [str(p) for p in args.replay if not p.is_file()]
    if missing:
        raise SystemExit(f"replay file(s) not found: {', '.join(missing)}")
    report = backtest(
        rule,
        args.replay,
        parsers=ReplayParsers(
            hash_key=(os.environ.get(_HASH_KEY_ENV) or _DEV_HASH_KEY).encode(),
            app_log_patterns=cfg.logs.app_log_patterns,
            error_signatures=cfg.parsing.error_signatures,
            max_dynamic_signature_labels=cfg.parsing.max_dynamic_signature_labels,
        ),
        instance_id=cfg.instance_id,
        agent_id=cfg.agent_id,
        evaluation_interval_seconds=cfg.evaluation_interval_seconds,
        actions=cfg.actions,
        replay_date=args.replay_date,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.render_text())


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
    if args.test_rule:
        _test_rule(cfg, args)
        return
    if args.check_config:
        callbacks = (
            "" if cfg.callbacks is None else f", callbacks -> {cfg.callbacks.endpoint}"
        )
        print(
            f"config ok: agent {cfg.agent_id} ({cfg.instance_id}), "
            f"{len(cfg.logs.paths)} log files, {len(cfg.rules)} rules, "
            f"{len(cfg.actions)} actions, "
            f"publish -> {cfg.publish.endpoint}{callbacks}"
        )
        return
    try:
        asyncio.run(_main_async(cfg))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
