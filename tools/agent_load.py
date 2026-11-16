"""Agent footprint load test: NFR-PERF-001/003 at Q-1's synthetic rates (spec 012 s5).

    make agent-load        # 5,000 lines/s for 300 s, then a 20,000 lines/s burst
    uv run python tools/agent_load.py --rate 5000 --seconds 300

Starts the real agent entrypoint (`telemetry_agent.main`) on a temp copy of
config/agent.yaml with publish and callbacks in dry-run (no network), appends
the simulator's synthetic FIX and Application.log lines at a fixed rate,
samples the agent's CPU and RSS once a second with psutil, stops it with
SIGTERM and prints one JSON summary, including the agent's own shutdown
counters (lines ingested, drops). Results: docs/plan/agent-load-test.md.
"""

from __future__ import annotations

import argparse
import ast
import json
import platform
import random
import re
import signal
import subprocess
import sys
import tempfile
import time
from collections import deque
from pathlib import Path
from typing import Any

import psutil
import yaml
from simulator.mock_logger import (
    SYMBOLS,
    format_fix_line,
    generate_application_log,
    generate_fix_order_messages,
    get_timestamps,
)

AGENT_YAML = Path(__file__).resolve().parents[1] / "config" / "agent.yaml"
MB = 1024 * 1024
TAIL_SECONDS = 1.0  # after the last write, so the agent reads the final lines
_STOPPED = re.compile(
    r"stopped: ingest (\{.*?\}), pipeline (\{.*?\}), evaluator (\{.*?\}), "
    r"publisher (\{.*?\}), events (\{.*?\})"
)


def _config(tmp: Path) -> Path:
    cfg = yaml.safe_load(AGENT_YAML.read_text())
    cfg["logs"]["paths"] = [str(tmp / "Application.log"), str(tmp / "Fix.log")]
    cfg["logs"]["stateDir"] = str(tmp / "state")
    cfg["rules"]["path"] = str(AGENT_YAML.parent / cfg["rules"]["path"])
    cfg["publish"]["dryRun"] = True
    cfg["callbacks"]["dryRun"] = True
    path = tmp / "agent.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path


def run(rate: int, seconds: float) -> dict[str, Any]:
    random.seed(0)
    with tempfile.TemporaryDirectory(prefix="agent-load-") as name:
        tmp = Path(name)
        config = _config(tmp)
        app_log = (tmp / "Application.log").open("a", encoding="ascii")
        fix_log = (tmp / "Fix.log").open("a", encoding="ascii")
        agent_log = tmp / "agent.log"
        with agent_log.open("w") as out:
            agent = subprocess.Popen(
                [sys.executable, "-m", "telemetry_agent.main", "--config", str(config)],
                stdout=out,
                stderr=out,
            )
        try:
            deadline = time.monotonic() + 30
            while " tailing " not in agent_log.read_text():  # the startup log line
                if agent.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("agent did not start")
                time.sleep(0.2)
            time.sleep(1)  # let it settle before the idle RSS reading
            proc = psutil.Process(agent.pid)
            rss_idle = proc.memory_info().rss

            fix_backlog: deque[str] = deque()
            orders = written = bytes_written = 0
            cores: list[float] = []
            rss: list[int] = []
            start = last_t = time.monotonic()
            cpu0 = last_cpu = sum(proc.cpu_times()[:2])  # user + system
            while (now := time.monotonic()) < start + seconds + TAIL_SECONDS:
                due = int(min(now - start, seconds) * rate) - written
                app_ts, fix_ts = get_timestamps()
                app_lines, fix_lines = [], []
                for i in range(written, written + due):
                    if i % 2:
                        app_lines.append(generate_application_log(app_ts))
                        continue
                    if not fix_backlog:
                        orders += 1
                        fix_backlog.extend(
                            generate_fix_order_messages(
                                f"ORD{orders}", random.choice(SYMBOLS)
                            )
                        )
                    fix_lines.append(format_fix_line(fix_ts, fix_backlog.popleft()))
                for f, lines in ((app_log, app_lines), (fix_log, fix_lines)):
                    if lines:
                        chunk = "\n".join(lines) + "\n"
                        f.write(chunk)
                        f.flush()
                        bytes_written += len(chunk)
                written += due

                if now - last_t >= 1.0:
                    if agent.poll() is not None:
                        raise RuntimeError(f"agent exited with {agent.returncode}")
                    cpu = sum(proc.cpu_times()[:2])
                    cores.append((cpu - last_cpu) / (now - last_t))
                    rss.append(proc.memory_info().rss)
                    last_cpu, last_t = cpu, now
                time.sleep(0.01)
            elapsed = time.monotonic() - start
            cpu_total = sum(proc.cpu_times()[:2]) - cpu0

            # shortcut: SIGTERM is POSIX-only (Windows would hard-kill and lose the
            # shutdown counters); add a Windows path if the load test runs there.
            agent.send_signal(signal.SIGTERM)
            try:
                agent.wait(timeout=30)
            except subprocess.TimeoutExpired:  # reported as agent_exit_code -9
                agent.kill()
                agent.wait()
            match = _STOPPED.search(agent_log.read_text())
            if match is None:
                raise RuntimeError("no shutdown counters in the agent log")
        except BaseException:
            agent.kill()
            print(agent_log.read_text()[-3000:], file=sys.stderr)
            raise
        finally:
            app_log.close()
            fix_log.close()

    ingest, pipeline, evaluator, publisher, events = map(
        ast.literal_eval, match.groups()
    )
    cpu_avg, cpu_peak, rss_peak = cpu_total / elapsed, max(cores), max(rss) / MB
    agent_rate = ingest["lines_ingested"] / elapsed
    return {
        "host": f"{platform.platform()}, {psutil.cpu_count()} CPUs, "
        f"{psutil.virtual_memory().total // MB} MB RAM",
        "python": platform.python_version(),
        "target_lines_per_s": rate,
        "seconds": seconds,
        "lines_written": written,
        "written_lines_per_s": round(written / seconds),
        "avg_line_bytes": round(bytes_written / written),
        "agent_lines_per_s": round(agent_rate),
        "backlog_lines_at_stop": written - ingest["lines_ingested"],
        "agent_exit_code": agent.returncode,  # 0 = clean shutdown on SIGTERM
        "cpu_cores_avg": round(cpu_avg, 3),
        "cpu_cores_peak_1s": round(cpu_peak, 3),
        "rss_mb_idle": round(rss_idle / MB, 1),
        "rss_mb_peak_1s": round(rss_peak, 1),
        "rss_mb_each_minute": [round(r / MB, 1) for r in rss[59::60]],  # plateau?
        "budgets": {
            # The CPU figures only count if the agent kept up with the rate.
            "NFR-PERF-001 sustains >= 95% of target": agent_rate >= 0.95 * rate,
            "NFR-PERF-001 avg < 1 core": cpu_avg < 1,
            "NFR-PERF-001 peak <= 2 cores": cpu_peak <= 2,
            "NFR-PERF-003 RSS < 150 MB": rss_peak < 150,
        },
        "agent_counters": {
            "ingest": ingest,
            "pipeline": pipeline,  # queue depths and drop counters
            "evaluator": evaluator,
            "publisher": publisher,
            "events": events,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent footprint load test")
    parser.add_argument("--rate", type=int, default=5000, help="lines per second")
    parser.add_argument("--seconds", type=float, default=300)
    args = parser.parse_args()
    print(json.dumps(run(args.rate, args.seconds), indent=2))


if __name__ == "__main__":
    main()
