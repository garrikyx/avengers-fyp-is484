"""UBS-120: the Teams app posts backend alert notifications into the group chat."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from microsoft_agents.activity import (
    Activity,
    ChannelAccount,
    ConversationAccount,
)
from teams_agent.main import _authorize
from teams_agent.notify import (
    NOTIFY_PATH,
    TOKEN_ENV,
    ConversationStore,
    NotifyConfig,
    NotifyHandler,
    build_alert_card,
    register_conversation_capture,
)
from telemetry_shared.models.alerts_query import AlertDelivery, AlertRecord
from telemetry_shared.models.notifications import AlertNotification

TOKEN = "notify-secret"
SGT = ZoneInfo("Asia/Singapore")


def group_chat_activity(conversation_id: str = "19:chat-a@thread.v2") -> Activity:
    return Activity(
        type="message",
        text="how is magic doing",
        channel_id="msteams",
        service_url="https://smba.trafficmanager.net/apac/",
        from_property=ChannelAccount(id="user-1", name="Jasdev"),
        recipient=ChannelAccount(id="bot-1", name="Magic Telemetry"),
        conversation=ConversationAccount(
            id=conversation_id, conversation_type="groupChat", is_group=True
        ),
    )


def personal_activity() -> Activity:
    activity = group_chat_activity("a:personal-chat")
    return activity.model_copy(
        update={
            "conversation": ConversationAccount(
                id="a:personal-chat", conversation_type="personal"
            )
        }
    )


def alert(**overrides: Any) -> AlertRecord:
    values: dict[str, Any] = {
        "alert_id": "alert-1024",
        "source": "agent",
        "agent_id": "magic-agent-sg-01",
        "application": "Magic",
        "instance_id": "magic-prod-01",
        "rule_name": "HighRejectRate",
        "severity": "critical",
        "status": "firing",
        "matched_condition": "rejectRate > 0.05 for 5 minutes",
        "observed_value": 0.064,
        "threshold": 0.05,
        "first_observed_utc": datetime(2026, 11, 3, 4, 0, tzinfo=UTC),
        "last_observed_utc": datetime(2026, 11, 3, 4, 0, tzinfo=UTC),
        "notification_count": 1,
        "delivery": AlertDelivery(status="delivered", attempts=1),
    }
    values.update(overrides)
    return AlertRecord(**values)


def notification(kind: str = "firing", **overrides: Any) -> dict[str, Any]:
    return AlertNotification(kind=kind, alert=alert(**overrides)).model_dump(  # type: ignore[arg-type]
        mode="json", by_alias=True
    )


class FakeAdapter:
    """Stands in for CloudAdapter.continue_conversation."""

    def __init__(self, *, fail: bool = False) -> None:
        self.sent: list[dict[str, Any]] = []
        self.calls: list[tuple[str, Activity]] = []
        self.fail = fail
        self.anonymous_calls = 0

    async def continue_conversation(
        self,
        app_id: str,
        continuation: Activity,
        callback: Callable[[Any], Awaitable[None]],
    ) -> None:
        if self.fail:
            raise RuntimeError("Teams said no")
        self.calls.append((app_id, continuation))

        class Context:
            async def send_activity(_self, activity: Activity) -> None:
                self.sent.append(activity.attachments[0].content)

        await callback(Context())

    async def continue_conversation_with_claims(
        self,
        claims: Any,
        continuation: Activity,
        callback: Callable[[Any], Awaitable[None]],
        audience: str | None = None,
    ) -> None:
        self.anonymous_calls += 1
        await self.continue_conversation("", continuation, callback)


def run(
    tmp_path: Path,
    requests: list[tuple[dict[str, Any] | str, dict[str, str]]],
    *,
    adapter: FakeAdapter | None = None,
    registered: bool = True,
    token: str | None = TOKEN,
    anonymous: bool = False,
) -> tuple[list[tuple[int, dict[str, Any]]], FakeAdapter]:
    adapter = adapter or FakeAdapter()
    store = ConversationStore(tmp_path / "conv.json")
    if registered:
        store.offer(group_chat_activity())
    handler = NotifyHandler(
        adapter=adapter,
        app_id="app-id-1",
        store=store,
        config=NotifyConfig(token=token),
        anonymous=anonymous,
    )
    app = web.Application(middlewares=[_authorize])
    app.router.add_post(NOTIFY_PATH, handler.handle)

    async def scenario() -> list[tuple[int, dict[str, Any]]]:
        results = []
        async with TestClient(TestServer(app)) as client:
            for body, headers in requests:
                data = body if isinstance(body, str) else json.dumps(body)
                response = await client.post(NOTIFY_PATH, data=data, headers=headers)
                results.append((response.status, await response.json()))
        return results

    return asyncio.run(scenario()), adapter


AUTH = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def test_a_notification_is_posted_into_the_registered_group_chat(
    tmp_path: Path,
) -> None:
    results, adapter = run(tmp_path, [(notification(), AUTH)])
    assert results == [(202, {"status": "sent"})]
    app_id, continuation = adapter.calls[0]
    assert app_id == "app-id-1"
    assert continuation.conversation.id == "19:chat-a@thread.v2"
    assert continuation.service_url == "https://smba.trafficmanager.net/apac/"
    card = adapter.sent[0]
    assert card["type"] == "AdaptiveCard"
    assert "HighRejectRate" in card["body"][0]["text"]


def test_anonymous_dev_mode_sends_without_an_entra_token(tmp_path: Path) -> None:
    results, adapter = run(tmp_path, [(notification(), AUTH)], anonymous=True)
    assert results == [(202, {"status": "sent"})]
    assert adapter.anonymous_calls == 1
    assert len(adapter.sent) == 1


def test_the_same_transition_twice_posts_one_card(tmp_path: Path) -> None:
    results, adapter = run(tmp_path, [(notification(), AUTH), (notification(), AUTH)])
    assert [status for status, _ in results] == [202, 200]
    assert results[1][1] == {"status": "duplicate"}
    assert len(adapter.sent) == 1


def test_firing_then_resolved_posts_two_cards(tmp_path: Path) -> None:
    resolved = notification(
        "resolved",
        status="resolved",
        resolved_at_utc=datetime(2026, 11, 3, 4, 5, tzinfo=UTC),
    )
    _, adapter = run(tmp_path, [(notification(), AUTH), (resolved, AUTH)])
    titles = [card["body"][0]["text"] for card in adapter.sent]
    assert titles == ["Alert firing: HighRejectRate", "Resolved: HighRejectRate"]


def test_the_route_needs_the_backend_token_not_a_teams_jwt(tmp_path: Path) -> None:
    results, adapter = run(
        tmp_path,
        [
            (notification(), {"Content-Type": "application/json"}),
            (notification(), {"Authorization": "Bearer wrong"}),
            (notification(), {"Authorization": f"Basic {TOKEN}"}),
        ],
    )
    assert [status for status, _ in results] == [401, 401, 401]
    assert adapter.sent == []


def test_the_route_is_closed_when_no_token_is_configured(tmp_path: Path) -> None:
    results, _ = run(tmp_path, [(notification(), AUTH)], token=None)
    assert results[0][0] == 401


def test_no_group_chat_yet_is_a_409_the_backend_can_explain(tmp_path: Path) -> None:
    results, _ = run(tmp_path, [(notification(), AUTH)], registered=False)
    assert results == [(409, {"code": "no_conversation"})]


def test_a_bad_payload_is_a_400(tmp_path: Path) -> None:
    results, _ = run(tmp_path, [("{not json", AUTH), ({"kind": "firing"}, AUTH)])
    assert [status for status, _ in results] == [400, 400]


def test_teams_failing_is_a_502_and_is_not_marked_sent(tmp_path: Path) -> None:
    results, _ = run(
        tmp_path,
        [(notification(), AUTH)],
        adapter=FakeAdapter(fail=True),
    )
    assert results == [(502, {"code": "teams_error"})]


# --- remembering the chat ------------------------------------------------------


def test_only_group_chats_are_remembered_and_the_first_one_wins(
    tmp_path: Path,
) -> None:
    store = ConversationStore(tmp_path / "conv.json")
    assert store.offer(personal_activity()) is False
    assert store.get() is None
    assert store.offer(group_chat_activity("19:chat-a@thread.v2")) is True
    assert store.offer(group_chat_activity("19:chat-b@thread.v2")) is False
    reference = store.get()
    assert reference is not None
    assert reference.conversation.id == "19:chat-a@thread.v2"


def test_a_personal_chat_counts_only_when_allowed_for_local_demos(
    tmp_path: Path,
) -> None:
    store = ConversationStore(tmp_path / "a.json", allow_personal=True)
    assert store.offer(personal_activity()) is True
    reference = store.get()
    assert reference is not None
    assert reference.conversation.id == "a:personal-chat"
    assert NotifyConfig.from_env({"TEAMS_NOTIFY_ALLOW_PERSONAL": "true"}).allow_personal
    assert not NotifyConfig.from_env({}).allow_personal


def test_the_chat_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "state" / "conv.json"
    ConversationStore(path).offer(group_chat_activity())
    reloaded = ConversationStore(path).get()
    assert reloaded is not None
    assert reloaded.conversation.id == "19:chat-a@thread.v2"
    assert reloaded.service_url == "https://smba.trafficmanager.net/apac/"


def test_a_pinned_chat_ignores_others_and_can_replace_a_stored_one(
    tmp_path: Path,
) -> None:
    path = tmp_path / "conv.json"
    ConversationStore(path).offer(group_chat_activity("19:chat-a@thread.v2"))
    pinned = ConversationStore(path, pinned_conversation_id="19:chat-b@thread.v2")
    assert pinned.get() is None  # the stored chat is not the pinned one
    assert pinned.offer(group_chat_activity("19:chat-a@thread.v2")) is False
    assert pinned.offer(group_chat_activity("19:chat-b@thread.v2")) is True


def test_an_unreadable_state_file_is_ignored(tmp_path: Path) -> None:
    path = tmp_path / "conv.json"
    path.write_text("{garbage", encoding="utf-8")
    assert ConversationStore(path).get() is None


def test_capture_runs_before_every_turn_and_never_blocks_it(tmp_path: Path) -> None:
    hooks: list[Callable[..., Awaitable[bool]]] = []

    class FakeApp:
        def before_turn(self, handler: Callable[..., Awaitable[bool]]) -> Any:
            hooks.append(handler)
            return handler

    class Broken(ConversationStore):
        def offer(self, activity: Activity) -> bool:
            raise RuntimeError("disk full")

    class Ctx:
        activity = group_chat_activity()

    store = ConversationStore(tmp_path / "conv.json")
    register_conversation_capture(FakeApp(), store)  # type: ignore[arg-type]
    register_conversation_capture(FakeApp(), Broken(tmp_path / "x.json"))  # type: ignore[arg-type]
    assert asyncio.run(hooks[0](Ctx(), None)) is True
    assert store.get() is not None
    assert asyncio.run(hooks[1](Ctx(), None)) is True  # error swallowed


# --- the card ------------------------------------------------------------------


def test_the_card_escapes_every_dynamic_string() -> None:
    hostile = AlertNotification(
        kind="firing",
        alert=alert(
            rule_name="**Bold**[link](http://x)",
            matched_condition="<script>",
            instance_id="- item",
        ),
    )
    card = build_alert_card(hostile, SGT)
    text = json.dumps(card)
    assert "**Bold**" not in text
    assert "\\\\*\\\\*Bold" in text  # escaped, as JSON shows it
    assert "<script>" not in text


def test_the_firing_card_shows_local_time_and_the_resolved_card_says_when() -> None:
    firing = build_alert_card(AlertNotification(kind="firing", alert=alert()), SGT)
    facts = {f["title"]: f["value"] for f in firing["body"][1]["facts"]}
    assert facts["First seen"] == "03 Nov 12:00:00 +08"
    assert "Resolved at" not in facts
    assert firing["body"][0]["color"] == "Attention"

    resolved = build_alert_card(
        AlertNotification(
            kind="resolved",
            alert=alert(
                status="resolved",
                resolved_at_utc=datetime(2026, 11, 3, 4, 5, tzinfo=UTC),
            ),
        ),
        SGT,
    )
    facts = {f["title"]: f["value"] for f in resolved["body"][1]["facts"]}
    assert facts["Resolved at"] == "03 Nov 12:05:00 +08"
    assert resolved["body"][0]["color"] == "Good"


def test_config_reads_the_environment() -> None:
    config = NotifyConfig.from_env(
        {
            TOKEN_ENV: "t",
            "TEAMS_NOTIFY_STATE_PATH": "/tmp/x.json",
            "TEAMS_NOTIFY_CONVERSATION_ID": "19:chat@thread.v2",
        }
    )
    assert config.token == "t"
    assert config.state_path == Path("/tmp/x.json")
    assert config.conversation_id == "19:chat@thread.v2"
    assert NotifyConfig.from_env({}).token is None
