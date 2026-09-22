"""FR-PUB-*: the `publish:` YAML config section (spec 010), following the
same load/validate pattern as `callbacks/config.py`.

UBS-103 scope: batching, compression, transport and the response-code
contract (`interval`, `maxBatchItems`, `compressThreshold`,
`maxBufferItems`, `haltProbeInterval`). The exponential-backoff retry
policy for transient failures (`retry.*`) is UBS-104's extension, mirroring
how UBS-33 added `retry.*`/`maxAttempts` on top of UBS-32's transport-only
`callbacks:` config.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel

from telemetry_agent.rules.config_loader import _parse_duration_seconds

_TOKEN_ENV_VAR = "MAGIC_TELEMETRY_PUBLISH_TOKEN"


class PublishConfigError(Exception):
    """Raised at load time; refuses to start on a malformed config
    (`FR-RUL-009`'s "refuse to start" convention applied to publishing).
    """


class _PublishYaml(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid"
    )

    enabled: bool = True
    endpoint: str
    allow_insecure_endpoint: bool = False
    dry_run: bool = False
    interval: str = "10s"
    connect_timeout: str = "3s"
    timeout: str = "10s"
    max_batch_items: int = 500
    compress_threshold: int = 4096
    max_buffer_items: int = 2000
    halt_probe_interval: str = "5m"


class PublishConfig(BaseModel):
    """Resolved config the publisher/sink actually consume — durations
    already parsed to seconds.
    """

    model_config = ConfigDict(frozen=True)

    enabled: bool
    endpoint: str
    allow_insecure_endpoint: bool
    dry_run: bool
    interval_seconds: float
    connect_timeout_seconds: float
    timeout_seconds: float
    max_batch_items: int
    compress_threshold: int
    max_buffer_items: int
    halt_probe_interval_seconds: float


def parse_publish_config(raw: dict[str, Any]) -> PublishConfig:
    """Parses an already-loaded `publish:` YAML section. Pure — no file
    I/O — so it's directly unit-testable against dict fixtures.
    """
    try:
        parsed = _PublishYaml.model_validate(raw)
    except ValidationError as exc:
        raise PublishConfigError(f"invalid publish config: {exc}") from exc

    insecure = not parsed.endpoint.startswith("https://")
    if insecure and not parsed.allow_insecure_endpoint:
        msg = (
            f"publish.endpoint must be https:// (got {parsed.endpoint!r}); "
            "set allowInsecureEndpoint: true for local development only"
        )
        raise PublishConfigError(msg)
    if parsed.max_batch_items < 1:
        raise PublishConfigError("publish.maxBatchItems must be >= 1")
    if parsed.max_buffer_items < 1:
        raise PublishConfigError("publish.maxBufferItems must be >= 1")

    return PublishConfig(
        enabled=parsed.enabled,
        endpoint=parsed.endpoint,
        allow_insecure_endpoint=parsed.allow_insecure_endpoint,
        dry_run=parsed.dry_run,
        interval_seconds=_parse_duration_seconds(parsed.interval),
        connect_timeout_seconds=_parse_duration_seconds(parsed.connect_timeout),
        timeout_seconds=_parse_duration_seconds(parsed.timeout),
        max_batch_items=parsed.max_batch_items,
        compress_threshold=parsed.compress_threshold,
        max_buffer_items=parsed.max_buffer_items,
        halt_probe_interval_seconds=_parse_duration_seconds(
            parsed.halt_probe_interval
        ),
    )


def load_publish_config(path: Path) -> PublishConfig:
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise PublishConfigError(f"{path}: invalid YAML: {exc}") from exc

    section = (raw or {}).get("publish", {}) if isinstance(raw, dict) else {}
    if not section:
        raise PublishConfigError(f"{path}: no publish section defined")
    return parse_publish_config(section)


def load_publish_token(env: Mapping[str, str] | None = None) -> str:
    """Read the publish bearer token from the environment (`NFR-SEC-004`).

    Raises RuntimeError if unset or empty rather than falling back to an
    insecure default — call once at process startup so a missing token
    fails the process to start, not a per-batch send attempt.
    """
    source = env if env is not None else os.environ
    value = source.get(_TOKEN_ENV_VAR, "")
    if not value:
        raise RuntimeError(f"{_TOKEN_ENV_VAR} is required but not set")
    return value
