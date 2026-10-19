"""OpenAI-compatible LLM slot filler (Ollama / vLLM)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

import httpx
import pytest
from telemetry_backend.config import LlmConfig
from telemetry_backend.nl.llm.openai_compatible import OpenAiCompatibleSlotFiller
from telemetry_backend.nl.llm.protocol import LlmSlotFillError

SAMPLE_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": json.dumps(
                    {
                        "intent": "latency_summary",
                        "timeRange": {"last": "15m"},
                        "filters": {"application": "Magic"},
                    }
                )
            }
        }
    ]
}


def test_fill_slots_parses_json_without_auth_header() -> None:
    config = LlmConfig(
        provider="ollama",
        base_url="http://127.0.0.1:11434/v1",
        model="llama3.2",
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json=SAMPLE_RESPONSE,
            request=request,
        )
    )

    async def run() -> None:
        client = httpx.AsyncClient(transport=transport)
        filler = OpenAiCompatibleSlotFiller(config, client=client)
        with patch.dict("os.environ", {}, clear=True):
            result = await filler.fill_slots(
                "is magic slow",
                catalogue_summary="cat",
                schema_json="{}",
            )
        assert result.intent == "latency_summary"
        await client.aclose()

    asyncio.run(run())


def test_fill_slots_sends_bearer_when_api_key_set() -> None:
    config = LlmConfig(
        provider="vllm",
        base_url="http://127.0.0.1:8000/v1",
        model="mistral",
    )
    seen_auth: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_auth.append(request.headers.get("Authorization"))
        return httpx.Response(200, json=SAMPLE_RESPONSE, request=request)

    async def run() -> None:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        filler = OpenAiCompatibleSlotFiller(config, client=client)
        with patch.dict("os.environ", {"MAGIC_TELEMETRY_LLM_API_KEY": "secret-token"}):
            await filler.fill_slots("q", catalogue_summary="c", schema_json="{}")
        await client.aclose()

    asyncio.run(run())
    assert seen_auth == ["Bearer secret-token"]


def test_json_mode_rejected_retries_without_response_format() -> None:
    config = LlmConfig(
        provider="ollama",
        base_url="http://127.0.0.1:11434/v1",
        model="llama3.2",
        structured_output=True,
    )
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content.decode())
        if calls == 1:
            assert body.get("response_format") == {"type": "json_object"}
            return httpx.Response(400, json={"error": "unsupported"}, request=request)
        assert "response_format" not in body
        return httpx.Response(200, json=SAMPLE_RESPONSE, request=request)

    async def run() -> None:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        filler = OpenAiCompatibleSlotFiller(config, client=client)
        result = await filler.fill_slots("q", catalogue_summary="c", schema_json="{}")
        assert result.intent == "latency_summary"
        await client.aclose()

    asyncio.run(run())
    assert calls == 2


def test_require_api_key_without_env_raises() -> None:
    config = LlmConfig(
        provider="openai-compatible",
        base_url="http://127.0.0.1:8000/v1",
        model="m",
        require_api_key=True,
    )
    filler = OpenAiCompatibleSlotFiller(config)

    async def run() -> None:
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LlmSlotFillError, match="API key"):
                await filler.fill_slots("q", catalogue_summary="c", schema_json="{}")

    asyncio.run(run())
