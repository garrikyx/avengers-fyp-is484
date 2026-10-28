"""MCP server settings, read from the environment. Nothing secret lives here."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class McpServerConfig:
    backend_base_url: str = "http://127.0.0.1:8080"
    default_application: str = "Magic"
    default_timezone: str = "Asia/Singapore"
    # Above the backend's LLM budget (nl.llm.timeout, 6s) plus query time, so the
    # backend's fallback reply arrives before this client gives up.
    request_timeout_seconds: float = 12.0
    bind_host: str = "127.0.0.1"
    port: int = 8765

    def __post_init__(self) -> None:
        if self.request_timeout_seconds <= 0:
            raise ValueError("MCP_BACKEND_TIMEOUT_SECONDS must be positive")
        if not 0 < self.port < 65536:
            raise ValueError("MCP_PORT must be between 1 and 65535")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> McpServerConfig:
        source = os.environ if env is None else env
        defaults = cls()
        return cls(
            backend_base_url=source.get(
                "TELEMETRY_BACKEND_URL", defaults.backend_base_url
            ),
            default_application=source.get(
                "MCP_DEFAULT_APPLICATION", defaults.default_application
            ),
            default_timezone=source.get(
                "MCP_DEFAULT_TIMEZONE", defaults.default_timezone
            ),
            request_timeout_seconds=_number(
                source,
                "MCP_BACKEND_TIMEOUT_SECONDS",
                float,
                defaults.request_timeout_seconds,
            ),
            bind_host=source.get("MCP_BIND_HOST", defaults.bind_host),
            port=_number(source, "MCP_PORT", int, defaults.port),
        )


def _number[T: (int, float)](
    source: Mapping[str, str], name: str, parse: type[T], default: T
) -> T:
    raw = source.get(name)
    if raw is None:
        return default
    try:
        return parse(raw)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {raw!r}") from None
