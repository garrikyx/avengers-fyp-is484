"""RE-05: `config/rules.yaml` loading (`FR-RUL-008`/`009`)."""

from decimal import Decimal
from pathlib import Path

import pytest
from telemetry_agent.rules.config_loader import (
    RuleConfigError,
    _parse_duration_seconds,
    load_rules,
    load_rules_from_yaml,
)
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.types import RuleConfig, RuleKind, SeverityTier, ValueSource

_VALID_YAML = """
rules:
  - name: HighRejectRate
    kind: rate
    source: indicator
    metric: reject_rate
    operator: ">"
    tiers:
      - severity: warning
        threshold: 0.03
      - severity: critical
        threshold: 0.05
    window: 5m
    minSamples: 20
    for: 2m
    resolveAfter: 5m
"""

_EXPECTED_HIGH_REJECT_RATE = RuleConfig(
    name="HighRejectRate",
    kind=RuleKind.RATE,
    source=ValueSource.INDICATOR,
    metric="reject_rate",
    operator=">",
    tiers=(
        SeverityTier(severity="warning", threshold=Decimal("0.03")),
        SeverityTier(severity="critical", threshold=Decimal("0.05")),
    ),
    window="5m",
    min_samples=20,
    for_seconds=120,
    resolve_after_seconds=300,
)


def test_valid_yaml_round_trips_to_equivalent_rule_config(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(_VALID_YAML)
    rules = load_rules_from_yaml(path)
    assert rules == (_EXPECTED_HIGH_REJECT_RATE,)


def test_missing_file_falls_back_to_default_rules(tmp_path: Path) -> None:
    path = tmp_path / "does-not-exist.yaml"
    assert load_rules(path) == DEFAULT_RULES


def test_real_rules_yaml_matches_default_rules_one_for_one() -> None:
    """The live config/rules.yaml is a hand-kept transcription of
    DEFAULT_RULES — this catches drift between the two.
    """
    repo_root = Path(__file__).resolve().parents[4]
    loaded = load_rules_from_yaml(repo_root / "config" / "rules.yaml")
    assert loaded == DEFAULT_RULES


@pytest.mark.parametrize(
    "bad_yaml,expected_message_part",
    [
        (
            """
rules:
  - name: BadKind
    kind: not-a-real-kind
    source: counter
    metric: x
    operator: ">"
    tiers: [{severity: warning, threshold: 1}]
""",
            "BadKind",
        ),
        (
            """
rules:
  - name: BadOperator
    kind: threshold
    source: counter
    metric: x
    operator: "!!"
    tiers: [{severity: warning, threshold: 1}]
""",
            "BadOperator",
        ),
        (
            """
rules:
  - name: EmptyTiers
    kind: threshold
    source: counter
    metric: x
    operator: ">"
    tiers: []
""",
            "EmptyTiers",
        ),
        (
            """
rules:
  - name: UnknownField
    kind: threshold
    source: counter
    metric: x
    operator: ">"
    tiers: [{severity: warning, threshold: 1}]
    notARealField: true
""",
            "UnknownField",
        ),
        (
            """
rules: []
""",
            "no rules defined",
        ),
    ],
)
def test_malformed_rule_raises_naming_the_rule(
    tmp_path: Path, bad_yaml: str, expected_message_part: str
) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(bad_yaml)
    with pytest.raises(RuleConfigError, match=expected_message_part):
        load_rules_from_yaml(path)


def test_duplicate_rule_name_raises(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(
        """
rules:
  - name: Dup
    kind: threshold
    source: counter
    metric: x
    operator: ">"
    tiers: [{severity: warning, threshold: 1}]
  - name: Dup
    kind: threshold
    source: counter
    metric: y
    operator: ">"
    tiers: [{severity: warning, threshold: 1}]
"""
    )
    with pytest.raises(RuleConfigError, match="Dup"):
        load_rules_from_yaml(path)


def test_existing_but_malformed_file_never_falls_back_to_defaults(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text("rules: []")
    with pytest.raises(RuleConfigError):
        load_rules(path)


@pytest.mark.parametrize(
    "text,expected_seconds",
    [("30s", 30), ("2m", 120), ("1h", 3600), ("300s", 300)],
)
def test_parse_duration_seconds(text: str, expected_seconds: int) -> None:
    assert _parse_duration_seconds(text) == expected_seconds


def test_parse_duration_seconds_rejects_bad_format() -> None:
    with pytest.raises(RuleConfigError):
        _parse_duration_seconds("five minutes")
