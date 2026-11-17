"""UBS-134: guided Day-1 demo on the real entrypoints.

    uv run python -m scripts.demo            # guided: press Enter between steps
    uv run python -m scripts.demo --auto     # rehearsal: timed, no input

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
agent raising AgentHeartbeatMissing. See the runbook in the PR notes.

Local hosting only. Process output goes to .demo-run/proc/<name>.log.
"""

from __future__ import annotations

import argparse
import json
import os
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


def port_in_use(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


class Demo:
    def __init__(self, *, auto: bool, teams: bool) -> None:
        self.auto = auto
        self.teams = teams
        self.env = {**os.environ, **DEV_ENV}
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
                str(ROOT / "config/demo/agent.yaml"),
            ],
            RUN,
        )

    def stop_all(self) -> None:
        for name in ("simulator", "agent", "teams", "magic-stub", "backend"):
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
        rate = t.get("reject_rate", 0.0)
        say(
            f"  {label:<26} submitted={t.get('orders_submitted', 0):>6.0f}"
            f"  acked={t.get('orders_acked', 0):>6.0f}"
            f"  rejected={t.get('orders_rejected', 0):>6.0f}"
            f"  reject_rate={rate:6.1%}"
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
        banner("0/7", "Preflight")
        busy = [p for p in (8080, 8081, 9000, 3978) if port_in_use(p)]
        if not self.teams and 3978 in busy:
            busy.remove(3978)
        if busy:
            raise DemoError(f"ports already in use: {busy}; stop old runs first")
        try:
            tags = httpx.get("http://127.0.0.1:11434/api/tags", timeout=2).json()
            models = [m.get("name", "") for m in tags.get("models", [])]
            if any(m.startswith("llama3.2") for m in models):
                say("  Ollama: llama3.2 available")
            else:
                say("  Ollama: running, but llama3.2 is not pulled (ollama pull)")
        except httpx.HTTPError:
            say("  Ollama: not running. Rule-matched questions still answer;")
            say("  free-form questions get the backend's fallback reply.")
        if RUN.exists():
            shutil.rmtree(RUN)
        (RUN / "logs").mkdir(parents=True)
        say(f"  Fresh run folder: {RUN}")

    def step_start(self) -> None:
        banner("1/7", "Start the stack (real entrypoints)")
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
        banner("2/7", "Normal trading: query the backend")
        say("  POST /telemetry/query/metrics  (derived counters only, no raw logs)")
        for _ in range(3):
            self.show_totals("last 5 minutes", "5m")
            time.sleep(2)
        health = self.http.get(f"/telemetry/health/agents/{AGENT_ID}")
        if health.status_code == 200:
            say(f"  Agent health: {health.json().get('status', '?')}")

    def step_burst(self) -> None:
        banner("3/7", "Reject burst visible within 5 s  (spec 000 s7 #1)")
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
        banner("4/7", "HighRejectRate fires and resolves  (spec 000 s7 #2)")
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
            say(
                f"  GET /telemetry/alerts: {alert['ruleName']} {alert['status']}"
                f" severity={alert['severity']} observed={alert['observedValue']}"
            )
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
        banner("5/7", "Ask in Teams  (spec 000 s7 #3)")
        if self.teams:
            say("  Teams bot is on http://localhost:3978/api/messages.")
            say("  Open the Teams App Test Tool in another terminal:")
            say("    npx @microsoft/teams-app-test-tool start \\")
            say("      -e http://localhost:3978/api/messages -c msteams")
            say(f'  and ask: "{QUESTION}"')
        say("  The same question through the backend NL API the bot calls:")
        response = self.http.post("/telemetry/nl/query", json={"question": QUESTION})
        response.raise_for_status()
        answer = response.json()
        say(f"  Answer: {answer.get('answer', answer)}")
        if answer.get("kind") == "answer":
            say(
                f"  intent={answer.get('intent')} source={answer.get('source')}"
                f" confidence={answer.get('confidence')}"
            )
            data = (answer.get("data") or {}).get("totals") or {}
            say(f"  Numbers behind the answer: {data}")
        self.show_totals("metrics query, last 30m", "30m")
        self.pause("Ask the question in the Test Tool now", 2)

    def step_restart(self) -> None:
        banner("6/7", "Rotation and agent restart  (spec 000 s7 #4, short form)")
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
        say(f"  restartedBuckets={completeness.get('restartedBuckets', 0)}")
        say("  Full evidence (5 min outage at 5,000 lines/s, exact counts):")
        say("  docs/plan/ubs140-day1-acceptance.md")

    def step_heartbeat(self) -> None:
        banner("7/7", "Agent stops: AgentHeartbeatMissing")
        say("  Stopping the agent. The backend alerts after 20s without a heartbeat")
        say("  (demo profile; default 60s).")
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
            lambda: self.alerts("AgentHeartbeatMissing", "resolved"),
            timeout=60,
            interval=1,
        )
        say("  Agent is back; the alert resolved.")
        say("  Known limit: a second outage of the same agent does not alert")
        say("  again yet (UBS-136).")

    def run(self) -> None:
        self.preflight()
        self.step_start()
        steps = (
            ("Normal trading", self.step_normal),
            ("Reject burst", self.step_burst),
            ("HighRejectRate alert", self.step_alert),
            ("Ask in Teams", self.step_nl),
            ("Rotation and restart", self.step_restart),
            ("Agent stops", self.step_heartbeat),
        )
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
    args = parser.parse_args(argv)
    demo = Demo(auto=args.auto, teams=not args.no_teams)
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
