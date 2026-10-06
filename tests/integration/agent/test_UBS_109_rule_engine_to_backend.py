"""UBS-109 integration: raw FIX bytes -> FixParser -> MetricsAggregator ->
RuleEngine -> AlertRouter -> BackendPublisher -> POST /telemetry/batch ->
IngestionService consumer -> AlertStore -> GET /telemetry/alerts.

Before this, `BackendPublisher.enqueue_alert()` was called nowhere in the
repo: the Rule Engine fired alerts and the backend never learned they
existed. With UBS-93/94/95's alert store now merged, the alert has a real
destination, so this follows one all the way from log bytes to a query
response. No hand-built `AlertEvent` anywhere — the alert asserted on is one
the engine actually derived from a reject burst in the log.

Uses `httpx.ASGITransport` over `create_app()`, the pattern established in
`test_UBS_103_publisher_backend.py`: no socket, but the exact
`HttpsPublishSink` -> `httpx.AsyncClient` -> FastAPI path production uses.
`ASGITransport` does not run the app's lifespan, so the ingestion consumer
is driven explicitly — see `_drain_backend`.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import build_parsed_message_event
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_backend.main import create_app
from telemetry_shared.models.alerts import AlertEvent

_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_AGENT_ID = "magic-agent-sg-01"
_APPLICATION = "Magic"
_INSTANCE = "magic-prod-01"
_ENDPOINT = "https://backend.example/telemetry/batch"
_KEY = b"ubs109-integration-key"


def _order(tag: int, seq: int) -> bytes:
    return (
        b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|"
        b"11=C%d|55=AAPL|54=1|40=2|38=100|10=000|" % (seq, tag)
    )


def _reject(tag: int, seq: int) -> bytes:
    return (
        b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|"
        b"11=C%d|37=O%d|17=E%d|55=AAPL|54=1|150=8|39=8|103=3|10=000|"
        % (seq, tag, tag, tag)
    )


def _aggregator_with_a_reject_burst() -> MetricsAggregator:
    """51 rejected orders in the window — past `RejectSpike`'s `> 50`."""
    parser = FixParser(hash_key=_KEY)
    config = AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS))
    aggregator = MetricsAggregator(config=config, clock=lambda: _T0.timestamp())
    meta = SourceMeta(
        instance_id=_INSTANCE, path="Fix.log", log_type="fix", read_at=_T0
    )
    seq = 1
    for tag in range(51):
        for line in (_order(tag, seq), _reject(tag, seq + 1)):
            result = parser.parse(line, meta)
            event = build_parsed_message_event(result, meta)
            if event is not None:
                aggregator.ingest_counters(event, derive_counters(event))
        seq += 2
    return aggregator


def _engine() -> tuple[RuleEngine, int]:
    rule = next(r for r in DEFAULT_RULES if r.name == "RejectSpike")
    engine = RuleEngine(
        rules=(rule,),
        instance_id=_INSTANCE,
        application=_APPLICATION,
        agent_id=_AGENT_ID,
        started_at=_T0 - timedelta(hours=1),
    )
    return engine, rule.for_seconds


def _fire_reject_spike(aggregator: MetricsAggregator) -> list[AlertEvent]:
    engine, for_seconds = _engine()
    snap = snapshot(aggregator, "1m", group_by=(), now=_T0)
    engine.evaluate(snap, _T0)  # -> pending
    return engine.evaluate(snap, _T0 + timedelta(seconds=for_seconds + 1))


def _publisher(app: object) -> BackendPublisher:
    sink = HttpsPublishSink(
        _ENDPOINT, "test-token", transport=httpx.ASGITransport(app=app)
    )
    config = parse_publish_config({"endpoint": _ENDPOINT})
    return BackendPublisher(
        sink, config, agent_id=_AGENT_ID, application=_APPLICATION
    )


def _router(publisher: BackendPublisher) -> AlertRouter:
    return AlertRouter(
        publisher, agent_id=_AGENT_ID, application=_APPLICATION
    )


async def _drain_backend(app: object) -> None:
    """Run the ingestion consumer until the queued batch is fully processed.

    `ASGITransport` skips the lifespan that normally starts this task, so the
    test starts it by hand. Awaiting `_queue.join()` rather than polling
    `queue_depth`: qsize drops when `get()` returns, but the alert is merged
    in a `to_thread` *after* that, with `task_done()` in the `finally`. So
    only `join()` actually waits for the merge — polling qsize would race.
    """
    service = app.state.ingestion  # type: ignore[attr-defined]
    worker = asyncio.create_task(service.run())
    try:
        await service._queue.join()  # noqa: SLF001 - see docstring
    finally:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass


async def _publish_and_drain(
    app: object, publisher: BackendPublisher
) -> PublishAction | None:
    action = await publisher.publish_once(now=_T0)
    await _drain_backend(app)
    return action


# --- the whole seam, end to end ------------------------------------------


def test_a_real_alert_reaches_the_backend_alert_store() -> None:
    aggregator = _aggregator_with_a_reject_burst()
    row = aggregator.snapshot("1m", group_by=()).get(())
    assert row is not None
    assert row.counters["orders_rejected"] == Decimal(51)

    alerts = _fire_reject_spike(aggregator)
    assert [a.rule_name for a in alerts] == ["RejectSpike"]

    app = create_app()
    publisher = _publisher(app)
    assert _router(publisher).route(alerts, now=_T0) == 1

    action = asyncio.run(_publish_and_drain(app, publisher))

    assert action is PublishAction.COMMIT
    assert publisher.queue_depth() == 0

    # Queryable through the store's own public API, not an internal peek.
    listed = app.state.alert_store.list_alerts(status="active")
    assert [a.alert_id for a in listed.alerts] == [alerts[0].alert_id]
    assert listed.alerts[0].rule_name == "RejectSpike"
    assert listed.alerts[0].source == "agent"


def test_the_alert_is_served_by_the_query_endpoint() -> None:
    """The full round trip a Teams/Copilot caller would make: the agent's
    alert comes back out of `GET /telemetry/alerts`.

    The GET runs in the *same* event loop as the publish. `IngestionService`'s
    `asyncio.Queue` binds to the first loop that touches it, so reaching for
    `TestClient` here — which spins its own loop for the lifespan — raises
    "Queue is bound to a different event loop".
    """
    alerts = _fire_reject_spike(_aggregator_with_a_reject_burst())
    app = create_app()
    publisher = _publisher(app)
    _router(publisher).route(alerts, now=_T0)

    async def round_trip() -> httpx.Response:
        await _publish_and_drain(app, publisher)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://backend"
        ) as client:
            return await client.get(
                "/telemetry/alerts", params={"status": "active"}
            )

    response = asyncio.run(round_trip())

    assert response.status_code == 200
    body = response.json()
    assert [a["alertId"] for a in body["alerts"]] == [alerts[0].alert_id]
    assert body["alerts"][0]["ruleName"] == "RejectSpike"


def test_the_alert_survives_the_wire_with_its_fields_intact() -> None:
    """The batch is JSON over HTTP, so the store holds a re-parsed model, not
    our object. Check the fields an on-call engineer would read."""
    alerts = _fire_reject_spike(_aggregator_with_a_reject_burst())
    app = create_app()
    publisher = _publisher(app)
    _router(publisher).route(alerts, now=_T0)
    asyncio.run(_publish_and_drain(app, publisher))

    stored = app.state.alert_store.list_alerts(status="active").alerts[0]

    assert stored.severity == "warning"
    assert stored.instance_id == _INSTANCE
    assert stored.application == _APPLICATION
    assert stored.observed_value == 51
    assert stored.threshold == 50
    assert "orders_rejected" in stored.matched_condition


def test_firing_then_resolved_is_one_stored_alert_with_both_transitions() -> None:
    """`alertId` stability finally pays off across the wire: the engine
    reuses one id for an incident's whole lifecycle, so the store merges the
    resolution into the same alert instead of recording a second one.
    """
    aggregator = _aggregator_with_a_reject_burst()
    engine, for_seconds = _engine()
    hot = snapshot(aggregator, "1m", group_by=(), now=_T0)
    engine.evaluate(hot, _T0)
    firing = engine.evaluate(hot, _T0 + timedelta(seconds=for_seconds + 1))
    assert firing[0].status == "firing"

    # A later window with no rejects at all clears the condition.
    quiet_agg = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS)),
        clock=lambda: _T0.timestamp(),
    )
    quiet = snapshot(quiet_agg, "1m", group_by=(), now=_T0)
    rule = next(r for r in DEFAULT_RULES if r.name == "RejectSpike")
    at = _T0 + timedelta(seconds=for_seconds + 2)
    engine.evaluate(quiet, at)  # firing -> resolving
    resolved = engine.evaluate(
        quiet, at + timedelta(seconds=rule.resolve_after_seconds + 1)
    )
    assert [a.status for a in resolved] == ["resolved"]
    assert resolved[0].alert_id == firing[0].alert_id

    app = create_app()
    publisher = _publisher(app)
    router = _router(publisher)
    router.route(firing, now=_T0)
    router.route(resolved, now=_T0)
    asyncio.run(_publish_and_drain(app, publisher))

    assert app.state.alert_store.list_alerts(status="active").alerts == []
    detail = app.state.alert_store.get_alert(firing[0].alert_id)
    assert detail is not None
    assert detail.alert.status == "resolved"
    assert len(detail.transitions) == 2


def test_a_backend_outage_does_not_lose_the_alert() -> None:
    """`NFR-REL-003`'s other half: alerting works without the backend, and
    the alert waits in the buffer rather than being dropped."""
    alerts = _fire_reject_spike(_aggregator_with_a_reject_burst())
    sink = HttpsPublishSink(
        _ENDPOINT,
        "test-token",
        transport=httpx.MockTransport(
            lambda _req: (_ for _ in ()).throw(httpx.ConnectError("down"))
        ),
    )
    publisher = BackendPublisher(
        sink,
        parse_publish_config({"endpoint": _ENDPOINT}),
        agent_id=_AGENT_ID,
        application=_APPLICATION,
    )

    assert _router(publisher).route(alerts, now=_T0) == 1
    action = asyncio.run(publisher.publish_once(now=_T0))

    assert action is PublishAction.BACKOFF
    assert publisher.queue_depth() == 1  # buffered for retry, not lost
