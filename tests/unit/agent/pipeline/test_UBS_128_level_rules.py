"""UBS-128: a `threshold` rule with `level:` counts only one Application.log
level (`FR-RUL-023`), and the default `AppLogFailure` alerts on `[F]` lines.

Driven through `RuleEvaluator` (the UBS-113 `_Stack`) for the same reason as
UBS-122: picking the per-level snapshot is the evaluator's job and reading the
right group is the engine's.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from telemetry_agent.rules.config_loader import RuleConfigError, load_rules_from_yaml
from telemetry_shared.models.alerts import AlertEvent
from test_UBS_113_evaluator import _INSTANCE, _rule, _Stack


def _seed_app_errors(stack: _Stack, level: str, count: int) -> None:
    stack.aggregator.ingest_agent_counters(
        dims={"instance_id": _INSTANCE, "level": level, "component": "Orders"},
        counters={"app_log_errors": Decimal(count)},
        at=stack.clock.now,
    )


def _summary(alerts: list[AlertEvent]) -> list[tuple[str, str, str]]:
    return [(a.rule_name, a.status, a.severity) for a in alerts]


# --- AppLogFailure (FR-RUL-023, FR-MET-033) -------------------------------


def test_one_failure_line_fires_app_log_failure_with_level_group_by() -> None:
    stack = _Stack((_rule("AppLogFailure"),))
    _seed_app_errors(stack, "F", 1)

    fired = stack.fire()

    assert _summary(fired) == [("AppLogFailure", "firing", "critical")]
    assert fired[0].group_by == {"level": "F"}
    assert fired[0].observed_value == 1.0


def test_error_lines_do_not_fire_the_default_level_rule() -> None:
    stack = _Stack((_rule("AppLogFailure"),))
    _seed_app_errors(stack, "E", 50)

    assert stack.fire() == []


def test_errors_are_still_counted_in_app_log_errors() -> None:
    stack = _Stack((_rule("AppLogFailure"),))
    _seed_app_errors(stack, "E", 3)
    _seed_app_errors(stack, "F", 2)
    stack.fire()

    from telemetry_agent.metrics.snapshot import snapshot

    snap = snapshot(stack.aggregator, "1m", group_by=(), now=stack.clock.now)

    assert snap.groups[0].counters["app_log_errors"] == Decimal(5)


def test_level_rule_is_independent_of_signature_rules() -> None:
    from test_UBS_122_signature_rules import _seed_signature

    stack = _Stack((_rule("AppLogFailure"), _rule("AppOutOfMemory")))
    _seed_signature(stack, "out_of_memory", 1)

    assert _summary(stack.fire()) == [("AppOutOfMemory", "firing", "warning")]


def test_instance_rules_still_evaluate_alongside_level_rules() -> None:
    stack = _Stack((_rule("RejectSpike"), _rule("AppLogFailure")))
    stack.seed(orders_rejected=51)
    _seed_app_errors(stack, "F", 1)

    assert sorted(a.rule_name for a in stack.fire()) == ["AppLogFailure", "RejectSpike"]


# --- rules.yaml validation -------------------------------------------------


_LEVEL_RULE = """
rules:
  - name: Custom
    kind: {kind}
    source: counter
    metric: {metric}
    level: E
    operator: ">="
    tiers:
      - severity: warning
        threshold: 1
    window: 1m
"""


def _write(tmp_path: Path, *, kind: str = "threshold", metric: str) -> Path:
    path = tmp_path / "rules.yaml"
    path.write_text(_LEVEL_RULE.format(kind=kind, metric=metric))
    return path


def test_a_level_rule_loads_with_its_level(tmp_path: Path) -> None:
    (rule,) = load_rules_from_yaml(_write(tmp_path, metric="app_log_lines"))

    assert rule.level == "E"


def test_level_on_a_metric_without_a_level_dimension_fails_load(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path, metric="orders_rejected")

    with pytest.raises(RuleConfigError, match="level"):
        load_rules_from_yaml(path)


def test_level_on_an_unknown_metric_fails_load(tmp_path: Path) -> None:
    with pytest.raises(RuleConfigError, match="level"):
        load_rules_from_yaml(_write(tmp_path, metric="no_such_metric"))


def test_level_on_a_non_threshold_rule_fails_load(tmp_path: Path) -> None:
    path = _write(tmp_path, kind="absence", metric="app_log_lines")

    with pytest.raises(RuleConfigError, match="level"):
        load_rules_from_yaml(path)


def test_level_must_be_one_of_the_closed_level_set(tmp_path: Path) -> None:
    path = _write(tmp_path, metric="app_log_lines")
    path.write_text(path.read_text().replace("level: E", "level: C"))

    with pytest.raises(RuleConfigError, match="level"):
        load_rules_from_yaml(path)
