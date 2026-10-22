"""Read-only MCP server over the telemetry backend HTTP APIs (UBS-131; ADR 0007).

A thin adapter (FR-NLQ-026): every tool is one call to a backend read
endpoint and returns its JSON unchanged, `dataCompleteness` included where
the endpoint has it. It never touches Redis, the stores or logs, and has no
mutating tool. Auth, rate limits and audit are the backend's (UBS-135).
Tool descriptions are static docstrings; no telemetry text reaches them
(FR-NLQ-024).

    uv run telemetry-mcp                                   # stdio (MCP Inspector)
    uv run telemetry-mcp --transport streamable-http       # Copilot, via HTTPS
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import Any, Literal
from urllib.parse import quote

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from telemetry_shared.models.metrics_query import MetricsQueryRequest

BACKEND_URL = os.environ.get("TELEMETRY_BACKEND_URL", "http://127.0.0.1:8080")
_READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)

mcp = MCPServer(
    "magic-telemetry",
    instructions=(
        "Read-only Magic trading telemetry. Quote numbers exactly as returned. "
        "If dataCompleteness.confidence is not 'complete', say the numbers are "
        "incomplete."
    ),
)

# shortcut: no Authorization forwarding; the POC backend needs no token
# (spec 009 §3.3). Forward the caller's Entra token here once UBS-135 enforces it.
_transport: httpx.AsyncBaseTransport | None = None  # test seam


async def _call(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = {k: v for k, v in (params or {}).items() if v is not None}
    async with httpx.AsyncClient(
        base_url=BACKEND_URL, timeout=10.0, transport=_transport
    ) as client:
        try:
            response = await client.request(method, path, params=query, json=json)
        except httpx.HTTPError as exc:
            raise ToolError(f"telemetry backend unreachable: {exc!r}") from exc
    if response.is_error:
        # The backend's error envelope (spec 007 §7) tells the model what to fix.
        raise ToolError(f"backend {response.status_code}: {response.text}")
    body: dict[str, Any] = response.json()
    return body


@mcp.tool(annotations=_READ_ONLY)
async def nl_query(question: str) -> dict[str, Any]:
    """Answer a natural-language question about Magic telemetry, for example
    "Why are orders rejecting?" or "Is Magic slow right now?". Returns the
    answer text, the interpreted query, the numbers it came from, caveats and
    dataCompleteness. An unsupported question returns a clarification listing
    supported intents."""
    return await _call("POST", "/telemetry/nl/query", json={"question": question})


@mcp.tool(annotations=_READ_ONLY)
async def query_metrics(query: MetricsQueryRequest) -> dict[str, Any]:
    """Run a structured metrics query over a time range, with optional filters,
    groupBy, percentiles and a time series. Returns totals, groups, latency and
    dataCompleteness."""
    body = query.model_dump(mode="json", by_alias=True, exclude_none=True)
    return await _call("POST", "/telemetry/query/metrics", json=body)


@mcp.tool(annotations=_READ_ONLY)
async def list_alerts(
    status: Literal["active", "resolved", "all"] = "active",
    application: str | None = None,
    instance_id: str | None = None,
    rule_name: str | None = None,
    severity: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """List alerts (active by default) with severity, rule, instance and
    timing. Filter by application, instance, rule, severity or start time."""
    return await _call(
        "GET",
        "/telemetry/alerts",
        params={
            "status": status,
            "application": application,
            "instanceId": instance_id,
            "ruleName": rule_name,
            "severity": severity,
            "since": since.isoformat() if since else None,
            "limit": limit,
        },
    )


@mcp.tool(annotations=_READ_ONLY)
async def get_alert(alert_id: str) -> dict[str, Any]:
    """Get one alert by ID, including its transitions and callback delivery
    status."""
    return await _call("GET", f"/telemetry/alerts/{quote(alert_id, safe='')}")


@mcp.tool(annotations=_READ_ONLY)
async def list_agent_health() -> dict[str, Any]:
    """List telemetry agents with status (healthy, degraded, unhealthy or
    missing), heartbeat age and version, plus a count per status."""
    return await _call("GET", "/telemetry/health/agents")


@mcp.tool(annotations=_READ_ONLY)
async def list_events(
    application: str | None = None,
    instance_id: str | None = None,
    event_type: str | None = None,
    severity: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """List recent telemetry events such as FIX session logons, logouts,
    heartbeat timeouts and sequence gaps. Filter by application, instance,
    event type, severity or start time."""
    return await _call(
        "GET",
        "/telemetry/events",
        params={
            "application": application,
            "instanceId": instance_id,
            "eventType": event_type,
            "severity": severity,
            "since": since.isoformat() if since else None,
            "limit": limit,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Magic telemetry MCP server")
    parser.add_argument(
        "--transport", choices=["stdio", "streamable-http"], default="stdio"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=[],
        help="public hostname a tunnel forwards to this server (repeatable)",
    )
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.run()
        return
    # Keep the SDK's DNS-rebinding check, but also accept the tunnel's Host.
    local = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    security = TransportSecuritySettings(
        allowed_hosts=local + args.allowed_host,
        allowed_origins=[f"https://{h}" for h in args.allowed_host],
    )
    mcp.run(
        "streamable-http",
        host=args.host,
        port=args.port,
        transport_security=security,
    )


if __name__ == "__main__":
    main()
