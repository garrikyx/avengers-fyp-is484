"""MCP server exposing read-only telemetry tools to Copilot (ADR 0007).

Tool descriptions are static text: no telemetry values, hostnames or log content.
Every tool is read-only and answers through the backend APIs (FR-NLQ-026).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field
from telemetry_shared.models.nl_query import Audience

from telemetry_mcp.backend import TelemetryBackend, ToolResult
from telemetry_mcp.config import McpServerConfig

logger = logging.getLogger(__name__)

READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)

AlertStatus = Literal["active", "resolved", "all"]
Limit = Annotated[int, Field(ge=1, le=500)]

INSTRUCTIONS = (
    "Read-only telemetry for the Magic trading application. Prefer nl_query for "
    "questions in plain language and quote its answer as written; do not recompute "
    "or invent numbers. When it returns a reply instead of an answer, offer its "
    "suggestedQuestions."
)


def build_server(
    config: McpServerConfig, *, client: httpx.AsyncClient | None = None
) -> MCPServer:
    """One backend client lives as long as the server. `client` is for tests; the
    caller then owns closing it."""
    http = client or httpx.AsyncClient(
        base_url=config.backend_base_url,
        timeout=config.request_timeout_seconds,
    )
    backend = TelemetryBackend(
        http,
        default_application=config.default_application,
        default_timezone=config.default_timezone,
    )

    @asynccontextmanager
    async def lifespan(_: MCPServer) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if client is None:
                await http.aclose()

    server = MCPServer("magic-telemetry", instructions=INSTRUCTIONS, lifespan=lifespan)

    @server.tool(annotations=READ_ONLY)
    async def nl_query(
        question: Annotated[str, Field(min_length=1, max_length=500)],
        timezone: str | None = None,
        audience: Audience = "technical",
    ) -> ToolResult:
        """Ask a plain-language question about Magic order flow, rejections,
        latency, alerts or agent health. Returns a templated answer with the
        interpreted query, time range and data completeness, or a short reply with
        suggested questions when the question is not about telemetry."""
        return await backend.nl_query(question, timezone=timezone, audience=audience)

    @server.tool(annotations=READ_ONLY)
    async def query_metrics(request: dict[str, Any]) -> ToolResult:
        """Run a structured metrics query (the backend MetricsQueryRequest body:
        timeRange, filters, groupBy, metrics, percentiles, topK, series, step)."""
        return await backend.query_metrics(request)

    @server.tool(annotations=READ_ONLY)
    async def list_alerts(
        status: AlertStatus = "active",
        application: str | None = None,
        instance_id: str | None = None,
        limit: Limit = 50,
    ) -> ToolResult:
        """List alerts, newest first. Defaults to active alerts."""
        return await backend.list_alerts(
            _params(
                status=status,
                application=application,
                instanceId=instance_id,
                limit=limit,
            )
        )

    @server.tool(annotations=READ_ONLY)
    async def get_alert(
        alert_id: Annotated[str, Field(min_length=1, max_length=200)],
    ) -> ToolResult:
        """Get one alert by its ID."""
        return await backend.get_alert(alert_id)

    @server.tool(annotations=READ_ONLY)
    async def list_agent_health() -> ToolResult:
        """List telemetry agents with their last heartbeat and health status."""
        return await backend.list_agent_health()

    @server.tool(annotations=READ_ONLY)
    async def list_events(
        application: str | None = None,
        instance_id: str | None = None,
        event_type: str | None = None,
        severity: str | None = None,
        since: Annotated[str | None, Field(description="ISO 8601 UTC time")] = None,
        limit: Limit = 50,
    ) -> ToolResult:
        """List sanitized operational events, newest first."""
        return await backend.list_events(
            _params(
                application=application,
                instanceId=instance_id,
                eventType=event_type,
                severity=severity,
                since=since,
                limit=limit,
            )
        )

    return server


def _params(**values: str | int | None) -> dict[str, str | int]:
    return {key: value for key, value in values.items() if value is not None}


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = McpServerConfig.from_env()
    logger.info(
        "telemetry MCP server on http://%s:%s/mcp -> %s",
        config.bind_host,
        config.port,
        config.backend_base_url,
    )
    build_server(config).run(
        transport="streamable-http", host=config.bind_host, port=config.port
    )
