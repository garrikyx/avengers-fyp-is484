from pathlib import Path

import pytest
from telemetry_agent.health.config import (
    HealthConfigError,
    HealthThresholds,
    HeartbeatConfig,
    load_health_config,
    parse_duration_seconds,
)


def test_defaults_follow_spec_not_ticket() -> None:
    hb, thresholds = load_health_config(None)
    assert hb.interval_seconds == 10.0  # spec 010 heartbeat.interval, not 30s
    assert thresholds.read_lag_degraded_ms == 5_000.0  # spec 011 §1.1
    assert thresholds.rolling_window_seconds == 300.0  # ...Last5Min


def test_missing_file_yields_defaults(tmp_path: Path) -> None:
    assert load_health_config(tmp_path / "nope.yaml") == (
        HeartbeatConfig(),
        HealthThresholds(),
    )


@pytest.mark.parametrize(
    ("text", "seconds"),
    [("10s", 10.0), ("250ms", 0.25), ("5m", 300.0), ("1h", 3600.0), (7, 7.0)],
)
def test_parse_duration(text: str | int, seconds: float) -> None:
    assert parse_duration_seconds(text) == seconds


def test_parse_duration_rejects_garbage() -> None:
    with pytest.raises(HealthConfigError):
        parse_duration_seconds("ten seconds")


def test_loads_sections_and_ignores_siblings(tmp_path: Path) -> None:
    cfg = tmp_path / "agent.yaml"
    cfg.write_text(
        "agent:\n  id: magic-agent-sg-01\n"
        "  instanceIds: [magic-prod-01, magic-prod-02]\n"
        "log:\n  path: /logs/magic.log\n"  # someone else's section, passed through
        "heartbeat:\n  interval: 30s\n"
        "health:\n  readLagDegraded: 2s\n  rollingWindow: 1m\n"
        "  publishQueueHighWatermark: 5\n",
        encoding="utf-8",
    )
    hb, thresholds = load_health_config(cfg)
    assert hb.agent_id == "magic-agent-sg-01"
    assert hb.instance_ids == ("magic-prod-01", "magic-prod-02")
    assert hb.interval_seconds == 30.0
    assert thresholds.read_lag_degraded_ms == 2_000.0
    assert thresholds.rolling_window_seconds == 60.0
    assert thresholds.publish_queue_high_watermark == 5
    # untouched values keep their defaults
    assert thresholds.parse_error_rate_unhealthy == 0.25


def test_single_instance_id_alias(tmp_path: Path) -> None:
    cfg = tmp_path / "agent.yaml"
    cfg.write_text("agent:\n  id: a\n  instanceId: only-one\n", encoding="utf-8")
    hb, _ = load_health_config(cfg)
    assert hb.instance_ids == ("only-one",)


def test_unknown_key_is_refused(tmp_path: Path) -> None:
    cfg = tmp_path / "agent.yaml"
    cfg.write_text("heartbeat:\n  intervl: 10s\n", encoding="utf-8")
    with pytest.raises(HealthConfigError):
        load_health_config(cfg)


def test_invalid_yaml_is_refused(tmp_path: Path) -> None:
    cfg = tmp_path / "agent.yaml"
    cfg.write_text("heartbeat: [unclosed\n", encoding="utf-8")
    with pytest.raises(HealthConfigError):
        load_health_config(cfg)


def test_threshold_ordering_is_enforced() -> None:
    with pytest.raises(HealthConfigError):
        HealthThresholds(parse_error_rate_degraded=0.5, parse_error_rate_unhealthy=0.1)
    with pytest.raises(HealthConfigError):
        HealthThresholds(
            publish_queue_high_watermark=100, publish_queue_critical_watermark=10
        )
    with pytest.raises(HealthConfigError):
        HeartbeatConfig(interval_seconds=0)
    with pytest.raises(HealthConfigError, match=">= 1s"):
        HealthThresholds(rolling_window_seconds=0.5)  # below bucket size
