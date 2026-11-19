"""Demo showcase commands: show the built features the core storyline doesn't.

    uv run python -m scripts.demo_showcase <command> [args]

Run them against a demo stack started by `scripts\\demo_windows.bat`,
`scripts/demo_mac/demo.sh` or `scripts/demo.py`. The launchers expose each one as
a command of their own (`demo_windows.bat privacy`, `demo.sh replay`, ...).

    prepare            copy config/demo/*.yaml into .demo-run/config (launchers do this)
    alerts             every alert so far, with callback delivery status and attempts
    tamper             re-post the last callback, forged signature: the stub says 401
    privacy            UBS-137 leak sentinel, then live events and callbacks checked
    replay [RULE]      rule test mode on this run's own logs; nothing is dispatched
    reload strict|reset  edit the run's rules.yaml; the agent reloads it within ~10 s
    reconcile          generated vs queried order and reject counts (simulator stopped)
    outage [SECONDS]   the UBS-140 acceptance harness in quick mode
    malformed [N]      append N broken lines: parse errors rise, the agent stays up
    ask [QUESTION]     ask through the MCP server (the Copilot path); no question = tour
    health             agent health detail plus backend Prometheus counters
    mcp-check          would a dev-tunnel Host header be accepted by the MCP server?

Like scripts/demo.py, this holds no telemetry logic: it calls the public APIs,
the MCP server, the Magic stub and the real CLIs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import yaml

from scripts.demo import (
    AGENT_ID,
    BACKEND,
    INSTANCE,
    QUESTION,
    ROOT,
    RUN,
    DemoError,
    console_script,
    say,
)

DEMO_CONFIG = ROOT / "config" / "demo"
RUN_CONFIG = RUN / "config"
# Written by `prepare` when a run starts; `reconcile` counts from here.
RUN_STARTED = RUN / "started-at.txt"
# The bot's saved alert chat (TEAMS_NOTIFY_STATE_PATH, relative to the repo,
# where every launcher starts the bot). The Agents Playground opens a new chat
# each run, and the bot keeps the first chat it sees, so a saved one from an
# earlier run sends every alert card to a dead chat (404 ConversationNotFound)
# even after "hi". `prepare` clears it; the next "hi" registers the new chat.
TEAMS_CHAT_STATE = ROOT / os.environ.get(
    "TEAMS_NOTIFY_STATE_PATH", ".teams-state/conversation.json"
)
CONFIG_FILES = ("agent.yaml", "rules.yaml", "anomaly.yaml")
MCP_URL = "http://127.0.0.1:8765/mcp"
STUB_URL = "http://127.0.0.1:9000/magic/callbacks/telemetry-alerts"
INTERNAL = "http://127.0.0.1:8081"
SENTINEL_TEST = ROOT / "tests" / "integration" / "test_UBS_137_data_leak_sentinel.py"
STRICT_RULE, STRICT_SEVERITY, STRICT_THRESHOLD = "HighRejectRate", "warning", 0.004
TOUR = (
    QUESTION,
    "How is Magic doing today?",
    "Any alerts open for Magic?",
    "Which reject reasons are increasing?",
    "Is telemetry actually working?",
    "Are we failing to parse anything?",
)
# What a leak would look like in this run: the simulator's plaintext order IDs
# (`11=ORD1234`) and its tag-58 reject text.
LEAK_PATTERNS = (re.compile(r"ORD\d{3,}"), re.compile(r"Price exceeds limit"))


# --- pure helpers (unit-tested) --------------------------------------------------


def rotated_logs(logs: Path, name: str) -> list[Path]:
    """`name` and its numbered archives, oldest first: `name.N` ... `name.1`, `name`."""
    archives = sorted(
        (p for p in logs.glob(f"{name}.*") if p.suffix[1:].isdigit()),
        key=lambda p: int(p.suffix[1:]),
        reverse=True,
    )
    current = logs / name
    return [*archives, *([current] if current.exists() else [])]


def count_fix_orders(paths: Iterable[Path]) -> tuple[int, int]:
    """(orders submitted, orders rejected) in Magic FIX logs, by message type.

    Only complete messages count (ending in a `10=` checksum field), the same as
    the agent: a broken line such as the ones `malformed` writes is a parse
    error, not an order.
    """
    orders = rejects = 0
    for path in paths:
        with path.open(encoding="utf-8", errors="replace") as lines:
            for line in lines:
                if "|10=" not in line:
                    continue
                if "|35=D|" in line:
                    orders += 1
                elif "|35=8|" in line and "|39=8|" in line:
                    rejects += 1
    return orders, rejects


def set_tier_threshold(
    rules_yaml: str, rule: str, severity: str, threshold: float
) -> str:
    """`rules_yaml` with one tier of one rule changed (comments are not kept)."""
    doc = yaml.safe_load(rules_yaml)
    for entry in doc.get("rules", []):
        if entry.get("name") == rule:
            for tier in entry.get("tiers", []):
                if tier.get("severity") == severity:
                    tier["threshold"] = threshold
                    return yaml.safe_dump(doc, sort_keys=False)
    raise DemoError(f"rule {rule!r} has no {severity!r} tier")


def leaks_in(text: str) -> list[str]:
    """Plaintext order IDs or tag-58 text found in `text`."""
    return sorted({m.group(0) for p in LEAK_PATTERNS for m in p.finditer(text)})


def _clock(value: str | None) -> str:
    if not value:
        return ""
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return moment.astimezone().strftime("%H:%M:%S")


def short_id(alert_id: str) -> str:
    """8 characters that tell occurrences apart. Agent IDs are UUIDs (use the
    head); backend IDs are `backend-<rule>-<hash>` (use the hash)."""
    return (
        alert_id.rsplit("-", 1)[-1][:8]
        if alert_id.startswith("backend-")
        else (alert_id[:8])
    )


def _delivery(alert: dict[str, Any]) -> str:
    if alert.get("source") == "backend":
        return "n/a (raised by the backend)"
    delivery = alert.get("delivery") or {}
    attempts = delivery.get("attempts", 0)
    plural = "" if attempts == 1 else "s"
    return f"{delivery.get('status', '?')} ({attempts} attempt{plural})"


def alerts_table(alerts: Sequence[dict[str, Any]]) -> list[str]:
    """One row per alert: id, rule, severity, status, values, times, delivery."""
    if not alerts:
        return ["No alerts yet."]
    fmt = "{:<8} {:<27} {:<8} {:<9} {:>9} {:>9} {:>8} {:>8}  {}"
    rows = [
        fmt.format(
            "id",
            "rule",
            "severity",
            "status",
            "observed",
            "threshold",
            "first",
            "resolved",
            "callback to Magic",
        )
    ]
    for a in alerts:
        observed = a.get("observedValue")
        rows.append(
            fmt.format(
                short_id(str(a.get("alertId", ""))),
                str(a.get("ruleName", ""))[:27],
                a.get("severity", ""),
                a.get("status", ""),
                "" if observed is None else f"{observed:.4g}",
                f"{a.get('threshold', ''):.4g}"
                if isinstance(a.get("threshold"), (int, float))
                else "",
                _clock(a.get("firstObservedUtc")),
                _clock(a.get("resolvedAtUtc")),
                _delivery(a),
            )
        )
    return rows


def answer_lines(result: dict[str, Any]) -> list[str]:
    """The parts of an `nl_query` result worth showing on screen."""
    if "error" in result:
        return [f"  error: {result['error']} {result.get('message', '')}".rstrip()]
    if result.get("kind") != "answer":
        lines = [f"  {result.get('message') or result.get('reply') or result}"]
        suggested = result.get("suggestedQuestions") or []
        lines += [f"    try: {q}" for q in suggested[:3]]
        return lines
    completeness = result.get("dataCompleteness") or {}
    citations = ", ".join(
        f"{c.get('type')} {c.get('queryId') or c.get('alertId') or ''}".strip()
        for c in result.get("citations") or []
    )
    lines = [
        f"  A: {result.get('answer')}",
        f"     intent {result.get('intent')}, answered by {result.get('source')}, "
        f"data {completeness.get('confidence', '?')} "
        f"({completeness.get('agentsReporting', '?')}/"
        f"{completeness.get('agentsExpected', '?')} agents)",
    ]
    if citations:
        lines.append(f"     cites: {citations}")
    for caveat in result.get("caveats") or []:
        lines.append(f"     caveat: {caveat}")
    return lines


# --- live commands ---------------------------------------------------------------


def _http() -> httpx.Client:
    return httpx.Client(base_url=BACKEND, timeout=15.0)


def _need_run() -> None:
    if not (RUN / "logs").is_dir():
        raise DemoError("no .demo-run/logs; start the demo stack first")


def agent_config() -> Path:
    """The agent config the launchers start: the run copy if there is one."""
    copy = RUN_CONFIG / "agent.yaml"
    return copy if copy.exists() else DEMO_CONFIG / "agent.yaml"


def cmd_prepare() -> int:
    RUN_CONFIG.mkdir(parents=True, exist_ok=True)
    RUN_STARTED.write_text(datetime.now(UTC).isoformat() + "\n", encoding="utf-8")
    if TEAMS_CHAT_STATE.exists():
        TEAMS_CHAT_STATE.unlink()
        say('  Cleared the saved alert chat; say "hi" in the Playground for cards.')
    for name in CONFIG_FILES:
        shutil.copyfile(DEMO_CONFIG / name, RUN_CONFIG / name)
    say(f"  Demo config copied to {RUN_CONFIG} (edits there never touch the repo).")
    return 0


def cmd_alerts() -> int:
    with _http() as http:
        body = http.get("/telemetry/alerts", params={"status": "all", "limit": 50})
        body.raise_for_status()
        data = body.json()
    for row in alerts_table(data.get("alerts") or []):
        say(row)
    counts = data.get("counts") or {}
    say(
        f"Active: {counts.get('active', 0)}  (critical {counts.get('critical', 0)},"
        f" warning {counts.get('warning', 0)})"
    )
    return 0


def _last_callback() -> dict[str, Any] | None:
    path = RUN / "callbacks.jsonl"
    if not path.exists():
        return None
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None
    alert: dict[str, Any] = json.loads(lines[-1])["alert"]
    return alert


def cmd_tamper(url: str = STUB_URL) -> int:
    alert = _last_callback()
    body = json.dumps(alert or {"demo": "tamper test"}).encode()
    what = f"the last {alert.get('ruleName')} callback" if alert else "a test body"
    say(f"  Re-sending {what} to the Magic stub with a forged signature ...")
    response = httpx.post(
        url,
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Telemetry-Timestamp": str(int(time.time())),
            "X-Telemetry-Signature": "v1=" + "0" * 64,
            "X-Telemetry-Delivery-Id": "demo-tamper",
        },
        timeout=5,
    )
    verdict = "rejected" if response.status_code == 401 else "NOT rejected"
    say(f"  Magic stub answered {response.status_code}: tampered callback {verdict}.")
    say("  Genuine callbacks carry v1=HMAC-SHA256(timestamp.body) with the shared")
    say("  secret (FR-CBK-005); the stub checks it with the agent's own `sign`.")
    return 0 if response.status_code == 401 else 1


def cmd_privacy() -> int:
    say("  1. Automated leak sentinel (UBS-137, FR-TST-005, NFR-SEC-002):")
    say(f"     pytest {SENTINEL_TEST.relative_to(ROOT).as_posix()}")
    result = subprocess.run(  # noqa: S603 - fixed argv
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            str(SENTINEL_TEST),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    tail = [ln for ln in result.stdout.splitlines() if ln.strip()][-1:]
    say(f"     {tail[0] if tail else result.stderr.strip()[-200:]}")
    say("  2. This run's live output:")
    with _http() as http:
        events = http.get("/telemetry/events", params={"limit": 200}).json()
        alerts = http.get(
            "/telemetry/alerts", params={"status": "all", "limit": 50}
        ).json()
    items = events.get("events") or events.get("items") or []
    sample = next((e for e in items if any("Hash" in k for k in _flat_keys(e))), None)
    if sample is not None:
        say("     One sanitised event (identifiers hashed, no raw line or tag 58):")
        for line in json.dumps(sample, indent=2).splitlines()[:24]:
            say(f"       {line}")
    callbacks = (
        (RUN / "callbacks.jsonl").read_text(encoding="utf-8")
        if (RUN / "callbacks.jsonl").exists()
        else ""
    )
    checked = {
        "events API": json.dumps(events),
        "alerts API": json.dumps(alerts),
        "callbacks to Magic": callbacks,
    }
    # The same patterns in the raw logs on this host, to show they are there.
    raw = sum(
        len(LEAK_PATTERNS[0].findall(p.read_text(encoding="utf-8", errors="replace")))
        for p in (RUN / "logs").glob("Fix.log*")
    )
    leaks_found = False
    for name, text in checked.items():
        found = leaks_in(text)
        leaks_found |= bool(found)
        say(
            f"     {name:<20} plaintext order IDs / tag-58 text: "
            f"{', '.join(found[:3]) if found else 'none'}"
        )
    say(f"     For contrast, the raw Fix logs on this host hold {raw:,} plaintext")
    say("     order IDs; none of them left the host.")
    return 1 if result.returncode or leaks_found else 0


def _flat_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, inner in value.items():
            yield key
            yield from _flat_keys(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from _flat_keys(inner)


def cmd_replay(rule: str) -> int:
    _need_run()
    logs = RUN / "logs"
    name = "Application.log" if rule.startswith("App") else "Fix.log"
    files = rotated_logs(logs, name)
    if not files:
        raise DemoError(f"no {name} in {logs} yet")
    say(f"  Rule test mode: replaying {len(files)} {name} file(s) through {rule}.")
    say("  It evaluates exactly like the live agent but never calls Magic.")
    result = subprocess.run(  # noqa: S603 - fixed argv
        [
            console_script("telemetry-agent"),
            "--config",
            str(agent_config()),
            "--log-level",
            "warning",
            "--test-rule",
            rule,
            "--replay",
            *(str(f.relative_to(RUN)) for f in files),
        ],
        cwd=RUN,
        capture_output=True,
        text=True,
        check=False,
    )
    for line in result.stdout.splitlines():
        say(f"    {line}")
    if result.returncode:
        say(result.stderr.strip()[-600:])
    return result.returncode


def cmd_reload(mode: str) -> int:
    rules = RUN_CONFIG / "rules.yaml"
    if not rules.exists():
        raise DemoError(
            "no .demo-run/config/rules.yaml; restart the stack with the launcher"
        )
    original = (DEMO_CONFIG / "rules.yaml").read_text(encoding="utf-8")
    if mode == "strict":
        rules.write_text(
            set_tier_threshold(
                original, STRICT_RULE, STRICT_SEVERITY, STRICT_THRESHOLD
            ),
            encoding="utf-8",
        )
        say(
            f"  Saved {rules}: {STRICT_RULE} {STRICT_SEVERITY} tier 0.03 -> "
            f"{STRICT_THRESHOLD} (normal traffic now breaches it)."
        )
    else:
        rules.write_text(original, encoding="utf-8")
        say(f"  Saved {rules}: back to the demo thresholds.")
    want_firing = mode == "strict"
    start = time.monotonic()
    say("  The agent was not restarted; waiting for it to pick up the file ...")
    with _http() as http:
        while time.monotonic() - start < 90:
            active = http.get(
                "/telemetry/alerts",
                params={"status": "active", "ruleName": STRICT_RULE},
            ).json()["alerts"]
            if bool(active) == want_firing:
                state = "firing" if want_firing else "no longer active"
                say(
                    f"  {STRICT_RULE} {state} {time.monotonic() - start:.0f}s after "
                    f"the save (reload check every 10s, then its for/resolveAfter)."
                )
                return 0
            time.sleep(1)
    say("  No change within 90s; check the agent window for a reload message.")
    return 1


def _totals(http: httpx.Client, since: datetime) -> tuple[int, int]:
    body = http.post(
        "/telemetry/query/metrics",
        json={
            "timeRange": {
                "fromUtc": since.isoformat().replace("+00:00", "Z"),
                "toUtc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            },
            "filters": {"instanceId": INSTANCE},
            "metrics": ["orders_submitted", "orders_rejected"],
        },
    )
    body.raise_for_status()
    totals = body.json().get("totals") or {}
    return int(totals.get("orders_submitted") or 0), int(
        totals.get("orders_rejected") or 0
    )


def _run_started() -> datetime:
    """When this run began. Not the logs folder's ctime: on macOS and Linux
    that changes on every rotation (a rename in the folder), so the "whole run"
    query would cover only the last minute or two and report false losses."""
    try:
        return datetime.fromisoformat(RUN_STARTED.read_text(encoding="utf-8").strip())
    except OSError, ValueError:
        st = (RUN / "logs").stat()
        # st_birthtime is creation time on macOS/BSD; Windows ctime is creation time.
        return datetime.fromtimestamp(getattr(st, "st_birthtime", st.st_ctime), UTC)


def cmd_reconcile() -> int:
    _need_run()
    files = rotated_logs(RUN / "logs", "Fix.log")
    since = _run_started() - timedelta(minutes=1)
    say("  Waiting for the backend counts to settle (simulator stopped) ...")
    with _http() as http:
        last, stable = (-1, -1), 0
        deadline = time.monotonic() + 90
        while stable < 3 and time.monotonic() < deadline:
            now = _totals(http, since)
            stable = stable + 1 if now == last else 0
            last = now
            time.sleep(2)
    generated = count_fix_orders(files)
    lost = (generated[0] - last[0], generated[1] - last[1])
    say(
        f"  Generated in {len(files)} Fix.log file(s), rotations included: "
        f"{generated[0]:,} orders, {generated[1]:,} rejects"
    )
    say(
        f"  Backend metrics query for the whole run:          "
        f"{last[0]:,} orders, {last[1]:,} rejects"
    )
    say(
        f"  Lost: {lost[0]:,} orders, {lost[1]:,} rejects"
        + ("  (exact)" if lost == (0, 0) else "")
    )
    if len(files) > 1 and not (RUN / "logs" / "Fix.log.1").exists():
        say("  Note: archive numbering has gaps; some rotated files may be gone.")
    return 0 if lost == (0, 0) else 1


def cmd_outage(seconds: float) -> int:
    say(f"  UBS-140 acceptance harness, quick mode: a {seconds:.0f}s connectivity")
    say("  outage, log rotation and a graceful agent restart in one run, compared")
    say("  with ground truth. (The recorded run: 300s outage at 5,000 lines/s.)")
    with tempfile.TemporaryDirectory(prefix="demo-outage-") as tmp:
        out = Path(tmp) / "report.json"
        result = subprocess.run(  # noqa: S603 - fixed argv
            [
                sys.executable,
                "-m",
                "scripts.day1_acceptance",
                "--rate",
                "100",
                "--outage-seconds",
                str(seconds),
                "--bucket-seconds",
                "1",
                "--output",
                str(out),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if not out.exists():
            say(result.stderr.strip()[-800:])
            return 1
        report = json.loads(out.read_text(encoding="utf-8"))
    vis = ", ".join(
        "missed" if v is None else f"{v:.2f}s" for v in report["visibility_seconds"]
    )
    say(f"  Burst visibility trials:        {vis}")
    say(
        f"  Orders generated / queried:     {report['generated_orders']:,} / "
        f"{report['queried_orders']:,}  (missing {report['missing_orders']}, "
        f"excess {report['excess_orders']})"
    )
    say(f"  Signed callbacks during outage: {report['signed_callbacks_during_outage']}")
    say(
        f"  Failed publish attempts (buffered, then sent): "
        f"{report['failed_publish_attempts']}"
    )
    resume = report.get("restart_resume_seconds")
    say(
        f"  Restart resumed ingestion in:   "
        f"{'-' if resume is None else f'{resume:.3f}s'}"
    )
    say(f"  Findings: {'; '.join(report['findings']) or 'none'}")
    return result.returncode


def _agent_health(http: httpx.Client) -> dict[str, Any]:
    response = http.get(f"/telemetry/health/agents/{AGENT_ID}")
    response.raise_for_status()
    detail: dict[str, Any] = response.json()
    return detail


def cmd_malformed(count: int) -> int:
    _need_run()
    with _http() as http:
        before = _agent_health(http).get("parseErrorCountLast5Min", 0)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        broken = [
            f"{stamp} : 8=FIX.4.2|9=999|35=D|49=CLIENT|BROKEN-NO-CHECKSUM",
            f"{stamp} : 8=FIX.4.2|9=5|35=|10=000|",
            "\x00\x07garbage bytes ÿþ not a log line",
            f"{stamp} : 8=FIX.4.2|9=40|35=8|39=|150=|10=999|",
        ]
        with (RUN / "logs" / "Fix.log").open("a", encoding="utf-8") as fix:
            for n in range(count):
                fix.write(broken[n % len(broken)] + "\n")
        say(
            f"  Appended {count} malformed line(s) to Fix.log "
            f"(parse errors in the last 5 min before: {before})."
        )
        deadline = time.monotonic() + 30
        after = before
        while time.monotonic() < deadline:
            time.sleep(2)
            health = _agent_health(http)
            after = health.get("parseErrorCountLast5Min", 0)
            if after > before:
                break
        say(
            f"  Parse errors in the last 5 min now: {after} "
            f"(agent status {health.get('status')}, still reading)."
        )
    return 0 if after > before else 1


def cmd_health() -> int:
    with _http() as http:
        h = _agent_health(http)
    say(
        f"  Agent {h.get('agentId')} v{h.get('agentVersion')}: {h.get('status')} "
        f"(reports {h.get('reportedStatus')}), up {h.get('uptimeSeconds')}s, "
        f"last heartbeat {h.get('heartbeatAgeMs')} ms ago"
    )
    say(
        f"  Log read lag {h.get('logReadLagMs')} ms, parse errors (5 min) "
        f"{h.get('parseErrorCountLast5Min')}, callback failures (5 min) "
        f"{h.get('callbackFailuresLast5Min')}"
    )
    say(
        f"  Publish queue {h.get('publishQueueDepth')} batches / "
        f"{h.get('publishBufferBytes')} bytes, dropped events (5 min) "
        f"{h.get('droppedEventsLast5Min')}, active alerts {h.get('activeAlertCount')}"
    )
    for f in h.get("files") or []:
        rest = {k: v for k, v in f.items() if k != "path"}
        say(f"    file {f.get('path')}: {json.dumps(rest)}")
    usage = h.get("resourceUsage")
    if usage:
        say(f"  Resource usage: {json.dumps(usage)}")
    try:
        text = httpx.get(f"{INTERNAL}/metrics", timeout=5).text
    except httpx.HTTPError:
        return 0
    wanted = re.compile(
        r"^telemetry_backend_\w*(batches|alerts|queries|events)\w*(\{.*\})? "
    )
    picked = [ln for ln in text.splitlines() if wanted.match(ln)][:10]
    if picked:
        say("  Backend Prometheus counters (:8081/metrics):")
        for line in picked:
            say(f"    {line}")
    return 0


async def _mcp_ask(questions: Sequence[str], audience: str | None) -> int:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(MCP_URL) as (read, write, *_):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for question in questions:
                say(f"  Q: {question}")
                args: dict[str, Any] = {"question": question}
                if audience:
                    args["audience"] = audience
                result = await session.call_tool("nl_query", args)
                payload: Any = result.structured_content
                if not payload:
                    text = "".join(getattr(c, "text", "") for c in result.content)
                    payload = json.loads(text) if text else {}
                for line in answer_lines(payload):
                    say(line)
                say()
    return 0


def cmd_ask(questions: Sequence[str], executive: bool) -> int:
    say(f"  Through the MCP server Copilot uses ({MCP_URL}, tool nl_query):")
    return asyncio.run(_mcp_ask(questions, "executive" if executive else None))


def cmd_mcp_check() -> int:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "demo-check", "version": "1"},
        },
    }
    configured = [
        h.strip() for h in os.environ.get("MCP_ALLOWED_HOSTS", "").split(",") if h
    ]
    host = configured[0] if configured else "demo-1234.asse.devtunnels.ms"
    headers = {"Accept": "application/json, text/event-stream"}
    local = httpx.post(MCP_URL, json=body, headers=headers, timeout=5)
    tunnel = httpx.post(
        MCP_URL, json=body, headers={**headers, "Host": host}, timeout=5
    )
    say(f"  Local request:              HTTP {local.status_code}")
    say(f"  Host: {host}  HTTP {tunnel.status_code}")
    if tunnel.status_code == 421:
        say("  The MCP server refuses that Host header, so Copilot Studio through a")
        say("  dev tunnel would get 421. Start the stack with MCP_ALLOWED_HOSTS set")
        say("  to the tunnel's hostname (see the runbook's Copilot section).")
        return 1
    say("  That Host header is accepted; a dev tunnel with it will work.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in (
        "prepare",
        "alerts",
        "tamper",
        "privacy",
        "reconcile",
        "health",
        "mcp-check",
    ):
        sub.add_parser(name)
    p = sub.add_parser("replay")
    p.add_argument("rule", nargs="?", default="HighRejectRate")
    p = sub.add_parser("reload")
    p.add_argument("mode", choices=("strict", "reset"))
    p = sub.add_parser("outage")
    p.add_argument("seconds", nargs="?", type=float, default=30.0)
    p = sub.add_parser("malformed")
    p.add_argument("count", nargs="?", type=int, default=20)
    p = sub.add_parser("ask")
    p.add_argument("question", nargs="*")
    p.add_argument("--executive", action="store_true", help="executive audience")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "prepare":
            return cmd_prepare()
        if args.cmd == "alerts":
            return cmd_alerts()
        if args.cmd == "tamper":
            return cmd_tamper()
        if args.cmd == "privacy":
            return cmd_privacy()
        if args.cmd == "replay":
            return cmd_replay(args.rule)
        if args.cmd == "reload":
            return cmd_reload(args.mode)
        if args.cmd == "reconcile":
            return cmd_reconcile()
        if args.cmd == "outage":
            return cmd_outage(args.seconds)
        if args.cmd == "malformed":
            return cmd_malformed(args.count)
        if args.cmd == "health":
            return cmd_health()
        if args.cmd == "mcp-check":
            return cmd_mcp_check()
        question = " ".join(args.question)
        return cmd_ask([question] if question else list(TOUR), args.executive)
    except DemoError as exc:
        say(f"  {exc}")
        return 1
    except httpx.HTTPError as exc:
        say(f"  Could not reach the demo stack: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
