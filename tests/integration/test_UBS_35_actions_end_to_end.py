"""UBS-35 / spec 005 §5: rule actions in the real agent process, end to end.

`build_agent` + `run_agent` (what `telemetry-agent` runs) with the real
backend app in-process, a stub Magic endpoint and a stub ops webhook:

    Fix.log reject burst -> agent -> RejectSpike fires
      -> backend alert store and the signed Magic callback, as before
      -> its actions, once: a command (real child process, alert JSON on
         stdin), a callback to another endpoint, and a command that fails,
         which must change nothing else (FR-CBK-017)

and a live edit of rules.yaml, picked up with no signal (works on Windows),
that binds an action to a rule which had none.
"""

from __future__ import annotations

import asyncio
import json
import sys
import textwrap
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.config import load_agent_config
from telemetry_agent.main import Agent, build_agent, run_agent
from telemetry_backend.main import create_app

AGENT_ID = "magic-agent-e2e-35"
SECRET = "e2e-callback-secret"
BURST = 51  # RejectSpike fires above 50 rejects in 1m
PYTHON = Path(sys.executable).as_posix()

_CONFIG = """
agent:
  id: {agent_id}
  instanceIds: [magic-e2e-01]
logs:
  paths: [{log_dir}/Application.log, {log_dir}/Fix.log]
  stateDir: {state_dir}
pipeline:
  evaluationInterval: 200ms
rules:
  path: rules.yaml
  reloadCheckInterval: 200ms
actions:
  allowedCommands: ['{python}']
publish:
  endpoint: https://backend.example/telemetry/batch
  interval: 1s
callbacks:
  endpoint: https://magic.example/magic/callbacks/telemetry-alerts
"""

_RECORDER = textwrap.dedent(
    """
    import json, sys
    data = sys.stdin.read()
    with open(sys.argv[1], "a", encoding="utf-8") as f:
        f.write(json.dumps({"argv": sys.argv[1:], "stdin": data}) + "\\n")
    """
)

_ACTIONS = """
actions:
  - name: record
    type: command
    command: '{python}'
    args: ['{recorder}', '{runs}']
    timeout: 20s
    dryRun: false
  - name: broken
    type: command
    command: '{python}'
    args: ['-c', 'import sys; sys.exit(3)']
    dryRun: false
  - name: ops-webhook
    type: callback
    endpoint: https://ops.example/hooks/telemetry
    dryRun: false
"""

_RULE = """
  - name: RejectSpike
    kind: threshold
    source: counter
    metric: orders_rejected
    operator: ">"
    tiers: [{{severity: warning, threshold: 50}}]
    window: 1m
    for: 0s
    actions: [{actions}]
"""


def _burst(sending_time: str) -> list[str]:
    lines = []
    for tag in range(BURST):
        seq = 2 * tag + 1
        lines.append(
            f"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34={seq}|52={sending_time}"
            f"|11=C{tag}|55=AAPL|54=1|40=2|38=100|10=000|"
        )
        lines.append(
            f"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34={seq + 1}|52={sending_time}"
            f"|11=C{tag}|37=O{tag}|17=E{tag}|55=AAPL|54=1|150=8|39=8|103=3|10=000|"
        )
    return lines


class _Stack:
    def __init__(self, tmp_path: Path, actions: str) -> None:
        self.tmp_path = tmp_path
        self.runs = tmp_path / "runs.jsonl"
        recorder = tmp_path / "record.py"
        recorder.write_text(_RECORDER, encoding="utf-8")
        self.actions_block = _ACTIONS.format(
            python=PYTHON, recorder=recorder.as_posix(), runs=self.runs.as_posix()
        )
        self.write_rules(actions)
        config_path = tmp_path / "agent.yaml"
        config_path.write_text(
            _CONFIG.format(
                agent_id=AGENT_ID,
                log_dir=(tmp_path / "logs").as_posix(),
                state_dir=(tmp_path / "state").as_posix(),
                python=PYTHON,
            ),
            encoding="utf-8",
        )
        self.magic: list[httpx.Request] = []
        self.ops: list[httpx.Request] = []
        self.app = create_app()
        self.agent: Agent = build_agent(
            load_agent_config(config_path),
            publish_transport=httpx.ASGITransport(app=self.app),
            callback_transport=httpx.MockTransport(self._callback),
            started_at=datetime.now(UTC) - timedelta(hours=1),
            env={
                "MAGIC_TELEMETRY_ID_HASH_KEY": "e2e-hash-key",
                "MAGIC_TELEMETRY_PUBLISH_TOKEN": "e2e-token",
                "MAGIC_TELEMETRY_CALLBACK_SECRET": SECRET,
            },
        )

    def write_rules(self, actions: str) -> None:
        (self.tmp_path / "rules.yaml").write_text(
            self.actions_block + "rules:" + _RULE.format(actions=actions),
            encoding="utf-8",
        )

    def _callback(self, request: httpx.Request) -> httpx.Response:
        (self.ops if request.url.host == "ops.example" else self.magic).append(request)
        return httpx.Response(200, json={})

    def recorded_runs(self) -> list[dict[str, object]]:
        if not self.runs.exists():
            return []
        return [json.loads(line) for line in self.runs.read_text().splitlines()]

    def counters(self) -> dict[str, int]:
        return self.agent.actions.counters.snapshot()

    async def run(self, before_burst=None, done=None):  # type: ignore[no-untyped-def]
        worker = asyncio.create_task(self.app.state.ingestion.run())
        stop = asyncio.Event()
        running = asyncio.create_task(run_agent(self.agent, stop))
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url="http://backend"
        )
        try:
            await asyncio.sleep(0.3)  # tailing before the burst lands
            if before_burst is not None:
                await before_burst()
            stamp = datetime.now(UTC).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
            fix_log = self.tmp_path / "logs" / "Fix.log"
            with fix_log.open("a", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(_burst(stamp)) + "\n")
            alerts: list[dict[str, object]] = []
            for _ in range(200):  # up to ~20s
                await asyncio.sleep(0.1)
                alerts = (await client.get("/telemetry/alerts")).json()["alerts"]
                if alerts and self.magic and done():
                    break
            await asyncio.sleep(1.0)  # room for any (wrong) second run
        finally:
            stop.set()
            await asyncio.wait_for(running, 15)
            worker.cancel()
            await client.aclose()
        return alerts


def test_a_firing_rule_runs_each_of_its_actions_once(tmp_path: Path) -> None:
    stack = _Stack(tmp_path, "record, broken, ops-webhook")

    def done() -> bool:
        counters = stack.counters()
        return (
            bool(stack.recorded_runs())
            and bool(stack.ops)
            and any(k.startswith("action_runs:broken:") for k in counters)
        )

    alerts = asyncio.run(stack.run(done=done))

    # --- the alert went where it always went, unaffected by the failing action
    assert [a["ruleName"] for a in alerts] == ["RejectSpike"]
    assert len(stack.magic) == 1
    alert_id = alerts[0]["alertId"]

    # --- the command ran once, the alert JSON on stdin, the argv as configured
    (run,) = stack.recorded_runs()
    assert run["argv"] == [stack.runs.as_posix()]
    body = json.loads(str(run["stdin"]))
    assert body["alertId"] == alert_id
    assert body["status"] == "firing"

    # --- the callback action went to its own endpoint, signed
    (hook,) = stack.ops
    timestamp = hook.headers["X-Telemetry-Timestamp"]
    assert hook.headers["X-Telemetry-Signature"] == sign(
        SECRET.encode(), timestamp, hook.read()
    )
    assert json.loads(hook.read())["alertId"] == alert_id

    # --- outcomes counted; the failure stayed on its own path
    counters = stack.counters()
    assert counters["action_runs:record:ok"] == 1
    assert counters["action_runs:broken:failed"] == 1
    assert counters["action_runs:ops-webhook:ok"] == 1
    assert "alerts_action_enqueue_failed" not in stack.agent.router.counters.snapshot()


def test_an_edited_rules_file_binds_an_action_without_a_restart(
    tmp_path: Path,
) -> None:
    stack = _Stack(tmp_path, "")  # RejectSpike starts with no actions
    assert stack.agent.engine.rules[0].actions == ()

    async def edit_rules() -> None:
        stack.write_rules("record")
        for _ in range(50):  # the evaluator checks the mtime every 200ms
            await asyncio.sleep(0.1)
            if stack.agent.engine.rules[0].actions == ("record",):
                return
        raise AssertionError("rules.yaml edit was not picked up")

    asyncio.run(stack.run(before_burst=edit_rules, done=stack.recorded_runs))

    assert len(stack.recorded_runs()) == 1
    assert stack.counters()["action_runs:record:ok"] == 1


def test_a_bad_edit_is_rejected_and_the_agent_keeps_its_actions(
    tmp_path: Path,
) -> None:
    stack = _Stack(tmp_path, "record")

    async def break_rules() -> None:
        (tmp_path / "rules.yaml").write_text(
            stack.actions_block.replace(PYTHON, "/usr/bin/not-allowlisted")
            + "rules:"
            + _RULE.format(actions="record"),
            encoding="utf-8",
        )
        await asyncio.sleep(0.6)  # past at least two reload checks

    asyncio.run(stack.run(before_burst=break_rules, done=stack.recorded_runs))

    # The rejected file changed nothing: the old command still ran.
    assert stack.agent.actions.catalogue["record"].command == Path(PYTHON)
    assert len(stack.recorded_runs()) == 1
