"""Ollama native `/api/chat` slot filler (FR-NLQ-007, FR-NLQ-021)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import pytest
from telemetry_backend.config import LlmConfig
from telemetry_backend.nl.llm.ollama_native import OllamaSlotFiller, native_base_url
from telemetry_backend.nl.llm.protocol import (
    NO_INTENT,
    LlmSlotFillError,
    LlmUnavailableError,
)

CONFIG = LlmConfig(
    provider="ollama", base_url="http://127.0.0.1:11434/v1", model="llama3.2"
)


def _chat(content: dict[str, Any]) -> dict[str, Any]:
    return {"message": {"role": "assistant", "content": json.dumps(content)}}


def _run(handler: Any, question: str = "q") -> tuple[Any, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)  # type: ignore[no-any-return]

    async def go() -> Any:
        client = httpx.AsyncClient(transport=httpx.MockTransport(record))
        filler = OllamaSlotFiller(CONFIG, client=client)
        try:
            return await filler.fill_slots(
                question, catalogue_summary="c", schema_json="{}"
            )
        finally:
            await filler.aclose()

    return asyncio.run(go()), seen


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        ("http://h:11434/v1", "http://h:11434"),
        ("http://h:11434/v1/", "http://h:11434"),
        ("http://h:11434", "http://h:11434"),
        (None, "http://127.0.0.1:11434"),
    ],
)
def test_native_base_url_strips_openai_suffix(base: str | None, expected: str) -> None:
    assert native_base_url(base) == expected


def test_FR_NLQ_007_payload_uses_schema_keep_alive_and_token_cap() -> None:
    result, seen = _run(
        lambda request: httpx.Response(
            200,
            json=_chat({"intent": "latency_summary", "timeRange": {"last": "15m"}}),
            request=request,
        )
    )
    assert result.intent == "latency_summary"
    request = seen[0]
    assert request.url.path == "/api/chat"
    body = json.loads(request.content)
    assert body["stream"] is False
    assert body["keep_alive"] == "30m"
    assert body["options"]["num_predict"] == 256
    assert NO_INTENT in body["format"]["properties"]["intent"]["enum"]


def test_FR_NLQ_030_none_intent_carries_reply() -> None:
    result, _ = _run(
        lambda request: httpx.Response(
            200, json=_chat({"intent": "none", "reply": "Hello!"}), request=request
        )
    )
    assert result.intent == NO_INTENT
    assert result.reply == "Hello!"


def test_FR_NLQ_021_connection_error_is_unavailable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(LlmUnavailableError):
        _run(refuse)


def test_unparseable_content_is_slot_fill_error() -> None:
    with pytest.raises(LlmSlotFillError) as info:
        _run(
            lambda request: httpx.Response(
                200, json={"message": {"content": "not json"}}, request=request
            )
        )
    assert not isinstance(info.value, LlmUnavailableError)


def test_warm_up_loads_model_and_swallows_errors() -> None:
    seen: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(500, request=request)

    async def go() -> None:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        filler = OllamaSlotFiller(CONFIG, client=client)
        await filler.warm_up()
        await filler.aclose()

    asyncio.run(go())
    assert seen == [{"model": "llama3.2", "messages": [], "keep_alive": "30m"}]
