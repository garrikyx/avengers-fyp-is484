"""UBS-140: repeatable spec 000 §7 #1/#4 evidence, using synthetic logs only.

Real agent lifecycle and backend routes, with an in-process transport outage.
This is a component acceptance harness, not a process-kill or TLS test.
Only aggregate results are retained; temporary synthetic logs are removed.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import gzip
import json
import os
import platform
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI
from simulator.mock_logger import format_fix_line, generate_fix_order_messages
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.config import load_agent_config
from telemetry_agent.main import Agent, build_agent, run_agent
from telemetry_backend.config import BackendHealthConfig, IngestGuardConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app

INSTANCE = "ubs-140-synthetic"
SECRET = "synthetic-acceptance-only"


@dataclass
class Report:
    requested_lines_per_second: int
    outage_seconds: float
    bucket_seconds: int
    python: str = field(default_factory=platform.python_version)
    platform: str = field(default_factory=platform.platform)
    logical_cpus: int | None = field(default_factory=os.cpu_count)
    visibility_seconds: list[float | None] = field(default_factory=list)
    generated_lines: int = 0
    generated_orders: int = 0
    generated_bytes: int = 0
    stream_lines_per_second: list[float] = field(default_factory=list)
    queried_orders: int = 0
    queried_rejections: int = 0
    pre_restart_missing_orders: int = 0
    pre_restart_missing_rejections: int = 0
    missing_orders: int = 0
    excess_orders: int = 0
    failed_publish_attempts: int = 0
    outage_ingested_lines: int = 0
    signed_callbacks_during_outage: int = 0
    restart_resume_seconds: float | None = None
    restarted_snapshots: int = 0
    rotation_events: int = 0
    findings: list[str] = field(default_factory=list)
    pre_restart_ingested_lines: int = 0
    final_ingested_lines: int = 0
    publisher_counters: dict[str, int] = field(default_factory=dict)


class OutageTransport(httpx.AsyncBaseTransport):
    """Fail all agent HTTP requests while offline; never inspect raw logs."""

    def __init__(self, app: FastAPI, report: Report) -> None:
        self.inner = httpx.ASGITransport(app=app)
        self.offline = False
        self.report = report

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if self.offline:
            self.report.failed_publish_attempts += 1
            raise httpx.ConnectError("synthetic backend outage", request=request)
        response = await self.inner.handle_async_request(request)
        if response.status_code == 202:
            body = await request.aread()
            if request.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            batch = json.loads(body)
            self.report.restarted_snapshots += sum(
                bool(s.get("restarted")) for s in batch.get("snapshots", [])
            )
            self.report.rotation_events += sum(
                e.get("eventType") == "log.rotated" for e in batch.get("events", [])
            )
        return response


class SyntheticWriter:
    """Bounded batches from the existing simulator, with exact ground truth."""

    def __init__(self, path: Path, report: Report) -> None:
        self.path = path
        self.report = report

    def append(self, orders: int) -> None:
        stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        lines: list[str] = []
        for _ in range(orders):
            self.report.generated_orders += 1
            messages = generate_fix_order_messages(
                f"UBS140-{self.report.generated_orders}", "AAPL", reject_rate=1.0
            )
            lines.extend(format_fix_line(stamp, msg) + "\n" for msg in messages)
        text = "".join(lines)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        self.report.generated_lines += len(lines)
        self.report.generated_bytes += len(text.encode())

    async def stream(self, rate: int, stop: asyncio.Event) -> None:
        started = time.monotonic()
        initial = self.report.generated_lines
        orders_per_tick = max(1, rate // 40)
        tick = 2 * orders_per_tick / rate
        deadline = started
        while not stop.is_set():
            self.append(orders_per_tick)
            deadline += tick
            await asyncio.sleep(max(0, deadline - time.monotonic()))
        self.report.stream_lines_per_second.append(
            (self.report.generated_lines - initial) / (time.monotonic() - started)
        )


def _config(root: Path, bucket_seconds: int) -> Path:
    # The outage rule must fire only after connectivity is removed. This checks
    # NFR-REL-003 with a fresh, signed callback rather than a prior callback.
    (root / "rules.yaml").write_text(
        """rules:
  - name: AcceptanceBackendUnavailable
    kind: threshold
    source: gauge
    metric: consecutive_publish_failures
    operator: ">"
    tiers: [{severity: warning, threshold: 0}]
    window: 1m
    for: 0s
""",
        encoding="utf-8",
    )
    path = root / "agent.yaml"
    path.write_text(
        f"""agent:
  id: ubs-140-agent
  instanceIds: [{INSTANCE}]
logs:
  paths: [{json.dumps(str(root / "Fix.log"))}]
  stateDir: {json.dumps(str(root / "state"))}
host:
  enabled: false
pipeline:
  evaluationInterval: 100ms
rules:
  path: rules.yaml
publish:
  endpoint: https://backend.example/telemetry/batch
  interval: 1s
  metricsBucketSeconds: {bucket_seconds}
  retry:
    base: 1s
    cap: 2s
    jitter: 0
callbacks:
  endpoint: https://magic.example/callbacks
""",
        encoding="utf-8",
    )
    return path


async def _counts(client: httpx.AsyncClient) -> tuple[int, int]:
    response = await client.post(
        "/telemetry/query/metrics",
        json={
            "timeRange": {"last": "1h"},
            "filters": {"instanceId": INSTANCE},
            "metrics": ["orders_submitted", "orders_rejected"],
        },
    )
    response.raise_for_status()
    totals = response.json()["totals"]
    return int(totals.get("orders_submitted") or 0), int(
        totals.get("orders_rejected") or 0
    )


async def _wait_counts(
    client: httpx.AsyncClient, expected: int, timeout: float
) -> tuple[int, int]:
    deadline = time.monotonic() + timeout
    while True:
        counts = await _counts(client)
        if min(counts) >= expected or time.monotonic() >= deadline:
            return counts
        await asyncio.sleep(0.05)


async def run_acceptance(
    root: Path, *, rate: int = 5000, outage: float = 300, bucket_seconds: int = 1
) -> Report:
    """Run both ticket checks; return measured gaps without declaring them passes."""
    if rate < 2 or outage < 2 or bucket_seconds < 1:
        raise ValueError("rate >= 2, outage >= 2 and bucket_seconds >= 1 required")
    report = Report(rate, outage, bucket_seconds)
    cfg = load_agent_config(_config(root, bucket_seconds))
    app = create_app(
        deps=AppDeps(
            config=BackendHealthConfig(
                ingest=IngestGuardConfig(max_batches_per_minute_per_agent=120)
            )
        )
    )
    transport = OutageTransport(app, report)

    def callback(request: httpx.Request) -> httpx.Response:
        expected = sign(
            SECRET.encode(), request.headers["X-Telemetry-Timestamp"], request.read()
        )
        if request.headers["X-Telemetry-Signature"] != expected:
            raise AssertionError("callback signature mismatch")
        if transport.offline:
            report.signed_callbacks_during_outage += 1
        return httpx.Response(200, json={})

    def new_agent() -> Agent:
        return build_agent(
            cfg,
            publish_transport=transport,
            callback_transport=httpx.MockTransport(callback),
            started_at=datetime.now(UTC) - timedelta(minutes=2),
            env={
                "MAGIC_TELEMETRY_ID_HASH_KEY": SECRET,
                "MAGIC_TELEMETRY_PUBLISH_TOKEN": SECRET,
                "MAGIC_TELEMETRY_CALLBACK_SECRET": SECRET,
            },
        )

    agent = new_agent()
    writer = SyntheticWriter(root / "Fix.log", report)
    stop = asyncio.Event()
    running = asyncio.create_task(run_agent(agent, stop))
    streaming: asyncio.Task[None] | None = None
    stream_stop = asyncio.Event()
    worker = asyncio.create_task(app.state.ingestion.run())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://backend"
    ) as client:
        try:
            # Readiness via a real log-to-query probe, not an arbitrary startup sleep.
            writer.append(1)
            if min(await _wait_counts(client, 1, bucket_seconds + 10)) != 1:
                raise RuntimeError("agent readiness probe did not reach the query API")
            for _ in range(3):
                started = time.monotonic()
                writer.append(max(20, rate // 2))
                counts = await _wait_counts(client, report.generated_orders, 5)
                elapsed = time.monotonic() - started
                report.visibility_seconds.append(
                    elapsed
                    if min(counts) >= report.generated_orders and elapsed <= 5
                    else None
                )
                # Separate trials so a failed trial cannot satisfy the next one.
                await _wait_counts(client, report.generated_orders, bucket_seconds + 5)

            streaming = asyncio.create_task(writer.stream(rate, stream_stop))
            await asyncio.sleep(1)
            # FR-TST-004 / NFR-REL-002: rotate while appends and parsing continue.
            writer.path.rename(root / "Fix.log.1")
            writer.path.touch()
            transport.offline = True
            before = agent.ingestor.stats()["lines_ingested"]
            await asyncio.sleep(outage)
            report.outage_ingested_lines = (
                agent.ingestor.stats()["lines_ingested"] - before
            )
            transport.offline = False
            stream_stop.set()
            await streaming
            streaming = None
            counts = await _wait_counts(
                client, report.generated_orders, max(15, bucket_seconds + 5)
            )
            report.pre_restart_missing_orders = report.generated_orders - counts[0]
            report.pre_restart_missing_rejections = report.generated_orders - counts[1]
            report.pre_restart_ingested_lines = agent.ingestor.stats()["lines_ingested"]

            # NFR-REL-004: reconstruct the whole agent using the same offset state.
            # Keep appending during shutdown and restart, including downtime.
            stream_stop = asyncio.Event()
            streaming = asyncio.create_task(writer.stream(rate, stream_stop))
            await asyncio.sleep(0.2)
            stop.set()
            await asyncio.wait_for(running, 15)
            first_ingested = agent.ingestor.stats()["lines_ingested"]
            report.publisher_counters = agent.publisher.counters.snapshot()
            restart_at = time.monotonic()
            agent = new_agent()
            stop = asyncio.Event()
            running = asyncio.create_task(run_agent(agent, stop))
            deadline = restart_at + 5
            while time.monotonic() < deadline:
                if agent.ingestor.stats()["lines_ingested"] > 0:
                    report.restart_resume_seconds = time.monotonic() - restart_at
                    break
                await asyncio.sleep(0.02)
            await asyncio.sleep(1)
            stream_stop.set()
            await streaming
            streaming = None
            report.queried_orders, report.queried_rejections = await _wait_counts(
                client, report.generated_orders, max(15, bucket_seconds + 5)
            )
            report.final_ingested_lines = (
                first_ingested + agent.ingestor.stats()["lines_ingested"]
            )
        finally:
            stream_stop.set()
            if streaming is not None:
                await streaming
            transport.offline = False
            stop.set()
            try:
                await asyncio.wait_for(running, 15)
            finally:
                worker.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await worker

    report.missing_orders = max(0, report.generated_orders - report.queried_orders)
    report.excess_orders = max(0, report.queried_orders - report.generated_orders)
    if any(v is None for v in report.visibility_seconds):
        report.findings.append("Five-second visibility failed in at least one trial.")
    if report.pre_restart_missing_orders or report.pre_restart_missing_rejections:
        report.findings.append(
            "Rotation/outage recovery counts differ from ground truth."
        )
    if report.missing_orders or report.excess_orders:
        report.findings.append(
            "Final counts differ from ground truth; compare the pre-restart deficit "
            "before attributing it to restart. Offsets acknowledge ingestion, not "
            "publication; open buckets and unpublished memory are lost when the "
            "agent is rebuilt (FR-PUB-008). Backlogged lines may remain on disk."
        )
    if report.queried_orders != report.queried_rejections:
        report.findings.append(
            "Order/rejection totals differ for the 100% reject stream."
        )
    if not report.restarted_snapshots:
        report.findings.append("No restarted:true snapshot observed (NFR-REL-004 gap).")
    if report.restart_resume_seconds is None:
        report.findings.append("Agent did not resume ingestion within five seconds.")
    if not report.signed_callbacks_during_outage or not report.outage_ingested_lines:
        report.findings.append("Outage isolation evidence incomplete (NFR-REL-003).")
    if not report.failed_publish_attempts or not report.rotation_events:
        report.findings.append("Outage or rotation was not observed by the agent.")
    if any(actual < rate * 0.95 for actual in report.stream_lines_per_second):
        report.findings.append("Writer achieved less than 95% of the requested rate.")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rate", type=int, default=5000)
    parser.add_argument("--outage-seconds", type=float, default=300)
    parser.add_argument("--bucket-seconds", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="ubs140-") as directory:
        report = asyncio.run(
            run_acceptance(
                Path(directory),
                rate=args.rate,
                outage=args.outage_seconds,
                bucket_seconds=args.bucket_seconds,
            )
        )
    payload: dict[str, Any] = asdict(report)
    text = json.dumps(payload, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(1 if report.findings else 0)


if __name__ == "__main__":
    main()
