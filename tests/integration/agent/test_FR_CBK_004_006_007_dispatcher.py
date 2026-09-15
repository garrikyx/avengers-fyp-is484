"""UBS-32 integration test: dispatch against a mock Magic endpoint.

Uses `httpx.MockTransport` instead of a real socket/server — it exercises
the exact same `httpx.AsyncClient` request/response path `HttpsCallbackSink`
uses in production, just without opening a real connection.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import httpx
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import HttpsCallbackSink
from telemetry_shared.models.alerts import AlertEvent

_CONFIG = parse_callbacks_config({"endpoint": "https://magic.example/callbacks"})


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


async def _run_one(dispatcher: CallbackDispatcher, alert: AlertEvent) -> None:
    dispatcher.enqueue(alert)
    task = asyncio.create_task(dispatcher.run())
    await asyncio.sleep(0.1)
    task.cancel()


def test_FR_CBK_001_success_marks_delivered() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://magic.example/callbacks"
        assert request.headers["Content-Type"] == "application/json"
        assert "X-Telemetry-Signature" in request.headers
        return httpx.Response(200, json={"status": "received", "correlationId": "cb-1"})

    sink = HttpsCallbackSink(
        _CONFIG.endpoint, transport=httpx.MockTransport(handler)
    )
    dispatcher = CallbackDispatcher(sink, _CONFIG, b"test-secret")
    asyncio.run(_run_one(dispatcher, _make_alert()))

    assert dispatcher.counters.snapshot() == {"callback_delivered": 1}


def test_FR_CBK_006_permanent_4xx_logs_failure_without_crashing() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad request"})

    sink = HttpsCallbackSink(
        _CONFIG.endpoint, transport=httpx.MockTransport(handler)
    )
    dispatcher = CallbackDispatcher(sink, _CONFIG, b"test-secret")
    asyncio.run(_run_one(dispatcher, _make_alert()))

    assert dispatcher.counters.snapshot() == {"callback_failures": 1}


def test_FR_CBK_006_5xx_logs_failure_without_crashing_no_retry_yet() -> None:
    """UBS-32 scope: no retry loop yet (that's UBS-33) — a single 5xx is
    just logged and counted."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    sink = HttpsCallbackSink(
        _CONFIG.endpoint, transport=httpx.MockTransport(handler)
    )
    dispatcher = CallbackDispatcher(sink, _CONFIG, b"test-secret")
    asyncio.run(_run_one(dispatcher, _make_alert()))

    assert dispatcher.counters.snapshot() == {"callback_failures": 1}


def test_FR_CBK_007_oversized_payload_is_dropped_without_sending() -> None:
    called = False

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200)

    tiny_config = parse_callbacks_config(
        {"endpoint": "https://magic.example/callbacks", "maxBytes": 10}
    )
    sink = HttpsCallbackSink(
        tiny_config.endpoint, transport=httpx.MockTransport(handler)
    )
    dispatcher = CallbackDispatcher(sink, tiny_config, b"test-secret")
    asyncio.run(_run_one(dispatcher, _make_alert()))

    assert called is False
    assert dispatcher.counters.snapshot() == {"callback_failures": 1}
