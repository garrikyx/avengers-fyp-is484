"""UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback
endpoint, retrying transient failures with backoff and tracking each
alert's delivery status.

`enqueue()` is the entry point a future supervisor/pipeline-wiring step
calls with each `AlertEvent` `RuleEngine.evaluate()`/`apply_rules()`
produces; nothing in this repo calls it yet (see docs/plan/scaffold.md).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.callbacks.backoff import RetryPolicy
from telemetry_agent.callbacks.config import CallbacksConfig
from telemetry_agent.callbacks.payload import from_alert_event
from telemetry_agent.callbacks.queue import DropOldestQueue
from telemetry_agent.callbacks.retry import RetryDecision, classify_http_status
from telemetry_agent.callbacks.self_metrics import CounterRegistry
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.callbacks.sink import CallbackSink
from telemetry_agent.callbacks.status import DeliveryStatus, DeliveryTracker


class CallbackDispatcher:
    def __init__(
        self,
        sink: CallbackSink,
        config: CallbacksConfig,
        secret: bytes,
        *,
        counters: CounterRegistry | None = None,
        tracker: DeliveryTracker | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._sink = sink
        self._config = config
        self._secret = secret
        self._counters = counters or CounterRegistry()
        self._tracker = tracker or DeliveryTracker()
        self._logger = logger or logging.getLogger(__name__)
        self._queue: DropOldestQueue[AlertEvent] = DropOldestQueue(
            config.queue_size,
            on_drop=lambda: self._counters.increment("callback_queue_dropped"),
        )
        self._retry_policy = RetryPolicy(
            base_seconds=config.retry_base_seconds,
            factor=config.retry_factor,
            cap_seconds=config.retry_cap_seconds,
            jitter=config.retry_jitter,
            max_attempts=config.max_attempts,
        )

    @property
    def counters(self) -> CounterRegistry:
        return self._counters

    @property
    def tracker(self) -> DeliveryTracker:
        return self._tracker

    def enqueue(self, alert: AlertEvent) -> None:
        """Sync, non-blocking — the entry point a future wiring step calls
        from the same site that calls `RuleEngine.evaluate()`.
        """
        self._tracker.record(
            alert.alert_id, DeliveryStatus.PENDING, now=datetime.now(UTC)
        )
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
        """Signs and sends `alert`, retrying transient failures with
        backoff (`FR-CBK-004`/`006`) up to `maxAttempts`. A single fixed
        `X-Telemetry-Idempotency-Key` covers every attempt of this
        occurrence (`FR-CBK-003`); each attempt gets its own
        `X-Telemetry-Delivery-Id` so Magic can distinguish retries in logs.
        """
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
            self._tracker.record(
                alert.alert_id,
                DeliveryStatus.FAILED,
                now=datetime.now(UTC),
                error="payload_too_large",
            )
            return

        for attempt in range(1, self._config.max_attempts + 1):
            self._tracker.record(
                alert.alert_id, DeliveryStatus.SENT, now=datetime.now(UTC)
            )
            timestamp = str(int(datetime.now(UTC).timestamp()))
            headers = {
                "Content-Type": "application/json",
                "X-Telemetry-Delivery-Id": str(uuid.uuid4()),
                "X-Telemetry-Idempotency-Key": idempotency_key,
                "X-Telemetry-Timestamp": timestamp,
                "X-Telemetry-Signature": sign(self._secret, timestamp, body),
            }
            result = await self._sink.send(body=body, headers=headers)
            decision = (
                classify_http_status(result.status_code)
                if result.status_code is not None
                else RetryDecision.RETRY  # transport error: never reached Magic
            )

            if decision is RetryDecision.SUCCESS:
                self._counters.increment("callback_delivered")
                self._tracker.record(
                    alert.alert_id, DeliveryStatus.DELIVERED, now=datetime.now(UTC)
                )
                return

            if result.status_code is not None:
                failure_reason = f"http_{result.status_code}"
            else:
                failure_reason = result.error_class or "transport_error"

            if decision is RetryDecision.PERMANENT_FAILURE:
                self._logger.error(
                    "callback delivery permanently failed for alert %s: "
                    "status=%s error=%s",
                    alert.alert_id,
                    result.status_code,
                    result.error_class,
                )
                self._counters.increment("callback_failures")
                self._tracker.record(
                    alert.alert_id,
                    DeliveryStatus.FAILED,
                    now=datetime.now(UTC),
                    error=failure_reason,
                )
                return

            if attempt >= self._config.max_attempts:
                self._logger.error(
                    "callback delivery failed for alert %s after %d attempts: "
                    "status=%s error=%s",
                    alert.alert_id,
                    attempt,
                    result.status_code,
                    result.error_class,
                )
                self._counters.increment("callback_failures")
                self._tracker.record(
                    alert.alert_id,
                    DeliveryStatus.FAILED,
                    now=datetime.now(UTC),
                    error=failure_reason,
                )
                return

            delay = self._retry_policy.delay_for_attempt(
                attempt, retry_after=result.retry_after_seconds
            )
            self._logger.warning(
                "callback delivery attempt %d/%d failed for alert %s: "
                "status=%s error=%s; retrying in %.1fs",
                attempt,
                self._config.max_attempts,
                alert.alert_id,
                result.status_code,
                result.error_class,
                delay,
            )
            self._tracker.record(
                alert.alert_id,
                DeliveryStatus.RETRYING,
                now=datetime.now(UTC),
                error=failure_reason,
            )
            await asyncio.sleep(delay)
