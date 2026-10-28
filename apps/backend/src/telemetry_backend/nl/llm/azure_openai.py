"""Azure OpenAI structured slot filling (FR-NLQ-007)."""

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
    LlmUnavailableError,
)

logger = logging.getLogger(__name__)


class AzureOpenAiSlotFiller(LlmSlotFiller):
    def __init__(
        self, config: LlmConfig, *, client: httpx.AsyncClient | None = None
    ) -> None:
        self._config = config
        self._client = client
        self._api_key = os.environ.get("MAGIC_TELEMETRY_LLM_API_KEY", "")

    async def fill_slots(
        self,
        question: str,
        *,
        catalogue_summary: str,
        schema_json: str,
    ) -> LlmSlotResult:
        if not self._api_key:
            raise LlmSlotFillError("LLM API key is not configured")
        if not self._config.endpoint:
            raise LlmSlotFillError("nl.llm.endpoint is required for azure-openai")

        url = (
            f"{self._config.endpoint.rstrip('/')}/openai/deployments/"
            f"{self._config.deployment}/chat/completions"
            f"?api-version={self._config.api_version}"
        )
        payload: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": SLOT_FILL_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Catalogue:\n{catalogue_summary}\n\n"
                        f"Schema:\n{schema_json}\n\n"
                        f"Question:\n{question}"
                    ),
                },
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {"api-key": self._api_key, "Content-Type": "application/json"}
        client = self._client or httpx.AsyncClient(timeout=self._config.timeout_seconds)
        owns_client = self._client is None
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return parse_llm_slot_payload(parsed)
        except (
            httpx.HTTPError,
            KeyError,
            json.JSONDecodeError,
            LlmSlotFillError,
        ) as exc:
            if isinstance(exc, httpx.HTTPError):
                logger.warning("azure openai is unavailable: %s", type(exc).__name__)
                raise LlmUnavailableError("LLM is unavailable") from exc
            logger.warning("azure openai slot fill failed: %s", exc)
            raise LlmSlotFillError("LLM slot fill failed") from exc
        finally:
            if owns_client:
                await client.aclose()
