"""Proactive alert cards in the team's group chat (UBS-120).

The backend posts an `AlertNotification` to `POST /api/notify` for each firing
or resolved transition. This module:

1. remembers *which* group chat to post into: the first group-chat activity
   the bot sees (being added to the chat, or any message in it) is saved as a
   `ConversationReference` in a small JSON file, so it survives a restart.
   `TEAMS_NOTIFY_CONVERSATION_ID` pins one chat when the bot is in several.
   `TEAMS_NOTIFY_ALLOW_PERSONAL=true` also accepts a 1:1 chat, so the local
   Agents Playground (a personal chat) can show alerts. Dev and demo only;
2. checks the backend's bearer token (`MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN`);
   the route is not a Teams activity, so the Teams JWT middleware skips it;
3. renders the alert as an Adaptive Card (every dynamic string escaped,
   FR-NLQ-022) and sends it with `adapter.continue_conversation`. When the
   connection runs with `ANONYMOUS_ALLOWED` (the local Playground's dummy
   credentials), the send uses an anonymous identity, the same way the SDK
   answers an anonymous incoming message, instead of asking Entra ID for a
   token it cannot get.

Responses: 202 sent, 200 duplicate (same `alertId:kind` already posted),
400 bad payload, 401 bad token, 409 no group chat registered yet, 502 Teams
refused the message (the backend retries 5xx).
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import threading
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import web
from microsoft_agents.activity import Activity, ConversationReference
from microsoft_agents.hosting.core import (
    AgentApplication,
    CardFactory,
    MessageFactory,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.authorization import (
    AuthenticationConstants,
    ClaimsIdentity,
)
from pydantic import ValidationError
from telemetry_shared.models.notifications import AlertNotification

from teams_agent.cards import SCHEMA_VERSION
from teams_agent.escape import escape_card_text

logger = logging.getLogger(__name__)

TOKEN_ENV = "MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN"
NOTIFY_PATH = "/api/notify"
_MAX_BODY_BYTES = 64 * 1024
_DEDUPE_CAPACITY = 2048


@dataclass(frozen=True, slots=True)
class NotifyConfig:
    token: str | None = None
    state_path: Path = Path(".teams-state/conversation.json")
    conversation_id: str | None = None
    timezone: str = "Asia/Singapore"
    allow_personal: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> NotifyConfig:
        source = os.environ if env is None else env
        defaults = cls()
        return cls(
            token=source.get(TOKEN_ENV) or None,
            state_path=Path(
                source.get("TEAMS_NOTIFY_STATE_PATH", str(defaults.state_path))
            ),
            conversation_id=source.get("TEAMS_NOTIFY_CONVERSATION_ID") or None,
            timezone=source.get("TEAMS_DEFAULT_TIMEZONE", defaults.timezone),
            allow_personal=source.get("TEAMS_NOTIFY_ALLOW_PERSONAL", "").lower()
            in {"1", "true", "yes"},
        )


class ConversationStore:
    """The one group chat alerts go to, persisted as JSON."""

    def __init__(
        self,
        path: Path,
        *,
        pinned_conversation_id: str | None = None,
        allow_personal: bool = False,
    ):
        self._path = path
        self._pinned = pinned_conversation_id
        self._types = {"groupChat", "personal"} if allow_personal else {"groupChat"}
        self._lock = threading.Lock()
        self._reference: ConversationReference | None = self._load()

    def _load(self) -> ConversationReference | None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            reference = ConversationReference.model_validate(raw)
        except FileNotFoundError:
            return None
        except ValueError, ValidationError:
            logger.warning("ignoring unreadable %s", self._path)
            return None
        if self._pinned and reference.conversation.id != self._pinned:
            return None
        return reference

    def get(self) -> ConversationReference | None:
        with self._lock:
            return self._reference

    def offer(self, activity: Activity) -> bool:
        """Remember `activity`'s conversation if it is the alert chat.
        Returns True when the stored reference changed."""
        conversation = activity.conversation
        if conversation is None:
            return False
        kind = conversation.conversation_type or "personal"  # Teams omits it 1:1
        if kind not in self._types:
            return False
        if self._pinned and conversation.id != self._pinned:
            return False
        reference = activity.get_conversation_reference()
        with self._lock:
            current = self._reference
            if current is not None and not self._pinned:
                # First chat wins; a second chat needs the pin to take over.
                if current.conversation.id != conversation.id:
                    return False
            if current is not None and (
                current.conversation.id == reference.conversation.id
                and current.service_url == reference.service_url
            ):
                return False
            self._reference = reference
            self._save(reference)
        logger.info(
            "alert notifications will post to chat %s (%s)", conversation.id, kind
        )
        return True

    def _save(self, reference: ConversationReference) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(
            reference.model_dump_json(by_alias=True, exclude_none=True),
            encoding="utf-8",
        )
        os.replace(tmp, self._path)  # atomic: a crash never leaves half a file


def register_conversation_capture(
    app: AgentApplication[TurnState], store: ConversationStore
) -> None:
    """Capture the group chat on every turn, before the normal handlers run,
    so the bot keeps answering questions exactly as before."""

    @app.before_turn
    async def capture(context: TurnContext, _state: TurnState) -> bool:
        try:
            store.offer(context.activity)
        except Exception:  # never block a user's question on this
            logger.exception("could not record the alert group chat")
        return True


# --- the card ---------------------------------------------------------------------


def _fmt_time(value: datetime | None, tz: tzinfo) -> str:
    if value is None:
        return "-"
    return value.astimezone(tz).strftime("%d %b %H:%M:%S %Z")


def _fmt_number(value: float | None) -> str:
    if value is None:
        return "not enough data"
    if float(value).is_integer():
        return f"{int(value):,}"
    return f"{value:,.3g}" if abs(value) < 1 else f"{value:,.2f}"


def build_alert_card(notification: AlertNotification, tz: tzinfo) -> dict[str, Any]:
    alert = notification.alert
    firing = notification.kind == "firing"
    title = (
        f"Alert firing: {alert.rule_name}" if firing else f"Resolved: {alert.rule_name}"
    )
    facts = [
        ("Severity", alert.severity),
        ("Instance", alert.instance_id),
        ("Agent", alert.agent_id),
        ("Condition", alert.matched_condition),
        ("Observed", _fmt_number(alert.observed_value)),
        ("Threshold", _fmt_number(alert.threshold)),
        ("First seen", _fmt_time(alert.first_observed_utc, tz)),
    ]
    if not firing:
        facts.append(("Resolved at", _fmt_time(alert.resolved_at_utc, tz)))
    facts.append(("Alert ID", alert.alert_id))
    body: list[dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": escape_card_text(title),
            "weight": "Bolder",
            "size": "Medium",
            "wrap": True,
            "color": (
                ("Attention" if alert.severity == "critical" else "Warning")
                if firing
                else "Good"
            ),
        },
        {
            "type": "FactSet",
            "facts": [
                {"title": escape_card_text(name), "value": escape_card_text(value)}
                for name, value in facts
            ],
        },
        {
            "type": "TextBlock",
            "text": escape_card_text(
                'Ask me "Any alerts open for Magic?" for the current list.'
            ),
            "isSubtle": True,
            "wrap": True,
            "size": "Small",
        },
    ]
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": SCHEMA_VERSION,
        "body": body,
    }


# --- the route --------------------------------------------------------------------


class NotifyHandler:
    """`POST /api/notify`: backend -> group chat."""

    def __init__(
        self,
        *,
        adapter: Any,
        app_id: str,
        store: ConversationStore,
        config: NotifyConfig,
        anonymous: bool = False,
    ) -> None:
        self._adapter = adapter
        self._app_id = app_id
        self._anonymous = anonymous
        self._store = store
        self._config = config
        try:
            self._tz: tzinfo = ZoneInfo(config.timezone)
        except Exception:
            self._tz = ZoneInfo("Asia/Singapore")
        self._sent: OrderedDict[str, None] = OrderedDict()

    def _authorised(self, request: web.Request) -> bool:
        expected = self._config.token
        if not expected:
            return False  # no token configured: the route is closed
        header = request.headers.get("Authorization", "")
        scheme, _, presented = header.partition(" ")
        return scheme.lower() == "bearer" and hmac.compare_digest(
            presented.encode(), expected.encode()
        )

    async def handle(self, request: web.Request) -> web.Response:
        if not self._authorised(request):
            return web.json_response({"code": "unauthorized"}, status=401)
        if (request.content_length or 0) > _MAX_BODY_BYTES:
            return web.json_response({"code": "body_too_large"}, status=413)
        try:
            notification = AlertNotification.model_validate_json(await request.read())
        except ValidationError:
            return web.json_response({"code": "invalid_payload"}, status=400)
        key = notification.dedupe_key
        if key in self._sent:
            return web.json_response({"status": "duplicate"}, status=200)
        reference = self._store.get()
        if reference is None:
            return web.json_response({"code": "no_conversation"}, status=409)

        card = build_alert_card(notification, self._tz)

        async def send(context: TurnContext) -> None:
            await context.send_activity(
                MessageFactory.attachment(CardFactory.adaptive_card(card))
            )

        continuation = reference.get_continuation_activity()
        try:
            if self._anonymous:
                await self._adapter.continue_conversation_with_claims(
                    ClaimsIdentity(),
                    continuation,
                    send,
                    audience=AuthenticationConstants.AGENTS_SDK_SCOPE,
                )
            else:
                await self._adapter.continue_conversation(
                    self._app_id, continuation, send
                )
        except Exception as exc:
            logger.error("posting alert card failed: %s", type(exc).__name__)
            return web.json_response({"code": "teams_error"}, status=502)
        self._sent[key] = None
        while len(self._sent) > _DEDUPE_CAPACITY:
            self._sent.popitem(last=False)
        return web.json_response({"status": "sent"}, status=202)
