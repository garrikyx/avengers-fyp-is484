"""UBS-36: test mode replays log files through one rule and reports whether,
when and with what payload it would have fired, without dispatching."""

import json
import sys
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from telemetry_agent import main as agent_main
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.pipeline.backtest import (
    ReplayParsers,
    _app_log_time,
    backtest,
)
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.types import RuleConfig, RuleState

_T0 = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)
_PARSERS = ReplayParsers(hash_key=b"test-key")


def _rule(name: str) -> RuleConfig:
    return next(r for r in DEFAULT_RULES if r.name == name)


def _fix_log(path: Path, *, minutes: int, burst: tuple[int, int] | None = None) -> Path:
    """Two orders every 5s; inside `burst` (start, end seconds) 2 of every 5
    ticks reject both orders, a reject rate of about 40%."""
    lines: list[str] = []
    seq = 1
    for sec in range(0, minutes * 60, 5):
        ts = (_T0 + timedelta(seconds=sec)).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
        reject = burst is not None and burst[0] <= sec < burst[1] and (sec // 5) % 5 < 2
        for k in range(2):
            cl = f"C{sec}_{k}"
            lines.append(
                f"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34={seq}|52={ts}|11={cl}"
                "|55=AAPL|54=1|40=2|38=100|10=000|"
            )
            status = "150=8|39=8|103=3" if reject else "150=0|39=0"
            lines.append(
                f"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34={seq + 1}|52={ts}|11={cl}"
                f"|37=O{cl}|17=E{cl}|55=AAPL|54=1|{status}|10=000|"
            )
            seq += 2
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def _run(rule: RuleConfig, *paths: Path, **kwargs: object):  # type: ignore[no-untyped-def]
    return backtest(
        rule,
        list(paths),
        parsers=_PARSERS,
        instance_id="magic-prod-01",
        agent_id="magic-agent-sg-01",
        evaluation_interval_seconds=10,
        **kwargs,  # type: ignore[arg-type]
    )


@pytest.fixture(autouse=True)
def _nothing_may_be_dispatched(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("test mode must never dispatch or publish")

    monkeypatch.setattr(CallbackDispatcher, "enqueue", refuse)
    monkeypatch.setattr(CallbackDispatcher, "deliver", refuse)
    monkeypatch.setattr(BackendPublisher, "enqueue_alert", refuse)


def test_a_reject_burst_is_reported_firing_then_resolved(tmp_path: Path) -> None:
    log = _fix_log(tmp_path / "Fix.log", minutes=30, burst=(300, 900))

    report = _run(_rule("HighRejectRate"), log)

    assert report.fired
    assert report.dispatched == 0
    statuses = [t.status for t in report.transitions]
    assert statuses[0] == "pending"
    assert statuses[-2:] == ["resolving", "resolved"]
    first_fire = next(t for t in report.transitions if t.status == "firing")
    pending = report.transitions[0]
    # `for: 2m` is honoured on the simulated clock.
    assert first_fire.at - pending.at >= timedelta(minutes=2)
    assert first_fire.at > _T0 + timedelta(minutes=5)  # not before the burst
    assert first_fire.payload is not None
    assert first_fire.payload["ruleName"] == "HighRejectRate"
    assert first_fire.payload["notificationCount"] == 1
    assert report.lines == 30 * 12 * 4
    assert report.unparsed_lines == 0


def test_a_quiet_log_never_fires(tmp_path: Path) -> None:
    log = _fix_log(tmp_path / "Fix.log", minutes=20)

    report = _run(_rule("HighRejectRate"), log)

    assert not report.fired
    assert report.transitions == []
    assert "would not have fired" in report.render_text()


def test_a_draft_rule_is_evaluated_and_reported_as_draft(tmp_path: Path) -> None:
    log = _fix_log(tmp_path / "Fix.log", minutes=30, burst=(300, 900))
    draft = replace(_rule("HighRejectRate"), state=RuleState.DRAFT)

    report = _run(draft, log)

    assert report.state == "draft"
    assert report.fired


def test_actions_would_run_on_the_first_firing_only(tmp_path: Path) -> None:
    log = _fix_log(tmp_path / "Fix.log", minutes=30, burst=(300, 900))
    rule = replace(_rule("HighRejectRate"), actions=("ops-webhook",))

    report = _run(rule, log, actions={})

    runs = [t.would_run for t in report.transitions if t.would_run]
    assert runs == [("ops-webhook",)]
    assert any("not in the catalogue" in c for c in report.caveats)


def test_a_gauge_rule_carries_a_caveat(tmp_path: Path) -> None:
    log = _fix_log(tmp_path / "Fix.log", minutes=1)
    gauge_rule = next(r for r in DEFAULT_RULES if r.window is None)

    report = _run(gauge_rule, log)

    assert any("live gauge" in c for c in report.caveats)


def test_app_log_times_take_the_date_and_wrap_at_midnight() -> None:
    late = datetime(2026, 10, 20, 23, 59, 58, tzinfo=UTC)
    assert _app_log_time(b"23:59:59.500 <1> [E] x", late) == late.replace(
        second=59, microsecond=500000
    )
    assert _app_log_time(b"00:00:01.000 <1> [E] x", late) == datetime(
        2026, 10, 21, 0, 0, 1, tzinfo=UTC
    )
    assert _app_log_time(b"8=FIX.4.2|35=D", late) is None


def test_files_are_merged_in_timestamp_order(tmp_path: Path) -> None:
    first = _fix_log(tmp_path / "a.log", minutes=30, burst=(300, 900))
    quiet = _fix_log(tmp_path / "b.log", minutes=30)

    report = _run(_rule("HighRejectRate"), first, quiet)

    assert report.replay_from == _T0
    assert report.lines == 2 * 30 * 12 * 4
    assert report.fired  # diluted to ~20%, still above both tiers


def test_replay_date_anchors_logs_with_no_fix_timestamps(tmp_path: Path) -> None:
    app_log = tmp_path / "Application.log"
    app_log.write_text("09:00:00.000 <1> [I] started\n", encoding="utf-8")

    report = _run(_rule("HighRejectRate"), app_log, replay_date=date(2026, 1, 2))

    assert report.replay_from == datetime(2026, 1, 2, 9, 0, tzinfo=UTC)


def test_the_cli_prints_a_json_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    log = _fix_log(tmp_path / "Fix.log", minutes=30, burst=(300, 900))
    config = Path(__file__).resolve().parents[4] / "config" / "agent.yaml"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "telemetry-agent",
            "--config",
            str(config),
            "--test-rule",
            "HighRejectRate",
            "--replay",
            str(log),
            "--json",
        ],
    )

    agent_main.main()

    report = json.loads(capsys.readouterr().out)
    assert report["rule"] == "HighRejectRate"
    assert report["fired"] is True
    assert report["dispatched"] == 0
    assert report["transitions"][-1]["status"] == "resolved"


def test_the_cli_names_the_rules_when_one_is_unknown(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = Path(__file__).resolve().parents[4] / "config" / "agent.yaml"
    monkeypatch.setattr(
        sys,
        "argv",
        ["telemetry-agent", "--config", str(config), "--test-rule", "Nope"],
    )
    with pytest.raises(SystemExit, match="unknown rule 'Nope'.*HighRejectRate"):
        agent_main.main()


def test_a_date_time_line_prefix_anchors_the_replay(tmp_path: Path) -> None:
    # The simulator's Fix.log shape: no SendingTime, a local date-time prefix.
    log = tmp_path / "Fix.log"
    log.write_text(
        "2026-03-04 10:00:00.250 : 8=FIX.4.2|9=140|35=8|49=MAGIC|56=CLIENT|10=1|\n"
        "no timestamp on this one\n"
        "2026-03-04 10:00:05.000 : 8=FIX.4.2|9=140|35=8|49=MAGIC|56=CLIENT|10=1|\n",
        encoding="utf-8",
    )

    report = _run(_rule("HighRejectRate"), log)

    assert report.replay_from == datetime(2026, 3, 4, 10, 0, 0, 250000, tzinfo=UTC)
    assert report.replay_to is not None
    assert report.replay_to - report.replay_from < timedelta(hours=1)
