from __future__ import annotations

from pathlib import Path

import pytest
from telemetry_agent.publishing.config import (
    PublishConfigError,
    load_publish_config,
    load_publish_token,
    parse_publish_config,
)

_ENDPOINT = "https://telemetry.internal.example/telemetry/batch"


def test_defaults_match_spec_010() -> None:
    """docs/specs/010-configuration.md:90-100's `publish:` block, minus the
    `retry:`/`tls:` sections (UBS-104's extension)."""
    config = parse_publish_config({"endpoint": _ENDPOINT})

    assert config.enabled is True
    assert config.endpoint == _ENDPOINT
    assert config.dry_run is False
    assert config.interval_seconds == 10
    assert config.timeout_seconds == 10
    assert config.connect_timeout_seconds == 3
    assert config.max_batch_items == 500
    assert config.compress_threshold == 4096
    assert config.halt_probe_interval_seconds == 300


def test_rejects_plain_http_by_default() -> None:
    with pytest.raises(PublishConfigError, match="https"):
        parse_publish_config({"endpoint": "http://insecure.example/batch"})


def test_allows_plain_http_when_explicitly_opted_in() -> None:
    config = parse_publish_config(
        {"endpoint": "http://insecure.example/batch", "allowInsecureEndpoint": True}
    )
    assert config.endpoint == "http://insecure.example/batch"


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(PublishConfigError):
        parse_publish_config({"endpoint": _ENDPOINT, "bogusField": 1})


def test_max_batch_items_must_be_positive() -> None:
    with pytest.raises(PublishConfigError):
        parse_publish_config({"endpoint": _ENDPOINT, "maxBatchItems": 0})


def test_load_publish_config_missing_section_raises(tmp_path: Path) -> None:
    path = tmp_path / "agent.yaml"
    path.write_text("other: {}\n")

    with pytest.raises(PublishConfigError, match="no publish section"):
        load_publish_config(path)


def test_load_publish_config_reads_the_section(tmp_path: Path) -> None:
    path = tmp_path / "agent.yaml"
    path.write_text(f"publish:\n  endpoint: {_ENDPOINT}\n")

    config = load_publish_config(path)

    assert config.endpoint == _ENDPOINT


def test_load_publish_config_invalid_yaml_raises(tmp_path: Path) -> None:
    path = tmp_path / "agent.yaml"
    path.write_text("publish: [unbalanced\n")

    with pytest.raises(PublishConfigError, match="invalid YAML"):
        load_publish_config(path)


def test_load_publish_token_from_explicit_env() -> None:
    token = load_publish_token({"MAGIC_TELEMETRY_PUBLISH_TOKEN": "secret-token"})
    assert token == "secret-token"


def test_load_publish_token_missing_raises() -> None:
    with pytest.raises(RuntimeError, match="MAGIC_TELEMETRY_PUBLISH_TOKEN"):
        load_publish_token({})
