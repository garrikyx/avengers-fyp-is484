"""UBS-36: test mode. Replays log files through one rule without dispatching.

    uv run telemetry-agent --config config/agent.yaml \\
        --test-rule HighRejectRate --replay logs/Fix.log [logs/Application.log]

The replay uses the agent's own pieces, so the result is what the running
agent would have done with those lines:

    each line -> the configured parsers -> MetricsIngestor (UBS-112)
              -> RuleEvaluator.evaluate_once every pipeline.evaluationInterval
                 (UBS-113) -> a RuleEngine holding only the candidate rule

The clock is simulated. Each line is stamped with its own timestamp: FIX
SendingTime, else a leading `YYYY-MM-DD HH:MM:SS` (as the simulator writes),
else an Application.log time of day, dated from the first dated line or
`replay_date`. Times are read as UTC, so files written in different zones
would merge skewed. Evaluation ticks are interleaved at
those times, so a 2-hour log replays in seconds with the same windows,
`for:` delays and `resolveAfter` the live agent applies.

Nothing can leave the host. No publisher, callback dispatcher, action runner
or snapshot emitter is built, and the evaluator's router discards what it is
given. The rule's state is ignored: a `draft` rule is evaluated here exactly
as an `active` one would be, which is how a draft gets validated (FR-RUL-032).

Not reproducible from logs: gauge-sourced rules (host disk/memory, queue
depth) read live process state, so the report says so instead of guessing.
"""

from __future__ import annotations

import heapq
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any, cast

from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.actions.config import ActionCatalogue
from telemetry_agent.callbacks.payload import from_alert_event
from telemetry_agent.parser.applog.parser import AppLogParser
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.fix.timestamps import parse_fix_timestamp
from telemetry_agent.parser.protocol import LineClassification, ParseResult, SourceMeta
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.rules.config_loader import _parse_duration_seconds
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import AlertStatus, RuleConfig, RuleState, ValueSource

_FIX_SENDING_TIME = re.compile(rb"(?:^|[|\x01])52=([0-9]{8}-[0-9:.]+)")
_APP_LOG_TIME = re.compile(rb"^(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?")
# A full date-time at the start of a line, e.g. the simulator's
# `2026-10-20 09:00:00.123 : 8=FIX...` prefix.
_LINE_DATETIME = re.compile(
    rb"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})(?:[.,](\d+))?"
)
_APPLICATION = "Magic"


@dataclass(frozen=True, slots=True)
class ReplayParsers:
    """The parsers a replay uses; built from agent config by the CLI."""

    hash_key: bytes
    app_log_patterns: tuple[str, ...] = ()
    error_signatures: tuple[tuple[str, str], ...] = ()
    max_dynamic_signature_labels: int = 50

    def registry(self) -> tuple[Registry, list[str]]:
        parsers: dict[str, FixParser | AppLogParser] = {
            "fix": FixParser(hash_key=self.hash_key)
        }
        chain = ["fix"]
        if self.app_log_patterns:
            parsers["applog"] = AppLogParser(
                app_log_patterns=list(self.app_log_patterns),
                error_signatures=list(self.error_signatures),
                max_dynamic_signature_labels=self.max_dynamic_signature_labels,
            )
            chain.append("applog")
        return Registry(parsers=parsers), chain


@dataclass(frozen=True, slots=True)
class Transition:
    """One change the candidate rule would have made."""

    at: datetime
    status: str  # pending | firing | resolving | resolved
    severity: str | None = None
    observed_value: float | None = None
    matched_condition: str | None = None
    notification_count: int | None = None
    # The §3.3 callback body the alert would have carried (firing/resolved).
    payload: dict[str, Any] | None = None
    # Actions that would have run: only on the occurrence's first firing.
    would_run: tuple[str, ...] = ()


@dataclass(slots=True)
class BacktestReport:
    rule: str
    state: str
    files: tuple[str, ...]
    replay_from: datetime | None = None
    replay_to: datetime | None = None
    lines: int = 0
    unparsed_lines: int = 0
    evaluations: int = 0
    transitions: list[Transition] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    dispatched: int = 0  # always 0; asserted by tests and shown in the report

    @property
    def fired(self) -> bool:
        return any(t.status == AlertStatus.FIRING.value for t in self.transitions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "state": self.state,
            "files": list(self.files),
            "replayFrom": _iso(self.replay_from),
            "replayTo": _iso(self.replay_to),
            "lines": self.lines,
            "unparsedLines": self.unparsed_lines,
            "evaluations": self.evaluations,
            "fired": self.fired,
            "dispatched": self.dispatched,
            "caveats": list(self.caveats),
            "transitions": [
                {
                    "at": _iso(t.at),
                    "status": t.status,
                    "severity": t.severity,
                    "observedValue": t.observed_value,
                    "matchedCondition": t.matched_condition,
                    "notificationCount": t.notification_count,
                    "wouldRun": list(t.would_run),
                    "payload": t.payload,
                }
                for t in self.transitions
            ],
        }

    def render_text(self) -> str:
        out = [
            f"test mode: rule {self.rule} ({self.state}) over {', '.join(self.files)}",
            f"  replayed {self.lines} lines ({self.unparsed_lines} unparsed), "
            f"{_iso(self.replay_from)} -> {_iso(self.replay_to)}, "
            f"{self.evaluations} evaluations",
        ]
        out.extend(f"  caveat: {c}" for c in self.caveats)
        if not self.transitions:
            out.append("  result: never left inactive - the rule would not have fired")
        for t in self.transitions:
            line = f"  {_iso(t.at)}  {t.status:<9}"
            if t.severity:
                line += f" {t.severity}"
            if t.matched_condition and t.status == AlertStatus.FIRING.value:
                line += f"  {t.matched_condition}"
            if t.would_run:
                line += f"  would run: {', '.join(t.would_run)}"
            out.append(line)
            if t.payload is not None and t.status == AlertStatus.FIRING.value:
                out.append(f"      payload: {t.payload}")
        out.append(
            f"  dispatched: {self.dispatched} (test mode never calls Magic, "
            "publishes or runs actions)"
        )
        return "\n".join(out)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


class _DiscardRouter:
    """Stands in for `AlertRouter`: what the evaluator routes is already in
    `evaluate_once`'s return value, and must go nowhere else."""

    def route(
        self, alerts: Sequence[AlertEvent], *, now: datetime | None = None
    ) -> int:
        return 0


class _ReplayClock:
    def __init__(self, start: datetime) -> None:
        self.now = start

    def wall(self) -> float:
        return self.now.timestamp()


def _fix_time(line: bytes, wall: datetime) -> datetime | None:
    match = _FIX_SENDING_TIME.search(line)
    if match is None:
        return None
    result = parse_fix_timestamp(
        match.group(1).decode("ascii"), wall=wall, max_skew=timedelta.max
    )
    return None if result.bad_timestamp else result.event_time


def _micro(frac: bytes | None) -> int:
    return int(frac.decode().ljust(6, "0")[:6]) if frac else 0


def _prefix_time(line: bytes) -> datetime | None:
    match = _LINE_DATETIME.match(line)
    if match is None:
        return None
    year, month, day, hour, minute, second, frac = match.groups()
    try:
        return datetime(
            int(year),
            int(month),
            int(day),
            int(hour),
            int(minute),
            int(second),
            _micro(frac),
            tzinfo=UTC,
        )
    except ValueError:
        return None


def _app_log_time(line: bytes, last: datetime) -> datetime | None:
    match = _APP_LOG_TIME.match(line)
    if match is None:
        return None
    hour, minute, second, frac = match.groups()
    candidate = datetime.combine(
        last.date(),
        time(int(hour), int(minute), int(second), _micro(frac)),
        tzinfo=UTC,
    )
    if candidate < last - timedelta(hours=12):
        candidate += timedelta(days=1)  # time of day wrapped past midnight
    return candidate


def _line_time(line: bytes, last: datetime) -> datetime | None:
    return _fix_time(line, last) or _prefix_time(line) or _app_log_time(line, last)


def _timed_lines(
    path: Path, start: datetime, index: int
) -> Iterator[tuple[datetime, int, int, bytes]]:
    """(event time, file index, line number, line). A line with no timestamp
    of its own takes the previous line's time. Lines before the file's first
    timestamp take that one, not the replay start, so a file that dates only
    some of its lines doesn't drag the replay back to midnight."""
    last = _first_time(path, start) or start
    with path.open("rb") as handle:
        for number, raw in enumerate(handle):
            line = raw.rstrip(b"\r\n")
            if not line:
                continue
            last = _line_time(line, last) or last
            yield last, index, number, line


def _first_time(path: Path, context: datetime) -> datetime | None:
    with path.open("rb") as handle:
        for raw in handle:
            stamp = _line_time(raw.rstrip(b"\r\n"), context)
            if stamp is not None:
                return stamp
    return None


def _first_dated_time(paths: Sequence[Path]) -> datetime | None:
    """The first timestamp that carries its own date (FIX SendingTime or a
    date-time prefix). An Application.log time of day can't anchor a date."""
    now = datetime.now(UTC)
    for path in paths:
        with path.open("rb") as handle:
            for raw in handle:
                stamp = _fix_time(raw, now) or _prefix_time(raw)
                if stamp is not None:
                    return stamp
    return None


def _tail_seconds(rule: RuleConfig, interval: float) -> float:
    """How long to keep ticking after the last line, so a condition that
    was true at the end can still clear `for:`, decay out of its window and
    clear `resolveAfter` - the replay should show the resolve too."""
    window = _parse_duration_seconds(rule.window) if rule.window else 0
    return window + rule.for_seconds + rule.resolve_after_seconds + 2 * interval


def backtest(
    rule: RuleConfig,
    log_paths: Sequence[Path],
    *,
    parsers: ReplayParsers,
    instance_id: str,
    agent_id: str,
    evaluation_interval_seconds: float,
    actions: ActionCatalogue | None = None,
    replay_date: date | None = None,
) -> BacktestReport:
    """Replay `log_paths` (merged in timestamp order) through `rule` alone.
    Returns every lifecycle change the rule would have gone through, with
    the payload each notification would have carried. Never dispatches."""
    report = BacktestReport(
        rule=rule.name,
        state=rule.state.value,
        files=tuple(str(p) for p in log_paths),
    )
    if rule.source is ValueSource.GAUGE:
        report.caveats.append(
            f"{rule.name} reads the live gauge {rule.metric!r}, which log lines "
            "don't carry; the replay can't show whether it would fire"
        )
    unknown = [a for a in rule.actions if actions is not None and a not in actions]
    if unknown:
        report.caveats.append(f"actions not in the catalogue: {unknown}")

    if replay_date is not None:
        start = datetime.combine(replay_date, time(), tzinfo=UTC)
    else:
        start = _first_dated_time(log_paths) or datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    clock = _ReplayClock(start)
    ingestor = MetricsIngestor.build_default(clock=clock.wall, monotonic=clock.wall)
    registry, chain = parsers.registry()
    candidate = replace(rule, state=RuleState.ACTIVE)  # draft is the point
    engine = RuleEngine(
        [candidate],
        instance_id=instance_id,
        application=_APPLICATION,
        agent_id=agent_id,
        started_at=start,
        startup_grace_seconds=0,
    )
    evaluator = RuleEvaluator(
        engine,
        ingestor.aggregator,
        cast(AlertRouter, _DiscardRouter()),
        instance_id=instance_id,
        correlator=ingestor.correlator,
        session_tracker=ingestor.session_tracker,
        interval_seconds=evaluation_interval_seconds,
        reload_check_seconds=0,
        clock=lambda: clock.now,
        monotonic=clock.wall,
    )
    status: AlertStatus | None = None
    next_tick: datetime | None = None

    def tick(at: datetime) -> None:
        nonlocal status
        clock.now = at
        changed = evaluator.evaluate_once(now=at, monotonic_now=at.timestamp())
        report.evaluations += 1
        for alert in changed:
            report.transitions.append(_transition(alert, at, rule, actions))
        current = engine.status_of(candidate.name)
        if current is not status and current in (
            AlertStatus.PENDING,
            AlertStatus.RESOLVING,
        ):
            report.transitions.append(Transition(at=at, status=current.value))
        status = current

    interval = timedelta(seconds=evaluation_interval_seconds)
    streams = [_timed_lines(path, start, index) for index, path in enumerate(log_paths)]
    last: datetime | None = None
    for stamp, index, number, line in heapq.merge(*streams):
        if next_tick is None:
            next_tick = stamp + interval
            report.replay_from = stamp
        while next_tick <= stamp:
            tick(next_tick)
            next_tick += interval
        clock.now = stamp
        meta = SourceMeta(
            instance_id=instance_id,
            path=str(log_paths[index]),
            log_type="fix",
            read_at=stamp,
            byte_offset=number,
        )
        parser, _ = registry.select(chain, line)
        result = (
            parser.parse(line, meta)
            if parser is not None
            else ParseResult(classification=LineClassification.UNSUPPORTED)
        )
        if parser is None:
            report.unparsed_lines += 1
        ingestor.ingest(result, meta)
        report.lines += 1
        last = stamp

    if last is not None and next_tick is not None:
        end = last + timedelta(
            seconds=_tail_seconds(candidate, evaluation_interval_seconds)
        )
        while next_tick <= end:
            tick(next_tick)
            next_tick += interval
            if status is None and report.fired:
                break  # resolved and deleted: nothing more can happen
        report.replay_to = next_tick - interval
    return report


def _transition(
    alert: AlertEvent,
    at: datetime,
    rule: RuleConfig,
    actions: ActionCatalogue | None,
) -> Transition:
    first_firing = (
        alert.status == AlertStatus.FIRING.value and alert.notification_count == 1
    )
    return Transition(
        at=at,
        status=alert.status,
        severity=alert.severity,
        observed_value=alert.observed_value,
        matched_condition=alert.matched_condition,
        notification_count=alert.notification_count,
        payload=from_alert_event(alert, now=at).model_dump(mode="json", by_alias=True),
        would_run=rule.actions if first_firing else (),
    )
