"""Minimal walkthrough of the Callback Dispatcher (UBS-32/33).

    uv run python -m telemetry_agent.callbacks.demo_quickstart

Four alerts through the dispatcher: one delivers cleanly, one gets a
permanent rejection from "Magic", one is oversized and never even gets
sent, and one fails twice with transient errors before succeeding on the
third attempt — so you can watch the retry/backoff loop (UBS-33) happen in
real time, not just read it in a test assertion. No real network calls — a
small scripted sink stands in for Magic so the outcomes are deterministic
and visible, the same idea as `metrics/demo_quickstart.py`.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Mapping
from datetime import UTC, datetime

from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult

# Line-buffer stdout so `print()` interleaves in true chronological order
# with logging's stderr output even when piped (not a TTY) — otherwise
# print() batches under a pipe while logging flushes per line.
sys.stdout.reconfigure(line_buffering=True)  # type: ignore[union-attr]
logging.basicConfig(level=logging.INFO, format="  %(message)s", stream=sys.stdout)


class _ScriptedSink:
    """Stands in for Magic: keys its canned response off the alert ID
    inside the request body (not call order — worker tasks pull from the
    queue concurrently, so call order isn't deterministic) to show the
    success, permanent-failure, and transient-then-success paths without a
    real endpoint.
    """

    _PERMANENT_FAIL_ALERT_ID = "alert-2"
    _TRANSIENT_FAIL_ALERT_ID = "alert-4"
    _TRANSIENT_FAILURES_BEFORE_SUCCESS = 2

    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint
        self._attempts: dict[str, int] = {}

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> CallbackResult:
        text = body.decode("utf-8")
        print(f"  >> POST {self._endpoint}")
        for name in ("X-Telemetry-Delivery-Id", "X-Telemetry-Idempotency-Key"):
            print(f"     {name}: {headers[name]}")
        print(f"     body ({len(body)} bytes): {text}")

        if f'"alertId":"{self._PERMANENT_FAIL_ALERT_ID}"' in text:
            print('  << 400 Bad Request {"error": "bad request"}')
            return CallbackResult(
                status_code=400, latency_ms=8.0, response_snippet="bad request"
            )

        if f'"alertId":"{self._TRANSIENT_FAIL_ALERT_ID}"' in text:
            seen = self._attempts.get(self._TRANSIENT_FAIL_ALERT_ID, 0) + 1
            self._attempts[self._TRANSIENT_FAIL_ALERT_ID] = seen
            if seen <= self._TRANSIENT_FAILURES_BEFORE_SUCCESS:
                print(f"  << 500 Internal Server Error (attempt {seen})")
                return CallbackResult(status_code=500, latency_ms=10.0)

        print('  << 200 OK {"status": "received", "correlationId": "cb-demo-1"}')
        return CallbackResult(status_code=200, latency_ms=12.0)


def _step(title: str) -> None:
    print(f"\n--- {title} ---")


def _make_alert(**overrides: object) -> AlertEvent:
    now = datetime.now(UTC)
    defaults: dict[str, object] = dict(
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
        metric_context={"orders_acked": 1188, "orders_rejected": 81},
        notification_count=1,
    )
    defaults.update(overrides)
    return AlertEvent(**defaults)  # type: ignore[arg-type]


async def _run_one(
    dispatcher: CallbackDispatcher, alert: AlertEvent, *, wait_seconds: float = 0.1
) -> None:
    dispatcher.enqueue(alert)
    task = asyncio.create_task(dispatcher.run())
    await asyncio.sleep(wait_seconds)
    task.cancel()


def _print_counters(dispatcher: CallbackDispatcher, *, alert_id: str) -> None:
    print(f"  counters: {dispatcher.counters.snapshot()}")
    record = dispatcher.tracker.status_of(alert_id)
    if record is not None:
        print(
            f"  delivery status ({alert_id}): {record.status.value} "
            f"(attempts={record.attempt_count}, last_error={record.last_error})"
        )


def main() -> None:
    print("=" * 60)
    print("CALLBACK DISPATCHER — delivered, rejected, oversized, retried")
    print("=" * 60)

    endpoint = "https://magic-host.internal.example/magic/callbacks/telemetry-alerts"
    config = parse_callbacks_config({"endpoint": endpoint})
    sink = _ScriptedSink(endpoint)

    # A fresh CallbackDispatcher (and therefore a fresh asyncio.Queue) per
    # step — each step runs under its own asyncio.run() event loop, and
    # asyncio primitives should not be reused across separate loops.

    _step("1. HighRejectRate fires critical -> Magic accepts it")
    dispatcher_1 = CallbackDispatcher(sink, config, secret=b"demo-secret")
    alert_1 = _make_alert(alert_id="alert-1", rule_name="HighRejectRate")
    asyncio.run(_run_one(dispatcher_1, alert_1))
    _print_counters(dispatcher_1, alert_id="alert-1")

    _step("2. ParseErrorRate fires warning -> Magic rejects it (permanent, no retry)")
    dispatcher_2 = CallbackDispatcher(sink, config, secret=b"demo-secret")
    alert_2 = _make_alert(
        alert_id="alert-2", rule_name="ParseErrorRate", severity="warning"
    )
    asyncio.run(_run_one(dispatcher_2, alert_2))
    _print_counters(dispatcher_2, alert_id="alert-2")

    _step("3. Oversized alert -> dropped locally, never reaches Magic at all")
    tiny_config = parse_callbacks_config({"endpoint": endpoint, "maxBytes": 10})
    dispatcher_3 = CallbackDispatcher(sink, tiny_config, secret=b"demo-secret")
    alert_3 = _make_alert(alert_id="alert-3", rule_name="AckLatencyBreach")
    asyncio.run(_run_one(dispatcher_3, alert_3))
    _print_counters(dispatcher_3, alert_id="alert-3")

    _step(
        "4. AckLatencyBreach fires -> Magic errors twice, then succeeds "
        "(watch the backoff delay between attempts)"
    )
    dispatcher_4 = CallbackDispatcher(sink, config, secret=b"demo-secret")
    alert_4 = _make_alert(alert_id="alert-4", rule_name="AckLatencyBreach")
    asyncio.run(_run_one(dispatcher_4, alert_4, wait_seconds=8.0))
    _print_counters(dispatcher_4, alert_id="alert-4")


if __name__ == "__main__":
    main()
