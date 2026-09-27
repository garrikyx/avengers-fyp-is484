"""UBS-104 integration test: `NFR-REL-003` -- a backend outage must never
affect alerting/callbacks. Runs a `CallbackDispatcher` against a healthy
mock Magic endpoint *concurrently*, in the same event loop, as a
`BackendPublisher` whose sink never returns -- proving the two share no
lock or blocking resource that would let one stall the other, not just
that they're separate classes.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime

import httpx
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import HttpsCallbackSink
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.snapshot import Snapshot

_CALLBACK_ENDPOINT = "https://magic.example/callbacks"
_PUBLISH_ENDPOINT = "https://backend.example/telemetry/batch"


class _HangingSink:
    """Stands in for a backend that never responds -- e.g. a dropped
    connection to a firewalled host. `send()` never returns within any
    timeframe this test could wait for."""

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> PublishResult:
        await asyncio.sleep(3600)
        raise AssertionError("unreachable")  # pragma: no cover


def _make_alert() -> AlertEvent:
    now = datetime.now(UTC)
    return AlertEvent(
        alert_id="alert-1024",
        rule_name="HighRejectRate",
        severity="critical",
        status="firing",
        application="Magic",
        instance_id="magic-prod-01",
        agent_id="magic-agent-sg-01",
        matched_condition="rejectRate > 0.05 for 5 minutes",
        observed_value=0.064,
        threshold=0.05,
        first_observed_utc=now,
        last_observed_utc=now,
        notification_count=1,
    )


def _make_snapshot() -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id="magic-agent-sg-01",
        application="Magic",
        instance_id="magic-prod-01",
        bucket_start_utc=datetime.now(UTC),
        bucket_seconds=10,
    )


async def _run_scenario() -> CallbackDispatcher:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "received", "correlationId": "cb-1"})

    callback_config = parse_callbacks_config({"endpoint": _CALLBACK_ENDPOINT})
    callback_sink = HttpsCallbackSink(
        _CALLBACK_ENDPOINT, transport=httpx.MockTransport(handler)
    )
    dispatcher = CallbackDispatcher(callback_sink, callback_config, b"test-secret")
    dispatcher.enqueue(_make_alert())

    publish_config = parse_publish_config({"endpoint": _PUBLISH_ENDPOINT})
    publisher = BackendPublisher(
        _HangingSink(),
        publish_config,
        agent_id="magic-agent-sg-01",
        application="Magic",
    )
    # Must return immediately even though this publisher's sink never will
    # (FR-PUB-007) -- if enqueue blocked on the hung sink, this line alone
    # would hang the whole test.
    publisher.enqueue_snapshot(_make_snapshot())

    dispatcher_task = asyncio.create_task(dispatcher.run())
    publisher_task = asyncio.create_task(publisher.run())
    try:
        # Both loops share this event loop; if the Publisher's stuck send
        # blocked anything shared, the dispatcher would never get to run.
        await asyncio.sleep(0.3)
    finally:
        dispatcher_task.cancel()
        publisher_task.cancel()

    return dispatcher


def test_callback_delivery_is_unaffected_by_a_hung_publisher() -> None:
    dispatcher = asyncio.run(_run_scenario())

    assert dispatcher.counters.snapshot().get("callback_delivered") == 1
