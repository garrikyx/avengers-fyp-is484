"""Helpers for driving the Teams bot through its message boundary."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
from microsoft_agents.activity import Activity, ChannelAccount, Entity
from teams_agent.backend_client import NlBackendClient
from teams_agent.bot import build_reply
from teams_agent.config import TeamsBotConfig
from telemetry_shared.models.metrics_query import (
    DataCompleteness,
    EffectiveTimeRange,
    MetricsQueryResponse,
    QueryGroup,
    QueryInterpretation,
    QueryTimeRange,
)
from telemetry_shared.models.nl_query import (
    InterpretedQuery,
    NlCitation,
    NlClarificationResponse,
    NlQueryResponse,
)

CONFIG = TeamsBotConfig()
BOT_ID = "bot-1"


def message(
    text: str,
    *,
    mention: bool = False,
    local_timezone: str | None = None,
    client_info_timezone: str | None = None,
) -> Activity:
    entities: list[Entity] = []
    if mention:
        text = f"<at>Telemetry</at> {text}"
        entities.append(
            Entity.model_validate(
                {
                    "type": "mention",
                    "mentioned": {"id": BOT_ID, "name": "Telemetry"},
                    "text": "<at>Telemetry</at>",
                }
            )
        )
    if client_info_timezone:
        entities.append(
            Entity.model_validate(
                {"type": "clientInfo", "timezone": client_info_timezone}
            )
        )
    kwargs: dict[str, Any] = {}
    if local_timezone:
        kwargs["local_timezone"] = local_timezone
    return Activity(
        type="message",
        text=text,
        recipient=ChannelAccount(id=BOT_ID, name="Telemetry"),
        entities=entities,
        **kwargs,
    )


def answer(
    *,
    text: str = "Magic recorded 62 rejected orders out of 1,250 submitted.",
    groups: list[QueryGroup] | None = None,
    totals: dict[str, int | float | None] | None = None,
    citations: list[NlCitation] | None = None,
    caveats: list[str] | None = None,
    completeness: DataCompleteness | None = None,
    truncated: bool = False,
    filters: dict[str, str | list[str]] | None = None,
) -> NlQueryResponse:
    interpreted = InterpretedQuery(
        intent="rejection_summary",
        time_range=QueryTimeRange(last="30m"),
        filters=filters or {"application": "Magic"},
        group_by=["rejectReason"],
        metrics=["orders_rejected"],
    )
    window = EffectiveTimeRange(
        from_utc=datetime(2026, 10, 21, 14, 0, tzinfo=UTC),
        to_utc=datetime(2026, 10, 21, 14, 30, tzinfo=UTC),
    )
    data = MetricsQueryResponse(
        query_id="q-1",
        evaluated_at_utc=window.to_utc,
        effective_time_range=window,
        interpretation=QueryInterpretation(
            metrics=["orders_rejected"], group_by=[], filters={}
        ),
        totals=totals or {},
        groups=groups or [],
        truncated=truncated,
        data_completeness=completeness or DataCompleteness(),
    )
    return NlQueryResponse(
        answer=text,
        intent="rejection_summary",
        confidence=0.9,
        source="rule",
        interpreted_query=interpreted,
        data=data,
        citations=citations or [NlCitation(type="metrics_query", query_id="q-1")],
        caveats=caveats or [],
    )


def clarification() -> NlClarificationResponse:
    return NlClarificationResponse(
        message="I could not interpret that question.",
        supported_intents=["rejection_summary", "alert_status"],
        details=["timeRange: unsupported"],
    )


def group(label: str, **counters: int | float) -> QueryGroup:
    return QueryGroup(dimensions={"rejectReason": label}, counters=counters)


Handler = Callable[[httpx.Request], httpx.Response]


def json_ok(model: NlQueryResponse | NlClarificationResponse) -> Handler:
    body = model.model_dump(mode="json", by_alias=True)
    return lambda _request: httpx.Response(200, json=body)


class Exchange:
    """What the bot sent to the backend, and the reply it produced."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.reply: Activity | None = None

    @property
    def card(self) -> dict[str, Any]:
        assert self.reply is not None and self.reply.attachments
        content = self.reply.attachments[0].content
        assert isinstance(content, dict)
        return content


def converse(activity: Activity, handler: Handler) -> Exchange:
    exchange = Exchange()

    def recording(request: httpx.Request) -> httpx.Response:
        exchange.requests.append(json.loads(request.content))
        return handler(request)

    async def run() -> Activity | None:
        async with httpx.AsyncClient(
            base_url="http://backend", transport=httpx.MockTransport(recording)
        ) as http:
            return await build_reply(activity, NlBackendClient(http), CONFIG)

    exchange.reply = asyncio.run(run())
    return exchange


def text_blocks(node: Any) -> list[dict[str, Any]]:
    """Every TextBlock in a card, depth first."""
    found: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if node.get("type") == "TextBlock":
            found.append(node)
        for value in node.values():
            found.extend(text_blocks(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(text_blocks(item))
    return found


def texts(card: dict[str, Any]) -> list[str]:
    return [block["text"] for block in text_blocks(card)]
