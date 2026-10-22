"""UBS-100: the Teams bot against the real backend app (mock LLM), in-process.

Catches response-shape drift between the bot's parsing and the backend's NL API.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi import FastAPI
from microsoft_agents.activity import Activity, ChannelAccount
from teams_agent.backend_client import NlBackendClient
from teams_agent.bot import build_reply
from teams_agent.config import TeamsBotConfig
from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app
from telemetry_backend.nl.factory import build_nl_service
from telemetry_backend.services.ingestion import IngestionService
from telemetry_backend.services.stream_processor import StreamProcessor

from tests.unit.backend.services.alert_fixtures import make_alert_event
from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot
from tests.unit.teams.fixtures import texts


def _backend(*, nl_enabled: bool = True, with_alert: bool = False) -> FastAPI:
    processor = StreamProcessor(StreamProcessorConfig())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 100, "orders_rejected": 10}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    ingestion = IngestionService(stream_processor=processor)
    nl_config = NlConfig(enabled=nl_enabled, llm=LlmConfig(provider="mock"))
    deps = AppDeps(nl_config=nl_config, clock=lambda: NOW)
    if with_alert:
        deps.alert_store.merge(make_alert_event(alert_id="alert-9"))
    app: FastAPI = create_app(service=ingestion, deps=deps)
    if nl_enabled:
        prebuilt = build_nl_service(
            nl_config,
            query_engine=app.state.query_engine,
            alert_store=deps.alert_store,
            stream_config=processor._config,
        )
        deps = AppDeps(
            nl_config=nl_config,
            nl_service=prebuilt,
            alert_store=deps.alert_store,
            clock=lambda: NOW,
        )
        app = create_app(service=ingestion, deps=deps)
    return app


def _ask(app: FastAPI, text: str) -> Activity | None:
    async def run() -> Activity | None:
        async with httpx.AsyncClient(
            base_url="http://backend", transport=httpx.ASGITransport(app=app)
        ) as http:
            activity = Activity(
                type="message",
                text=text,
                recipient=ChannelAccount(id="bot", name="Telemetry"),
            )
            return await build_reply(activity, NlBackendClient(http), TeamsBotConfig())

    return asyncio.run(run())


def _card(reply: Activity | None) -> dict[str, Any]:
    assert reply is not None and reply.attachments
    content = reply.attachments[0].content
    assert isinstance(content, dict)
    return content


def test_rejection_question_renders_a_real_answer_card() -> None:
    card = _card(_ask(_backend(), "Why are orders rejecting in the last 30 minutes?"))

    body_text = " ".join(texts(card))
    assert "rejected orders" in body_text
    assert card["actions"][0]["title"] == "Show query"
    assert not [c for c in card["body"] if c.get("style") == "attention"]


def test_alert_question_shows_the_alert_badge_from_real_citations() -> None:
    card = _card(_ask(_backend(with_alert=True), "Any alerts open for Magic?"))

    badges = [c for c in card["body"] if c.get("style") == "attention"]
    assert len(badges) == 1
    assert "1 active alert" in texts(badges[0])[0]


def test_disabled_backend_renders_the_disabled_card() -> None:
    card = _card(_ask(_backend(nl_enabled=False), "Why are orders rejecting?"))
    assert "currently disabled" in " ".join(texts(card))
