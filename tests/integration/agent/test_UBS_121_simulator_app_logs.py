"""UBS-121/122: actual simulator files -> shipped agent -> signature rules.

Keep the production parser patterns, signatures and rules. Only the log/state
paths and network delivery are replaced. Drive random choices deterministically
so signature isolation and escalation never depend on chance or wall-clock waits.
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Iterator, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypeVar

import httpx
import pytest
from simulator import mock_logger
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.callbacks.status import DeliveryStatus
from telemetry_agent.config import load_agent_config
from telemetry_agent.main import Agent, build_agent
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_backend.main import create_app
from telemetry_shared.models.alerts import AlertEvent

_REPO_ROOT = Path(__file__).resolve().parents[3]
_T = TypeVar("_T")


@pytest.fixture
def agent(tmp_path: Path) -> Iterator[Agent]:
    cfg = load_agent_config(_REPO_ROOT / "config" / "agent.yaml")
    cfg = replace(
        cfg,
        logs=replace(
            cfg.logs,
            paths=tuple(tmp_path / "logs" / path.name for path in cfg.logs.paths),
            state_dir=tmp_path / "state",
        ),
        publish=cfg.publish.model_copy(update={"dry_run": True}),
        callbacks=None,
    )
    runtime = build_agent(
        cfg,
        started_at=datetime.now(UTC) - timedelta(hours=1),
        env={"MAGIC_TELEMETRY_ID_HASH_KEY": "simulator-test-key"},
    )
    runtime.bridge.start()
    try:
        yield runtime
    finally:
        runtime.bridge.stop()
        runtime.monitor.close()


class _SimulationFinished(Exception):
    pass


def _simulate(
    agent: Agent,
    monkeypatch: pytest.MonkeyPatch,
    *,
    log_type: str,
    event_index: int = 0,
    count: int = 1,
    include_fix: bool = False,
) -> None:
    """Run the real infinite harness for a finite, controlled set of writes."""
    choice = mock_logger.random.choice
    written = 0

    def choose(options: Sequence[_T]) -> _T:
        if options == ["Application", "Fix"]:
            return options[1 if written == count else 0]
        if options is mock_logger.APPLICATION_LOG_TYPES:
            return options[mock_logger.APPLICATION_LOG_TYPES.index(log_type)]
        if options in (
            mock_logger.MAIN_EVENTS,
            mock_logger.CLIENT_EVENTS,
            mock_logger.VENUE_EVENTS,
        ):
            return options[event_index]
        return choice(options)

    def after_write(_interval: float) -> None:
        nonlocal written
        written += 1
        if written == count + int(include_fix):
            raise _SimulationFinished

    with monkeypatch.context() as patch:
        patch.setattr(mock_logger, "LOG_DIR", agent.config.logs.paths[0].parent)
        patch.setattr(mock_logger.random, "choice", choose)
        patch.setattr(mock_logger.time, "sleep", after_write)
        with pytest.raises(_SimulationFinished):
            mock_logger.run_harness(max_bytes=1_000_000, interval=0)

    events = list(agent.adapter.run_until(idle_rounds=3))
    assert len(events) == count + int(include_fix)
    for event in events:
        if Path(event.meta.path).name == "Application.log":
            assert event.result.app_log_telemetry is not None
        else:
            assert event.result.telemetry is not None
    assert agent.ingestor.stats()["ingest_errors"] == 0


def _tick(agent: Agent, seconds: int) -> list[AlertEvent]:
    return agent.evaluator.evaluate_once(
        now=datetime.now(UTC) + timedelta(seconds=seconds)
    )


def test_every_simulator_application_variant_reaches_the_shipped_counters(
    agent: Agent, monkeypatch: pytest.MonkeyPatch
) -> None:
    for log_type, events in (
        ("main", mock_logger.MAIN_EVENTS),
        ("client", mock_logger.CLIENT_EVENTS),
        ("venue", mock_logger.VENUE_EVENTS),
    ):
        for index in range(len(events)):
            _simulate(agent, monkeypatch, log_type=log_type, event_index=index)

    totals = agent.ingestor.aggregator.snapshot("1m", group_by=())[()].counters
    assert totals["app_log_lines"] == 12
    assert totals["app_log_errors"] == 5
    assert totals["app_error_signatures"] == 5
    assert "parse_errors" not in totals
    levels = agent.ingestor.aggregator.snapshot("1m", group_by=("level",))
    assert {
        level: row.counters["app_log_lines"] for (level,), row in levels.items()
    } == {"N": 2, "I": 2, "W": 3, "E": 3, "F": 2}
    signatures = agent.ingestor.aggregator.snapshot(
        "1m", group_by=("error_signature",)
    )
    assert {
        label: row.counters["app_error_signatures"]
        for (label,), row in signatures.items()
        if "app_error_signatures" in row.counters
    } == {
        "out_of_memory": 1,
        "db_connection_lost": 1,
        "connection_disconnected": 1,
        "connection_timeout": 1,
        "venue_connection_failed": 1,
    }


@pytest.mark.parametrize(
    ("event_index", "signature", "rule_name", "critical_count"),
    [
        (4, "out_of_memory", "AppOutOfMemory", 3),
        (3, "db_connection_lost", "AppDbConnectionLost", 5),
    ],
)
def test_simulator_signatures_fire_only_their_own_shipped_rule(
    agent: Agent,
    monkeypatch: pytest.MonkeyPatch,
    event_index: int,
    signature: str,
    rule_name: str,
    critical_count: int,
) -> None:
    # Sponsor venue disconnects count, but must not trip memory/database rules.
    _simulate(agent, monkeypatch, log_type="venue", event_index=3, count=4)
    _simulate(agent, monkeypatch, log_type="client")
    assert _tick(agent, 1) == []
    assert _tick(agent, 2) == []

    _simulate(agent, monkeypatch, log_type="main", event_index=event_index)
    assert _tick(agent, 3) == []  # first tick: pending
    warning = _tick(agent, 4)
    assert [(a.rule_name, a.severity) for a in warning] == [(rule_name, "warning")]
    assert warning[0].group_by == {"error_signature": signature}
    assert warning[0].observed_value == 1

    _simulate(
        agent,
        monkeypatch,
        log_type="main",
        event_index=event_index,
        count=critical_count - 1,
    )
    critical = _tick(agent, 5)
    assert [(a.rule_name, a.severity) for a in critical] == [(rule_name, "critical")]
    assert critical[0].observed_value == critical_count

    totals = agent.ingestor.aggregator.snapshot("1m", group_by=())[()].counters
    assert totals["app_log_lines"] == 5 + critical_count
    assert totals["app_log_errors"] == 4 + critical_count
    grouped = agent.ingestor.aggregator.snapshot("1m", group_by=("error_signature",))
    assert grouped[(signature,)].counters["app_error_signatures"] == critical_count
    assert grouped[("connection_disconnected",)].counters["app_error_signatures"] == 4
    assert "messages_total" not in totals  # app-only activity keeps liveness quiet


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows refuses to rename a log file held open by the monitor",
)
def test_simulator_rotation_preserves_application_counters_and_fix_parsing(
    agent: Agent, monkeypatch: pytest.MonkeyPatch
) -> None:
    _simulate(agent, monkeypatch, log_type="main", event_index=1, include_fix=True)
    _simulate(agent, monkeypatch, log_type="client", event_index=1)
    app_log = agent.config.logs.paths[0]
    assert mock_logger.rotate_if_needed(app_log, max_bytes=1, keep_rotated_files=2)
    _simulate(agent, monkeypatch, log_type="venue", event_index=0)

    assert _tick(agent, 1) == []
    assert _tick(agent, 2) == []
    totals = agent.ingestor.aggregator.snapshot("1m", group_by=())[()].counters
    assert totals["app_log_lines"] == 3
    assert totals["messages_total"] == 1
    assert totals["log_lines_read"] == 4
    assert "parse_errors" not in totals
    assert {path.name for path in app_log.parent.iterdir()} == {
        "Application.log", "Application.log.1", "Fix.log"
    }
    assert agent.monitor.monitors["Application.log"].get_status().offset == (
        app_log.stat().st_size
    )


def test_simulator_signature_alert_reaches_backend_and_signed_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = create_app()
    callbacks: list[httpx.Request] = []

    def receive_callback(request: httpx.Request) -> httpx.Response:
        callbacks.append(request)
        return httpx.Response(200, json={})

    cfg = load_agent_config(_REPO_ROOT / "config" / "agent.yaml")
    cfg = replace(
        cfg,
        logs=replace(
            cfg.logs,
            paths=tuple(tmp_path / "logs" / path.name for path in cfg.logs.paths),
            state_dir=tmp_path / "state",
        ),
    )
    agent = build_agent(
        cfg,
        publish_transport=httpx.ASGITransport(app=backend),
        callback_transport=httpx.MockTransport(receive_callback),
        started_at=datetime.now(UTC) - timedelta(hours=1),
        env={
            "MAGIC_TELEMETRY_ID_HASH_KEY": "simulator-test-key",
            "MAGIC_TELEMETRY_PUBLISH_TOKEN": "simulator-test-token",
            "MAGIC_TELEMETRY_CALLBACK_SECRET": "simulator-test-secret",
        },
    )

    async def deliver(alert: AlertEvent) -> None:
        assert agent.dispatcher is not None
        ingestion = asyncio.create_task(backend.state.ingestion.run())
        delivery = asyncio.create_task(agent.dispatcher.run())
        try:
            assert await agent.publisher.publish_once() is PublishAction.COMMIT
            await asyncio.wait_for(backend.state.ingestion._queue.join(), timeout=5)
            for _ in range(200):
                record = agent.dispatcher.tracker.status_of(alert.alert_id)
                if record is not None and record.status is DeliveryStatus.DELIVERED:
                    break
                await asyncio.sleep(0.01)
            else:
                raise AssertionError("simulator signature callback was not delivered")

            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=backend), base_url="http://backend"
            ) as client:
                response = await client.get("/telemetry/alerts")
                assert response.status_code == 200
                assert [a["ruleName"] for a in response.json()["alerts"]] == [
                    "AppOutOfMemory"
                ]
                health = await client.get(f"/telemetry/health/agents/{cfg.agent_id}")
                assert health.status_code == 200
                assert health.json()["parseErrorCountLast5Min"] == 0
        finally:
            ingestion.cancel()
            delivery.cancel()
            await asyncio.gather(ingestion, delivery, return_exceptions=True)
            for sink in (agent.publish_sink, agent.callback_sink):
                if sink is not None:
                    await sink.aclose()

    agent.bridge.start()
    try:
        _simulate(agent, monkeypatch, log_type="main", event_index=4, count=3)
        assert _tick(agent, 1) == []
        (alert,) = _tick(agent, 2)
        assert alert.rule_name == "AppOutOfMemory"
        assert alert.severity == "critical"
        asyncio.run(deliver(alert))
        assert len(callbacks) == 1
        request = callbacks[0]
        assert json.loads(request.content)["ruleName"] == "AppOutOfMemory"
        assert request.headers["X-Telemetry-Signature"] == sign(
            b"simulator-test-secret",
            request.headers["X-Telemetry-Timestamp"],
            request.content,
        )
    finally:
        agent.bridge.stop()
        agent.monitor.close()
