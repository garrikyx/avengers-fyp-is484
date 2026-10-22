"""UBS-35: runs a rule's actions when its alert fires (spec 005 §5).

`AlertRouter` hands every routed alert to `enqueue()`. Most are ignored:

- `FR-CBK-016`: only the `pending→firing` event of an occurrence starts
  actions. The engine emits that event with `notificationCount == 1`; a
  renotify or a severity change while firing carries a higher count, and a
  resolve has another status. A bounded seen-set keyed by `alertId` covers
  anything that re-delivers the same first event.
- Actions run **one at a time**, from one queue, each under its own timeout.
- `FR-CBK-015`: a `command` is started with `create_subprocess_exec` (no
  shell), the configured argv only, and the §3.3 callback JSON on stdin.
  Nothing from the alert reaches an argument.
- `FR-CBK-014`: a `callback` action is its own `CallbackDispatcher`, so
  signing, retry, delivery tracking and dry run are the §3 ones. Its counters
  are its own, so a failing hook never trips `CallbackFailing` for Magic.
- `FR-CBK-017`: whatever happens here is counted and logged, never raised.
  The router's guard is the second line of defence.

Outcomes are counted as `action_runs:<action>:<outcome>`, and run time as
`action_run_ms:<action>`. `CounterRegistry` has no labels, so the labels are
folded into the name. Outcomes:

    ok        exit status 0, or the callback was delivered
    failed    non-zero exit status, or the callback failed for good
    timeout   killed (command) or abandoned (callback) at its timeout
    error     could not be started, e.g. the executable is missing
    dry_run   logged what would run (the default)
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime

import httpx
from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.actions.config import ActionCatalogue, ActionDef, ActionType
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.payload import from_alert_event
from telemetry_agent.callbacks.queue import DropOldestQueue
from telemetry_agent.callbacks.sink import DryRunCallbackSink, HttpsCallbackSink
from telemetry_agent.callbacks.status import DeliveryStatus
from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_agent.rules.types import AlertStatus

DEFAULT_QUEUE_SIZE = 64
DEFAULT_SEEN_CAPACITY = 1024


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ActionRunner:
    def __init__(
        self,
        catalogue: ActionCatalogue,
        rule_actions: Callable[[str], Sequence[str]],
        *,
        secret: bytes,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        seen_capacity: int = DEFAULT_SEEN_CAPACITY,
        callback_transport: httpx.AsyncBaseTransport | None = None,
        counters: CounterRegistry | None = None,
        clock: Callable[[], datetime] = _utc_now,
        logger: logging.Logger | None = None,
    ) -> None:
        self._rule_actions = rule_actions
        self._secret = secret
        self._callback_transport = callback_transport
        self._counters = counters or CounterRegistry()
        self._clock = clock
        self._logger = logger or logging.getLogger(__name__)
        self._queue: DropOldestQueue[tuple[AlertEvent, str]] = DropOldestQueue(
            queue_size,
            on_drop=lambda: self._counters.increment("action_queue_dropped"),
        )
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._seen_capacity = seen_capacity
        self._catalogue: dict[str, ActionDef] = {}
        self._dispatchers: dict[str, CallbackDispatcher] = {}
        self._sinks: dict[str, HttpsCallbackSink | DryRunCallbackSink] = {}
        self._retired_sinks: list[HttpsCallbackSink | DryRunCallbackSink] = []
        self.replace_catalogue(catalogue)

    @property
    def counters(self) -> CounterRegistry:
        return self._counters

    @property
    def catalogue(self) -> Mapping[str, ActionDef]:
        return self._catalogue

    def replace_catalogue(self, catalogue: ActionCatalogue) -> None:
        """Swap in a reloaded catalogue. A callback action whose definition
        is unchanged keeps its dispatcher; the sinks of changed or removed
        ones are closed by `aclose()`. A run already queued looks its action
        up when it starts, so it uses the new definition, or is skipped
        (counted `unknown`) if the action was removed."""
        new = dict(catalogue)
        for name, sink in list(self._sinks.items()):
            if new.get(name) != self._catalogue.get(name):
                self._retired_sinks.append(sink)
                del self._sinks[name]
                del self._dispatchers[name]
        for name, action in new.items():
            if action.type is ActionType.CALLBACK and name not in self._dispatchers:
                self._dispatchers[name] = self._build_dispatcher(action)
        self._catalogue = new

    def _build_dispatcher(self, action: ActionDef) -> CallbackDispatcher:
        assert action.callbacks is not None  # ActionType.CALLBACK
        config = action.callbacks
        sink: HttpsCallbackSink | DryRunCallbackSink
        if config.dry_run:
            sink = DryRunCallbackSink(logger=self._logger)
        else:
            sink = HttpsCallbackSink(
                config.endpoint,
                connect_timeout_seconds=config.connect_timeout_seconds,
                total_timeout_seconds=config.timeout_seconds,
                allow_insecure_callback=config.allow_insecure_callback,
                transport=self._callback_transport,
            )
        self._sinks[action.name] = sink
        return CallbackDispatcher(sink, config, self._secret, logger=self._logger)

    def enqueue(self, alert: AlertEvent) -> int:
        """Sync and non-blocking, called from `AlertRouter.route`. Returns
        how many action runs were queued for this alert (usually 0)."""
        if alert.status != AlertStatus.FIRING.value or alert.notification_count != 1:
            return 0  # FR-CBK-016: renotify, severity change or resolve
        names = tuple(self._rule_actions(alert.rule_name))
        if not names or alert.alert_id in self._seen:
            return 0
        self._seen[alert.alert_id] = None
        while len(self._seen) > self._seen_capacity:
            self._seen.popitem(last=False)
        for name in names:
            self._queue.put_dropping_oldest((alert, name))
        return len(names)

    async def run(self) -> None:
        """Drain the queue one run at a time until cancelled."""
        while True:
            alert, name = await self._queue.get()
            await self.execute(alert, name)

    async def execute(self, alert: AlertEvent, name: str) -> str:
        """Run one action for one alert and return its outcome. Never raises
        (except cancellation)."""
        action = self._catalogue.get(name)
        if action is None:
            self._record(name, "unknown", 0.0)
            return "unknown"
        started = time.monotonic()
        try:
            if action.type is ActionType.COMMAND:
                outcome = await self._run_command(action, alert)
            else:
                outcome = await self._run_callback(action, alert)
        except asyncio.CancelledError:
            raise
        except Exception:
            self._logger.exception(
                "action %s failed for alert %s", name, alert.alert_id
            )
            outcome = "error"
        self._record(name, outcome, time.monotonic() - started)
        return outcome

    def _record(self, name: str, outcome: str, elapsed_seconds: float) -> None:
        self._counters.increment(f"action_runs:{name}:{outcome}")
        self._counters.increment(f"action_run_ms:{name}", int(elapsed_seconds * 1000))

    def _stdin(self, alert: AlertEvent) -> bytes:
        payload = from_alert_event(alert, now=self._clock())
        return payload.model_dump_json(by_alias=True).encode("utf-8")

    async def _run_command(self, action: ActionDef, alert: AlertEvent) -> str:
        assert action.command is not None  # ActionType.COMMAND
        stdin = self._stdin(alert)
        if action.dry_run:
            self._logger.info(
                "dry-run action %s for alert %s (%s): would run %s with "
                "%d bytes of alert JSON on stdin",
                action.name,
                alert.alert_id,
                alert.rule_name,
                [str(action.command), *action.args],
                len(stdin),
            )
            return "dry_run"
        try:
            process = await asyncio.create_subprocess_exec(
                str(action.command),
                *action.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            self._logger.error(
                "action %s could not start %s: %s", action.name, action.command, exc
            )
            return "error"
        try:
            _, stderr = await asyncio.wait_for(
                process.communicate(stdin), timeout=action.timeout_seconds
            )
        except TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                process.kill()
            await process.wait()
            self._logger.error(
                "action %s timed out after %.0fs for alert %s; killed",
                action.name,
                action.timeout_seconds,
                alert.alert_id,
            )
            return "timeout"
        if process.returncode != 0:
            self._logger.error(
                "action %s exited %s for alert %s: %s",
                action.name,
                process.returncode,
                alert.alert_id,
                stderr.decode("utf-8", errors="replace")[-500:],
            )
            return "failed"
        self._logger.info("action %s ran for alert %s", action.name, alert.alert_id)
        return "ok"

    async def _run_callback(self, action: ActionDef, alert: AlertEvent) -> str:
        dispatcher = self._dispatchers[action.name]
        try:
            status = await asyncio.wait_for(
                dispatcher.deliver(alert), timeout=action.timeout_seconds
            )
        except TimeoutError:
            self._logger.error(
                "callback action %s timed out after %.0fs for alert %s",
                action.name,
                action.timeout_seconds,
                alert.alert_id,
            )
            return "timeout"
        if action.dry_run:
            return "dry_run"
        return "ok" if status is DeliveryStatus.DELIVERED else "failed"

    async def aclose(self) -> None:
        for sink in [*self._sinks.values(), *self._retired_sinks]:
            aclose = getattr(sink, "aclose", None)
            if aclose is not None:
                with contextlib.suppress(Exception):
                    await aclose()
        self._retired_sinks.clear()
