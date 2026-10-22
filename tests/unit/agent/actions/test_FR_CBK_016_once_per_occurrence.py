"""FR-CBK-016: an action runs at most once per alert occurrence, on
pending→firing only, and actions run one at a time (UBS-35)."""

import asyncio
import json
import textwrap
from pathlib import Path

from action_fixtures import command_action, make_alert, write_script
from telemetry_agent.actions.runner import ActionRunner


def _runner(rule_actions: dict[str, tuple[str, ...]]) -> ActionRunner:
    catalogue = {
        name: command_action(name, dry_run=True)
        for names in rule_actions.values()
        for name in names
    }
    return ActionRunner(catalogue, lambda rule: rule_actions.get(rule, ()), secret=b"s")


def test_only_the_first_firing_of_an_occurrence_queues_actions() -> None:
    runner = _runner({"HostDiskFull": ("cleanup",)})

    assert runner.enqueue(make_alert(notification_count=1)) == 1
    # The same event delivered twice, a renotify, a severity change (both
    # carry a higher count) and the resolve: none of them runs it again.
    assert runner.enqueue(make_alert(notification_count=1)) == 0
    assert runner.enqueue(make_alert(notification_count=2)) == 0
    assert runner.enqueue(make_alert(notification_count=3, severity="warning")) == 0
    assert runner.enqueue(make_alert(status="resolved", notification_count=4)) == 0
    # The next occurrence has a new alertId and runs again.
    assert runner.enqueue(make_alert(alert_id="alert-2")) == 1


def test_rules_without_actions_and_other_statuses_queue_nothing() -> None:
    runner = _runner({"HostDiskFull": ("cleanup",)})
    assert runner.enqueue(make_alert(rule_name="RejectSpike")) == 0
    assert runner.enqueue(make_alert(rule_name="AlertStorm")) == 0
    assert runner.enqueue(make_alert(status="pending")) == 0


def test_every_named_action_is_queued_in_order() -> None:
    runner = _runner({"HostDiskFull": ("cleanup", "notify")})
    assert runner.enqueue(make_alert()) == 2


def test_the_seen_set_is_bounded() -> None:
    runner = ActionRunner(
        {"cleanup": command_action(dry_run=True)},
        lambda _rule: ("cleanup",),
        secret=b"s",
        seen_capacity=2,
    )
    for n in range(3):
        runner.enqueue(make_alert(alert_id=f"a{n}"))
    # a0 fell out of the window; a2 is still remembered.
    assert runner.enqueue(make_alert(alert_id="a2")) == 0
    assert runner.enqueue(make_alert(alert_id="a0")) == 1


_STAMP = textwrap.dedent(
    """
    import json, sys, time
    start = time.monotonic()
    time.sleep(0.3)
    with open(sys.argv[1], "a", encoding="utf-8") as f:
        f.write(json.dumps([sys.argv[2], start, time.monotonic()]) + "\\n")
    """
)


def test_actions_run_one_at_a_time(tmp_path: Path) -> None:
    script = write_script(tmp_path, "stamp.py", _STAMP)
    log = tmp_path / "runs.jsonl"
    catalogue = {
        name: command_action(name, args=(str(script), str(log), name))
        for name in ("first", "second")
    }
    runner = ActionRunner(catalogue, lambda _rule: ("first", "second"), secret=b"s")

    async def scenario() -> None:
        task = asyncio.create_task(runner.run())
        runner.enqueue(make_alert())
        for _ in range(200):
            await asyncio.sleep(0.05)
            if log.exists() and len(log.read_text().splitlines()) == 2:
                break
        task.cancel()

    asyncio.run(scenario())

    (name1, _, end1), (name2, start2, _) = (
        json.loads(line) for line in log.read_text().splitlines()
    )
    assert (name1, name2) == ("first", "second")
    assert end1 <= start2
