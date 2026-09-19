"""STUB backend for checking heartbeat output (UBS-58). Not the real ingestion.

The real receiver is the Ingestion Service (UBS-66/87) and the health read
side is UBS-69 — neither exists yet. This script stands in for both just far
enough to prove the agent's wire format is right and that a stopped agent
becomes visibly stale. Delete it when those tickets land.

What it does:
  * `POST /telemetry/heartbeat` (spec 007 §2.3): validates the body against
    `telemetry_shared.models.health.AgentHeartbeat` -> 202, or 400 with the
    pydantic error so any drift from spec 004 §6 fails loudly.
  * `GET /telemetry/health/agents`: dumps the in-memory registry (a preview
    of UBS-69's list endpoint, not its contract).
  * Prints one line per heartbeat and `STALE <agentId>` once no heartbeat has
    arrived for `--stale-after` seconds (spec 005 `missingHeartbeatThreshold`).

Run: uv run python scripts/heartbeat_receiver_stub.py --stale-after 30
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pydantic import ValidationError
from telemetry_shared.models.health import AgentHeartbeat


@dataclass
class _AgentRecord:
    last_heartbeat_utc: datetime
    received_at: float  # time.monotonic()
    status: str
    reasons: list[str]
    stale_announced: bool = False


class _Registry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._agents: dict[str, _AgentRecord] = {}

    def record(self, hb: AgentHeartbeat) -> None:
        with self._lock:
            self._agents[hb.agent_id] = _AgentRecord(
                last_heartbeat_utc=hb.sent_at_utc,
                received_at=time.monotonic(),
                status=hb.status,
                reasons=list(hb.status_reasons),
            )

    def snapshot(self, stale_after: float) -> list[dict[str, object]]:
        now = time.monotonic()
        with self._lock:
            return [
                {
                    "agentId": agent_id,
                    "status": "missing"
                    if now - r.received_at > stale_after
                    else r.status,
                    "lastHeartbeatUtc": r.last_heartbeat_utc.isoformat(),
                    "heartbeatAgeMs": int((now - r.received_at) * 1000),
                    "statusReasons": r.reasons,
                }
                for agent_id, r in self._agents.items()
            ]

    def newly_stale(self, stale_after: float) -> list[str]:
        now = time.monotonic()
        out = []
        with self._lock:
            for agent_id, r in self._agents.items():
                if now - r.received_at > stale_after and not r.stale_announced:
                    r.stale_announced = True
                    out.append(agent_id)
        return out


def _make_handler(
    registry: _Registry, stale_after: float
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_: object) -> None:  # quiet default access log
            pass

        def _send(self, status: HTTPStatus, payload: object) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if self.path != "/telemetry/heartbeat":
                self._send(HTTPStatus.NOT_FOUND, {"error": "unknown path"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            try:
                hb = AgentHeartbeat.model_validate_json(raw)
            except ValidationError as exc:
                print(
                    f"400 schema mismatch: {exc.errors(include_url=False)}", flush=True
                )
                self._send(
                    HTTPStatus.BAD_REQUEST, {"errors": exc.errors(include_url=False)}
                )
                return
            registry.record(hb)
            age_ms = int((datetime.now(UTC) - hb.sent_at_utc).total_seconds() * 1000)
            lag = f"{hb.read_lag_ms:.0f}ms" if hb.read_lag_ms is not None else "n/a"
            print(
                f"202 {hb.agent_id} status={hb.status} readLag={lag} "
                f"files={len(hb.files)} uptime={hb.uptime_seconds:.0f}s "
                f"transitAge={age_ms}ms reasons={hb.status_reasons}",
                flush=True,
            )
            self._send(HTTPStatus.ACCEPTED, {"accepted": True})

        def do_GET(self) -> None:
            if self.path != "/telemetry/health/agents":
                self._send(HTTPStatus.NOT_FOUND, {"error": "unknown path"})
                return
            self._send(HTTPStatus.OK, {"agents": registry.snapshot(stale_after)})

    return Handler


def _stale_watch(
    registry: _Registry, stale_after: float, stop: threading.Event
) -> None:
    while not stop.wait(1.0):
        for agent_id in registry.newly_stale(stale_after):
            print(
                f"STALE {agent_id}: no heartbeat for > {stale_after:.0f}s", flush=True
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--stale-after",
        type=float,
        default=60.0,
        help="seconds without a heartbeat before an agent is reported STALE",
    )
    args = parser.parse_args()

    registry = _Registry()
    server = ThreadingHTTPServer(
        (args.host, args.port), _make_handler(registry, args.stale_after)
    )
    stop = threading.Event()
    threading.Thread(
        target=_stale_watch, args=(registry, args.stale_after, stop), daemon=True
    ).start()
    print(
        f"stub receiver on http://{args.host}:{args.port}/telemetry/heartbeat "
        f"(stale after {args.stale_after:.0f}s) - NOT the real backend",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
