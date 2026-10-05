from pathlib import Path

import pytest
from telemetry_backend.config import (
    BackendConfigError,
    BackendHealthConfig,
    load_backend_health_config,
)


def test_defaults_follow_spec_010() -> None:
    cfg = load_backend_health_config(None)
    assert cfg.missing_heartbeat_threshold_seconds == 60.0
    assert cfg.warmup_window_seconds == 120.0
    assert cfg.listen_host_port == ("0.0.0.0", 8080)
    assert cfg.internal_listen_host_port == ("127.0.0.1", 8081)


def test_missing_file_yields_defaults(tmp_path: Path) -> None:
    assert load_backend_health_config(tmp_path / "nope.yaml") == BackendHealthConfig()


def test_reads_backend_store_alerting_sections(tmp_path: Path) -> None:
    cfg_file = tmp_path / "backend.yaml"
    cfg_file.write_text(
        "backend:\n  listen: 0.0.0.0:9000\n  internalListen: 127.0.0.1:9001\n"
        "  workers: 4\n"  # someone else's key, tolerated
        "store:\n  warmupWindow: 30s\n"
        "alerting:\n  missingHeartbeatThreshold: 2m\n"
        "ingest:\n  queueSize: 10\n",  # sibling section passed through
        encoding="utf-8",
    )
    cfg = load_backend_health_config(cfg_file)
    assert cfg.listen_host_port == ("0.0.0.0", 9000)
    assert cfg.internal_listen_host_port == ("127.0.0.1", 9001)
    assert cfg.warmup_window_seconds == 30.0
    assert cfg.missing_heartbeat_threshold_seconds == 120.0


def test_invalid_values_are_refused(tmp_path: Path) -> None:
    cfg_file = tmp_path / "backend.yaml"
    cfg_file.write_text(
        "alerting:\n  missingHeartbeatThreshold: soon\n", encoding="utf-8"
    )
    with pytest.raises(BackendConfigError):
        load_backend_health_config(cfg_file)
    with pytest.raises(BackendConfigError):
        BackendHealthConfig(listen="no-port")
    with pytest.raises(BackendConfigError):
        BackendHealthConfig(missing_heartbeat_threshold_seconds=0)


def test_invalid_yaml_is_refused(tmp_path: Path) -> None:
    cfg_file = tmp_path / "backend.yaml"
    cfg_file.write_text("backend: [oops\n", encoding="utf-8")
    with pytest.raises(BackendConfigError):
        load_backend_health_config(cfg_file)
