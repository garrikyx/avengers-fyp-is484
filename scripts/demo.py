"""UBS-134: guided Day-1 demo on the real entrypoints.

    uv run python -m scripts.demo            # guided: press Enter between steps
    uv run python -m scripts.demo --auto     # rehearsal: timed, no input
    uv run python -m scripts.demo --showcase # plus the extra feature showcase

This launcher only starts and drives the real processes; it holds no telemetry
logic of its own:

    simulator (apps/simulator mock_logger.py)  ->  .demo-run/logs/*.log
    telemetry-agent  --config config/demo/agent.yaml   (tails, parses, rules)
    telemetry-backend --config config/demo/backend.yaml (:8080 query + NL API)
    telemetry-teams  (:3978, local Bot Framework endpoint, dev credentials)
    STUB scripts.mock_magic_callback_receiver (:9000, Magic's callback endpoint)

The steps follow spec 000 §7: normal flow, reject burst visible within 5 s
(#1), HighRejectRate fires and resolves through a signed callback (#2), the
headline NL question (#3), rotation plus agent restart with counts continuing
(#4, short form; the full 5-minute outage evidence is UBS-140), and a stopped
agent raising AgentHeartbeatMissing. `--showcase` adds the extras from
scripts/demo_showcase.py: a tampered callback, exact generated-vs-queried
counts, a second outage alerting again, the leak sentinel, rule test mode and
questions through the MCP server. See docs/plan/ubs134-demo-runbook.md.

Local hosting only. Process output goes to .demo-run/proc/<name>.log.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / ".demo-run"
BACKEND = "http://127.0.0.1:8080"
INSTANCE = "magic-prod-01"
AGENT_ID = "magic-agent-sg-01"
QUESTION = "Why are Magic orders rejecting in the last 30 minutes?"
NORMAL_REJECT_RATE = 0.005  # below HighRejectRate's 3% warning tier
BURST_REJECT_RATE = 0.6
SIM_INTERVAL = 0.05  # ~4 orders/s from the simulator
SIM_MAX_BYTES = 100_000  # small files, so rotation happens during the demo
SIM_KEEP_ROTATED = 50  # keep every archive, so the counts can be reconciled
MIN_ORDERS_FOR_RATE = 20  # don't print a reject rate from a handful of orders
WINDOWS = sys.platform == "win32"

DEV_ENV = {
    # Same dev fallbacks as .env.example; localhost only.
    "MAGIC_TELEMETRY_ID_HASH_KEY": "dev-only",
    "MAGIC_TELEMETRY_PUBLISH_TOKEN": "dev-local-token",
    "MAGIC_TELEMETRY_CALLBACK_SECRET": "dev-local-secret",
    # Dev-only anonymous Bot Framework access, as in `make teams-run`.
    "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": (
        "00000000-0000-0000-0000-000000000000"
    ),
    "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET": "dummy",
    "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": (
        "00000000-0000-0000-0000-000000000000"
    ),
    "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED": "true",
    # UBS-120 alert cards: the Playground is a 1:1 chat.
    "TEAMS_NOTIFY_ALLOW_PERSONAL": "true",
    "TELEMETRY_BACKEND_URL": BACKEND,
    "PYTHONUNBUFFERED": "1",
    "PYTHONIOENCODING": "utf-8",
}


class DemoError(RuntimeError):
    """A step could not show what it should; the message says why."""


def console_script(name: str) -> str:
    """Path of a workspace console script (`telemetry-agent`, ...) in this venv."""
    folder = Path(sys.executable).parent
    found = shutil.which(name, path=str(folder))
    if found is None:
        raise DemoError(f"{name} not found next to {sys.executable}; run `uv sync`")
    return found


@dataclass
class Proc:
    name: str
    argv: Sequence[str]
    cwd: Path
    env: dict[str, str]
    popen: subprocess.Popen[bytes] | None = None
    _log: IO[bytes] | None = field(default=None, repr=False)

    @property
    def log_path(self) -> Path:
        return RUN / "proc" / f"{self.name}.log"

    def start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log = self.log_path.open("ab")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0
        self.popen = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
            list(self.argv),
            cwd=self.cwd,
            env=self.env,
            stdin=subprocess.DEVNULL,
            stdout=self._log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
            start_new_session=not WINDOWS,
        )

    def running(self) -> bool:
        return self.popen is not None and self.popen.poll() is None

    def stop(self, *, graceful: bool = True, timeout: float = 20.0) -> None:
        """Graceful stop: Ctrl+Break on Windows, SIGINT elsewhere; kill if stuck."""
        if self.popen is None:
            return
        if self.popen.poll() is None:
            if graceful:
                sig = signal.CTRL_BREAK_EVENT if WINDOWS else signal.SIGINT
                self.popen.send_signal(sig)
                try:
                    self.popen.wait(timeout)
                except subprocess.TimeoutExpired:
                    self.popen.kill()
            else:
                self.popen.kill()
            self.popen.wait(10)
        if self._log is not None:
            self._log.close()
            self._log = None
        self.popen = None


def say(text: str = "") -> None:
    print(text, flush=True)


def banner(step: str, title: str) -> None:
    say()
    say("=" * 72)
    say(f"  {step}  {title}")
    say("=" * 72)


def wait_for(
    what: str,
    check: Callable[[], Any],
    timeout: float,
    interval: float = 0.25,
) -> Any:
    """Poll `check` until it returns something truthy; raise after `timeout`."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            result = check()
        except httpx.HTTPError:
            result = None
        if result:
            return result
        if time.monotonic() >= deadline:
            raise DemoError(f"timed out after {timeout:.0f}s waiting for {what}")
        time.sleep(interval)


def ollama_status() -> str:
    """Whether the backend's configured Ollama model really answers.

    Asks Ollama about the exact model in config/demo/backend.yaml: a tagged
    variant such as `llama3.2:3b` does not satisfy `llama3.2`.
    """
    import yaml

    text = (ROOT / "config/demo/backend.yaml").read_text(encoding="utf-8")
    llm = (yaml.safe_load(text).get("nl") or {}).get("llm") or {}
    model = llm.get("model", "llama3.2")
    base = llm.get("baseUrl", "http://127.0.0.1:11434")
    try:
        response = httpx.post(f"{base}/api/show", json={"model": model}, timeout=5)
    except httpx.HTTPError:
        return (
            "Ollama: not running. Rule-matched questions (the headline one) still "
            "answer; free-form questions get the fallback reply."
        )
    if response.status_code == 200:
        return f"Ollama: {model} ready"
    return (
        f"WARNING: Ollama has no model named {model!r} (config/demo/backend.yaml)."
        f" Free-form questions will fail. Fix: ollama pull {model}, or"
        f" ollama cp <installed tag> {model}"
    )


def port_in_use(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


class Demo:
    def __init__(self, *, auto: bool, teams: bool, showcase: bool = False) -> None:
        self.auto = auto
        self.teams = teams
        self.showcase = showcase
        self.steps_total = 8 if showcase else 7
        self.env = {**os.environ, **DEV_ENV}
        # UBS-120: one random secret per run, shared by the backend and the bot
        # (the backend deliberately has no dev fallback for it).
        self.env.setdefault("MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN", secrets.token_hex(24))
        self.http = httpx.Client(base_url=BACKEND, timeout=15.0)
        self.procs: dict[str, Proc] = {}

    # --- process control ---------------------------------------------------

    def _proc(self, name: str, argv: Sequence[str], cwd: Path) -> Proc:
        proc = Proc(name, argv, cwd, self.env)
        self.procs[name] = proc
        proc.start()
        return proc

    def start_simulator(self, reject_rate: float) -> None:
        old = self.procs.get("simulator")
        if old is not None:
            old.stop(graceful=False)
        self._proc(
            "simulator",
            [
                sys.executable,
                str(ROOT / "apps/simulator/src/simulator/mock_logger.py"),
                "--interval",
                str(SIM_INTERVAL),
                "--max-bytes",
                str(SIM_MAX_BYTES),
                "--reject-rate",
                str(reject_rate),
                "--keep-rotated-files",
                str(SIM_KEEP_ROTATED),
                # No random [F] lines, so AppOutOfMemory and AppLogFailure stay
                # quiet unless a presenter runs `demo_windows.bat app-fault`.
                "--app-faults",
                "0",
            ],
            RUN,
        )

    def start_agent(self) -> None:
        self._proc(
            "agent",
            [
                console_script("telemetry-agent"),
                "--config",
                # The run folder's copy (scripts.demo_showcase prepare), so a
                # live rule edit never touches the repo.
                str(RUN / "config" / "agent.yaml"),
            ],
            RUN,
        )

    def stop_all(self) -> None:
        for name in ("simulator", "agent", "mcp", "teams", "magic-stub", "backend"):
            proc = self.procs.get(name)
            if proc is not None:
                proc.stop(graceful=name == "agent", timeout=10)

    # --- backend queries ---------------------------------------------------

    def metrics(self, last: str = "30m") -> dict[str, Any]:
        response = self.http.post(
            "/telemetry/query/metrics",
            json={
                "timeRange": {"last": last},
                "filters": {"instanceId": INSTANCE},
                "metrics": [
                    "orders_submitted",
                    "orders_acked",
                    "orders_rejected",
                    "reject_rate",
                ],
            },
        )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        return body

    def totals(self, last: str = "30m") -> dict[str, float]:
        totals = self.metrics(last).get("totals") or {}
        return {k: float(v or 0) for k, v in totals.items()}

    def alerts(self, rule: str, status: str = "active") -> list[dict[str, Any]]:
        """`GET /telemetry/alerts`; `status` is the API filter: active|resolved|all."""
        params = {"ruleName": rule, "status": status}
        response = self.http.get("/telemetry/alerts", params=params)
        response.raise_for_status()
        found: list[dict[str, Any]] = response.json()["alerts"]
        return found

    def callbacks(self) -> list[dict[str, Any]]:
        path = RUN / "callbacks.jsonl"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def show_totals(self, label: str, last: str = "30m") -> dict[str, float]:
        t = self.totals(last)
        decided = t.get("orders_acked", 0) + t.get("orders_rejected", 0)
        rate = (
            f"{t.get('reject_rate', 0.0):6.1%}"
            if decided >= MIN_ORDERS_FOR_RATE
            else f"n/a (<{MIN_ORDERS_FOR_RATE} orders)"
        )
        say(
            f"  {label:<26} submitted={t.get('orders_submitted', 0):>6.0f}"
            f"  acked={t.get('orders_acked', 0):>6.0f}"
            f"  rejected={t.get('orders_rejected', 0):>6.0f}"
            f"  reject_rate={rate}"
        )
        return t

    def show_callbacks(self, since: int = 0) -> int:
        received = self.callbacks()
        for item in received[since:]:
            alert = item["alert"]
            say(
                f"  [Magic stub {item['receivedAt']}] signed callback: "
                f"{alert.get('ruleName')} -> {alert.get('status')}"
                f" ({alert.get('severity')})"
            )
        return len(received)

    # --- pacing --------------------------------------------------------------

    def pause(self, prompt: str, seconds: float = 3.0) -> None:
        if self.auto:
            say(f"  ... {prompt} (auto, {seconds:.0f}s)")
            time.sleep(seconds)
        else:
            input(f"\n  >> {prompt} [Enter] ")

    # --- steps ---------------------------------------------------------------

    def preflight(self) -> None:
        banner(f"0/{self.steps_total}", "Preflight")
        busy = [p for p in (8080, 8081, 9000, 3978, 8765) if port_in_use(p)]
        if not self.teams and 3978 in busy:
            busy.remove(3978)
        if busy:
            raise DemoError(f"ports already in use: {busy}; stop old runs first")
        say(f"  {ollama_status()}")
        if RUN.exists():
            shutil.rmtree(RUN)
        (RUN / "logs").mkdir(parents=True)
        from scripts.demo_showcase import cmd_prepare

        cmd_prepare()
        say(f"  Fresh run folder: {RUN}")

    def step_start(self) -> None:
        banner(f"1/{self.steps_total}", "Start the stack (real entrypoints)")
        self._proc(
            "backend",
            [
                console_script("telemetry-backend"),
                "--config",
                str(ROOT / "config/demo/backend.yaml"),
                "--log-level",
                "warning",
            ],
            ROOT,
        )
        self._proc(
            "magic-stub",
            [
                sys.executable,
                "-m",
                "scripts.mock_magic_callback_receiver",
                "--record",
                str(RUN / "callbacks.jsonl"),
            ],
            ROOT,
        )
        wait_for(
            "backend /healthz",
            lambda: self.http.get("/healthz").status_code == 200,
            timeout=60,
        )
        say("  backend      :8080  telemetry-backend (query, alerts, NL API)")
        say("  Magic stub   :9000  STUB callback endpoint (verifies HMAC)")
        if self.teams:
            self._proc("teams", [console_script("telemetry-teams")], ROOT)
            wait_for("Teams bot on :3978", lambda: port_in_use(3978), timeout=60)
            say("  Teams bot    :3978  telemetry-teams (dev credentials)")
        self._proc("mcp", [console_script("telemetry-mcp")], ROOT)
        wait_for("MCP server on :8765", lambda: port_in_use(8765), timeout=60)
        say("  MCP server   :8765  telemetry-mcp (the read-only tools Copilot uses)")
        self.start_simulator(NORMAL_REJECT_RATE)
        say(f"  simulator           Magic-format logs -> {RUN / 'logs'}")
        self.start_agent()
        say("  agent               telemetry-agent tailing those logs")
        wait_for(
            "first orders in the metrics query",
            lambda: self.totals("5m").get("orders_submitted", 0) > 0,
            timeout=60,
        )
        say("  Orders are flowing end to end.")

    def step_normal(self) -> None:
        banner(f"2/{self.steps_total}", "Normal trading: query the backend")
        say("  POST /telemetry/query/metrics  (derived counters only, no raw logs)")
        for _ in range(3):
            self.show_totals("last 5 minutes", "5m")
            time.sleep(2)
        health = self.http.get(f"/telemetry/health/agents/{AGENT_ID}")
        if health.status_code == 200:
            say(f"  Agent health: {health.json().get('status', '?')}")

    def step_burst(self) -> None:
        banner(
            f"3/{self.steps_total}", "Reject burst visible within 5 seconds  [Day-1 #1]"
        )
        before = self.totals("5m").get("orders_rejected", 0)
        say(f"  Magic starts rejecting {BURST_REJECT_RATE:.0%} of orders now.")
        start = time.monotonic()
        self.start_simulator(BURST_REJECT_RATE)
        wait_for(
            "rejections in the query",
            lambda: self.totals("5m").get("orders_rejected", 0) >= before + 3,
            timeout=30,
            interval=0.1,
        )
        elapsed = time.monotonic() - start
        verdict = "within" if elapsed <= 5 else "OVER"
        say(f"  Burst visible in the query after {elapsed:.2f}s ({verdict} 5 s).")
        self.show_totals("last 5 minutes", "5m")

    def step_alert(self) -> None:
        banner(
            f"4/{self.steps_total}",
            "HighRejectRate alert, signed callback to Magic  [Day-1 #2]",
        )
        say("  Demo rule: >3% warning, >5% critical over 1m, for 10s,")
        say("  resolveAfter 15s (production: 5m window, for 2m, resolveAfter 5m).")
        seen = 0
        wait_for(
            "HighRejectRate firing callback",
            lambda: any(
                c["alert"].get("ruleName") == "HighRejectRate"
                and c["alert"].get("status") == "firing"
                for c in self.callbacks()
            ),
            timeout=120,
            interval=0.5,
        )
        seen = self.show_callbacks(seen)
        for alert in self.alerts("HighRejectRate"):
            observed = alert.get("observedValue")
            shown = "-" if observed is None else f"{observed:.1%}"
            delivery = alert.get("delivery") or {}
            say(
                f"  GET /telemetry/alerts: {alert['ruleName']} {alert['status']}"
                f" severity={alert['severity']} reject rate={shown},"
                f" callback {delivery.get('status', '?')}"
            )
        if self.showcase:
            from scripts.demo_showcase import cmd_tamper

            cmd_tamper()
        self.pause("Stop the burst and watch it resolve", 3)
        self.start_simulator(NORMAL_REJECT_RATE)
        say("  Magic back to normal; waiting for the resolved callback ...")
        wait_for(
            "HighRejectRate resolved callback",
            lambda: any(
                c["alert"].get("ruleName") == "HighRejectRate"
                and c["alert"].get("status") == "resolved"
                for c in self.callbacks()
            ),
            timeout=180,
            interval=0.5,
        )
        self.show_callbacks(seen)

    def step_nl(self) -> None:
        banner(
            f"5/{self.steps_total}",
            "Ask in plain English: Playground or Copilot  [Day-1 #3]",
        )
        if self.teams:
            say("  Teams bot is on http://localhost:3978/api/messages.")
            say("  Open the Agents Playground in another terminal:")
            say("    npx -y @microsoft/teams-app-test-tool start \\")
            say("      -e http://localhost:3978/api/messages -c msteams")
            say(f'  and ask: "{QUESTION}"')
        say("  Copilot (Copilot Studio through a dev tunnel) or MCP Inspector:")
        say("    http://127.0.0.1:8765/mcp, tool nl_query")
        say("  The same question through the backend NL API both of them call:")
        response = self.http.post("/telemetry/nl/query", json={"question": QUESTION})
        response.raise_for_status()
        answer = response.json()
        say(f"  Answer: {answer.get('answer', answer)}")
        if answer.get("kind") == "answer":
            confidence = answer.get("confidence")
            completeness = answer.get("dataCompleteness") or {}
            say(
                f"  intent={answer.get('intent')} source={answer.get('source')}"
                f" confidence={'-' if confidence is None else f'{confidence:.2f}'}"
                f" data={completeness.get('confidence', '?')}"
            )
            data = (answer.get("data") or {}).get("totals") or {}
            say(f"  Numbers behind the answer: {data}")
        self.show_totals("metrics query, last 30m", "30m")
        self.pause("Ask the question in the Playground or Copilot now", 2)

    def step_restart(self) -> None:
        banner(
            f"6/{self.steps_total}",
            "Log rotation and agent restart, no data lost  [Day-1 #4]",
        )
        rotated = sorted(p.name for p in (RUN / "logs").glob("*.log.*"))
        say(f"  Rotated archives so far: {', '.join(rotated) or 'none yet'}")
        before = self.show_totals("before restart", "30m")
        say("  Stopping the agent gracefully; Magic keeps writing logs ...")
        self.procs["agent"].stop(graceful=True)
        self.pause("Agent is down; logs keep growing", 6)
        self.start_agent()
        say("  Agent restarted with its saved offsets.")
        target = before.get("orders_submitted", 0) + 10
        wait_for(
            "counts to continue after restart",
            lambda: self.totals("30m").get("orders_submitted", 0) >= target,
            timeout=60,
        )
        self.show_totals("after restart", "30m")
        completeness = self.metrics("30m").get("dataCompleteness") or {}
        flagged = completeness.get("restartedBuckets", 0)
        say(f"  {flagged} time bucket(s) flagged as spanning the restart; answers")
        say("  that cover them say so (restartedBuckets).")
        if self.showcase:
            from scripts.demo_showcase import cmd_reconcile

            say("  Stopping the log generator to compare exact counts ...")
            self.procs["simulator"].stop(graceful=False)
            cmd_reconcile()
            self.start_simulator(NORMAL_REJECT_RATE)
        say("  Full evidence (5 min outage at 5,000 lines/s, exact counts):")
        say("  docs/plan/ubs140-day1-acceptance.md")

    def step_heartbeat(self) -> None:
        banner(f"7/{self.steps_total}", "Agent stops: AgentHeartbeatMissing")
        say("  Stopping the agent. The backend alerts after 20s without a heartbeat")
        say("  (demo profile; default 60s).")
        self.agent_outage()
        if self.showcase:
            say("  Second outage of the same agent: it alerts again, with a new")
            say("  alert ID (UBS-136).")
            self.agent_outage()
        from scripts.demo_showcase import short_id

        ids = sorted(
            short_id(a["alertId"]) for a in self.alerts("AgentHeartbeatMissing", "all")
        )
        say(f"  AgentHeartbeatMissing occurrences: {', '.join(ids)}")

    def agent_outage(self) -> None:
        resolved_before = len(self.alerts("AgentHeartbeatMissing", "resolved"))
        self.procs["agent"].stop(graceful=True)
        start = time.monotonic()
        alert = wait_for(
            "AgentHeartbeatMissing firing",
            lambda: [
                a
                for a in self.alerts("AgentHeartbeatMissing", "active")
                if a["status"] == "firing"
            ],
            timeout=90,
            interval=1,
        )[0]
        say(
            f"  After {time.monotonic() - start:.0f}s: {alert['ruleName']}"
            f" {alert['status']} for {alert['agentId']}"
        )
        self.pause("Bring the agent back", 2)
        self.start_agent()
        wait_for(
            "AgentHeartbeatMissing resolved",
            lambda: (
                len(self.alerts("AgentHeartbeatMissing", "resolved")) > resolved_before
            ),
            timeout=60,
            interval=1,
        )
        say("  Agent is back; the alert resolved.")

    def step_showcase(self) -> None:
        from scripts import demo_showcase as show

        banner(
            f"8/{self.steps_total}",
            "Privacy, rule test mode and questions via Copilot's tools",
        )
        say("  Privacy  [Day-1 #5]")
        show.cmd_privacy()
        self.pause("Next: rule test mode", 2)
        show.cmd_replay("HighRejectRate")
        self.pause("Next: questions through the MCP server", 2)
        show.cmd_ask(list(show.TOUR), executive=False)

    def run(self) -> None:
        self.preflight()
        self.step_start()
        steps = [
            ("Normal trading", self.step_normal),
            ("Reject burst", self.step_burst),
            ("HighRejectRate alert", self.step_alert),
            ("Ask in plain English", self.step_nl),
            ("Rotation and restart", self.step_restart),
            ("Agent stops", self.step_heartbeat),
        ]
        if self.showcase:
            steps.append(("Privacy, rule test mode, Copilot", self.step_showcase))
        for title, step in steps:
            self.pause(f"Next: {title}")
            step()
        banner("Done", f"Process logs: {RUN / 'proc'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UBS-134 guided Day-1 demo")
    parser.add_argument(
        "--auto", action="store_true", help="run every step with timed waits"
    )
    parser.add_argument(
        "--no-teams", action="store_true", help="don't start the Teams bot"
    )
    parser.add_argument(
        "--showcase",
        action="store_true",
        help="add the feature showcase (scripts/demo_showcase.py) to the storyline",
    )
    args = parser.parse_args(argv)
    demo = Demo(auto=args.auto, teams=not args.no_teams, showcase=args.showcase)
    try:
        demo.run()
    except DemoError as exc:
        say(f"\n  DEMO STOPPED: {exc}")
        say(f"  Process logs: {RUN / 'proc'}")
        return 1
    except KeyboardInterrupt:
        say("\n  Interrupted.")
        return 130
    finally:
        demo.stop_all()
        demo.http.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
