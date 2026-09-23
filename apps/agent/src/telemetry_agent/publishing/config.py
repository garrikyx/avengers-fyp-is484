"""FR-PUB-*: the `publish:` YAML config section (spec 010), following the
same load/validate pattern as `callbacks/config.py`.

UBS-103 shipped batching, compression, transport and the response-code
contract, with a placeholder item-count buffer cap (`maxBufferItems` --
`FR-PUB-004`'s actual bound is bytes/age, not item count). UBS-104 adds
the spec-exact `bufferBytes`/`bufferMaxAge` and the `retry.*` backoff
policy for transient failures, mirroring how UBS-33 added
`retry.*`/`maxAttempts` on top of UBS-32's transport-only `callbacks:`
config -- except `publish:` has no `maxAttempts` (`FR-PUB-005`: retries
are unbounded in count, bounded only by the buffer's own eviction, unlike
the Callback Dispatcher's give-up-after-N-tries policy).
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


class _RetryYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base: str = "1s"
    factor: float = 2.0
    cap: str = "60s"
    jitter: float = 0.2


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
    buffer_bytes: int = 67_108_864  # 64 MiB, memory only (FR-PUB-008)
    buffer_max_age: str = "15m"
    halt_probe_interval: str = "5m"
    retry: _RetryYaml = _RetryYaml()


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
    buffer_bytes: int
    buffer_max_age_seconds: float
    halt_probe_interval_seconds: float
    retry_base_seconds: float
    retry_factor: float
    retry_cap_seconds: float
    retry_jitter: float


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
    if parsed.buffer_bytes < 1:
        raise PublishConfigError("publish.bufferBytes must be >= 1")
    if not 0 <= parsed.retry.jitter < 1:
        raise PublishConfigError("publish.retry.jitter must be in [0, 1)")

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
        buffer_bytes=parsed.buffer_bytes,
        buffer_max_age_seconds=_parse_duration_seconds(parsed.buffer_max_age),
        halt_probe_interval_seconds=_parse_duration_seconds(
            parsed.halt_probe_interval
        ),
        retry_base_seconds=_parse_duration_seconds(parsed.retry.base),
        retry_factor=parsed.retry.factor,
        retry_cap_seconds=_parse_duration_seconds(parsed.retry.cap),
        retry_jitter=parsed.retry.jitter,
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
