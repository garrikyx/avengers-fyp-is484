"""Teams bot settings, read from the environment.

Microsoft app credentials (`CONNECTIONS__SERVICE_CONNECTION__SETTINGS__*`) are
read by the Agents SDK itself; nothing secret lives here.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TeamsBotConfig:
    backend_base_url: str = "http://127.0.0.1:8080"
    default_application: str = "Magic"
    default_timezone: str = "Asia/Singapore"
    # Must stay above the backend's LLM budget (nl.llm.timeout, 6s) plus query time,
    # so the backend's fallback reply arrives before this client gives up.
    request_timeout_seconds: float = 12.0
    bind_host: str = "127.0.0.1"
    port: int = 3978

    def __post_init__(self) -> None:
        if self.request_timeout_seconds <= 0:
            raise ValueError("TEAMS_BACKEND_TIMEOUT_SECONDS must be positive")
        if not 0 < self.port < 65536:
            raise ValueError("PORT must be between 1 and 65535")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> TeamsBotConfig:
        source = os.environ if env is None else env
        defaults = cls()
        return cls(
            backend_base_url=source.get(
                "TELEMETRY_BACKEND_URL", defaults.backend_base_url
            ),
            default_application=source.get(
                "TEAMS_DEFAULT_APPLICATION", defaults.default_application
            ),
            default_timezone=source.get(
                "TEAMS_DEFAULT_TIMEZONE", defaults.default_timezone
            ),
            request_timeout_seconds=_number(
                source,
                "TEAMS_BACKEND_TIMEOUT_SECONDS",
                float,
                defaults.request_timeout_seconds,
            ),
            bind_host=source.get("TEAMS_BIND_HOST", defaults.bind_host),
            port=_number(source, "PORT", int, defaults.port),
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
