"""FR-CBK-* callbacks: config parsing tests."""

from __future__ import annotations

import pytest
from telemetry_agent.callbacks.config import (
    CallbackConfigError,
    parse_callbacks_config,
)


def test_FR_CBK_config_defaults_match_spec_010() -> None:
    """Golden-defaults test, matching this repo's NFR-CFG-004 convention:
    only `endpoint` is required, everything else defaults per spec 010."""
    config = parse_callbacks_config({"endpoint": "https://magic.example/callbacks"})

    assert config.enabled is True
    assert config.dry_run is False
    assert config.allow_insecure_callback is False
    assert config.connect_timeout_seconds == 3
    assert config.timeout_seconds == 10
    assert config.max_inflight == 4
    assert config.queue_size == 256
    assert config.max_bytes == 16384


def test_FR_CBK_001_rejects_plain_http_by_default() -> None:
    with pytest.raises(CallbackConfigError, match="https://"):
        parse_callbacks_config({"endpoint": "http://magic.example/callbacks"})


def test_FR_CBK_001_allows_plain_http_with_explicit_opt_in() -> None:
    config = parse_callbacks_config(
        {"endpoint": "http://localhost:8080/callbacks", "allowInsecureCallback": True}
    )
    assert config.endpoint == "http://localhost:8080/callbacks"


def test_FR_CBK_config_rejects_unknown_fields() -> None:
    with pytest.raises(CallbackConfigError):
        parse_callbacks_config(
            {"endpoint": "https://magic.example/callbacks", "notAField": 1}
        )


def test_FR_CBK_config_missing_endpoint_is_an_error() -> None:
    with pytest.raises(CallbackConfigError):
        parse_callbacks_config({})


def test_FR_CBK_config_custom_timeouts_and_limits() -> None:
    config = parse_callbacks_config(
        {
            "endpoint": "https://magic.example/callbacks",
            "connectTimeout": "5s",
            "timeout": "20s",
            "maxInflight": 8,
            "queueSize": 512,
            "maxBytes": 8192,
            "dryRun": True,
        }
    )
    assert config.connect_timeout_seconds == 5
    assert config.timeout_seconds == 20
    assert config.max_inflight == 8
    assert config.queue_size == 512
    assert config.max_bytes == 8192
    assert config.dry_run is True
