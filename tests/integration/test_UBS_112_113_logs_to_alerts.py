"""UBS-112 + UBS-113 together: a reject burst in a tailed log becomes an alert
in the backend's alert store, with no hand-fed step in between.

    Fix.log -> MultiLogMonitor -> PipelineBridge (parser worker thread)
      -> committer -> MetricsIngestor (UBS-112)
      -> RuleEvaluator (UBS-113, sharing the ingestor's lock and clock)
      -> AlertRouter (UBS-109/110) -> BackendPublisher (+ CallbackDispatcher)
      -> POST /telemetry/batch -> alert store -> GET /telemetry/alerts

The same batches carry the Health Reporter's heartbeat, so the agent also
shows up in GET /telemetry/health/agents.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.publishing import (
    connect_reporter_to_publisher,
    drop_hook,
    heartbeat_provider,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
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
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_backend.main import create_app

AGENT_ID = "magic-agent-sg-01"
APPLICATION = "Magic"
INSTANCE = "magic-prod-01"
ENDPOINT = "https://backend.example/telemetry/batch"
HASH_KEY = b"ubs-112-113-integration-key"
BURST = 51  # RejectSpike fires above 50 rejects in its window


class _NullCallbackSink:
    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> CallbackResult:
        return CallbackResult(status_code=200, latency_ms=1.0)


def _burst_lines(sending_time: str) -> list[str]:
    lines: list[str] = []
    seq = 1
    for tag in range(BURST):
        lines.append(
            f"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34={seq}|52={sending_time}"
            f"|11=C{tag}|55=AAPL|54=1|40=2|38=100|10=000|"
        )
        lines.append(
            f"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34={seq + 1}|52={sending_time}"
            f"|11=C{tag}|37=O{tag}|17=E{tag}|55=AAPL|54=1|150=8|39=8|103=3|10=000|"
        )
        seq += 2
    return lines


async def _publish_and_query(
    app: object, publisher: BackendPublisher
) -> tuple[PublishAction | None, dict[str, object], httpx.Response]:
    """Publish, let the backend's ingestion worker process the batch, then
    read it back - all in one event loop (the ingestion queue binds to the
    first loop that touches it)."""
    action = await publisher.publish_once()
    service = app.state.ingestion  # type: ignore[attr-defined]
    worker = asyncio.create_task(service.run())
    try:
        await service._queue.join()  # noqa: SLF001 - same as test_UBS_109
    finally:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://backend"
    ) as client:
        alerts = (
            await client.get("/telemetry/alerts", params={"status": "active"})
        ).json()
        agent = await client.get(f"/telemetry/health/agents/{AGENT_ID}")
    return action, alerts, agent


def test_a_logged_reject_burst_reaches_the_backend_alert_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAGIC_TELEMETRY_ID_HASH_KEY", HASH_KEY.decode())
    now = datetime.now(UTC)
    fix_log = tmp_path / "Fix.log"
    with fix_log.open("w", encoding="utf-8", newline="\n") as f:
        for line in _burst_lines(now.strftime("%Y%m%d-%H:%M:%S.%f")[:-3]):
            f.write(line + "\n")

    # --- agent: tail -> pipeline -> UBS-112 ingestor -----------------------------
    monitor = MultiLogMonitor(
        [fix_log], registry_path=tmp_path / "offsets.json", commit_on_read=False
    )
    reporter = HealthReporter(
        monitor.monitors,
        heartbeat=HeartbeatConfig(agent_id=AGENT_ID, instance_ids=(INSTANCE,)),
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
        committed = sum(1 for _ in adapter.run_until(max_lines=500, idle_rounds=3))
    finally:
        bridge.stop()
        monitor.close()
    assert committed == 2 * BURST
    assert ingestor.stats()["ingest_errors"] == 0

    # --- agent: publisher, router, dispatcher, UBS-113 evaluator ------------------
    app = create_app()
    publisher = BackendPublisher(
        HttpsPublishSink(
            ENDPOINT, "test-token", transport=httpx.ASGITransport(app=app)
        ),
        parse_publish_config({"endpoint": ENDPOINT}),
        agent_id=AGENT_ID,
        application=APPLICATION,
        heartbeat_provider=heartbeat_provider(reporter),
        on_drop=drop_hook(reporter),
    )
    connect_reporter_to_publisher(reporter, publisher)
    dispatcher = CallbackDispatcher(
        _NullCallbackSink(),
        parse_callbacks_config({"endpoint": "https://magic.example/cb"}),
        b"secret",
    )
    router = AlertRouter(
        publisher, agent_id=AGENT_ID, application=APPLICATION, dispatcher=dispatcher
    )
    rule = replace(
        next(r for r in DEFAULT_RULES if r.name == "RejectSpike"), for_seconds=0
    )
    engine = RuleEngine(
        rules=(rule,),
        instance_id=INSTANCE,
        application=APPLICATION,
        agent_id=AGENT_ID,
        started_at=now - timedelta(hours=1),
    )
    evaluator = RuleEvaluator(
        engine,
        ingestor.aggregator,
        router,
        instance_id=INSTANCE,
        correlator=ingestor.correlator,
        session_tracker=ingestor.session_tracker,
        publisher=publisher,
        dispatcher=dispatcher,
        lock=ingestor.lock,  # the convention both tickets document
        monotonic=ingestor.monotonic,
    )

    routed = evaluator.evaluate_once(now=now) + evaluator.evaluate_once(
        now=now + timedelta(seconds=1)
    )
    assert [(a.rule_name, a.status) for a in routed] == [("RejectSpike", "firing")]
    assert publisher.queue_depth() == 1  # the alert, waiting for the next batch
    assert len(dispatcher.tracker.snapshot()) == 1  # and queued for Magic (UBS-110)

    # --- backend: one batch carries the alert and the heartbeat --------------------
    action, alerts, agent = asyncio.run(_publish_and_query(app, publisher))
    assert action is PublishAction.COMMIT
    assert [a["ruleName"] for a in alerts["alerts"]] == ["RejectSpike"]  # type: ignore[index]
    assert alerts["alerts"][0]["source"] == "agent"  # type: ignore[index]
    assert agent.status_code == 200
    assert agent.json()["status"] == "healthy"
