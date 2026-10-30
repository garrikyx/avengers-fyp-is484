"""Delivery state is per notification: a firing callback that is still
retrying must not share attempts or status with the resolved one sent while
it waited."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_shared.models.alerts import AlertEvent

from tests.unit.backend.services.alert_fixtures import make_alert_event


class _SlowFiringSink:
    """The first firing attempt waits on `gate`, then fails with a 500; every
    other request succeeds."""

    def __init__(self) -> None:
        self.gate = asyncio.Event()
        self.entered = asyncio.Event()
        self._firing_calls = 0

    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> CallbackResult:
        if ":firing:" in headers["X-Telemetry-Idempotency-Key"]:
            self._firing_calls += 1
            if self._firing_calls == 1:
                self.entered.set()
                await self.gate.wait()
                return CallbackResult(status_code=500, latency_ms=1.0)
        return CallbackResult(status_code=200, latency_ms=1.0)


def test_a_retrying_firing_callback_does_not_share_state_with_resolved() -> None:
    settled: list[AlertEvent] = []
    sink = _SlowFiringSink()
    dispatcher = CallbackDispatcher(
        sink,
        parse_callbacks_config(
            {
                "endpoint": "https://magic.example/cb",
                "retry": {"base": "0s", "cap": "0s"},
            }
        ),
        b"secret",
        on_delivery_settled=settled.append,
    )
    firing = make_alert_event(alert_id="a-1", status="firing")
    resolved = make_alert_event(alert_id="a-1", status="resolved")

    async def scenario() -> None:
        dispatcher.enqueue(firing)
        dispatcher.enqueue(resolved)
        firing_task = asyncio.create_task(dispatcher._deliver(firing))
        await sink.entered.wait()  # firing is mid-attempt
        await dispatcher._deliver(resolved)  # resolved settles while it waits
        sink.gate.set()
        await firing_task

    asyncio.run(scenario())

    by_status = {a.status: a.callback_delivery for a in settled}
    assert by_status["resolved"] is not None and by_status["firing"] is not None
    assert (by_status["resolved"].status, by_status["resolved"].attempts) == (
        "delivered",
        1,
    )
    assert (by_status["firing"].status, by_status["firing"].attempts) == (
        "delivered",
        2,
    )
    assert by_status["resolved"].correlation_id != by_status["firing"].correlation_id
