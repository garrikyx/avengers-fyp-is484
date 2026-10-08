"""UBS-122: signature rules count only their own pattern, and app-log lines
keep `NoLogActivity` quiet.

Driven through `RuleEvaluator` (the UBS-113 `_Stack`), because selecting the
per-signature snapshot is the evaluator's job and reading the right group is
the engine's: testing either half alone would miss the seam between them.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from telemetry_agent.rules.config_loader import RuleConfigError, load_rules_from_yaml
from telemetry_shared.models.alerts import AlertEvent
from test_UBS_113_evaluator import _INSTANCE, _rule, _Stack


def _seed_signature(stack: _Stack, label: str, count: int) -> None:
    stack.aggregator.ingest_agent_counters(
        dims={"instance_id": _INSTANCE, "error_signature": label},
        counters={"app_error_signatures": Decimal(count)},
        at=stack.clock.now,
    )


def _summary(alerts: list[AlertEvent]) -> list[tuple[str, str, str]]:
    return [(a.rule_name, a.status, a.severity) for a in alerts]


# --- signature rules -----------------------------------------------------


def test_a_signature_fires_its_own_rule_with_the_label_as_group_by() -> None:
    stack = _Stack((_rule("AppOutOfMemory"), _rule("AppDbConnectionLost")))
    _seed_signature(stack, "out_of_memory", 1)

    fired = stack.fire()

    assert _summary(fired) == [("AppOutOfMemory", "firing", "warning")]
    assert fired[0].group_by == {"error_signature": "out_of_memory"}
    assert fired[0].observed_value == 1.0


def test_other_signatures_do_not_trip_a_signature_rule() -> None:
    """The bug this closes: the instance-level snapshot sums every signature,
    so ten lost-DB lines used to read as ten out-of-memory matches."""
    stack = _Stack((_rule("AppOutOfMemory"),))
    _seed_signature(stack, "db_connection_lost", 10)
    _seed_signature(stack, "some_other_pattern", 10)

    assert stack.fire() == []


def test_repeated_matches_escalate_to_the_critical_tier() -> None:
    stack = _Stack((_rule("AppOutOfMemory"),))
    _seed_signature(stack, "out_of_memory", 1)
    stack.fire()

    _seed_signature(stack, "out_of_memory", 2)  # 3 in the 1m window
    escalated = stack.tick()

    assert _summary(escalated) == [("AppOutOfMemory", "firing", "critical")]


def test_signature_rules_ignore_ordinary_counters() -> None:
    """Only `app_error_signatures` labelled with the rule's signature counts,
    not any counter that happens to share the instance-level snapshot."""
    stack = _Stack((_rule("AppOutOfMemory"),))
    stack.seed(app_log_errors=50, orders_rejected=50)

    assert stack.fire() == []


def test_instance_rules_still_evaluate_alongside_signature_rules() -> None:
    """The extra grouped snapshot must not hide ordinary rules on the same
    window from their own (ungrouped) snapshot."""
    stack = _Stack((_rule("RejectSpike"), _rule("AppOutOfMemory")))
    stack.seed(orders_rejected=51)
    _seed_signature(stack, "out_of_memory", 1)

    names = sorted(a.rule_name for a in stack.fire())

    assert names == ["AppOutOfMemory", "RejectSpike"]


# --- rules.yaml validation ----------------------------------------------


_SIGNATURE_RULE = """
rules:
  - name: Custom
    kind: {kind}
    source: counter
    metric: app_error_signatures
    {signature}
    operator: ">="
    tiers:
      - severity: warning
        threshold: 1
    window: 1m
"""


def _load(tmp_path: Path, *, kind: str, signature: str) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(_SIGNATURE_RULE.format(kind=kind, signature=signature))
    load_rules_from_yaml(path)


def test_a_signature_rule_loads_with_its_label(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(
        _SIGNATURE_RULE.format(kind="signature", signature="signature: oom")
    )

    (rule,) = load_rules_from_yaml(path)

    assert rule.signature == "oom"


def test_a_signature_rule_without_a_label_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(RuleConfigError, match="Custom"):
        _load(tmp_path, kind="signature", signature="")


def test_a_label_on_a_non_signature_rule_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(RuleConfigError, match="Custom"):
        _load(tmp_path, kind="threshold", signature="signature: oom")


# --- NoLogActivity counts app-log lines ------------------------------------


def test_app_log_lines_alone_keep_no_log_activity_quiet() -> None:
    """A quiet FIX session with a busy Application.log is a live pipeline."""
    stack = _Stack((_rule("NoLogActivity"),))
    stack.seed(app_log_lines=5)

    assert stack.fire() == []


def test_no_log_activity_still_fires_when_both_logs_are_silent() -> None:
    stack = _Stack((_rule("NoLogActivity"),))

    fired = stack.fire()

    assert _summary(fired) == [("NoLogActivity", "firing", "critical")]
    assert "messages_total + app_log_lines" in fired[0].matched_condition
