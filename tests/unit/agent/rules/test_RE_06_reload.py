"""RE-05: `RuleEngine.apply_rules` and `SighupRuleReloader` (`FR-RUL-008`)."""

import logging
import os
import signal
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from rule_fixtures import make_snapshot
from telemetry_agent.rules.config_loader import SighupRuleReloader
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import (
    AlertStatus,
    RuleConfig,
    RuleKind,
    SeverityTier,
    ValueSource,
)
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.metrics import MetricsSnapshot

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)

_RULE = RuleConfig(
    name="TestRule",
    kind=RuleKind.THRESHOLD,
    source=ValueSource.COUNTER,
    metric="widgets_broken",
    operator=">",
    tiers=(SeverityTier(severity="warning", threshold=Decimal(5)),),
    window="1m",
    for_seconds=0,
    resolve_after_seconds=120,
)

_OTHER_RULE = RuleConfig(
    name="OtherRule",
    kind=RuleKind.THRESHOLD,
    source=ValueSource.COUNTER,
    metric="gizmos_broken",
    operator=">",
    tiers=(SeverityTier(severity="warning", threshold=Decimal(5)),),
    window="1m",
    for_seconds=0,
    resolve_after_seconds=120,
)

_OTHER_RULE_YAML = """
rules:
  - name: OtherRule
    kind: threshold
    source: counter
    metric: gizmos_broken
    operator: ">"
    tiers: [{severity: warning, threshold: 5}]
    window: 1m
    for: 0s
"""


def _engine(*rules: RuleConfig, renotify_interval_seconds: int = 1800) -> RuleEngine:
    return RuleEngine(
        rules=rules,
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
        startup_grace_seconds=60,
        renotify_interval_seconds=renotify_interval_seconds,
    )


def _snapshot(
    now: datetime, broken: int, metric: str = "widgets_broken"
) -> MetricsSnapshot:
    return make_snapshot(now=now, window="1m", counters={metric: Decimal(broken)})


def _fire(engine: RuleEngine, rule: RuleConfig, now: datetime) -> AlertEvent:
    """Two evaluate() calls: the first only enters `pending` (no event, per
    the FSM's own "always pending first" design — see test_RE_01_fsm.py);
    the second, at `for_seconds=0`, promotes to `firing`.
    """
    engine.evaluate(_snapshot(now, 10, rule.metric), now)
    events = engine.evaluate(_snapshot(now, 10, rule.metric), now)
    assert len(events) == 1
    return events[0]


def test_apply_rules_preserves_state_for_a_rule_whose_name_persists() -> None:
    engine = _engine(_RULE, renotify_interval_seconds=30)
    fired = _fire(engine, _RULE, _T0)

    tightened = replace(
        _RULE, tiers=(SeverityTier(severity="warning", threshold=Decimal(1)),)
    )
    events = engine.apply_rules((tightened,), now=_T0)

    assert events == []  # nothing removed, nothing to force-resolve
    assert engine.status_of("TestRule") is AlertStatus.FIRING

    # Past the renotify interval: confirm this is still the *same*
    # occurrence (alertId/firstObservedUtc survived the reload), not a new
    # one that happens to reuse the rule name.
    later = _T0 + timedelta(seconds=31)
    renotified = engine.evaluate(_snapshot(later, 10, "widgets_broken"), later)
    assert len(renotified) == 1
    assert renotified[0].alert_id == fired.alert_id
    assert renotified[0].first_observed_utc == fired.first_observed_utc


def test_apply_rules_force_resolves_a_firing_alert_whose_rule_was_removed() -> None:
    engine = _engine(_RULE)
    _fire(engine, _RULE, _T0)
    assert engine.active_alert_count() == 1

    events = engine.apply_rules((), now=_T0 + timedelta(seconds=1))

    assert len(events) == 1
    assert events[0].rule_name == "TestRule"
    assert events[0].status == "resolved"
    assert engine.active_alert_count() == 0
    assert engine.status_of("TestRule") is None


def test_apply_rules_removes_a_pending_state_without_an_event() -> None:
    long_for = replace(_RULE, for_seconds=999)
    engine = _engine(long_for)
    engine.evaluate(_snapshot(_T0, 10), _T0)
    assert engine.status_of("TestRule") is AlertStatus.PENDING

    events = engine.apply_rules((), now=_T0)

    assert events == []  # pending was never "active alert output"
    assert engine.status_of("TestRule") is None


def test_apply_rules_leaves_unrelated_rules_untouched() -> None:
    engine = _engine(_RULE, _OTHER_RULE)
    _fire(engine, _RULE, _T0)
    _fire(engine, _OTHER_RULE, _T0)

    events = engine.apply_rules((_OTHER_RULE,), now=_T0)

    assert len(events) == 1
    assert events[0].rule_name == "TestRule"
    assert engine.status_of("OtherRule") is AlertStatus.FIRING


def test_sighup_reloader_swaps_in_a_valid_file(tmp_path: Path) -> None:
    engine = _engine(_RULE)
    path = tmp_path / "rules.yaml"
    path.write_text(_OTHER_RULE_YAML)
    reloader = SighupRuleReloader(engine, path, logger=logging.getLogger("test"))

    reloader.reload(now=_T0)

    # TestRule is gone: even a clearly-tripping snapshot never fires it.
    engine.evaluate(_snapshot(_T0, 10, "widgets_broken"), _T0)
    no_event = engine.evaluate(_snapshot(_T0, 10, "widgets_broken"), _T0)
    assert no_event == []
    # OtherRule is now live and fires normally.
    fired = _fire(engine, _OTHER_RULE, _T0)
    assert fired.rule_name == "OtherRule"


def test_sighup_reloader_rejects_malformed_file_and_keeps_old_rules(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    engine = _engine(_RULE)
    path = tmp_path / "rules.yaml"
    path.write_text("rules: []")
    reloader = SighupRuleReloader(engine, path, logger=logging.getLogger("test"))

    with caplog.at_level(logging.ERROR):
        reloader.reload(now=_T0)

    # Old rule set still in effect.
    fired = _fire(engine, _RULE, _T0)
    assert fired.rule_name == "TestRule"
    assert any("reload rejected" in record.message for record in caplog.records)


@pytest.mark.skipif(not hasattr(signal, "SIGHUP"), reason="SIGHUP is POSIX-only")
def test_install_wires_a_real_sighup_to_a_reload(tmp_path: Path) -> None:
    engine = _engine(_RULE)
    path = tmp_path / "rules.yaml"
    path.write_text(_OTHER_RULE_YAML)
    reloader = SighupRuleReloader(engine, path, logger=logging.getLogger("test"))
    previous_handler = signal.getsignal(signal.SIGHUP)
    try:
        reloader.install()
        os.kill(os.getpid(), signal.SIGHUP)

        no_event = engine.evaluate(_snapshot(_T0, 10, "widgets_broken"), _T0)
        engine.evaluate(_snapshot(_T0, 10, "widgets_broken"), _T0)
        assert no_event == []  # TestRule no longer configured

        fired = _fire(engine, _OTHER_RULE, _T0)
        assert fired.rule_name == "OtherRule"
    finally:
        signal.signal(signal.SIGHUP, previous_handler)
