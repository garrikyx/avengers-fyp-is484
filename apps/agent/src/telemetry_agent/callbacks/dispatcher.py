"""UBS-32: dispatches Rule Engine alerts to Magic's callback endpoint.

`enqueue()` is the entry point a future supervisor/pipeline-wiring step
calls with each `AlertEvent` `RuleEngine.evaluate()`/`apply_rules()`
produces; nothing in this repo calls it yet (see docs/plan/scaffold.md).

UBS-32 scope: a single delivery attempt per alert. On anything other than a
2xx response, the failure is logged and counted — no retry loop yet. That's
UBS-33's extension to `_deliver()`.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.callbacks.config import CallbacksConfig
from telemetry_agent.callbacks.payload import from_alert_event
from telemetry_agent.callbacks.queue import DropOldestQueue
from telemetry_agent.callbacks.self_metrics import CounterRegistry
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.callbacks.sink import CallbackSink


class CallbackDispatcher:
    def __init__(
        self,
        sink: CallbackSink,
        config: CallbacksConfig,
        secret: bytes,
        *,
        counters: CounterRegistry | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._sink = sink
        self._config = config
        self._secret = secret
        self._counters = counters or CounterRegistry()
        self._logger = logger or logging.getLogger(__name__)
        self._queue: DropOldestQueue[AlertEvent] = DropOldestQueue(
            config.queue_size,
            on_drop=lambda: self._counters.increment("callback_queue_dropped"),
        )

    @property
    def counters(self) -> CounterRegistry:
        return self._counters

    def enqueue(self, alert: AlertEvent) -> None:
        """Sync, non-blocking — the entry point a future wiring step calls
        from the same site that calls `RuleEngine.evaluate()`.
        """
        self._queue.put_dropping_oldest(alert)

    async def run(self) -> None:
        """Spawns `maxInflight` workers pulling from the queue. Runs until
        cancelled by the caller.
        """
        workers = [
            asyncio.create_task(self._worker_loop())
            for _ in range(self._config.max_inflight)
        ]
        try:
            await asyncio.gather(*workers)
        finally:
            for worker in workers:
                worker.cancel()

    async def _worker_loop(self) -> None:
        while True:
            alert = await self._queue.get()
            await self._deliver(alert)

    async def _deliver(self, alert: AlertEvent) -> None:
        idempotency_key = (
            f"{alert.alert_id}:{alert.status}:{alert.notification_count}"
        )
        payload = from_alert_event(alert, now=datetime.now(UTC))
        body = payload.model_dump_json(by_alias=True).encode("utf-8")

        if len(body) > self._config.max_bytes:
            self._logger.error(
                "callback payload for alert %s exceeds max_bytes (%d > %d); dropping",
                alert.alert_id,
                len(body),
                self._config.max_bytes,
            )
            self._counters.increment("callback_failures")
            return

        timestamp = str(int(datetime.now(UTC).timestamp()))
        headers = {
            "Content-Type": "application/json",
            "X-Telemetry-Delivery-Id": str(uuid.uuid4()),
            "X-Telemetry-Idempotency-Key": idempotency_key,
            "X-Telemetry-Timestamp": timestamp,
            "X-Telemetry-Signature": sign(self._secret, timestamp, body),
        }
        result = await self._sink.send(body=body, headers=headers)

        if result.status_code is not None and 200 <= result.status_code < 300:
            self._counters.increment("callback_delivered")
            return

        self._logger.error(
            "callback delivery failed for alert %s: status=%s error=%s",
            alert.alert_id,
            result.status_code,
            result.error_class,
        )
        self._counters.increment("callback_failures")
