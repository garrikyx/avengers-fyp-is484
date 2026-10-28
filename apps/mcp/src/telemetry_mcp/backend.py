"""Thin read-only calls to the backend HTTP APIs (FR-NLQ-026).

No store, Redis or log access: every tool is one backend request. Backend failures
become a short `error` result rather than an exception, so Copilot can tell the user
what happened instead of retrying blindly.
"""

from __future__ import annotations

import logging
from typing import Any, Literal
from urllib.parse import quote

import httpx
from telemetry_shared.models.nl_query import (
    Audience,
    NlClarificationResponse,
    NlQueryContext,
    NlQueryRequest,
    NlQueryResponse,
)

logger = logging.getLogger(__name__)

ErrorKind = Literal["disabled", "bad_request", "not_found", "timeout", "unavailable"]
ToolResult = dict[str, Any]

_ERROR_MESSAGES: dict[ErrorKind, str] = {
    "disabled": "Natural-language queries are disabled on the telemetry backend.",
    "bad_request": "The telemetry backend rejected the request parameters.",
    "not_found": "No such item exists in the telemetry backend.",
    "timeout": "The telemetry backend took too long to answer. Try again.",
    "unavailable": "The telemetry backend could not be reached. Try again shortly.",
}


def error_result(kind: ErrorKind) -> ToolResult:
    return {"error": kind, "message": _ERROR_MESSAGES[kind]}


class TelemetryBackend:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        default_application: str = "Magic",
        default_timezone: str = "Asia/Singapore",
    ) -> None:
        self._client = client
        self._default_application = default_application
        self._default_timezone = default_timezone

    async def nl_query(
        self,
        question: str,
        *,
        timezone: str | None = None,
        audience: Audience = "technical",
    ) -> ToolResult:
        payload = NlQueryRequest(
            question=question,
            context=NlQueryContext(
                default_application=self._default_application,
                user_timezone=timezone or self._default_timezone,
                audience=audience,
            ),
        )
        body = await self._request(
            "POST",
            "/telemetry/nl/query",
            json=payload.model_dump(mode="json", by_alias=True),
        )
        if "error" in body:
            return body
        try:
            if body.get("kind") == "clarification":
                return _clarification_result(
                    NlClarificationResponse.model_validate(body)
                )
            return _answer_result(NlQueryResponse.model_validate(body))
        except ValueError:
            logger.warning("nl query returned an unrecognised body")
            return error_result("unavailable")

    async def query_metrics(self, request: dict[str, Any]) -> ToolResult:
        return await self._request("POST", "/telemetry/query/metrics", json=request)

    async def list_alerts(self, params: dict[str, str | int]) -> ToolResult:
        return await self._request("GET", "/telemetry/alerts", params=params)

    async def get_alert(self, alert_id: str) -> ToolResult:
        return await self._request("GET", f"/telemetry/alerts/{_path(alert_id)}")

    async def list_agent_health(self) -> ToolResult:
        return await self._request("GET", "/telemetry/health/agents")

    async def list_events(self, params: dict[str, str | int]) -> ToolResult:
        return await self._request("GET", "/telemetry/events", params=params)

    async def _request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str | int] | None = None,
    ) -> ToolResult:
        try:
            response = await self._client.request(
                method, path, json=json, params=params
            )
        except httpx.TimeoutException:
            logger.warning("backend %s timed out", path)
            return error_result("timeout")
        except httpx.HTTPError as exc:
            logger.warning("backend %s failed: %s", path, type(exc).__name__)
            return error_result("unavailable")
        kind = _error_kind(response.status_code)
        if kind is not None:
            return error_result(kind)
        try:
            body = response.json()
        except ValueError:
            return error_result("unavailable")
        if not isinstance(body, dict):
            return error_result("unavailable")
        return body


def _error_kind(status_code: int) -> ErrorKind | None:
    if status_code == httpx.codes.OK:
        return None
    if status_code == httpx.codes.SERVICE_UNAVAILABLE:
        return "disabled"
    if status_code in (httpx.codes.BAD_REQUEST, httpx.codes.UNPROCESSABLE_ENTITY):
        return "bad_request"
    if status_code == httpx.codes.NOT_FOUND:
        return "not_found"
    if status_code == httpx.codes.GATEWAY_TIMEOUT:
        return "timeout"
    logger.warning("backend returned HTTP %s", status_code)
    return "unavailable"


def _path(segment: str) -> str:
    # A path segment, never a path: `../` or `?` in an ID must not reach another route.
    return quote(segment, safe="")


def _answer_result(response: NlQueryResponse) -> ToolResult:
    """The templated answer plus what makes it checkable (FR-NLQ-017), without the
    full group breakdown that would invite Copilot to recompute numbers."""
    data = response.data
    return {
        "kind": "answer",
        "answer": response.answer,
        "intent": response.intent,
        "source": response.source,
        "caveats": response.caveats,
        "interpretedQuery": response.interpreted_query.model_dump(
            mode="json", by_alias=True
        ),
        "effectiveTimeRange": data.effective_time_range.model_dump(
            mode="json", by_alias=True
        ),
        "dataCompleteness": data.data_completeness.model_dump(
            mode="json", by_alias=True
        ),
        "chartRows": [
            row.model_dump(mode="json", by_alias=True) for row in response.chart_rows
        ],
        "alertSummaries": [
            alert.model_dump(mode="json", by_alias=True)
            for alert in response.alert_summaries
        ],
        "citations": [
            citation.model_dump(mode="json", by_alias=True, exclude_none=True)
            for citation in response.citations
        ],
    }


def _clarification_result(response: NlClarificationResponse) -> ToolResult:
    result: ToolResult = {
        "kind": "reply",
        "reason": response.reason,
        "message": response.message,
        "suggestedQuestions": response.suggested_questions,
    }
    if response.details:
        result["details"] = response.details
    if response.reason == "clarify":
        result["supportedIntents"] = response.supported_intents
    return result
