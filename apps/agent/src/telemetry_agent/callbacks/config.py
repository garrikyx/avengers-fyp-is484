"""FR-CBK-*: the `callbacks:` YAML config section (spec 010), following the
same load/validate pattern as `rules/config_loader.py`.

UBS-32 scope: transport/dispatch fields only. Retry-specific fields
(`retry.*`, `maxAttempts`) are added by UBS-33's pass over this file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel

from telemetry_agent.rules.config_loader import _parse_duration_seconds


class CallbackConfigError(Exception):
    """Raised at load time; refuses to start on a malformed config
    (`FR-RUL-009`'s "refuse to start" convention applied to callbacks).
    """


class _CallbacksYaml(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid"
    )

    enabled: bool = True
    endpoint: str
    allow_insecure_callback: bool = False
    dry_run: bool = False
    connect_timeout: str = "3s"
    timeout: str = "10s"
    max_inflight: int = 4
    queue_size: int = 256
    max_bytes: int = 16384


class CallbacksConfig(BaseModel):
    """Resolved config the dispatcher/sink actually consume — durations
    already parsed to seconds.
    """

    model_config = ConfigDict(frozen=True)

    enabled: bool
    endpoint: str
    allow_insecure_callback: bool
    dry_run: bool
    connect_timeout_seconds: float
    timeout_seconds: float
    max_inflight: int
    queue_size: int
    max_bytes: int


def parse_callbacks_config(raw: dict[str, Any]) -> CallbacksConfig:
    """Parses an already-loaded `callbacks:` YAML section. Pure — no file
    I/O — so it's directly unit-testable against dict fixtures.
    """
    try:
        parsed = _CallbacksYaml.model_validate(raw)
    except ValidationError as exc:
        raise CallbackConfigError(f"invalid callbacks config: {exc}") from exc

    insecure = not parsed.endpoint.startswith("https://")
    if insecure and not parsed.allow_insecure_callback:
        msg = (
            f"callbacks.endpoint must be https:// (got {parsed.endpoint!r}); "
            "set allowInsecureCallback: true for local development only"
        )
        raise CallbackConfigError(msg)

    return CallbacksConfig(
        enabled=parsed.enabled,
        endpoint=parsed.endpoint,
        allow_insecure_callback=parsed.allow_insecure_callback,
        dry_run=parsed.dry_run,
        connect_timeout_seconds=_parse_duration_seconds(parsed.connect_timeout),
        timeout_seconds=_parse_duration_seconds(parsed.timeout),
        max_inflight=parsed.max_inflight,
        queue_size=parsed.queue_size,
        max_bytes=parsed.max_bytes,
    )


def load_callbacks_config(path: Path) -> CallbacksConfig:
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise CallbackConfigError(f"{path}: invalid YAML: {exc}") from exc

    section = (raw or {}).get("callbacks", {}) if isinstance(raw, dict) else {}
    if not section:
        raise CallbackConfigError(f"{path}: no callbacks section defined")
    return parse_callbacks_config(section)
