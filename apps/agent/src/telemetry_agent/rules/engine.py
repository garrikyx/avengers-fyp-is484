"""RE-02: rule evaluation and the alert lifecycle FSM (spec 005 §1-4).

Pure consumer of `telemetry_shared.models.metrics.MetricsSnapshot` (MA-04) —
the engine never touches `MetricsAggregator`/`LatencyCorrelator` directly,
so it is testable purely from hand-built snapshot fixtures. Assumes the
snapshot was built with `group_by=()` (single-instance semantics — CLAUDE.md:
"One Magic instance has one Telemetry Agent deployed alongside it"), so
`snapshot.groups[0]` (if present) is the whole instance's data for this tick.

Callback dispatch (spec 005 §3) is out of scope — `evaluate()` returns the
`AlertEvent`s that changed or were re-notified this tick; wiring those to a
`CallbackSink` is a separate, later piece.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from telemetry_agent.rules.types import (
    AlertStatus,
    RuleConfig,
    RuleKind,
    SeverityTier,
    Silence,
    ValueSource,
)
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.metrics import MetricsGroup, MetricsSnapshot

_OPERATORS: dict[str, Callable[[Decimal, Decimal], bool]] = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}

_ALERT_STORM_RULE_NAME = "AlertStorm"


class ScheduleChecker(Protocol):
    """`FR-RUL-007` seam — real trading-calendar logic (spec 010 §5) is
    separate, unbuilt scope. Default `AlwaysActive` never gates a rule.
    """

    def is_active(self, schedule_ref: str, instance_id: str, now: datetime) -> bool: ...


class AlwaysActive:
    def is_active(self, schedule_ref: str, instance_id: str, now: datetime) -> bool:
        return True


@dataclass(slots=True)
class _AlertState:
    alert_id: str
    status: AlertStatus
    severity: str
    condition_since: datetime
    first_observed_utc: datetime
    last_observed_utc: datetime
    last_notified_at: datetime | None = None
    notification_count: int = 0


def _decimal_or_none(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _read_indicator(rule: RuleConfig, group: MetricsGroup | None) -> Decimal | None:
    """Sufficiency is recomputed from `denominator` against *this rule's*
    `min_samples` — deliberately not trusting `indicator.low_confidence`,
    which reflects MA-04's own default threshold (20) and would be wrong
    for a rule wanting a different bar (see `_read_latency`, which wants 50).
    """
    if group is None:
        return None
    indicator = getattr(group.indicators, rule.metric)
    if indicator.value is None:
        return None
    if rule.min_samples is not None and indicator.denominator < rule.min_samples:
        return None
    return _decimal_or_none(indicator.value)


def _read_latency(rule: RuleConfig, group: MetricsGroup | None) -> Decimal | None:
    """Sufficiency uses `summary.count` directly, not whether `p95` happens
    to be null — MA-04 nulls percentiles below its own default (20), but
    `AckLatencyBreach` wants 50; a count of 30 must still read insufficient
    here even though `p95` is a real, non-null number in the snapshot.
    """
    if group is None:
        return None
    summary = group.latency.get(rule.metric)
    if summary is None:
        return None
    if rule.min_samples is not None and summary.count < rule.min_samples:
        return None
    return _decimal_or_none(summary.p95)


def _read_counter_sum(rule: RuleConfig, group: MetricsGroup | None) -> Decimal:
    if group is None:
        return Decimal(0)
    total = group.counters.get(rule.metric, Decimal(0))
    for extra in rule.extra_counters:
        total += group.counters.get(extra, Decimal(0))
    return total


def _read_gauge(rule: RuleConfig, snapshot: MetricsSnapshot) -> Decimal | None:
    value = getattr(snapshot.gauges, rule.metric)
    return _decimal_or_none(value)


def _read_absence(rule: RuleConfig, group: MetricsGroup | None) -> Decimal | None:
    if rule.guard_metric is not None:
        guard_value = (
            group.counters.get(rule.guard_metric, Decimal(0)) if group else Decimal(0)
        )
        if guard_value <= 0:
            # Guard unmet: rule doesn't apply this tick, not "insufficient data".
            return None
    return _read_counter_sum(rule, group)


def _read_observed(rule: RuleConfig, snapshot: MetricsSnapshot) -> Decimal | None:
    group = snapshot.groups[0] if snapshot.groups else None
    if rule.kind is RuleKind.RATE:
        return _read_indicator(rule, group)
    if rule.kind is RuleKind.LATENCY:
        return _read_latency(rule, group)
    if rule.kind is RuleKind.ABSENCE:
        return _read_absence(rule, group)
    if rule.source is ValueSource.GAUGE:
        return _read_gauge(rule, snapshot)
    return _read_counter_sum(rule, group)  # THRESHOLD / SIGNATURE via counter


def _matched_tier(
    observed: Decimal | None, tiers: Sequence[SeverityTier], operator: str
) -> SeverityTier | None:
    """Highest tier whose condition holds — not the first configured.
    Correct for the monotonic operators (`>`/`>=`) every multi-tier rule
    uses today, since `tiers` is ordered least->most severe and a higher
    observed value that clears a stricter threshold also clears every
    looser one before it.
    """
    if observed is None:
        return None
    compare = _OPERATORS[operator]
    matched: SeverityTier | None = None
    for tier in tiers:
        if compare(observed, tier.threshold):
            matched = tier
    return matched


def _matched_condition(rule: RuleConfig, tier: SeverityTier, observed: Decimal) -> str:
    window_part = f" over {rule.window}" if rule.window else ""
    condition = f"{rule.metric} {rule.operator} {tier.threshold}{window_part}"
    return f"{condition} (observed {observed})"


def _metric_context(
    rule: RuleConfig, snapshot: MetricsSnapshot
) -> dict[str, float | int | str]:
    """`FR-RUL-016`: allowlisted snapshot fields only, capped at 10 entries."""
    group = snapshot.groups[0] if snapshot.groups else None
    context: dict[str, float | int | str] = {}
    if group is None:
        return context
    if rule.kind is RuleKind.RATE:
        indicator = getattr(group.indicators, rule.metric)
        context["denominator"] = indicator.denominator
    elif rule.kind is RuleKind.LATENCY:
        summary = group.latency.get(rule.metric)
        if summary is not None:
            context["count"] = summary.count
            if summary.avg is not None:
                context["avg"] = summary.avg
    else:
        context[rule.metric] = float(group.counters.get(rule.metric, Decimal(0)))
        for extra in rule.extra_counters:
            if len(context) >= 10:
                break
            context[extra] = float(group.counters.get(extra, Decimal(0)))
    return dict(list(context.items())[:10])


class RuleEngine:
    def __init__(
        self,
        rules: Sequence[RuleConfig],
        *,
        instance_id: str,
        application: str,
        agent_id: str,
        started_at: datetime,
        startup_grace_seconds: int = 60,
        renotify_interval_seconds: int = 1800,
        max_active_alerts: int = 100,
        schedule_checker: ScheduleChecker | None = None,
    ) -> None:
        self._rules = tuple(rules)
        self._instance_id = instance_id
        self._application = application
        self._agent_id = agent_id
        self._started_at = started_at
        self._startup_grace_seconds = startup_grace_seconds
        self._renotify_interval_seconds = renotify_interval_seconds
        self._max_active_alerts = max_active_alerts
        self._schedule_checker: ScheduleChecker = schedule_checker or AlwaysActive()
        self._states: dict[str, _AlertState] = {}
        self._silences: list[Silence] = []
        self._storm_active = False

    def add_silence(self, silence: Silence) -> None:
        self._silences.append(silence)

    def active_alert_count(self) -> int:
        """`FR-RUL-017`'s "active alert output" — firing/resolving alerts
        that have actually been notified, not `pending` internal bookkeeping
        for a condition that hasn't cleared its `for` delay yet.
        """
        return sum(
            1
            for state in self._states.values()
            if state.status in (AlertStatus.FIRING, AlertStatus.RESOLVING)
        )

    def status_of(self, rule_name: str) -> AlertStatus | None:
        """Current lifecycle status for one rule, or `None` if untracked
        (`inactive`). Read-only introspection, e.g. for a future health/debug
        surface — not used internally by `evaluate()` itself.
        """
        state = self._states.get(self._dedup_key(rule_name))
        return state.status if state is not None else None

    def _dedup_key(self, rule_name: str) -> str:
        return f"{rule_name}::{self._instance_id}"

    def _is_firing(self, rule_name: str) -> bool:
        state = self._states.get(self._dedup_key(rule_name))
        return state is not None and state.status is AlertStatus.FIRING

    def _is_silenced(self, rule_name: str, now: datetime) -> bool:
        return any(
            silence.rule_name == rule_name
            and silence.instance_id == self._instance_id
            and silence.starts_at <= now <= silence.ends_at
            for silence in self._silences
        )

    def evaluate(self, snapshot: MetricsSnapshot, now: datetime) -> list[AlertEvent]:
        """One `MetricsSnapshot` is built for one window (spec 004 §4's
        default windows: 1m/5m/15m), but `DEFAULT_RULES` spans all three.
        The caller is expected to call `evaluate()` once per window needed
        across the configured rules (e.g. once with a "1m" snapshot, once
        with "5m"); this only evaluates the rules matching that window.
        Gauge-sourced rules (`rule.window is None`) are window-independent
        (MA-04's gauges don't vary by window) and are evaluated on every
        call safely — re-evaluating one with an unchanged gauge and `now`
        a moment later is idempotent, not a double-fire.
        """
        if (now - self._started_at).total_seconds() < self._startup_grace_seconds:
            return []  # FR-RUL-019: cold start never pages anyone

        log_activity_firing = self._is_firing("NoLogActivity")
        changed: list[AlertEvent] = []

        for rule in self._rules:
            if rule.window is not None and rule.window != snapshot.window:
                continue
            if rule.schedule_ref is not None and not self._schedule_checker.is_active(
                rule.schedule_ref, self._instance_id, now
            ):
                continue  # FR-RUL-007: not evaluated at all while off-schedule

            if (
                rule.depends_on_log_activity
                and log_activity_firing
                and rule.name != "NoLogActivity"
            ):
                observed = None  # FR-RUL-021: absence of data isn't absence of rejects
            else:
                observed = _read_observed(rule, snapshot)

            tier = _matched_tier(observed, rule.tiers, rule.operator)
            alert = self._transition(rule, tier, observed, snapshot, now)
            if alert is not None:
                changed.append(alert)

        return changed

    def _transition(
        self,
        rule: RuleConfig,
        tier: SeverityTier | None,
        observed: Decimal | None,
        snapshot: MetricsSnapshot,
        now: datetime,
    ) -> AlertEvent | None:
        key = self._dedup_key(rule.name)
        state = self._states.get(key)

        if state is None:
            if tier is None:
                return None
            self._states[key] = _AlertState(
                alert_id=str(uuid.uuid4()),
                status=AlertStatus.PENDING,
                severity=tier.severity,
                condition_since=now,
                first_observed_utc=now,
                last_observed_utc=now,
            )
            return None  # only pending->firing emits (FR-RUL-012)

        if state.status is AlertStatus.PENDING:
            if tier is None:
                del self._states[key]
                return None
            state.severity = tier.severity
            state.last_observed_utc = now
            if (now - state.condition_since).total_seconds() < rule.for_seconds:
                return None
            return self._fire(rule, state, tier, observed, snapshot, now)

        if state.status is AlertStatus.FIRING:
            if tier is None:
                state.status = AlertStatus.RESOLVING
                state.condition_since = now
                return None
            state.last_observed_utc = now
            if tier.severity != state.severity:
                # FR-RUL-022: severity change while firing notifies immediately,
                # independent of renotifyInterval, same alertId.
                state.severity = tier.severity
                state.notification_count += 1
                state.last_notified_at = now
                return self._build_event(rule, state, tier, observed, snapshot, now)
            if (
                self._renotify_interval_seconds > 0
                and state.last_notified_at is not None
                and (now - state.last_notified_at).total_seconds()
                >= self._renotify_interval_seconds
            ):
                state.notification_count += 1
                state.last_notified_at = now
                return self._build_event(rule, state, tier, observed, snapshot, now)
            return None

        if state.status is AlertStatus.RESOLVING:
            if tier is not None:
                state.status = AlertStatus.FIRING
                state.severity = tier.severity
                state.last_observed_utc = now
                return None  # "condition true again -> firing, no new notification"
            elapsed = (now - state.condition_since).total_seconds()
            if elapsed < rule.resolve_after_seconds:
                return None
            event = self._build_event(
                rule, state, None, observed, snapshot, now, status=AlertStatus.RESOLVED
            )
            del self._states[key]  # frees the key: alertId rotates next occurrence
            return event

        return None  # RESOLVED is transient within one tick; never stored as a status

    def _fire(
        self,
        rule: RuleConfig,
        state: _AlertState,
        tier: SeverityTier,
        observed: Decimal | None,
        snapshot: MetricsSnapshot,
        now: datetime,
    ) -> AlertEvent | None:
        if self.active_alert_count() >= self._max_active_alerts:
            # FR-RUL-017: suppress every new pending->firing transition past the
            # cap (this rule's own state stays PENDING and is retried next tick,
            # so it fires normally once the cap clears) — emit the AlertStorm
            # meta-alert only once, on the tick the cap is first breached.
            storm_just_started = not self._storm_active
            self._storm_active = True
            if storm_just_started:
                return AlertEvent(
                    alert_id=str(uuid.uuid4()),
                    rule_name=_ALERT_STORM_RULE_NAME,
                    severity="critical",
                    status=AlertStatus.FIRING.value,
                    application=self._application,
                    instance_id=self._instance_id,
                    agent_id=self._agent_id,
                    matched_condition=f"active alerts >= {self._max_active_alerts}",
                    observed_value=float(self.active_alert_count()),
                    threshold=float(self._max_active_alerts),
                    first_observed_utc=now,
                    last_observed_utc=now,
                    notification_count=1,
                )
            return None
        self._storm_active = False
        state.status = AlertStatus.FIRING
        state.severity = tier.severity
        state.notification_count = 1
        state.last_notified_at = now
        return self._build_event(rule, state, tier, observed, snapshot, now)

    def _build_event(
        self,
        rule: RuleConfig,
        state: _AlertState,
        tier: SeverityTier | None,
        observed: Decimal | None,
        snapshot: MetricsSnapshot,
        now: datetime,
        *,
        status: AlertStatus | None = None,
    ) -> AlertEvent | None:
        effective_status = status or state.status
        group = snapshot.groups[0] if snapshot.groups else None
        event = AlertEvent(
            alert_id=state.alert_id,
            rule_name=rule.name,
            severity=state.severity,
            status=effective_status.value,
            application=self._application,
            instance_id=self._instance_id,
            agent_id=self._agent_id,
            matched_condition=(
                _matched_condition(rule, tier, observed)
                if tier is not None and observed is not None
                else f"{rule.name} resolved"
            ),
            observed_value=float(observed) if observed is not None else None,
            threshold=float(tier.threshold) if tier is not None else 0.0,
            first_observed_utc=state.first_observed_utc,
            last_observed_utc=now,
            resolved_at_utc=now if effective_status is AlertStatus.RESOLVED else None,
            group_by=dict(group.dimensions) if group is not None else {},
            metric_context=_metric_context(rule, snapshot),
            notification_count=state.notification_count,
        )
        if self._is_silenced(rule.name, now):
            # FR-RUL-018: state already updated above, notification suppressed.
            return None
        return event
