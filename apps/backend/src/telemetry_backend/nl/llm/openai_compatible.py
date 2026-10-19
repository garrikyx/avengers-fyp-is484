"""OpenAI-compatible chat completions (Ollama, vLLM, LiteLLM)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from telemetry_backend.config import LlmConfig
from telemetry_backend.nl.llm.parse_slots import (
    SLOT_FILL_SYSTEM_PROMPT,
    parse_llm_slot_payload,
)
from telemetry_backend.nl.llm.protocol import (
    LlmSlotFiller,
    LlmSlotFillError,
    LlmSlotResult,
)

logger = logging.getLogger(__name__)


class OpenAiCompatibleSlotFiller(LlmSlotFiller):
    def __init__(
        self, config: LlmConfig, *, client: httpx.AsyncClient | None = None
    ) -> None:
        self._config = config
        self._client = client

    async def fill_slots(
        self,
        question: str,
        *,
        catalogue_summary: str,
        schema_json: str,
    ) -> LlmSlotResult:
        if not self._config.base_url:
            raise LlmSlotFillError("nl.llm.baseUrl is required for openai-compatible")
        if not self._config.model:
            raise LlmSlotFillError("nl.llm.model is required for openai-compatible")

        url = f"{self._config.base_url.rstrip('/')}/chat/completions"
        user_content = (
            f"Catalogue:\n{catalogue_summary}\n\n"
            f"Schema:\n{schema_json}\n\n"
            f"Question:\n{question}"
        )
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get("MAGIC_TELEMETRY_LLM_API_KEY", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        elif self._config.require_api_key:
            raise LlmSlotFillError("LLM API key is not configured")

        client = self._client or httpx.AsyncClient(timeout=self._config.timeout_seconds)
        owns_client = self._client is None
        try:
            return await self._post_and_parse(
                client, url, headers, user_content, use_json_mode=True
            )
        except _JsonModeRejected:
            logger.warning(
                "LLM server rejected response_format json_object; retrying without it"
            )
            return await self._post_and_parse(
                client, url, headers, user_content, use_json_mode=False
            )
        except (
            httpx.HTTPError,
            KeyError,
            json.JSONDecodeError,
            LlmSlotFillError,
        ) as exc:
            logger.warning("openai-compatible slot fill failed: %s", exc)
            raise LlmSlotFillError("LLM slot fill failed") from exc
        finally:
            if owns_client:
                await client.aclose()

    async def _post_and_parse(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        user_content: str,
        *,
        use_json_mode: bool,
    ) -> LlmSlotResult:
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": SLOT_FILL_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0,
        }
        if use_json_mode and self._config.structured_output:
            payload["response_format"] = {"type": "json_object"}

        response = await client.post(url, headers=headers, json=payload)
        if (
            use_json_mode
            and self._config.structured_output
            and response.status_code in {400, 422}
        ):
            raise _JsonModeRejected()
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return parse_llm_slot_payload(parsed)


class _JsonModeRejected(Exception):
    """Server does not support response_format json_object."""
