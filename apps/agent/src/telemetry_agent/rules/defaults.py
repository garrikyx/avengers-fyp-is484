"""RE-03: the 14 default rules (spec 005 §1.2).

Concrete `RuleConfig` values, not YAML — wiring these to `config/rules.yaml`
(real parsing, `FR-RUL-008` SIGHUP reload) is a separate, existing gap
(`apps/agent/src/telemetry_agent/config.py` is empty for every config file,
not a rules-specific one).

`HighRejectRate`, `AckLatencyBreach`, and `ParseErrorRate`'s tier thresholds
are client-confirmed values, not spec 005's prior "provisional pending Q-5"
placeholders. `PendingOrderTimeout` has no spec or client-given number at
all — 30s is a domain default (typical institutional order-ack SLA; this
gauge measures time-to-first-response, never time-to-fill, so a resting
limit order is never penalized). Rules whose counters aren't wired yet
(`FixSessionDown`, `SeqGapDetected`, `ClockSkew`, `CallbackFailing`,
`BackendUnreachable`) are included for completeness — they read as 0/no-fire
structurally rather than raising, until their producers land.

`depends_on_log_activity=False` (`FR-RUL-021`) is set explicitly on the
self-health rules below (`NoLogActivity` itself, plus the rules that watch
the agent's own pipeline rather than order flow) — everything else keeps
`RuleConfig`'s own default of `True`.
"""

from __future__ import annotations

from decimal import Decimal

from telemetry_agent.rules.types import RuleConfig, RuleKind, SeverityTier, ValueSource


def _tier(severity: str, threshold: float) -> SeverityTier:
    return SeverityTier(severity=severity, threshold=Decimal(str(threshold)))


DEFAULT_RULES: tuple[RuleConfig, ...] = (
    RuleConfig(
        name="HighRejectRate",
        kind=RuleKind.RATE,
        source=ValueSource.INDICATOR,
        metric="reject_rate",
        operator=">",
        tiers=(_tier("warning", 0.03), _tier("critical", 0.05)),
        window="5m",
        min_samples=20,
        for_seconds=120,
        resolve_after_seconds=300,
    ),
    RuleConfig(
        name="RejectSpike",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="orders_rejected",
        operator=">",
        tiers=(_tier("warning", 50),),
        window="1m",
    ),
    RuleConfig(
        name="CancelRejectSpike",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="cancel_rejects",
        operator=">",
        tiers=(_tier("warning", 20),),
        window="5m",
    ),
    RuleConfig(
        name="SessionRejects",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="session_rejects",
        operator=">",
        tiers=(_tier("critical", 5),),
        window="5m",
    ),
    RuleConfig(
        name="PendingOrderTimeout",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.GAUGE,
        metric="oldest_pending_age_seconds",
        operator=">",
        tiers=(_tier("warning", 30),),
        window=None,
    ),
    RuleConfig(
        name="AckLatencyBreach",
        kind=RuleKind.LATENCY,
        source=ValueSource.LATENCY_P95,
        metric="ack_latency_ms",
        operator=">",
        tiers=(_tier("warning", 500), _tier("critical", 1000)),
        window="5m",
        min_samples=50,
    ),
    RuleConfig(
        name="ParseErrorRate",
        kind=RuleKind.RATE,
        source=ValueSource.INDICATOR,
        metric="parse_error_rate",
        operator=">",
        tiers=(_tier("warning", 0.01), _tier("critical", 0.25)),
        window="5m",
        min_samples=20,
        depends_on_log_activity=False,
    ),
    RuleConfig(
        name="NoLogActivity",
        kind=RuleKind.ABSENCE,
        source=ValueSource.COUNTER,
        metric="messages_total",
        operator="==",
        tiers=(_tier("critical", 0),),
        window="1m",
        depends_on_log_activity=False,
    ),
    RuleConfig(
        name="NoExecutions",
        kind=RuleKind.ABSENCE,
        source=ValueSource.COUNTER,
        metric="executions",
        operator="==",
        tiers=(_tier("warning", 0),),
        window="15m",
        guard_metric="orders_submitted",
    ),
    RuleConfig(
        name="FixSessionDown",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="logouts",
        extra_counters=("heartbeat_timeouts",),
        operator=">=",
        tiers=(_tier("critical", 1),),
        window="1m",
        depends_on_log_activity=False,
    ),
    RuleConfig(
        name="SeqGapDetected",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="seq_gaps",
        operator=">",
        tiers=(_tier("warning", 0),),
        window="1m",
        depends_on_log_activity=False,
    ),
    RuleConfig(
        name="ClockSkew",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="clock_skew_events",
        operator=">",
        tiers=(_tier("warning", 10),),
        window="5m",
        depends_on_log_activity=False,
    ),
    RuleConfig(
        name="CallbackFailing",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="callback_failures",
        operator=">",
        tiers=(_tier("warning", 3),),
        window="5m",
        depends_on_log_activity=False,
    ),
    RuleConfig(
        name="BackendUnreachable",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="publish_failures",
        operator=">",
        tiers=(_tier("warning", 5),),
        window="1m",
        depends_on_log_activity=False,
    ),
)
