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
    `tls:` section (not yet needed -- `HttpsPublishSink` always uses the
    system default TLS trust store)."""
    config = parse_publish_config({"endpoint": _ENDPOINT})

    assert config.enabled is True
    assert config.endpoint == _ENDPOINT
    assert config.dry_run is False
    assert config.interval_seconds == 10
    assert config.timeout_seconds == 10
    assert config.connect_timeout_seconds == 3
    assert config.max_batch_items == 500
    assert config.compress_threshold == 4096
    assert config.buffer_bytes == 67_108_864
    assert config.buffer_max_age_seconds == 900
    assert config.halt_probe_interval_seconds == 300
    assert config.retry_base_seconds == 1
    assert config.retry_factor == 2
    assert config.retry_cap_seconds == 60
    assert config.retry_jitter == 0.2


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


def test_buffer_bytes_must_be_positive() -> None:
    with pytest.raises(PublishConfigError):
        parse_publish_config({"endpoint": _ENDPOINT, "bufferBytes": 0})


def test_retry_jitter_must_be_in_valid_range() -> None:
    with pytest.raises(PublishConfigError, match="jitter"):
        parse_publish_config(
            {"endpoint": _ENDPOINT, "retry": {"jitter": 1.5}}
        )


def test_retry_fields_are_configurable() -> None:
    config = parse_publish_config(
        {
            "endpoint": _ENDPOINT,
            "retry": {"base": "2s", "factor": 3, "cap": "30s", "jitter": 0.1},
        }
    )

    assert config.retry_base_seconds == 2
    assert config.retry_factor == 3
    assert config.retry_cap_seconds == 30
    assert config.retry_jitter == 0.1


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
