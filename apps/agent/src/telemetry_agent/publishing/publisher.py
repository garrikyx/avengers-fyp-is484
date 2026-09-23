"""UBS-103/104: batches buffered telemetry, gzip-compresses it, and POSTs
it to the backend's Ingestion Service every `interval_seconds` (spec 002
§6, `FR-PUB-001`), buffering through an outage and backing off on
transient failures (`FR-PUB-004`/`005`).

`enqueue_snapshot()`/`enqueue_event()`/`enqueue_alert()` are the entry
points a future supervisor/pipeline-wiring step calls with each completed
`Snapshot`/`TelemetryEvent`/`AlertEvent` the Metrics Aggregator and Rule
Engine produce; nothing in this repo calls them yet (mirrors
`callbacks.dispatcher`'s own "nothing calls it yet" scope). Every
`enqueue_*` is a synchronous, non-blocking deque append (`FR-PUB-007`) --
publishing can never stall aggregation or rule evaluation, and it never
blocks the Callback Dispatcher either, since the two share no state
(`NFR-REL-003`).

Response classification (spec 007 §2.1's 202/400/401/403/408/413/429/5xx
table, UBS-103) drives one of six actions: `COMMIT` (drop, success),
`DROP_REJECTED` (drop, permanent), `HALT` (stop and probe slowly),
`SPLIT` (halve `maxBatchItems`, new batch identity), `RETRY_AFTER` (honour
the server's wait), or `BACKOFF` (UBS-104: real exponential backoff with
jitter via `RetryPolicy`, unbounded in count -- data loss on a sustained
outage happens through the buffer's own byte/age eviction, `FR-PUB-004`,
not through giving up on a batch).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import Heartbeat, TelemetryEvent
from telemetry_shared.models.snapshot import Snapshot

from telemetry_agent.common.backoff import RetryPolicy
from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_agent.publishing.batch import BatchSequencer, build_batch
from telemetry_agent.publishing.buffer import PublishBuffer, make_pending_item
from telemetry_agent.publishing.config import PublishConfig
from telemetry_agent.publishing.outcome import PublishAction, classify_publish_response
from telemetry_agent.publishing.sink import PublishSink

HeartbeatProvider = Callable[[], Heartbeat | None]
BackendUnreachableCallback = Callable[[str], None]
DropCallback = Callable[[], None]


class BackendPublisher:
    def __init__(
        self,
        sink: PublishSink,
        config: PublishConfig,
        *,
        agent_id: str,
        application: str,
        heartbeat_provider: HeartbeatProvider | None = None,
        on_backend_unreachable: BackendUnreachableCallback | None = None,
        on_drop: DropCallback | None = None,
        counters: CounterRegistry | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._sink = sink
        self._config = config
        self._agent_id = agent_id
        self._application = application
        self._heartbeat_provider = heartbeat_provider
        self._on_backend_unreachable = on_backend_unreachable
        self._counters = counters or CounterRegistry()

        def _on_buffer_drop() -> None:
            self._counters.increment("publish_dropped_items")
            if on_drop is not None:
                on_drop()

        self._logger = logger or logging.getLogger(__name__)
        self._buffer = PublishBuffer(
            max_bytes=config.buffer_bytes,
            max_age_seconds=config.buffer_max_age_seconds,
            on_drop=_on_buffer_drop,
        )
        self._sequencer = BatchSequencer()
        self._retry_policy = RetryPolicy(
            base_seconds=config.retry_base_seconds,
            factor=config.retry_factor,
            cap_seconds=config.retry_cap_seconds,
            jitter=config.retry_jitter,
        )
        self._max_batch_items = config.max_batch_items
        self._halted = False
        self._halted_at: datetime | None = None
        self._retry_after_until: datetime | None = None
        self._backoff_until: datetime | None = None
        self._consecutive_failures = 0
        self._logged_schema_error = False

    @property
    def counters(self) -> CounterRegistry:
        return self._counters

    @property
    def consecutive_failures(self) -> int:
        """UBS-75 / `FR-MET-031`: failed attempts in a row since the last
        successful commit — what `BackendUnreachable` alerts on.

        Read rather than a windowed `publish_failures` count because
        `FR-PUB-005`'s exponential backoff spaces attempts further and
        further apart, so a fixed window measures the backoff schedule
        instead of the outage (spec 005 §1.2). This rises monotonically
        while the backend is unreachable and `_on_commit` zeroes it on the
        first success, which is what resolves the alert.
        """
        return self._consecutive_failures

    def enqueue_snapshot(
        self, snapshot: Snapshot, *, now: datetime | None = None
    ) -> None:
        """Sync, non-blocking (`FR-PUB-007`) — never awaits, never blocks
        on a full buffer (it drops the oldest item instead)."""
        self._buffer.append(
            make_pending_item("snapshot", snapshot, now or datetime.now(UTC))
        )

    def enqueue_event(
        self, event: TelemetryEvent, *, now: datetime | None = None
    ) -> None:
        self._buffer.append(
            make_pending_item("event", event, now or datetime.now(UTC))
        )

    def enqueue_alert(self, alert: AlertEvent, *, now: datetime | None = None) -> None:
        self._buffer.append(
            make_pending_item("alert", alert, now or datetime.now(UTC))
        )

    def queue_depth(self) -> int:
        return self._buffer.depth()

    def buffer_bytes(self) -> int:
        return self._buffer.total_bytes()

    async def run(self, stop: asyncio.Event | None = None) -> None:
        """Ticks `publish_once` every `interval_seconds` until `stop` is
        set. First tick is immediate."""
        stop = stop or asyncio.Event()
        while not stop.is_set():
            await self.publish_once()
            try:
                await asyncio.wait_for(
                    stop.wait(), timeout=self._config.interval_seconds
                )
            except TimeoutError:
                continue

    async def publish_once(
        self, *, now: datetime | None = None
    ) -> PublishAction | None:
        """One expire-form-send-classify-act cycle. Returns the action
        taken, or `None` if nothing was sent (buffer+heartbeat both empty,
        or the publisher is currently halted/rate-limited/backing-off and
        not due to try again yet). Public and side-effect-free to call
        repeatedly, so tests can drive it deterministically instead of
        sleeping through real ticks or real backoff delays.
        """
        now = now or datetime.now(UTC)
        self._buffer.expire(now)  # FR-PUB-004: age-bounded loss

        if self._backoff_until is not None and now < self._backoff_until:
            return None
        if self._retry_after_until is not None and now < self._retry_after_until:
            return None
        if self._halted:
            probe_due = (
                self._halted_at is not None
                and (now - self._halted_at).total_seconds()
                >= self._config.halt_probe_interval_seconds
            )
            if not probe_due:
                return None

        heartbeat = self._heartbeat_provider() if self._heartbeat_provider else None
        items = self._buffer.take(self._max_batch_items)
        if not items and heartbeat is None:
            return None

        batch = build_batch(
            items,
            agent_id=self._agent_id,
            application=self._application,
            sequencer=self._sequencer,
            heartbeat=heartbeat,
            now=now,
        )
        body = batch.model_dump_json(by_alias=True).encode("utf-8")
        result = await self._sink.send(
            body=body, headers={"Content-Type": "application/json"}
        )
        outcome = classify_publish_response(result)

        if outcome.action is PublishAction.COMMIT:
            self._on_commit()
            self._counters.increment("publish_delivered")
            return outcome.action

        if outcome.action is PublishAction.DROP_REJECTED:
            self._counters.increment("publish_rejected")
            if not self._logged_schema_error:
                self._logger.error(
                    "publish batch %s rejected: status=%s",
                    batch.batch_id,
                    outcome.status_code,
                )
                self._logged_schema_error = True
            return outcome.action

        # Every other outcome keeps the data — put it back and retry later.
        self._buffer.requeue_front(items)

        if outcome.action is PublishAction.HALT:
            self._halt(now, reason=f"status={outcome.status_code}")
        elif outcome.action is PublishAction.SPLIT:
            self._max_batch_items = max(1, self._max_batch_items // 2)
            self._counters.increment("publish_split")
            self._logger.warning(
                "publish batch %s too large (413); halved maxBatchItems to %d",
                batch.batch_id,
                self._max_batch_items,
            )
        elif outcome.action is PublishAction.RETRY_AFTER:
            self._counters.increment("publish_rate_limited")
            if outcome.retry_after_seconds is not None:
                self._retry_after_until = now + timedelta(
                    seconds=outcome.retry_after_seconds
                )
        else:  # BACKOFF (FR-PUB-005): real exponential backoff, unbounded
            self._consecutive_failures += 1
            delay = self._retry_policy.delay_for_attempt(self._consecutive_failures)
            self._backoff_until = now + timedelta(seconds=delay)
            self._counters.increment("publish_failures")
            self._logger.warning(
                "publish batch %s failed: status=%s error=%s; "
                "backing off %.1fs (attempt %d)",
                batch.batch_id,
                outcome.status_code,
                outcome.error_class,
                delay,
                self._consecutive_failures,
            )

        return outcome.action

    def _on_commit(self) -> None:
        self._halted = False
        self._halted_at = None
        self._retry_after_until = None
        self._backoff_until = None
        self._consecutive_failures = 0
        self._logged_schema_error = False
        if self._max_batch_items < self._config.max_batch_items:
            self._max_batch_items = min(
                self._config.max_batch_items, self._max_batch_items * 2
            )

    def _halt(self, now: datetime, *, reason: str) -> None:
        """`FR-PUB-006`'s 401/403 case: stop publishing and alert, then
        probe slowly rather than hammering an unreachable/unauthorized
        backend every tick."""
        if not self._halted:
            self._counters.increment("publish_halted")
            self._logger.error("publish halted: %s", reason)
            if self._on_backend_unreachable is not None:
                self._on_backend_unreachable(reason)
        self._halted = True
        self._halted_at = now
