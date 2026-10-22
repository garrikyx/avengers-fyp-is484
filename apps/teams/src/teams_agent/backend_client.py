"""Async client for the backend's natural-language query API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from pydantic import ValidationError
from telemetry_shared.models.nl_query import (
    NlClarificationResponse,
    NlQueryContext,
    NlQueryRequest,
    NlQueryResponse,
)

logger = logging.getLogger(__name__)

ErrorKind = Literal["disabled", "bad_request", "timeout", "unavailable"]


@dataclass(frozen=True, slots=True)
class BackendError:
    kind: ErrorKind


NlOutcome = NlQueryResponse | NlClarificationResponse | BackendError


class NlBackendClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def ask(self, question: str, context: NlQueryContext) -> NlOutcome:
        payload = NlQueryRequest(question=question, context=context)
        try:
            response = await self._client.post(
                "/telemetry/nl/query",
                json=payload.model_dump(mode="json", by_alias=True),
            )
        except httpx.TimeoutException:
            logger.warning("nl query timed out")
            return BackendError("timeout")
        except httpx.HTTPError as exc:
            logger.warning("nl query failed: %s", type(exc).__name__)
            return BackendError("unavailable")
        return _parse(response)


def _parse(response: httpx.Response) -> NlOutcome:
    if response.status_code == httpx.codes.SERVICE_UNAVAILABLE:
        return BackendError("disabled")
    if response.status_code in (
        httpx.codes.BAD_REQUEST,
        httpx.codes.UNPROCESSABLE_ENTITY,
    ):
        return BackendError("bad_request")
    if response.status_code == httpx.codes.GATEWAY_TIMEOUT:
        return BackendError("timeout")
    if response.status_code != httpx.codes.OK:
        logger.warning("nl query returned HTTP %s", response.status_code)
        return BackendError("unavailable")
    try:
        body: Any = response.json()
        if isinstance(body, dict) and body.get("kind") == "clarification":
            return NlClarificationResponse.model_validate(body)
        return NlQueryResponse.model_validate(body)
    except ValueError, ValidationError:
        logger.warning("nl query returned an unrecognised body")
        return BackendError("unavailable")
