"""UBS-131: read-only MCP server over the backend HTTP APIs (FR-NLQ-026)."""

from __future__ import annotations

import ast
import asyncio
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app
from telemetry_backend.services.ingestion import IngestionService
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_mcp import server

from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot

TOOLS = {
    "nl_query",
    "query_metrics",
    "list_alerts",
    "get_alert",
    "list_agent_health",
    "list_events",
}


@pytest.fixture
def backend() -> Iterator[None]:
    """Route the MCP server's HTTP calls into an in-process backend."""
    processor = StreamProcessor(StreamProcessorConfig())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 50, "orders_rejected": 5}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    app = create_app(
        service=IngestionService(stream_processor=processor),
        deps=AppDeps(nl_config=NlConfig(enabled=True, llm=LlmConfig(provider="mock"))),
    )
    server._transport = httpx.ASGITransport(app=app)
    yield
    server._transport = None


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = asyncio.run(server.mcp.call_tool(name, arguments))
    structured: dict[str, Any] = result.structured_content  # type: ignore[union-attr]
    return structured


def test_FR_NLQ_026_lists_exactly_the_read_only_tools() -> None:
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == TOOLS
    assert all(t.annotations and t.annotations.read_only_hint for t in tools)


def test_FR_NLQ_026_never_imports_redis_or_backend_internals() -> None:
    source = Path(server.__file__).read_text()
    imported = {
        (node.module or "") if isinstance(node, ast.ImportFrom) else alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    }
    assert not {
        m for m in imported if m.split(".")[0] in {"redis", "telemetry_backend"}
    }


def test_FR_NLQ_026_nl_query_returns_data_completeness(backend: None) -> None:
    body = _call("nl_query", {"question": "Why are orders rejecting?"})
    assert body["kind"] == "answer"
    assert "interpretedQuery" in body
    assert "confidence" in body["data"]["dataCompleteness"]


def test_FR_NLQ_026_query_metrics_returns_data_completeness(backend: None) -> None:
    body = _call(
        "query_metrics",
        {"query": {"timeRange": {"last": "30m"}, "metrics": ["orders_rejected"]}},
    )
    assert "dataCompleteness" in body


@pytest.mark.parametrize(
    ("name", "key"),
    [
        ("list_alerts", "alerts"),
        ("list_agent_health", "agents"),
        ("list_events", "events"),
    ],
)
def test_FR_NLQ_026_list_tools_answer_from_backend(
    backend: None, name: str, key: str
) -> None:
    assert key in _call(name, {})


def test_get_alert_unknown_id_is_a_tool_error_not_a_path_escape(
    backend: None,
) -> None:
    # Quoted, so it cannot reach `/healthz` (200); the client sees isError.
    with pytest.raises(ToolError, match="backend 404"):
        asyncio.run(server.mcp.call_tool("get_alert", {"alert_id": "../healthz"}))
