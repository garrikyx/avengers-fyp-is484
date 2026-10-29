"""D2 anomaly rules (UBS-25/26/28/29): rolling-baseline comparison.

An `anomaly` rule (`RuleKind.ANOMALY`) compares the metric's value over its
window (e.g. the last 5m) with a baseline learned from earlier windows, and
reports the relative deviation `(current - baseline) / baseline`. Everything
after that — tiers, `for`/resolve hysteresis, silences, callbacks, backend
publishing — is the existing Rule Engine lifecycle, which sees the deviation
as the rule's observed value (so tier thresholds are deviations: `0.5` = +50%,
i.e. 1.5x baseline).

Baseline construction (`BaselineTracker`):

- One sample is taken per closed window (every `window` seconds, so samples
  never overlap each other) and sits as *pending* for one more window before
  it joins the history. That delay is what keeps the baseline strictly older
  than the window being judged; without it, a spike would be part of its own
  baseline within seconds.
- A window is dropped if the rule was anomalous at any tick inside it (not
  only at the tick that samples it), so an incident, and the tail of one still
  in the rolling window, does not teach the baseline that incidents are
  normal. History expiry never leaves fewer than `MIN_BASELINE_WINDOWS`
  samples, so a long incident keeps being judged against the last good
  baseline instead of auto-resolving. Trade-off: a permanent level shift keeps
  alerting until the operator re-baselines (restart, or reload with a changed
  window or baseline length). A slow ramp that stays under the lowest tier is
  never anomalous, so it can still creep into the baseline.
- Ratios are pooled (sum of numerators / sum of denominators), never an
  average of per-window ratios — the same rule `telemetry_shared.metrics.ratios`
  applies. Latency uses the median of the per-window p95s.
- No baseline means no reading (never a fabricated zero, `FR-HLT-004`'s spirit):
  fewer than `MIN_BASELINE_WINDOWS` samples, fewer than `baseline_min_samples`
  pooled denominator events, or a baseline of exactly 0 (a relative deviation
  from zero is undefined; the fixed-threshold rules own that case). While the
  baseline is untrusted the windows seen are still learned from, so the first
  baseline is whatever the first windows looked like.
"""

from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from telemetry_agent.rules.types import RuleConfig
from telemetry_shared.metrics.ratios import STANDARD_RATIOS
from telemetry_shared.models.metrics import MetricsGroup, MetricsSnapshot

# A baseline built from one or two windows is mostly noise.
MIN_BASELINE_WINDOWS = 3


@dataclass(frozen=True, slots=True)
class AnomalyMetric:
    """What an `anomaly` rule's `metric` name means in counter terms."""

    name: str
    label: str  # sentence-case noun phrase used in the explanation
    kind: Literal["ratio", "latency"]
    numerators: tuple[str, ...] = ()
    denominators: tuple[str, ...] = ()
    histogram: str | None = None


def _standard(name: str, label: str, *, standard: str | None = None) -> AnomalyMetric:
    """An anomaly metric whose formula is one of spec 004 §4.5's ratios, so a
    change to `STANDARD_RATIOS` carries through (`standard` when the anomaly
    metric is named differently)."""
    ratio = next(r for r in STANDARD_RATIOS if r.name == (standard or name))
    return AnomalyMetric(
        name=name,
        label=label,
        kind="ratio",
        numerators=(ratio.numerator,),
        denominators=ratio.denominator,
    )


ANOMALY_METRICS: dict[str, AnomalyMetric] = {
    # UBS-25: spec 004 §4.5's reject_rate, unchanged.
    "reject_rate": _standard("reject_rate", "reject rate"),
    # UBS-29: parser_failures / messages_processed is the parser's
    # `parse_errors / log_lines_read` (spec 004 §4.5 `parse_error_rate`).
    "parser_failure_rate": _standard(
        "parser_failure_rate", "parser failure rate", standard="parse_error_rate"
    ),
    # UBS-28: spec 004 defines no execution-issue counters, so this is the
    # project's working definition: order actions that did not execute
    # normally (rejected order, rejected cancel/replace, expired order) over
    # the order actions sent to the venue. Confirm with the sponsor.
    "execution_issue_rate": AnomalyMetric(
        name="execution_issue_rate",
        label="execution issue rate",
        kind="ratio",
        numerators=("orders_rejected", "cancel_rejects", "orders_expired"),
        denominators=("orders_submitted", "orders_cancel_requested", "orders_replaced"),
    ),
    # UBS-26: the p95 of ack latency, compared with the p95 baseline.
    "ack_latency_ms": AnomalyMetric(
        name="ack_latency_ms",
        label="processing latency",
        kind="latency",
        histogram="ack_latency_ms",
    ),
}


@dataclass(frozen=True, slots=True)
class AnomalyReading:
    """One evaluation of an anomaly rule: the numbers behind the alert."""

    metric: AnomalyMetric
    current: Decimal
    baseline: Decimal
    deviation: Decimal  # (current - baseline) / baseline; +1.0 means +100%
    baseline_windows: int
    baseline_events: int
    window_seconds: int
    # What to record for this window once the engine knows if it was anomalous.
    sample: _Sample = field(repr=False)

    def explain(self, *, instance_id: str) -> str:
        """The ticket's explanation, e.g. "Abnormal reject rate detected on
        magic-prod-01. Reject rate is 1.8% compared with its 0.6% baseline
        (+200%) over the last 5 minutes"."""
        label = self.metric.label
        return (
            f"Abnormal {label} detected on {instance_id}. "
            f"{label.capitalize()} is {self._format(self.current)} compared with "
            f"its {self._format(self.baseline)} baseline "
            f"({self.deviation * 100:+.0f}%) over the last "
            f"{_minutes(self.window_seconds)}"
        )

    def _format(self, value: Decimal) -> str:
        if self.metric.kind == "latency":
            return f"{value:.0f}ms"
        return _percent(value * 100)

    def context(self) -> dict[str, float | int | str]:
        """Allowlisted numbers for `AlertEvent.metric_context` (FR-RUL-016)."""
        return {
            "current": float(self.current),
            "baseline": float(self.baseline),
            "deviation_pct": float(self.deviation * 100),
            "baseline_windows": self.baseline_windows,
            "baseline_events": self.baseline_events,
        }


def _percent(value: Decimal) -> str:
    if value >= 10:
        return f"{value:.0f}%"
    if value >= 1:
        return f"{value:.1f}%"
    return f"{float(value):.2g}%"


def _minutes(seconds: int) -> str:
    if seconds % 60 != 0:
        return f"{seconds} seconds"
    minutes = seconds // 60
    return "minute" if minutes == 1 else f"{minutes} minutes"


@dataclass(frozen=True, slots=True)
class _Sample:
    at: datetime
    value: Decimal  # ratio: numerator sum; latency: the window's p95
    weight: Decimal  # ratio: denominator sum; latency: observation count


@dataclass(slots=True)
class _RuleBaseline:
    shape: tuple[str, int, int | None]
    history: deque[_Sample] = field(default_factory=deque)
    pending: _Sample | None = None
    last_anomalous_at: datetime | None = None


def _sum(group: MetricsGroup, names: tuple[str, ...]) -> Decimal:
    return sum((group.counters.get(n, Decimal(0)) for n in names), Decimal(0))


def _current_sample(
    rule: RuleConfig, metric: AnomalyMetric, group: MetricsGroup, now: datetime
) -> _Sample | None:
    """This window's sample, or None when it is too thin to judge
    (`min_samples`, the same bar the fixed rules use for their own reads)."""
    if metric.kind == "latency":
        assert metric.histogram is not None
        summary = group.latency.get(metric.histogram)
        if summary is None or summary.p95 is None:
            return None
        if rule.min_samples is not None and summary.count < rule.min_samples:
            return None
        return _Sample(now, Decimal(str(summary.p95)), Decimal(summary.count))
    denominator = _sum(group, metric.denominators)
    if denominator <= 0:
        return None
    if rule.min_samples is not None and denominator < rule.min_samples:
        return None
    return _Sample(now, _sum(group, metric.numerators), denominator)


def _current_value(metric: AnomalyMetric, sample: _Sample) -> Decimal:
    return sample.value if metric.kind == "latency" else sample.value / sample.weight


def _baseline_value(metric: AnomalyMetric, history: deque[_Sample]) -> Decimal | None:
    if metric.kind == "latency":
        return Decimal(str(statistics.median(float(s.value) for s in history)))
    total = sum((s.weight for s in history), Decimal(0))
    return sum((s.value for s in history), Decimal(0)) / total if total else None


def validate_anomaly_rule(rule: RuleConfig) -> int:
    """The rule's `baseline_seconds`; raises `ValueError` at construction time
    rather than mid-evaluation if an anomaly rule cannot be evaluated."""
    if rule.metric not in ANOMALY_METRICS:
        raise ValueError(
            f"anomaly rule {rule.name!r}: unknown metric {rule.metric!r}, "
            f"expected one of {sorted(ANOMALY_METRICS)}"
        )
    if rule.baseline_seconds is None or rule.window is None:
        raise ValueError(
            f"anomaly rule {rule.name!r} needs `window` and `baseline_seconds`"
        )
    return rule.baseline_seconds


class BaselineTracker:
    """Per-rule baseline state for the Rule Engine. Not thread-safe; the
    engine is driven from one evaluation loop."""

    def __init__(self, *, started_at: datetime) -> None:
        self._started_at = started_at
        self._rules: dict[str, _RuleBaseline] = {}

    def assess(
        self, rule: RuleConfig, snapshot: MetricsSnapshot, now: datetime
    ) -> AnomalyReading | None:
        """The reading for `rule` against `snapshot`, or None if there is not
        yet enough current or baseline data to judge. Call `settle()` with the
        outcome afterwards so the window can join the baseline."""
        baseline_seconds = validate_anomaly_rule(rule)
        metric = ANOMALY_METRICS[rule.metric]
        window_seconds = _window_seconds(snapshot)
        state = self._state(rule, window_seconds)
        self._promote(state, now, window_seconds, baseline_seconds)

        if not snapshot.groups:
            return None
        sample = _current_sample(rule, metric, snapshot.groups[0], now)
        if sample is None:
            return None

        # An agent younger than the window has a part-filled window; its
        # ratio is not comparable with a full-window baseline.
        warm = (now - self._started_at).total_seconds() >= window_seconds
        baseline = (
            _baseline_value(metric, state.history)
            if warm and len(state.history) >= MIN_BASELINE_WINDOWS
            else None
        )
        events = int(sum((s.weight for s in state.history), Decimal(0)))
        if baseline is None or baseline == 0 or events < rule.baseline_min_samples:
            self._offer(state, sample, now, window_seconds, warm=warm, anomalous=False)
            return None

        current = _current_value(metric, sample)
        return AnomalyReading(
            metric=metric,
            current=current,
            baseline=baseline,
            deviation=(current - baseline) / baseline,
            baseline_windows=len(state.history),
            baseline_events=events,
            window_seconds=window_seconds,
            sample=sample,
        )

    def settle(
        self,
        rule: RuleConfig,
        reading: AnomalyReading,
        now: datetime,
        *,
        anomalous: bool,
    ) -> None:
        """Offer this window to the baseline unless it was anomalous."""
        state = self._rules.get(rule.name)
        if state is None:
            return
        if anomalous:
            state.last_anomalous_at = now
        self._offer(
            state,
            reading.sample,
            now,
            reading.window_seconds,
            warm=True,
            anomalous=anomalous,
        )

    def retain(self, names: set[str]) -> None:
        """Forget rules that were removed or moved to draft."""
        for name in set(self._rules) - names:
            del self._rules[name]

    def _state(self, rule: RuleConfig, window_seconds: int) -> _RuleBaseline:
        shape = (rule.metric, window_seconds, rule.baseline_seconds)
        state = self._rules.get(rule.name)
        if state is None or state.shape != shape:
            # A reloaded rule with a different metric/window measures
            # something else; its old samples would be wrong, not just stale.
            state = _RuleBaseline(shape=shape)
            self._rules[rule.name] = state
        return state

    @staticmethod
    def _promote(
        state: _RuleBaseline, now: datetime, window_seconds: int, baseline_seconds: int
    ) -> None:
        pending = state.pending
        if pending is not None and (now - pending.at).total_seconds() >= window_seconds:
            state.history.append(pending)
            state.pending = None
        horizon = now - timedelta(seconds=baseline_seconds)
        # Never expire below the minimum: a long incident adds no samples, and
        # an emptied history would end the alert while the problem persists.
        while (
            len(state.history) > MIN_BASELINE_WINDOWS and state.history[0].at < horizon
        ):
            state.history.popleft()

    @staticmethod
    def _offer(
        state: _RuleBaseline,
        sample: _Sample,
        now: datetime,
        window_seconds: int,
        *,
        warm: bool,
        anomalous: bool,
    ) -> None:
        # One pending sample at a time: it is the window that closed at its
        # own timestamp, and the next is not taken until it has been promoted.
        if anomalous or not warm or state.pending is not None:
            return
        last = state.last_anomalous_at
        if last is not None and (now - last).total_seconds() < window_seconds:
            return  # this rolling window still holds part of the anomaly
        state.pending = _Sample(now, sample.value, sample.weight)


def _window_seconds(snapshot: MetricsSnapshot) -> int:
    bounds = snapshot.window_bounds
    return round((bounds.to_utc - bounds.from_utc).total_seconds())
