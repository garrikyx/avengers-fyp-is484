"""Heartbeat emitter (UBS-58, FR-HLT-001).

Ticks on a fixed interval regardless of log activity: an idle agent must still
be distinguishable from a dead one. The sink is pluggable because the real
transport is the Backend Publisher (spec 002 §6, not built yet); until then the
two sinks here cover local demos and the stub receiver in
`scripts/heartbeat_receiver_stub.py`. See docs/plan/ubs58-notes.md.
"""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime

from telemetry_agent.health.reporter import HealthReporter
from telemetry_shared.models.health import AgentHeartbeat

logger = logging.getLogger(__name__)

HeartbeatSink = Callable[[AgentHeartbeat], None]


class HeartbeatEmitter:
    def __init__(
        self,
        reporter: HealthReporter,
        sink: HeartbeatSink,
        interval_seconds: float | None = None,
    ) -> None:
        if interval_seconds is not None and interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        self.reporter = reporter
        self.sink = sink
        self.interval_seconds = (
            interval_seconds
            if interval_seconds is not None
            else reporter.heartbeat_config.interval_seconds
        )
        self.sent_count = 0
        self.failed_count = 0
        self.last_sent_at: datetime | None = None

    def tick(self, now: datetime | None = None) -> AgentHeartbeat:
        """Build and send one heartbeat. Sink failures are counted, not raised:
        a dead backend must never stop the agent (spec 002 §8.3)."""
        heartbeat = self.reporter.build_heartbeat(now=now)
        try:
            self.sink(heartbeat)
        except Exception:
            self.failed_count += 1
            logger.warning("heartbeat sink failed", exc_info=True)
        else:
            self.sent_count += 1
            self.last_sent_at = heartbeat.sent_at_utc
        return heartbeat

    async def run(self, stop: asyncio.Event | None = None) -> None:
        """Tick every `interval_seconds` until `stop` is set. First tick is
        immediate so a freshly started agent shows up without waiting.

        `tick()` runs in a worker thread: sinks do blocking I/O (the stdlib
        HTTP sink can sit in `urlopen` for its whole timeout), and that must
        not stall whatever else shares the loop (the demo's file polling)."""
        stop = stop or asyncio.Event()
        while not stop.is_set():
            await asyncio.to_thread(self.tick)
            try:
                await asyncio.wait_for(stop.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                continue


# --- sinks ---------------------------------------------------------------------


def heartbeat_json(heartbeat: AgentHeartbeat) -> str:
    """Wire encoding: camelCase per spec 004 §6."""
    return heartbeat.model_dump_json(by_alias=True)


class LoggingHeartbeatSink:
    """Emit the wire JSON through `logging` (demo / local runs)."""

    def __init__(self, log: logging.Logger | None = None) -> None:
        self.log = log or logger

    def __call__(self, heartbeat: AgentHeartbeat) -> None:
        self.log.info("%s", heartbeat_json(heartbeat))


class PrintHeartbeatSink:
    """Write one JSON line per heartbeat to stdout (demo)."""

    def __call__(self, heartbeat: AgentHeartbeat) -> None:
        print(heartbeat_json(heartbeat), flush=True)


class HttpHeartbeatSink:
    """`POST /telemetry/heartbeat` (spec 007 §2.3) with the stdlib only.

    Placeholder transport until the Publisher lands: no retry, no gzip, no
    auth. Any non-2xx or connection error raises so `HeartbeatEmitter.tick`
    counts it as a failure.
    """

    def __init__(self, url: str, timeout_seconds: float = 5.0) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    def __call__(self, heartbeat: AgentHeartbeat) -> None:
        body = heartbeat_json(heartbeat).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as resp:
                if not 200 <= resp.status < 300:
                    raise RuntimeError(f"heartbeat POST returned {resp.status}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.dumps(json.loads(detail))
            except ValueError:
                pass
            raise RuntimeError(f"heartbeat POST returned {exc.code}: {detail}") from exc
