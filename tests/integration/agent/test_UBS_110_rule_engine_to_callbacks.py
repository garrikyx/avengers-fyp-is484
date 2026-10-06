"""UBS-110 integration: raw FIX bytes -> FixParser -> MetricsAggregator ->
RuleEngine -> AlertRouter -> {CallbackDispatcher -> Magic,
BackendPublisher -> POST /telemetry/batch -> AlertStore}.

The same engine-derived alert goes to both destinations. Magic is a
`httpx.MockTransport` that records each request; the backend is the real
`create_app()` over `ASGITransport`, as in the UBS-109 test this reuses.
"""

from __future__ import annotations

import asyncio

import httpx
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.callbacks.sink import HttpsCallbackSink
from telemetry_agent.callbacks.status import DeliveryStatus
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_backend.main import create_app
from test_UBS_109_rule_engine_to_backend import (
    _AGENT_ID,
    _APPLICATION,
    _T0,
    _aggregator_with_a_reject_burst,
    _fire_reject_spike,
    _publish_and_drain,
    _publisher,
)

_CALLBACK_ENDPOINT = "https://magic.example/callbacks"
_SECRET = b"ubs110-callback-secret"
_TERMINAL = {DeliveryStatus.DELIVERED, DeliveryStatus.FAILED}


def _dispatcher(status: int, received: list[httpx.Request]) -> CallbackDispatcher:
    """A dispatcher pointed at a Magic endpoint that always answers `status`
    and records every request it receives. Zero backoff so retries are
    instant; the backoff maths are `test_FR_CBK_004_006_007_dispatcher.py`'s."""

    def handler(request: httpx.Request) -> httpx.Response:
        received.append(request)
        return httpx.Response(status)

    config = parse_callbacks_config(
        {
            "endpoint": _CALLBACK_ENDPOINT,
            "retry": {"base": "0s", "cap": "0s"},
            "maxAttempts": 3,
        }
    )
    sink = HttpsCallbackSink(_CALLBACK_ENDPOINT, transport=httpx.MockTransport(handler))
    return CallbackDispatcher(sink, config, _SECRET)


async def _deliver(dispatcher: CallbackDispatcher, alert_id: str) -> None:
    """Run the dispatcher until `alert_id` reaches a terminal state."""
    task = asyncio.create_task(dispatcher.run())
    try:
        for _ in range(200):
            record = dispatcher.tracker.status_of(alert_id)
            if record is not None and record.status in _TERMINAL:
                return
            await asyncio.sleep(0.01)
        raise AssertionError(f"alert {alert_id} never reached a terminal state")
    finally:
        task.cancel()


def _route_real_alert(
    callback_status: int, received: list[httpx.Request]
) -> tuple[str, CallbackDispatcher, object, object]:
    alerts = _fire_reject_spike(_aggregator_with_a_reject_burst())
    assert [a.rule_name for a in alerts] == ["RejectSpike"]

    app = create_app()
    publisher = _publisher(app)
    dispatcher = _dispatcher(callback_status, received)
    router = AlertRouter(
        publisher,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
        dispatcher=dispatcher,
    )
    assert router.route(alerts, now=_T0) == 1
    return alerts[0].alert_id, dispatcher, app, publisher


def test_a_real_alert_reaches_magic_signed_and_the_backend() -> None:
    received: list[httpx.Request] = []
    alert_id, dispatcher, app, publisher = _route_real_alert(200, received)

    async def both() -> PublishAction | None:
        await _deliver(dispatcher, alert_id)
        return await _publish_and_drain(app, publisher)  # type: ignore[arg-type]

    action = asyncio.run(both())

    # Magic: one signed callback carrying the engine's alert.
    assert len(received) == 1
    request = received[0]
    assert alert_id in request.content.decode()
    timestamp = request.headers["X-Telemetry-Timestamp"]
    assert request.headers["X-Telemetry-Signature"] == sign(
        _SECRET, timestamp, request.content
    )
    record = dispatcher.tracker.status_of(alert_id)
    assert record is not None and record.status is DeliveryStatus.DELIVERED

    # Backend: the same alert, stored.
    assert action is PublishAction.COMMIT
    listed = app.state.alert_store.list_alerts(status="active")  # type: ignore[attr-defined]
    assert [a.alert_id for a in listed.alerts] == [alert_id]


def test_magic_being_down_does_not_stop_the_backend_getting_the_alert() -> None:
    """`NFR-REL-003`: a failing callback path leaves the backend path intact."""
    received: list[httpx.Request] = []
    alert_id, dispatcher, app, publisher = _route_real_alert(503, received)

    async def both() -> PublishAction | None:
        await _deliver(dispatcher, alert_id)
        return await _publish_and_drain(app, publisher)  # type: ignore[arg-type]

    action = asyncio.run(both())

    record = dispatcher.tracker.status_of(alert_id)
    assert record is not None and record.status is DeliveryStatus.FAILED
    assert len(received) == 3  # retried to maxAttempts, then gave up
    assert dispatcher.counters.snapshot()["callback_failures"] == 1

    assert action is PublishAction.COMMIT
    listed = app.state.alert_store.list_alerts(status="active")  # type: ignore[attr-defined]
    assert [a.alert_id for a in listed.alerts] == [alert_id]
