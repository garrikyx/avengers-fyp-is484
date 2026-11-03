"""Push alert transitions to the Teams group chat (UBS-120; spec 000 s3.1, Q-10).

Every alert, agent-routed or backend-raised (`AgentHeartbeatMissing`), reaches
the Alert Store through `AlertStore.merge()`. `NotifyingAlertStore` wraps that
one call: it reads the alert's status before and after the merge and hands a
*transition* to `AlertNotifier`, which posts it to the Teams app's
`POST /api/notify` (the Integration Service). Teams renders the card; it
never reads the stores (UBS-120 "Teams never reads Redis or other stores").

What counts as a transition (`transition_kind`):

- `firing`   - the alert is now `firing` and was not already firing or
  resolving. A renotify (`notificationCount` > 1), a severity change while
  firing, the heartbeat monitor re-merging `firing` every tick, or a flap
  `resolving -> firing` is the same occurrence, so no new card.
- `resolved` - the alert is now `resolved` and was firing or resolving. A
  resolve for an alert this backend never saw fire (e.g. after a restart) or
  one that never got past `pending` posts nothing.

Each `alertId:kind` posts at most once (bounded LRU), which covers a retry or
the same transition arriving twice. `alertId` rotates per occurrence on the
agent (FR-QRY-019), so a new occurrence always gets its own cards.

Delivery never blocks ingestion: `merge()` only appends to a bounded queue
(drop-oldest), and one background task sends with retries. `merge()` may run
on the event loop (ingestion) or in a worker thread (the heartbeat monitor),
so the hand-off to the loop is thread-safe. Outcomes are exported on the
internal `/metrics` (`collector()`).
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from collections import OrderedDict, deque
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.parse import urlparse

import httpx
import yaml
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily, Metric
from prometheus_client.registry import Collector
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.alerts_query import AlertRecord
from telemetry_shared.models.notifications import AlertNotification, NotificationKind

from telemetry_backend.config import (
    AlertStoreConfig,
    BackendConfigError,
    parse_duration_seconds,
)
from telemetry_backend.services.alert_store import AlertStore

logger = logging.getLogger(__name__)

TOKEN_ENV = "MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN"
_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_WAS_FIRING = frozenset({"firing", "resolving"})
_NS = "telemetry_backend"

Outcome = Literal["delivered", "retry", "drop"]


# --- config -------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class TeamsNotifyConfig:
    """`notifications.teams` in `backend.yaml`. Off unless enabled."""

    enabled: bool = False
    endpoint: str = "http://127.0.0.1:3978/api/notify"
    timeout_seconds: float = 5.0
    queue_size: int = 256
    max_attempts: int = 3
    retry_base_seconds: float = 1.0
    dedupe_capacity: int = 10_000

    def __post_init__(self) -> None:
        url = urlparse(self.endpoint)
        if url.scheme not in {"http", "https"} or not url.hostname:
            raise BackendConfigError(
                f"notifications.teams.endpoint must be an http(s) URL, "
                f"got {self.endpoint!r}"
            )
        if url.scheme == "http" and url.hostname not in _LOCAL_HOSTS:
            # The bearer token would cross the network in clear text.
            raise BackendConfigError(
                "notifications.teams.endpoint must use https unless it is localhost"
            )
        if self.timeout_seconds <= 0:
            raise BackendConfigError("notifications.teams.timeout must be > 0")
        if self.queue_size < 1:
            raise BackendConfigError("notifications.teams.queueSize must be >= 1")
        if self.max_attempts < 1:
            raise BackendConfigError("notifications.teams.maxAttempts must be >= 1")
        if self.retry_base_seconds < 0:
            raise BackendConfigError("notifications.teams.retryBase must be >= 0")
        if self.dedupe_capacity < 1:
            raise BackendConfigError("notifications.teams.dedupeCapacity must be >= 1")


class _Strict(BaseModel):
    # This section is ours alone, so a typo fails `--check-config` instead of
    # silently keeping a default.
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid"
    )


class _TeamsYaml(_Strict):
    enabled: bool | None = None
    endpoint: str | None = None
    timeout: str | int | float | None = None
    queue_size: int | None = None
    max_attempts: int | None = None
    retry_base: str | int | float | None = None
    dedupe_capacity: int | None = None


class _NotificationsYaml(_Strict):
    teams: _TeamsYaml | None = None


def load_teams_notify_config(path: Path | str | None) -> TeamsNotifyConfig:
    """Read `notifications.teams` from `backend.yaml`; defaults if absent."""
    if path is None or not Path(path).exists():
        return TeamsNotifyConfig()
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise BackendConfigError(f"{path}: invalid YAML: {exc}") from exc
    section = raw.get("notifications") if isinstance(raw, dict) else None
    if section is None:
        return TeamsNotifyConfig()
    try:
        parsed = _NotificationsYaml.model_validate(section).teams or _TeamsYaml()
    except ValidationError as exc:
        raise BackendConfigError(f"{path}: notifications: {exc}") from exc
    values: dict[str, Any] = {
        "enabled": parsed.enabled,
        "endpoint": parsed.endpoint,
        "queue_size": parsed.queue_size,
        "max_attempts": parsed.max_attempts,
        "dedupe_capacity": parsed.dedupe_capacity,
    }
    if parsed.timeout is not None:
        values["timeout_seconds"] = parse_duration_seconds(parsed.timeout)
    if parsed.retry_base is not None:
        values["retry_base_seconds"] = parse_duration_seconds(parsed.retry_base)
    return TeamsNotifyConfig(**{k: v for k, v in values.items() if v is not None})


def notify_token(env: dict[str, str] | None = None) -> str:
    """The shared secret the Teams app checks on `/api/notify`. Required when
    notifications are enabled; there is deliberately no dev fallback."""
    token = (os.environ if env is None else env).get(TOKEN_ENV, "")
    if not token:
        raise BackendConfigError(
            f"{TOKEN_ENV} is required when notifications.teams.enabled is true"
        )
    return token


# --- transitions --------------------------------------------------------------


def transition_kind(before: str | None, after: str | None) -> NotificationKind | None:
    """Which card, if any, a status change `before -> after` deserves."""
    if after == "firing" and before not in _WAS_FIRING:
        return "firing"
    if after == "resolved" and before in _WAS_FIRING:
        return "resolved"
    return None


# --- delivery -----------------------------------------------------------------


class NotifySink(Protocol):
    async def send(self, notification: AlertNotification) -> Outcome: ...

    async def aclose(self) -> None: ...


class HttpNotifySink:
    """POSTs a notification to the Teams app's `/api/notify`."""

    def __init__(
        self,
        endpoint: str,
        token: str,
        *,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._client = httpx.AsyncClient(
            timeout=timeout_seconds,
            transport=transport,
            headers={"Authorization": f"Bearer {token}"},
        )
        self._warned_no_chat = False

    async def send(self, notification: AlertNotification) -> Outcome:
        try:
            response = await self._client.post(
                self._endpoint,
                content=notification.model_dump_json(by_alias=True),
                headers={"Content-Type": "application/json"},
            )
        except httpx.HTTPError as exc:
            logger.warning("teams notify failed: %s", type(exc).__name__)
            return "retry"
        status = response.status_code
        if 200 <= status < 300:
            return "delivered"
        if status == 409:
            # The bot has not been added to (or messaged in) a group chat yet.
            if not self._warned_no_chat:
                self._warned_no_chat = True
                logger.warning(
                    "teams notify: no group chat registered; add the bot to the "
                    "team's group chat (see apps/teams/README.md)"
                )
            return "drop"
        if status == 429 or status >= 500:
            return "retry"
        logger.error("teams notify rejected: status=%d", status)
        return "drop"

    async def aclose(self) -> None:
        await self._client.aclose()


class AlertNotifier:
    """Bounded, thread-safe hand-off from `merge()` to one sender task."""

    def __init__(self, sink: NotifySink, config: TeamsNotifyConfig) -> None:
        self._sink = sink
        self._config = config
        self._lock = threading.Lock()
        self._pending: deque[AlertNotification] = deque()
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._wake: asyncio.Event | None = None
        self._task: asyncio.Task[None] | None = None
        self.counts: dict[str, int] = {
            "queued": 0,
            "delivered": 0,
            "failed": 0,
            "dropped_queue_full": 0,
            "dropped_not_running": 0,
            "duplicates": 0,
        }

    # --- producer side: any thread ---------------------------------------------

    def observe(self, kind: NotificationKind, alert: AlertRecord) -> bool:
        """Queue a card for this transition. Returns False if it was a
        duplicate or could not be queued. Never raises, never blocks."""
        notification = AlertNotification(kind=kind, alert=alert)
        key = notification.dedupe_key
        with self._lock:
            if key in self._seen:
                self.counts["duplicates"] += 1
                return False
            self._seen[key] = None
            while len(self._seen) > self._config.dedupe_capacity:
                self._seen.popitem(last=False)
            loop = self._loop
            if loop is None or loop.is_closed():
                self.counts["dropped_not_running"] += 1
                return False
            if len(self._pending) >= self._config.queue_size:
                self._pending.popleft()  # oldest first: keep the latest state
                self.counts["dropped_queue_full"] += 1
            self._pending.append(notification)
            self.counts["queued"] += 1
        try:
            loop.call_soon_threadsafe(self._signal)
        except RuntimeError:  # loop closed between the check and the call
            pass
        return True

    def _signal(self) -> None:
        if self._wake is not None:
            self._wake.set()

    # --- consumer side: the event loop -------------------------------------------

    def start(self) -> None:
        """Call from inside the running loop that should do the sending."""
        if self._task is not None:
            return
        self._loop = asyncio.get_running_loop()
        self._wake = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="telemetry-teams-notify")

    async def aclose(self) -> None:
        with self._lock:
            self._loop = None
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._sink.aclose()

    def _take(self) -> AlertNotification | None:
        with self._lock:
            return self._pending.popleft() if self._pending else None

    async def _run(self) -> None:
        assert self._wake is not None
        while True:
            notification = self._take()
            if notification is None:
                # Safe without a re-check: `_signal` only runs on this loop,
                # so it cannot slip in between the empty take and the clear.
                self._wake.clear()
                await self._wake.wait()
                continue
            await self.deliver(notification)

    async def deliver(self, notification: AlertNotification) -> Outcome:
        """Send one notification with bounded retries; counts the outcome."""
        outcome: Outcome = "retry"
        for attempt in range(1, self._config.max_attempts + 1):
            try:
                outcome = await self._sink.send(notification)
            except Exception:
                logger.exception("teams notify sink raised")
                outcome = "retry"
            if outcome != "retry":
                break
            if attempt < self._config.max_attempts:
                await asyncio.sleep(
                    self._config.retry_base_seconds * (2 ** (attempt - 1))
                )
        with self._lock:
            self.counts["delivered" if outcome == "delivered" else "failed"] += 1
        if outcome != "delivered":
            logger.warning(
                "teams notify gave up on %s (%s)",
                notification.dedupe_key,
                notification.alert.rule_name,
            )
        return outcome

    # --- observability ----------------------------------------------------------

    def queue_depth(self) -> int:
        with self._lock:
            return len(self._pending)

    def collector(self) -> Collector:
        return _NotifierCollector(self)


class _NotifierCollector(Collector):
    def __init__(self, notifier: AlertNotifier) -> None:
        self._notifier = notifier

    def collect(self) -> Iterator[Metric]:
        with self._notifier._lock:
            counts = dict(self._notifier.counts)
        family = CounterMetricFamily(
            f"{_NS}_teams_notifications",
            "Teams alert notifications by outcome (UBS-120)",
            labels=["outcome"],
        )
        for outcome, value in sorted(counts.items()):
            family.add_metric([outcome], value)
        yield family
        yield GaugeMetricFamily(
            f"{_NS}_teams_notify_queue_depth",
            "Teams notifications waiting to be sent (UBS-120)",
            value=self._notifier.queue_depth(),
        )


# --- the store hook -------------------------------------------------------------


class NotifyingAlertStore(AlertStore):
    """`AlertStore` that reports firing/resolved transitions to a notifier.

    A subclass rather than a change to `AlertStore`, so the store's own code
    (UBS-93/94) is untouched; `merge()` is the single path every alert takes.
    """

    def __init__(
        self, notifier: AlertNotifier, config: AlertStoreConfig | None = None
    ) -> None:
        super().__init__(config)
        self._notifier = notifier
        # Serialises before/merge/after so two concurrent merges of one alert
        # cannot both see the same `before` and both report the transition.
        self._transition_lock = threading.Lock()

    @property
    def notifier(self) -> AlertNotifier:
        """`create_app`'s lifespan starts and stops this with the app."""
        return self._notifier

    def merge(
        self,
        event: AlertEvent,
        *,
        source: Literal["agent", "backend"] = "agent",
        now: datetime | None = None,
    ) -> None:
        with self._transition_lock:
            before = self.get_alert(event.alert_id)
            super().merge(event, source=source, now=now)
            after = self.get_alert(event.alert_id)
        if after is None:
            return
        kind = transition_kind(
            before.alert.status if before is not None else None, after.alert.status
        )
        if kind is None:
            return
        try:
            self._notifier.observe(kind, after.alert)
        except Exception:  # a notification problem must never fail ingestion
            logger.exception("teams notify observe failed")
