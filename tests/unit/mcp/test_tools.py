"""Read-only MCP server for Copilot (ADR 0007, FR-NLQ-026)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import pytest
from mcp import Client
from telemetry_mcp.config import McpServerConfig
from telemetry_mcp.server import build_server

ANSWER_BODY: dict[str, Any] = {
    "kind": "answer",
    "answer": "Magic p95 latency was 12 ms over the last 15 minutes.",
    "intent": "latency_summary",
    "confidence": 0.9,
    "source": "rule",
    "interpretedQuery": {
        "intent": "latency_summary",
        "timeRange": {"last": "15m"},
        "metrics": ["latency_ms"],
    },
    "data": {
        "queryId": "q-1",
        "evaluatedAtUtc": "2026-06-12T04:00:00Z",
        "effectiveTimeRange": {
            "fromUtc": "2026-06-12T03:45:00Z",
            "toUtc": "2026-06-12T04:00:00Z",
        },
        "interpretation": {"metrics": ["latency_ms"], "groupBy": [], "filters": {}},
        "dataCompleteness": {},
    },
    "citations": [{"type": "metrics_query", "queryId": "q-1"}],
}

REPLY_BODY: dict[str, Any] = {
    "kind": "clarification",
    "message": "Hi! Ask me about Magic.",
    "supportedIntents": ["latency_summary"],
    "reason": "greeting",
    "suggestedQuestions": ["Is Magic slow?"],
}


def _run(
    handler: Any, tool: str, arguments: dict[str, Any] | None = None
) -> dict[str, Any]:
    async def go() -> dict[str, Any]:
        http = httpx.AsyncClient(
            base_url="http://backend", transport=httpx.MockTransport(handler)
        )
        server = build_server(McpServerConfig(), client=http)
        async with Client(server) as client:
            result = await client.call_tool(tool, arguments or {})
        await http.aclose()
        content = result.structured_content
        assert isinstance(content, dict)
        return content

    return asyncio.run(go())


def _ok(body: dict[str, Any], seen: list[httpx.Request]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=body)

    return handler


def test_FR_NLQ_026_only_read_only_tools_are_exposed() -> None:
    server = build_server(McpServerConfig())
    tools = asyncio.run(server.list_tools())
    assert {tool.name for tool in tools} == {
        "nl_query",
        "query_metrics",
        "list_alerts",
        "get_alert",
        "list_agent_health",
        "list_events",
    }
    for tool in tools:
        assert tool.annotations is not None
        assert tool.annotations.read_only_hint is True
        assert tool.annotations.destructive_hint is False


@pytest.mark.parametrize(
    ("tool", "arguments", "method", "path"),
    [
        (
            "query_metrics",
            {"request": {"metrics": ["x"]}},
            "POST",
            "/telemetry/query/metrics",
        ),
        ("list_alerts", {}, "GET", "/telemetry/alerts"),
        ("get_alert", {"alert_id": "a-1"}, "GET", "/telemetry/alerts/a-1"),
        ("list_agent_health", {}, "GET", "/telemetry/health/agents"),
        ("list_events", {}, "GET", "/telemetry/events"),
    ],
)
def test_FR_NLQ_026_tools_call_backend_routes(
    tool: str, arguments: dict[str, Any], method: str, path: str
) -> None:
    seen: list[httpx.Request] = []
    _run(_ok({"items": []}, seen), tool, arguments)
    assert [(r.method, r.url.path) for r in seen] == [(method, path)]


def test_FR_NLQ_026_list_alerts_maps_params_and_drops_unset() -> None:
    seen: list[httpx.Request] = []
    _run(_ok({"items": []}, seen), "list_alerts", {"instance_id": "MAGIC-01"})
    assert dict(seen[0].url.params) == {
        "status": "active",
        "instanceId": "MAGIC-01",
        "limit": "50",
    }


def test_FR_NLQ_026_alert_id_cannot_escape_its_path_segment() -> None:
    seen: list[httpx.Request] = []
    _run(_ok({}, seen), "get_alert", {"alert_id": "../health/agents?x=1"})
    assert seen[0].url.raw_path == b"/telemetry/alerts/..%2Fhealth%2Fagents%3Fx%3D1"


def test_FR_NLQ_026_nl_query_returns_answer_with_provenance() -> None:
    seen: list[httpx.Request] = []
    result = _run(_ok(ANSWER_BODY, seen), "nl_query", {"question": "is magic slow"})
    sent = json.loads(seen[0].content)
    assert seen[0].url.path == "/telemetry/nl/query"
    assert sent["question"] == "is magic slow"
    assert sent["context"]["defaultApplication"] == "Magic"
    assert result["kind"] == "answer"
    assert result["answer"] == ANSWER_BODY["answer"]
    assert result["interpretedQuery"]["intent"] == "latency_summary"
    assert result["citations"] == [{"type": "metrics_query", "queryId": "q-1"}]
    # The raw group breakdown stays out of Copilot's context.
    assert "data" not in result


def test_FR_NLQ_030_nl_query_reply_carries_suggestions() -> None:
    result = _run(_ok(REPLY_BODY, []), "nl_query", {"question": "hi"})
    assert result == {
        "kind": "reply",
        "reason": "greeting",
        "message": "Hi! Ask me about Magic.",
        "suggestedQuestions": ["Is Magic slow?"],
    }


@pytest.mark.parametrize(
    ("status_code", "kind"),
    [(503, "disabled"), (422, "bad_request"), (404, "not_found"), (500, "unavailable")],
)
def test_FR_NLQ_026_backend_errors_become_short_results(
    status_code: int, kind: str
) -> None:
    result = _run(
        lambda request: httpx.Response(status_code, json={"detail": "x"}),
        "list_agent_health",
    )
    assert result["error"] == kind
    assert "detail" not in result


def test_FR_NLQ_026_unreachable_backend_is_reported() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    result = _run(handler, "nl_query", {"question": "is magic slow"})
    assert result["error"] == "unavailable"


def test_config_from_env() -> None:
    config = McpServerConfig.from_env(
        {
            "TELEMETRY_BACKEND_URL": "http://b:9000",
            "MCP_BACKEND_TIMEOUT_SECONDS": "20",
            "MCP_PORT": "9999",
        }
    )
    assert config.backend_base_url == "http://b:9000"
    assert config.request_timeout_seconds == 20.0
    assert config.port == 9999
    with pytest.raises(ValueError, match="MCP_PORT"):
        McpServerConfig.from_env({"MCP_PORT": "nope"})
