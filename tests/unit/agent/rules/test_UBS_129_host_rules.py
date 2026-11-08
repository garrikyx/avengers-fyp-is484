"""UBS-129: HostDiskFull / HostMemoryHigh (spec 005 §1.2, FR-MET-034).

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
from telemetry_shared.models.alerts import AlertEvent

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_RULES_YAML = Path(__file__).resolve().parents[4] / "config" / "rules.yaml"


def _rules(source: str, name: str) -> RuleConfig:
    rules = DEFAULT_RULES if source == "defaults" else load_rules(_RULES_YAML)
    return next(r for r in rules if r.name == name)


def _evaluate_held(
    rule: RuleConfig, **gauges: float | None
) -> tuple[list[AlertEvent], list[AlertEvent]]:
    """(on first sight, after the `for` hold) for a gauge-only snapshot."""
    engine = RuleEngine(
        rules=(rule,),
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
    )

    snap = make_snapshot(now=_T0, gauges=make_gauges(**gauges))
    first = engine.evaluate(snap, _T0)
    later = engine.evaluate(snap, _T0 + timedelta(seconds=rule.for_seconds))
    return first, later


@pytest.mark.parametrize("source", ["defaults", "yaml"])
class TestHostRules:
    def test_fr_met_034_host_disk_full_shape(self, source: str) -> None:
        rule = _rules(source, "HostDiskFull")
        assert rule.kind is RuleKind.THRESHOLD
        assert rule.source is ValueSource.GAUGE
        assert rule.metric == "host_disk_used_ratio"
        assert rule.operator == ">"
        assert [(t.severity, float(t.threshold)) for t in rule.tiers] == [
            ("warning", 0.85),
            ("critical", 0.95),
        ]
        assert rule.for_seconds == 60
        assert rule.window is None
        assert rule.depends_on_log_activity is False

    def test_fr_met_034_host_memory_high_shape(self, source: str) -> None:
        rule = _rules(source, "HostMemoryHigh")
        assert rule.source is ValueSource.GAUGE
        assert rule.metric == "host_memory_used_ratio"
        assert [(t.severity, float(t.threshold)) for t in rule.tiers] == [
            ("warning", 0.90),
            ("critical", 0.95),
        ]
        assert rule.for_seconds == 120
        assert rule.depends_on_log_activity is False

    def test_fr_met_034_disk_at_0_96_fires_critical_after_the_hold(
        self, source: str
    ) -> None:
        first, later = _evaluate_held(
            _rules(source, "HostDiskFull"), host_disk_used_ratio=0.96
        )
        assert first == []
        assert [(a.rule_name, a.severity) for a in later] == [
            ("HostDiskFull", "critical")
        ]

    def test_fr_rul_016_alert_context_carries_the_gauge_not_a_fabricated_zero(
        self, source: str
    ) -> None:
        _, later = _evaluate_held(
            _rules(source, "HostDiskFull"), host_disk_used_ratio=0.96
        )
        assert later[0].metric_context == {"host_disk_used_ratio": 0.96}
        assert later[0].observed_value == 0.96

    def test_fr_met_034_disk_at_0_90_is_warning_only(self, source: str) -> None:
        _, later = _evaluate_held(
            _rules(source, "HostDiskFull"), host_disk_used_ratio=0.90
        )
        assert [a.severity for a in later] == ["warning"]

    def test_fr_met_034_memory_at_0_96_fires_critical_after_two_minutes(
        self, source: str
    ) -> None:
        first, later = _evaluate_held(
            _rules(source, "HostMemoryHigh"), host_memory_used_ratio=0.96
        )
        assert first == []
        assert [(a.rule_name, a.severity) for a in later] == [
            ("HostMemoryHigh", "critical")
        ]

    def test_fr_met_034_below_threshold_never_fires(self, source: str) -> None:
        _, later = _evaluate_held(
            _rules(source, "HostDiskFull"), host_disk_used_ratio=0.85
        )
        assert later == []

    def test_fr_met_034_omitted_gauge_is_insufficient_data_not_an_alert(
        self, source: str
    ) -> None:
        for name in ("HostDiskFull", "HostMemoryHigh"):
            _, later = _evaluate_held(_rules(source, name))
            assert later == []


def test_fr_met_034_yaml_and_defaults_agree() -> None:
    for name in ("HostDiskFull", "HostMemoryHigh"):
        assert _rules("defaults", name) == _rules("yaml", name)
