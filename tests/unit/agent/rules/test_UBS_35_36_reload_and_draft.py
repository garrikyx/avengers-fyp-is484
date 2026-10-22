"""UBS-35: the rules file reloads on change without SIGHUP (so on Windows too),
with its action catalogue, all-or-nothing. UBS-36: `draft` rules are never
evaluated by the running engine."""

import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from rule_fixtures import make_snapshot
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.rules.config_loader import RuleConfigError, SighupRuleReloader
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import (
    AlertStatus,
    RuleConfig,
    RuleKind,
    RuleState,
    SeverityTier,
    ValueSource,
)

_T0 = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)

_RULE = RuleConfig(
    name="TestRule",
    kind=RuleKind.THRESHOLD,
    source=ValueSource.COUNTER,
    metric="widgets_broken",
    operator=">",
    tiers=(SeverityTier(severity="warning", threshold=Decimal(5)),),
    window="1m",
    for_seconds=0,
)


def _rules_yaml(name: str, state: str = "active") -> str:
    return (
        "rules:\n"
        f"  - name: {name}\n"
        "    kind: threshold\n"
        "    source: counter\n"
        "    metric: widgets_broken\n"
        '    operator: ">"\n'
        "    tiers: [{severity: warning, threshold: 5}]\n"
        "    window: 1m\n"
        f"    state: {state}\n"
    )


def _engine(*rules: RuleConfig) -> RuleEngine:
    return RuleEngine(
        rules,
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
    )


def _broken(now: datetime, n: int = 10):  # type: ignore[no-untyped-def]
    return make_snapshot(now=now, window="1m", counters={"widgets_broken": Decimal(n)})


def _touch(path: Path, text: str, bump: int) -> None:
    path.write_text(text, encoding="utf-8")
    stamp = path.stat().st_mtime + bump  # a distinct mtime on any filesystem
    os.utime(path, (stamp, stamp))


# --- UBS-36: draft -----------------------------------------------------------


def test_a_draft_rule_never_fires_in_the_running_engine() -> None:
    engine = _engine(replace(_RULE, state=RuleState.DRAFT))
    for second in range(5):
        now = _T0 + timedelta(seconds=second)
        assert engine.evaluate(_broken(now), now) == []
    assert engine.status_of("TestRule") is None


def test_moving_a_firing_rule_to_draft_resolves_its_alert() -> None:
    engine = _engine(_RULE)
    engine.evaluate(_broken(_T0), _T0)
    (fired,) = engine.evaluate(_broken(_T0), _T0)
    assert fired.status == "firing"

    events = engine.apply_rules((replace(_RULE, state=RuleState.DRAFT),), now=_T0)

    assert [(e.alert_id, e.status) for e in events] == [(fired.alert_id, "resolved")]
    assert events[0].matched_condition == "TestRule moved to draft"
    assert engine.status_of("TestRule") is None


# --- UBS-35: reload with a staged catalogue ----------------------------------


def test_a_rejected_stage_keeps_the_last_known_good_rules(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(_rules_yaml("NewRule"), encoding="utf-8")
    engine = _engine(_RULE)

    def stage(_path: Path):  # type: ignore[no-untyped-def]
        raise RuleConfigError("action 'x' is invalid")

    SighupRuleReloader(engine, path, stage=stage).reload(now=_T0)

    assert [r.name for r in engine.rules] == ["TestRule"]


def test_a_good_reload_commits_the_staged_catalogue_after_the_rules(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(_rules_yaml("NewRule"), encoding="utf-8")
    engine = _engine(_RULE)
    seen: list[list[str]] = []

    def stage(_path: Path):  # type: ignore[no-untyped-def]
        return lambda: seen.append([r.name for r in engine.rules])

    SighupRuleReloader(engine, path, stage=stage).reload(now=_T0)

    assert seen == [["NewRule"]]


def test_changed_on_disk_tracks_the_mtime_last_loaded(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(_rules_yaml("TestRule"), encoding="utf-8")
    reloader = SighupRuleReloader(_engine(_RULE), path)
    assert not reloader.changed_on_disk()

    _touch(path, "rules: [broken", bump=5)
    assert reloader.changed_on_disk()
    reloader.reload(now=_T0)  # rejected, but this version has been seen
    assert not reloader.changed_on_disk()


class _NullPublisher:
    def enqueue_alert(self, alert: object, *, now: object = None) -> None:
        pass


class _Clock:
    def __init__(self) -> None:
        self.now = _T0

    def __call__(self) -> datetime:
        return self.now


def _evaluator(
    engine: RuleEngine, path: Path, *, check_seconds: float
) -> tuple[RuleEvaluator, list[float]]:
    monotonic = [0.0]
    evaluator = RuleEvaluator(
        engine,
        MetricsAggregator(config=AggregatorConfig()),
        AlertRouter(
            _NullPublisher(),  # type: ignore[arg-type]
            agent_id="agent-1",
            application="Magic",
        ),
        instance_id="magic-prod-01",
        reloader=SighupRuleReloader(engine, path),
        reload_check_seconds=check_seconds,
        clock=_Clock(),
        monotonic=lambda: monotonic[0],
    )
    return evaluator, monotonic


def test_editing_the_file_reloads_it_without_a_signal(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(_rules_yaml("TestRule"), encoding="utf-8")
    engine = _engine(_RULE)
    evaluator, monotonic = _evaluator(engine, path, check_seconds=10)
    evaluator.evaluate_once()

    _touch(path, _rules_yaml("EditedRule"), bump=5)
    monotonic[0] = 5.0
    evaluator.evaluate_once()  # not due yet: checks are rate-limited
    assert [r.name for r in engine.rules] == ["TestRule"]

    monotonic[0] = 10.0
    evaluator.evaluate_once()
    assert [r.name for r in engine.rules] == ["EditedRule"]


def test_a_zero_check_interval_leaves_reload_to_sighup(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(_rules_yaml("TestRule"), encoding="utf-8")
    engine = _engine(_RULE)
    evaluator, monotonic = _evaluator(engine, path, check_seconds=0)

    _touch(path, _rules_yaml("EditedRule"), bump=5)
    monotonic[0] = 100.0
    evaluator.evaluate_once()
    assert [r.name for r in engine.rules] == ["TestRule"]

    evaluator.request_reload()
    evaluator.evaluate_once()
    assert [r.name for r in engine.rules] == ["EditedRule"]


def test_an_edit_to_draft_takes_a_rule_out_of_service(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(_rules_yaml("TestRule"), encoding="utf-8")
    engine = _engine(_RULE)
    evaluator, monotonic = _evaluator(engine, path, check_seconds=1)

    _touch(path, _rules_yaml("TestRule", state="draft"), bump=5)
    monotonic[0] = 1.0
    evaluator.evaluate_once()

    (rule,) = engine.rules
    assert rule.state is RuleState.DRAFT
    assert engine.status_of("TestRule") is not AlertStatus.FIRING
