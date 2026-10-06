"""UBS-110: AlertRouter fans each alert out to the Callback Dispatcher as well
as the Backend Publisher, and keeps the two paths isolated (`NFR-REL-003`).
"""

from __future__ import annotations

from collections.abc import Mapping

from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_agent.callbacks.status import DeliveryStatus
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_shared.models.alerts import AlertEvent
from test_UBS_109_alert_router import (
    _AGENT,
    _APPLICATION,
    _NOW,
    _alert,
    _publisher,
)


class _NullCallbackSink:
    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> CallbackResult:
        return CallbackResult(status_code=200, latency_ms=1.0)


def _dispatcher() -> CallbackDispatcher:
    config = parse_callbacks_config({"endpoint": "https://magic.example/cb"})
    return CallbackDispatcher(_NullCallbackSink(), config, b"secret")


def _router(publisher: BackendPublisher, dispatcher: CallbackDispatcher) -> AlertRouter:
    return AlertRouter(
        publisher,
        agent_id=_AGENT,
        application=_APPLICATION,
        dispatcher=dispatcher,
    )


def _pending(dispatcher: CallbackDispatcher, alert_id: str) -> bool:
    record = dispatcher.tracker.status_of(alert_id)
    return record is not None and record.status is DeliveryStatus.PENDING


def test_each_alert_reaches_both_paths() -> None:
    publisher, dispatcher = _publisher(), _dispatcher()
    router = _router(publisher, dispatcher)

    routed = router.route([_alert("a1"), _alert("a2")], now=_NOW)

    assert routed == 2
    assert publisher.queue_depth() == 2
    assert _pending(dispatcher, "a1") and _pending(dispatcher, "a2")
    counters = router.counters.snapshot()
    assert counters["alerts_routed"] == 2
    assert counters["alerts_dispatched"] == 2


def test_an_identity_mismatch_still_reaches_magic() -> None:
    """The guard protects the batch; a callback has no batch to poison."""
    publisher, dispatcher = _publisher(), _dispatcher()
    router = _router(publisher, dispatcher)

    routed = router.route([_alert("bad", agent_id="wrong")], now=_NOW)

    assert routed == 0
    assert publisher.queue_depth() == 0
    assert _pending(dispatcher, "bad")


def test_a_failing_dispatcher_does_not_cost_the_backend_its_alert() -> None:
    publisher, dispatcher = _publisher(), _dispatcher()

    def boom(_alert: AlertEvent) -> None:
        raise RuntimeError("callback queue broken")

    dispatcher.enqueue = boom  # type: ignore[method-assign]
    router = _router(publisher, dispatcher)

    routed = router.route([_alert("a1")], now=_NOW)  # must not raise

    assert routed == 1
    assert publisher.queue_depth() == 1
    counters = router.counters.snapshot()
    assert counters["alerts_callback_enqueue_failed"] == 1
    assert "alerts_dispatched" not in counters


def test_a_failing_publisher_does_not_cost_magic_its_alert() -> None:
    publisher, dispatcher = _publisher(), _dispatcher()

    def boom(_alert: AlertEvent, *, now: object = None) -> None:
        raise RuntimeError("publish buffer broken")

    publisher.enqueue_alert = boom  # type: ignore[method-assign,assignment]
    router = _router(publisher, dispatcher)

    routed = router.route([_alert("a1")], now=_NOW)  # must not raise

    assert routed == 0
    assert _pending(dispatcher, "a1")
    counters = router.counters.snapshot()
    assert counters["alerts_publish_enqueue_failed"] == 1
    assert "alerts_routed" not in counters


def test_without_a_dispatcher_nothing_is_dispatched() -> None:
    router = AlertRouter(_publisher(), agent_id=_AGENT, application=_APPLICATION)

    router.route([_alert("a1")], now=_NOW)

    assert "alerts_dispatched" not in router.counters.snapshot()
