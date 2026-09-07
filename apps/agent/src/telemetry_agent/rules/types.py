"""RE-01: rule and alert lifecycle types (spec 005 §1-2).

Agent-internal configuration/state types — plain dataclasses, mirroring
metrics/aggregator.py's own split: internal shapes stay agent-only, the
wire-format `AlertEvent` this engine emits lives in telemetry_shared
(telemetry_shared.models.alerts).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class RuleKind(StrEnum):
    """FR-RUL-001: Day-1 supports exactly these five."""

    RATE = "rate"
    THRESHOLD = "threshold"
    LATENCY = "latency"
    ABSENCE = "absence"
    SIGNATURE = "signature"


class ValueSource(StrEnum):
    """Where a rule's observed value is read from in a MetricsSnapshot."""

    COUNTER = "counter"
    GAUGE = "gauge"
    LATENCY_P95 = "latency_p95"
    INDICATOR = "indicator"


class AlertStatus(StrEnum):
    INACTIVE = "inactive"
    PENDING = "pending"
    FIRING = "firing"
    RESOLVING = "resolving"
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class SeverityTier:
    """One (severity, threshold) rung. `FR-RUL-022`: the matched tier is
    whichever, among all tiers whose condition holds, has the most extreme
    threshold — not simply "the first configured".
    """

    severity: str
    threshold: Decimal


@dataclass(frozen=True, slots=True)
class RuleConfig:
    """One named rule (spec 005 §1.1). `tiers` MUST be non-empty and
    ordered least->most severe (`FR-RUL-002`/`003`) — two conditions
    differing only in threshold are one rule with multiple tiers, not two
    separate rules.
    """

    name: str
    kind: RuleKind
    source: ValueSource
    metric: str  # counter/gauge/histogram/indicator field name, per `source`
    operator: str  # one of engine._OPERATORS' keys
    tiers: tuple[SeverityTier, ...]

    window: str | None = None  # None only for gauge-sourced rules
    min_samples: int | None = None  # rate/latency only (FR-RUL-006)
    guard_metric: str | None = None  # absence only: guard_metric > 0 required
    extra_counters: tuple[str, ...] = ()  # threshold: OR'd via sum, e.g. FixSessionDown

    for_seconds: int = 60  # FR-RUL-004 default
    resolve_after_seconds: int = 300  # FR-RUL-004 default
    group_by: tuple[str, ...] = ()  # FR-RUL-005 default: instance-scoped only
    schedule_ref: str | None = None  # FR-RUL-007
    depends_on_log_activity: bool = True  # FR-RUL-021


@dataclass(slots=True)
class Silence:
    """`FR-RUL-018`: suppress notification while still recording state."""

    rule_name: str
    instance_id: str
    starts_at: datetime
    ends_at: datetime
