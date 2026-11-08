"""UBS-130: ApplicationDown (spec 005 §1.2, FR-HLT-014, FR-MET-034).

Both rule sources are checked: `DEFAULT_RULES` (the fallback) and the shipped
`config/rules.yaml` (the live source of truth) must agree.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from rule_fixtures import make_gauges, make_snapshot
from telemetry_agent.rules.config_loader import load_rules
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig, RuleKind, ValueSource

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_RULES_YAML = Path(__file__).resolve().parents[4] / "config" / "rules.yaml"


def _rule(source: str) -> RuleConfig:
    rules = DEFAULT_RULES if source == "defaults" else load_rules(_RULES_YAML)
    return next(r for r in rules if r.name == "ApplicationDown")


def _engine(rule: RuleConfig) -> RuleEngine:
    return RuleEngine(
        rules=(rule,),
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
    )


@pytest.mark.parametrize("source", ["defaults", "yaml"])
class TestApplicationDown:
    def test_fr_hlt_014_shape(self, source: str) -> None:
        rule = _rule(source)
        assert rule.kind is RuleKind.THRESHOLD
        assert rule.source is ValueSource.GAUGE
        assert rule.metric == "magic_process_up"
        assert rule.operator == "=="
        assert [(t.severity, float(t.threshold)) for t in rule.tiers] == [
            ("critical", 0.0)
        ]
        assert rule.for_seconds == 30
        assert rule.window is None

    def test_fr_rul_021_not_silenced_by_no_log_activity(self, source: str) -> None:
        # Magic being down is exactly when logs go quiet.
        assert _rule(source).depends_on_log_activity is False

    def test_fr_hlt_014_down_fires_critical_after_thirty_seconds(
        self, source: str
    ) -> None:
        engine = _engine(_rule(source))
        snap = make_snapshot(now=_T0, gauges=make_gauges(magic_process_up=0.0))
        assert engine.evaluate(snap, _T0) == []
        assert engine.evaluate(snap, _T0 + timedelta(seconds=29)) == []
        fired = engine.evaluate(snap, _T0 + timedelta(seconds=30))
        assert [(a.rule_name, a.severity) for a in fired] == [
            ("ApplicationDown", "critical")
        ]
        assert fired[0].metric_context == {"magic_process_up": 0.0}

    def test_fr_hlt_014_up_never_fires(self, source: str) -> None:
        engine = _engine(_rule(source))
        snap = make_snapshot(now=_T0, gauges=make_gauges(magic_process_up=1.0))
        assert engine.evaluate(snap, _T0) == []
        assert engine.evaluate(snap, _T0 + timedelta(minutes=10)) == []

    def test_fr_met_034_omitted_gauge_is_inactive(self, source: str) -> None:
        engine = _engine(_rule(source))
        snap = make_snapshot(now=_T0, gauges=make_gauges())
        assert engine.evaluate(snap, _T0) == []
        assert engine.evaluate(snap, _T0 + timedelta(minutes=10)) == []


def test_fr_hlt_014_yaml_and_defaults_agree() -> None:
    assert _rule("defaults") == _rule("yaml")
