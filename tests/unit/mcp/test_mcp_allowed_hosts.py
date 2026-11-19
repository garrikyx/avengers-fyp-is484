"""MCP server Host allowlist (ADR 0007): a dev tunnel's hostname can be allowed
for Copilot Studio while DNS-rebinding protection stays on."""

from __future__ import annotations

from typing import Any

import pytest
from starlette.testclient import TestClient
from telemetry_mcp.config import McpServerConfig
from telemetry_mcp.server import build_server, transport_security

TUNNEL = "abcd-8765.asse.devtunnels.ms"
INITIALIZE: dict[str, Any] = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"},
    },
}
HEADERS = {"Accept": "application/json, text/event-stream"}


def test_allowed_hosts_are_read_from_the_environment() -> None:
    config = McpServerConfig.from_env({"MCP_ALLOWED_HOSTS": f" {TUNNEL} , other.test,"})
    assert config.allowed_hosts == (TUNNEL, "other.test")
    assert McpServerConfig.from_env({}).allowed_hosts == ()


def test_no_extra_hosts_leaves_the_sdk_local_only_default() -> None:
    assert transport_security(McpServerConfig()) is None


def test_extra_hosts_keep_rebinding_protection_and_localhost() -> None:
    settings = transport_security(McpServerConfig(allowed_hosts=(TUNNEL,)))
    assert settings is not None
    assert settings.enable_dns_rebinding_protection
    assert TUNNEL in settings.allowed_hosts
    assert "127.0.0.1:*" in settings.allowed_hosts
    assert f"https://{TUNNEL}" in settings.allowed_origins


def _status(config: McpServerConfig, host: str) -> int:
    app = build_server(config).streamable_http_app(
        transport_security=transport_security(config)
        or transport_security(McpServerConfig(allowed_hosts=("localhost",)))
    )
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        response = client.post(
            "/mcp", json=INITIALIZE, headers={**HEADERS, "Host": host}
        )
        return response.status_code


@pytest.mark.parametrize(
    ("allowed", "expected_ok"), [((TUNNEL,), True), (("someone-else.test",), False)]
)
def test_tunnel_host_header_is_accepted_only_when_allowed(
    allowed: tuple[str, ...], expected_ok: bool
) -> None:
    status = _status(McpServerConfig(allowed_hosts=allowed), TUNNEL)
    assert (status != 421) is expected_ok, status
