"""UBS-134 demo support: the mock Magic callback receiver (STUB), the agent's
Windows graceful-stop signal and the demo rule files (FR-CBK-005, spec 000 s7)."""

from __future__ import annotations

import asyncio
import json
import signal
import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.main import _install_signals
from telemetry_agent.rules.config_loader import (
    anomaly_path_for,
    load_anomaly_rules,
    load_rules,
)

from scripts import mock_magic_callback_receiver as receiver

SECRET = b"test-secret"
DEMO_RULES = Path(__file__).resolve().parents[3] / "config" / "demo" / "rules.yaml"
# The agent's configured windows; a rule with any other window loads but then
# fails every evaluation tick ("unknown window").
AGENT_WINDOWS = {"1m", "5m", "15m"}


@pytest.fixture
def server(tmp_path: Path) -> Iterator[tuple[str, Path]]:
    record = tmp_path / "callbacks.jsonl"
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), receiver.make_handler(SECRET, record))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    yield f"http://{host!s}:{port}{receiver.PATH}", record
    httpd.shutdown()
    httpd.server_close()


def _post(url: str, body: bytes, signature: str) -> httpx.Response:
    return httpx.post(
        url,
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Telemetry-Timestamp": "1700000000",
            "X-Telemetry-Signature": signature,
            "X-Telemetry-Delivery-Id": "d-1",
        },
    )


def test_FR_CBK_005_stub_accepts_and_records_a_signed_callback(
    server: tuple[str, Path],
) -> None:
    url, record = server
    body = json.dumps({"ruleName": "HighRejectRate", "status": "firing"}).encode()

    response = _post(url, body, sign(SECRET, "1700000000", body))

    assert response.status_code == 200
    (line,) = record.read_text(encoding="utf-8").splitlines()
    assert json.loads(line)["alert"]["ruleName"] == "HighRejectRate"


def test_FR_CBK_005_stub_rejects_a_bad_signature(server: tuple[str, Path]) -> None:
    url, record = server
    body = b'{"ruleName": "HighRejectRate"}'

    response = _post(url, body, sign(b"wrong-secret", "1700000000", body))

    assert response.status_code == 401
    assert not record.exists()


@pytest.mark.skipif(not hasattr(signal, "SIGBREAK"), reason="Windows only")
def test_agent_stops_gracefully_on_ctrl_break() -> None:
    sigbreak = signal.SIGBREAK  # type: ignore[attr-defined,unused-ignore]
    saved: dict[int, Any] = {
        s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM, sigbreak)
    }
    loop = asyncio.new_event_loop()
    try:
        stop = asyncio.Event()
        agent = SimpleNamespace(evaluator=SimpleNamespace(request_reload=None))
        _install_signals(loop, cast(Any, agent), stop)

        handler = signal.getsignal(sigbreak)
        assert callable(handler)
        handler(sigbreak, None)
        loop.run_until_complete(asyncio.sleep(0))
        assert stop.is_set()
    finally:
        for sig, previous in saved.items():
            signal.signal(sig, previous)
        loop.close()


def test_demo_rules_and_anomaly_files_load_every_showcase_rule() -> None:
    rules = load_rules(DEMO_RULES)

    assert {r.name for r in rules} == {
        "HighRejectRate",
        "RejectSpike",
        "NoLogActivity",
        "AppOutOfMemory",
        "AppLogFailure",
        "AbnormalRejectRate",
        "AbnormalExecutionIssueRate",
    }
    assert {r.window for r in rules if r.window is not None} <= AGENT_WINDOWS


def test_demo_anomaly_baselines_fit_a_live_demo() -> None:
    anomaly = load_anomaly_rules(anomaly_path_for(DEMO_RULES))

    assert anomaly, "config/demo/anomaly.yaml should enable anomaly rules"
    for rule in anomaly:
        assert rule.baseline_seconds is not None
        assert rule.baseline_seconds <= 3 * 60, rule.name
