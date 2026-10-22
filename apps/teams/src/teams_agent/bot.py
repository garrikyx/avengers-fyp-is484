"""Message handling: Teams activity in, Adaptive Card reply out."""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import (
    AgentApplication,
    CardFactory,
    MessageFactory,
    TurnContext,
    TurnState,
)
from telemetry_shared.models.nl_query import (
    NlClarificationResponse,
    NlQueryContext,
    NlQueryResponse,
)

from teams_agent.backend_client import BackendError, NlBackendClient
from teams_agent.cards import (
    build_answer_card,
    build_clarification_card,
    build_error_card,
)
from teams_agent.config import TeamsBotConfig

logger = logging.getLogger(__name__)


def resolve_timezone(activity: Activity, default: str) -> str:
    """Teams `localTimezone`, then the `clientInfo` entity, then the default."""
    candidates: list[str | None] = [activity.local_timezone]
    for entity in activity.entities or []:
        if entity.type == "clientInfo":
            extra = entity.model_extra or {}
            candidates.append(extra.get("timezone"))
    for candidate in candidates:
        if not candidate:
            continue
        try:
            ZoneInfo(candidate)
        except ZoneInfoNotFoundError, ValueError:
            continue
        return candidate
    return default


def question_text(activity: Activity) -> str:
    """The user's message with the bot's own @mention removed."""
    return (activity.remove_recipient_mention() or "").strip()


async def build_reply(
    activity: Activity, client: NlBackendClient, config: TeamsBotConfig
) -> Activity | None:
    """One message, one backend call. None when there is nothing to answer."""
    question = question_text(activity)
    if not question:
        return None
    timezone = resolve_timezone(activity, config.default_timezone)
    context = NlQueryContext(
        default_application=config.default_application, user_timezone=timezone
    )
    try:
        outcome = await client.ask(question, context)
        if isinstance(outcome, BackendError):
            card = build_error_card(outcome.kind)
        elif isinstance(outcome, NlClarificationResponse):
            card = build_clarification_card(outcome)
        else:
            assert isinstance(outcome, NlQueryResponse)
            card = build_answer_card(outcome, ZoneInfo(timezone))
    except Exception as exc:
        # Never leave the user with only a typing indicator. Log the type only:
        # validation errors can echo the question.
        logger.error("failed to build a reply: %s", type(exc).__name__)
        card = build_error_card("unavailable")
    reply: Activity = MessageFactory.attachment(CardFactory.adaptive_card(card))
    return reply


def register_handlers(
    app: AgentApplication[TurnState],
    client: NlBackendClient,
    config: TeamsBotConfig,
) -> None:
    @app.activity("message")
    async def on_message(context: TurnContext, _state: TurnState) -> None:
        await context.send_activity(Activity(type="typing"))
        reply = await build_reply(context.activity, client, config)
        if reply is not None:
            await context.send_activity(reply)
