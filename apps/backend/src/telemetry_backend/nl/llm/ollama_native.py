"""Ollama native chat API slot filling (FR-NLQ-007).

Uses `/api/chat` rather than the OpenAI-compatible `/v1` route because only the
native API supports `keep_alive` (no cold model reloads between questions) and a
JSON Schema `format` (constrained decoding, so no second request without JSON mode).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from telemetry_backend.config import DEFAULT_OLLAMA_BASE_URL, LlmConfig
from telemetry_backend.nl.llm.parse_slots import (
    SLOT_FILL_SYSTEM_PROMPT,
    parse_llm_slot_payload,
    slot_json_schema,
)
from telemetry_backend.nl.llm.protocol import (
    LlmSlotFillError,
    LlmSlotResult,
    LlmUnavailableError,
    ManagedLlmSlotFiller,
)

logger = logging.getLogger(__name__)

# A model that is down or not pulled should fail fast, not eat the whole budget.
_CONNECT_TIMEOUT_SECONDS = 2.0
# Loading a model from disk can take far longer than a question's budget; the
# warm-up runs in the background so it never delays a reply.
_WARM_UP_TIMEOUT_SECONDS = 120.0
_NUM_CTX = 2048


def native_base_url(base_url: str | None) -> str:
    """`http://host:11434/v1` -> `http://host:11434` (the `/v1` route is OpenAI's)."""
    url = (base_url or DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    if url.endswith("/v1"):
        url = url[: -len("/v1")]
    return url


class OllamaSlotFiller(ManagedLlmSlotFiller):
    def __init__(
        self, config: LlmConfig, *, client: httpx.AsyncClient | None = None
    ) -> None:
        self._config = config
        self._url = f"{native_base_url(config.base_url)}/api/chat"
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(
                config.timeout_seconds, connect=_CONNECT_TIMEOUT_SECONDS
            )
        )

    async def fill_slots(
        self,
        question: str,
        *,
        catalogue_summary: str,
        schema_json: str,
    ) -> LlmSlotResult:
        # The schema is enforced through `format`; repeating it in the prompt only
        # slows a small model down.
        del schema_json
        if not self._config.model:
            raise LlmSlotFillError("nl.llm.model is required for ollama")
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": SLOT_FILL_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Catalogue:\n{catalogue_summary}\n\nQuestion:\n{question}"
                    ),
                },
            ],
            "stream": False,
            "format": slot_json_schema() if self._config.structured_output else "json",
            "keep_alive": self._config.keep_alive,
            "options": {
                "temperature": 0,
                "num_predict": self._config.num_predict,
                "num_ctx": _NUM_CTX,
            },
        }
        try:
            response = await self._client.post(self._url, json=payload)
            response.raise_for_status()
            content = response.json()["message"]["content"]
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise LlmSlotFillError("LLM response is not a JSON object")
            return parse_llm_slot_payload(parsed)
        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            json.JSONDecodeError,
            LlmSlotFillError,
        ) as exc:
            if isinstance(exc, httpx.HTTPError):
                logger.warning("ollama is unavailable: %s", type(exc).__name__)
                raise LlmUnavailableError("LLM is unavailable") from exc
            logger.warning("ollama slot fill failed: %s", type(exc).__name__)
            raise LlmSlotFillError("LLM slot fill failed") from exc

    async def warm_up(self) -> None:
        """Load the model into memory. An empty `messages` list only loads it."""
        try:
            response = await self._client.post(
                self._url,
                json={
                    "model": self._config.model,
                    "messages": [],
                    "keep_alive": self._config.keep_alive,
                },
                timeout=_WARM_UP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            logger.info("ollama model %s is loaded", self._config.model)
        except httpx.HTTPError as exc:
            logger.warning(
                "ollama warm-up failed (%s); is `ollama serve` running and "
                "`%s` pulled?",
                type(exc).__name__,
                self._config.model,
            )

    async def aclose(self) -> None:
        await self._client.aclose()
