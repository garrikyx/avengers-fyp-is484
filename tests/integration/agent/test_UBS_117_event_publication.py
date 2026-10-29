"""UBS-117 + UBS-118: real files -> monitor/parser -> HTTP batch -> query API.

FR-PUB-001, FR-MET-020/022 and NFR-SEC-002. No host detector or MCP is mocked
into existence: only the transport is in-process, using the real backend app.
"""

from __future__ import annotations

import asyncio
import gzip
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from telemetry_agent.callbacks.sink import HttpsCallbackSink
from telemetry_agent.config import load_agent_config
from telemetry_agent.main import build_agent, run_agent
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.sink import HttpsPublishSink
from telemetry_backend.main import create_app

from tests.unit.agent.callbacks.callback_fixtures import make_alert_event

ROOT = Path(__file__).resolve().parents[3]


def config(tmp_path):
    cfg = load_agent_config(ROOT / "config/agent.yaml")
    return replace(
        cfg,
        logs=replace(
            cfg.logs,
            paths=(tmp_path / "Application.log", tmp_path / "Fix.log"),
            state_dir=tmp_path / "state",
        ),
        rules=tuple(
            replace(r, resolve_after_seconds=0)
            for r in cfg.rules
            if r.name == "AppOutOfMemory"
        ),
    )


class CaptureTransport(httpx.AsyncBaseTransport):
    def __init__(self, app):
        self.transport = httpx.ASGITransport(app=app)
        self.batches = []

    async def handle_async_request(self, request):
        body = await request.aread()
        if request.headers.get("content-encoding") == "gzip":
            body = gzip.decompress(body)
        self.batches.append(json.loads(body))
        return await self.transport.handle_async_request(request)


def test_monitor_parser_events_alerts_and_query_round_trip(tmp_path, monkeypatch):
    backend = create_app(enable_heartbeat_monitor=False)
    transport = CaptureTransport(backend)
    callbacks = []

    def callback(request):
        callbacks.append(json.loads(request.content))
        return httpx.Response(200)

    cfg = config(tmp_path)
    now = datetime.now(UTC)
    agent = build_agent(
        cfg,
        publish_transport=transport,
        callback_transport=httpx.MockTransport(callback),
        started_at=now - timedelta(hours=1),
        env={"MAGIC_TELEMETRY_ID_HASH_KEY": "test-key"},
    )
    cfg.logs.paths[0].write_text(
        "01:00:00.000001 <123456> [F] MAIN: OutOfMemoryError PRIVATE_APP_MESSAGE\n" * 3
        + "01:00:00.000002 <123456> [E] VS_788: PRIVATE_UNKNOWN_ERROR\n" * 2
        + "01:00:00.000003 <123456> [I] MAIN: PRIVATE_NORMAL_MESSAGE\n"
        + "01:00:00.000004 <123456> [E] VS_788: "
        "timed out after 00:00:30 PRIVATE_TIMEOUT\n"
        "01:00:00.000005 <123456> [W] VS_788: "
        "failed to complete connection PRIVATE_FAILURE\n"
        "01:00:00.000006 <123456> [F] VS_788: "
        "GR connection disconnected PRIVATE_DISCONNECT\n"
    )
    cfg.logs.paths[1].write_text(
        "8=FIX.4.2|9=99|35=A|34=1|49=MAGIC|56=VENUE|10=000|\n"
        "8=FIX.4.2|9=99|35=8|34=4|49=MAGIC|56=VENUE|150=8|39=8|103=3|"
        "11=PRIVATE_ORDER|1=PRIVATE_ACCOUNT|44=123.456789|58=PRIVATE_TEXT|10=000|\n"
    )
    agent.bridge.start()
    try:
        assert len(list(agent.adapter.run_until(idle_rounds=3))) == 11
        assert agent.ingestor.stats()["ingest_errors"] == 0
        assert agent.ingestor.event_emitter is not None
        assert (
            agent.ingestor.event_emitter.counters.snapshot().get(
                "event_build_errors", 0
            )
            == 0
        )
        assert agent.evaluator.evaluate_once(now=now + timedelta(seconds=1)) == []
        (fired,) = agent.evaluator.evaluate_once(now=now + timedelta(seconds=2))
        assert fired.rule_name == "AppOutOfMemory"
        mono = agent.ingestor.monotonic() + 61
        agent.evaluator.evaluate_once(
            now=now + timedelta(seconds=11), monotonic_now=mono
        )
        agent.evaluator.evaluate_once(
            now=now + timedelta(seconds=12), monotonic_now=mono + 1
        )
        monkeypatch.setattr(
            agent.ingestor.aggregator,
            "_clock",
            lambda: (now + timedelta(seconds=80)).timestamp(),
        )
        transitions = agent.evaluator.evaluate_once(
            now=now + timedelta(seconds=80), monotonic_now=mono + 2
        )
        transitions += agent.evaluator.evaluate_once(
            now=now + timedelta(seconds=81), monotonic_now=mono + 3
        )
        (resolved,) = transitions
        assert resolved.status == "resolved"

        async def deliver():
            worker = asyncio.create_task(backend.state.ingestion.run())
            try:
                # Local callbacks do not depend on successful backend delivery.
                assert agent.dispatcher is not None
                await agent.dispatcher._deliver(fired)
                await agent.dispatcher._deliver(resolved)
                assert len(callbacks) == 2
                assert await agent.publisher.publish_once() is PublishAction.COMMIT
                await asyncio.wait_for(backend.state.ingestion._queue.join(), 5)
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=backend),
                    base_url="http://backend",
                ) as client:
                    response = await client.get(
                        "/telemetry/events", params={"instanceId": cfg.instance_id}
                    )
                    assert response.status_code == 200
                    events = response.json()["events"]
                    types = [e["eventType"] for e in events]
                    assert types.count("fix.session_state") == 2  # logon + one timeout
                    assert types.count("fix.order_reject") == 1
                    assert types.count("fix.seq_gap") == 1
                    assert types.count("app.error_signature") == 6
                    # W-level venue problems also reach the event API without
                    # firing a rule or carrying the original message.
                    venue_events = {
                        e["dimensions"]["errorSignature"]: (
                            e["dimensions"]["level"],
                            e["severity"],
                        )
                        for e in events
                        if e["eventType"] == "app.error_signature"
                        and e["dimensions"]["errorSignature"] != "out_of_memory"
                    }
                    assert venue_events == {
                        "connection_timeout": ("E", "warning"),
                        "venue_connection_failed": ("W", "warning"),
                        "connection_disconnected": ("F", "critical"),
                    }
                    assert types.count("alert.fired") == 1
                    assert types.count("alert.resolved") == 1
                    summaries = [e for e in events if e["eventType"] == "app.error"]
                    # File processing can straddle a real bucket boundary.
                    assert {
                        level: sum(
                            e["fields"]["count"]
                            for e in summaries
                            if e["dimensions"]["level"] == level
                        )
                        for level in ("E", "F")
                    } == {"E": 3, "F": 4}
                    assert all(
                        e["fields"]["ruleName"] == "AppOutOfMemory"
                        for e in events
                        if e["eventType"].startswith("alert.")
                    )
                    critical = await client.get(
                        "/telemetry/events",
                        params={"severity": "critical", "eventType": "app.error"},
                    )
                    critical_events = critical.json()["events"]
                    assert all(e["dimensions"]["level"] == "F" for e in critical_events)
                    assert sum(e["fields"]["count"] for e in critical_events) == 4
                    detail = await client.get(
                        f"/telemetry/events/{events[0]['eventId']}"
                    )
                    assert detail.status_code == 200
                    # Unknown free-text fields still fail at the backend boundary.
                    unsafe = dict(events[0], fields={"message": "PRIVATE_INJECTION"})
                    assert (
                        await client.post(
                            "/telemetry/events", json={"events": [unsafe]}
                        )
                    ).status_code == 400
            finally:
                worker.cancel()
                await asyncio.gather(worker, return_exceptions=True)
                if isinstance(agent.publish_sink, HttpsPublishSink):
                    await agent.publish_sink.aclose()
                if isinstance(agent.callback_sink, HttpsCallbackSink):
                    await agent.callback_sink.aclose()

        asyncio.run(deliver())
        wire = json.dumps(transport.batches)
        assert "PRIVATE_" not in wire
        assert "123.456789" not in wire
        assert "8=FIX" not in wire
        # Each alert is published when routed, then again once its callback
        # settles, now carrying the delivery outcome (FR-CBK-009).
        assert [
            (a["status"], a["callbackDelivery"]["status"])
            for a in transport.batches[0]["alerts"]
        ] == [
            ("firing", "pending"),
            ("resolved", "pending"),
            ("firing", "delivered"),
            ("resolved", "delivered"),
        ]
        # One attempt each, tracked per notification: the resolved callback
        # does not inherit the firing one's attempt.
        settled = [a["callbackDelivery"] for a in transport.batches[0]["alerts"][2:]]
        assert [d["attempts"] for d in settled] == [1, 1]
        assert settled[0]["correlationId"] != settled[1]["correlationId"]
    finally:
        agent.bridge.stop()
        agent.monitor.close()


@pytest.mark.parametrize("state", [None, "corrupt", "[]"])
def test_runtime_emits_start_and_stop_without_requiring_log_activity(tmp_path, state):
    backend = create_app(enable_heartbeat_monitor=False)
    transport = CaptureTransport(backend)
    cfg = replace(config(tmp_path), callbacks=None)
    if state is not None:
        cfg.logs.state_dir.mkdir()
        (cfg.logs.state_dir / "offsets.json").write_text(state)
    agent = build_agent(cfg, publish_transport=transport, env={})

    async def run():
        stop = asyncio.Event()
        stop.set()
        await run_agent(agent, stop)

    asyncio.run(run())
    events = [e for batch in transport.batches for e in batch["events"]]
    if state == "[]":
        assert [e["eventType"] for e in events] == ["agent.started", "agent.stopping"]
    else:
        assert [e["eventType"] for e in events] == [
            "agent.started",
            "agent.state_reset",
            "agent.stopping",
        ]
        assert events[1]["fields"] == {
            "reason": "missing" if state is None else "corrupt"
        }


def test_operational_hooks_publish_and_are_queryable(tmp_path):
    backend = create_app(enable_heartbeat_monitor=False)
    transport = CaptureTransport(backend)
    cfg = config(tmp_path)
    agent = build_agent(
        cfg,
        publish_transport=transport,
        callback_transport=httpx.MockTransport(lambda request: httpx.Response(400)),
        env={},
    )
    clock = [0.0]
    monitor = agent.monitor.monitors["Application.log"]
    monitor._monotonic = lambda: clock[0]
    monitor._last_activity = 0
    path = cfg.logs.paths[0]
    try:
        path.write_text("first line\n")
        list(monitor.poll_lines())
        path.rename(path.with_suffix(".log.1"))
        path.write_text("second line\n")
        list(monitor.poll_lines())
        path.write_text("")
        list(monitor.poll_lines())
        clock[0] = cfg.logs.log_stall_threshold_seconds
        list(monitor.poll_lines())
        list(monitor.poll_lines())

        async def deliver():
            worker = asyncio.create_task(backend.state.ingestion.run())
            try:
                assert agent.dispatcher is not None
                await agent.dispatcher._deliver(
                    make_alert_event().model_copy(
                        update={
                            "agent_id": cfg.agent_id,
                            "instance_id": cfg.instance_id,
                        }
                    )
                )
                assert await agent.publisher.publish_once() is PublishAction.COMMIT
                await asyncio.wait_for(backend.state.ingestion._queue.join(), 5)
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=backend),
                    base_url="http://backend",
                ) as client:
                    response = await client.get("/telemetry/events")
                    assert response.status_code == 200
                    events = response.json()["events"]
                    assert sorted(e["eventType"] for e in events) == [
                        "callback.failed",
                        "log.rotated",
                        "log.stalled",
                        "log.truncated",
                    ]
                    assert str(tmp_path) not in json.dumps(events)
                    assert "first line" not in json.dumps(events)
                    assert (
                        next(e for e in events if e["eventType"] == "callback.failed")[
                            "fields"
                        ]["httpStatus"]
                        == 400
                    )
            finally:
                worker.cancel()
                await asyncio.gather(worker, return_exceptions=True)
                if isinstance(agent.publish_sink, HttpsPublishSink):
                    await agent.publish_sink.aclose()
                if isinstance(agent.callback_sink, HttpsCallbackSink):
                    await agent.callback_sink.aclose()

        asyncio.run(deliver())
    finally:
        agent.monitor.close()
