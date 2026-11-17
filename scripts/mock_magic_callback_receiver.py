"""STUB: mock Magic callback endpoint for local runs and the UBS-134 demo.

Magic owns the real callback endpoint (spec 000 §4), and the Day-1 scope says
to mock it (spec 000 §7). This stands in for it on
``http://127.0.0.1:9000/magic/callbacks/telemetry-alerts`` (config/agent.yaml):

- verifies the ``X-Telemetry-Signature`` HMAC with the agent's own ``sign``
  (``FR-CBK-005``) and rejects a bad signature with 401;
- prints one line per alert (rule, status, severity, delivery ID);
- appends each verified body to ``--record`` as JSON lines, if given.

Not production code: no TLS, no replay window, no idempotency store.

    uv run python -m scripts.mock_magic_callback_receiver [--port 9000]

The secret comes from ``MAGIC_TELEMETRY_CALLBACK_SECRET`` (dev value
``dev-local-secret``, the same fallback the agent uses on localhost).
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from telemetry_agent.callbacks.signing import sign

PATH = "/magic/callbacks/telemetry-alerts"
DEV_SECRET = "dev-local-secret"


def summarise(alert: dict[str, Any]) -> str:
    """One readable line for a callback body."""
    rule = alert.get("ruleName") or alert.get("rule") or "?"
    status = alert.get("status", "?")
    severity = alert.get("severity", "?")
    value = alert.get("value")
    shown = f" value={value:.3f}" if isinstance(value, int | float) else ""
    return f"{rule} {status} ({severity}){shown}"


def make_handler(secret: bytes, record: Path | None) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != PATH:
                self._reply(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            timestamp = self.headers.get("X-Telemetry-Timestamp", "")
            given = self.headers.get("X-Telemetry-Signature", "")
            if not hmac.compare_digest(given, sign(secret, timestamp, body)):
                print("[magic-stub] REJECTED callback: bad signature", flush=True)
                self._reply(401)
                return
            alert = json.loads(body)
            delivery = self.headers.get("X-Telemetry-Delivery-Id", "?")
            now = datetime.now().strftime("%H:%M:%S")
            print(
                f"[magic-stub] {now} signed callback OK: {summarise(alert)}"
                f" delivery={delivery[:8]}",
                flush=True,
            )
            if record is not None:
                with record.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"receivedAt": now, "alert": alert}) + "\n")
            self._reply(200)

        def _reply(self, code: int) -> None:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return  # one line per callback above is enough

    return Handler


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--record", type=Path, help="append verified bodies here")
    args = parser.parse_args(argv)
    secret = os.environ.get("MAGIC_TELEMETRY_CALLBACK_SECRET") or DEV_SECRET
    server = ThreadingHTTPServer(
        (args.host, args.port), make_handler(secret.encode(), args.record)
    )
    print(
        f"[magic-stub] STUB Magic callback endpoint on "
        f"http://{args.host}:{args.port}{PATH}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    sys.exit(0)


if __name__ == "__main__":
    main()
