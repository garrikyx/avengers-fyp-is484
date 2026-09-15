"""Minimal walkthrough of the Callback Dispatcher (UBS-32).

    uv run python -m telemetry_agent.callbacks.demo_quickstart

Three alerts through the dispatcher: one delivers cleanly, one gets a
permanent rejection from "Magic", one is oversized and never even gets
sent. No real network calls — a small scripted sink stands in for Magic so
the outcomes are deterministic and visible, the same idea as
`metrics/demo_quickstart.py`.
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
    queue concurrently, so call order isn't deterministic) to show both
    the success and failure paths without a real endpoint.
    """

    _REJECTED_ALERT_ID = "alert-2"

    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> CallbackResult:
        print(f"  >> POST {self._endpoint}")
        for name in ("X-Telemetry-Delivery-Id", "X-Telemetry-Idempotency-Key"):
            print(f"     {name}: {headers[name]}")
        print(f"     body ({len(body)} bytes): {body.decode('utf-8')}")

        if f'"alertId":"{self._REJECTED_ALERT_ID}"' in body.decode("utf-8"):
            print('  << 400 Bad Request {"error": "bad request"}')
            return CallbackResult(
                status_code=400, latency_ms=8.0, response_snippet="bad request"
            )
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


async def _run_one(dispatcher: CallbackDispatcher, alert: AlertEvent) -> None:
    dispatcher.enqueue(alert)
    task = asyncio.create_task(dispatcher.run())
    await asyncio.sleep(0.1)
    task.cancel()


def main() -> None:
    print("=" * 60)
    print("CALLBACK DISPATCHER — one delivered, one rejected, one oversized")
    print("=" * 60)

    endpoint = "https://magic-host.internal.example/magic/callbacks/telemetry-alerts"
    config = parse_callbacks_config({"endpoint": endpoint})
    sink = _ScriptedSink(endpoint)
    dispatcher = CallbackDispatcher(sink, config, secret=b"demo-secret")

    _step("1. HighRejectRate fires critical -> Magic accepts it")
    alert_1 = _make_alert(alert_id="alert-1", rule_name="HighRejectRate")
    asyncio.run(_run_one(dispatcher, alert_1))

    _step("2. ParseErrorRate fires warning -> Magic rejects it (permanent, no retry)")
    alert_2 = _make_alert(
        alert_id="alert-2", rule_name="ParseErrorRate", severity="warning"
    )
    asyncio.run(_run_one(dispatcher, alert_2))

    _step("3. Oversized alert -> dropped locally, never reaches Magic at all")
    tiny_config = parse_callbacks_config({"endpoint": endpoint, "maxBytes": 10})
    oversized_dispatcher = CallbackDispatcher(sink, tiny_config, secret=b"demo-secret")
    asyncio.run(
        _run_one(
            oversized_dispatcher,
            _make_alert(alert_id="alert-3", rule_name="AckLatencyBreach"),
        )
    )

    print("\n" + "=" * 60)
    print("FINAL COUNTERS")
    print("=" * 60)
    print("  main dispatcher:     ", dispatcher.counters.snapshot())
    print("  oversized dispatcher:", oversized_dispatcher.counters.snapshot())


if __name__ == "__main__":
    main()
