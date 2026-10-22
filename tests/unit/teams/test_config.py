"""Environment-driven bot configuration."""

from __future__ import annotations

import pytest
from teams_agent.config import TeamsBotConfig


def test_defaults_when_the_environment_is_empty() -> None:
    config = TeamsBotConfig.from_env({})
    assert config.backend_base_url == "http://127.0.0.1:8080"
    assert config.default_application == "Magic"
    assert config.default_timezone == "Asia/Singapore"
    assert config.request_timeout_seconds == 10.0
    assert config.bind_host == "127.0.0.1"
    assert config.port == 3978


def test_values_are_read_from_the_environment() -> None:
    config = TeamsBotConfig.from_env(
        {
            "TELEMETRY_BACKEND_URL": "http://backend:9000",
            "TEAMS_DEFAULT_APPLICATION": "Other",
            "TEAMS_DEFAULT_TIMEZONE": "Asia/Tokyo",
            "TEAMS_BACKEND_TIMEOUT_SECONDS": "2.5",
            "TEAMS_BIND_HOST": "0.0.0.0",
            "PORT": "4000",
        }
    )
    assert config.backend_base_url == "http://backend:9000"
    assert config.default_application == "Other"
    assert config.default_timezone == "Asia/Tokyo"
    assert config.request_timeout_seconds == 2.5
    assert config.bind_host == "0.0.0.0"
    assert config.port == 4000


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"TEAMS_BACKEND_TIMEOUT_SECONDS": ""}, "TEAMS_BACKEND_TIMEOUT_SECONDS"),
        ({"TEAMS_BACKEND_TIMEOUT_SECONDS": "0"}, "must be positive"),
        ({"TEAMS_BACKEND_TIMEOUT_SECONDS": "-1"}, "must be positive"),
        ({"PORT": "abc"}, "PORT"),
        ({"PORT": "70000"}, "PORT"),
    ],
)
def test_invalid_values_fail_with_a_clear_message(
    env: dict[str, str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        TeamsBotConfig.from_env(env)
