"""UBS-137 / FR-TST-005 (blocking gate): the data-leak sentinel test.

Spec 012 §4, `NFR-SEC-001`, `NFR-SEC-002`, `NFR-SEC-012` and ADR 0004: no raw log
line and no non-allowlisted FIX tag may leave the Magic host.

How it works: the real agent (`build_agent` + `run_agent`, as in UBS-114) tails a
synthetic corpus in which

* every FIX tag in 1..999 that is NOT on the spec 003 §4 allowlist carries a unique
  sentinel (``SENTINEL_TAG44_9c1f``),
* the identifier tags (11/41/37/17) carry plaintext sentinels,
* tag 58 carries sentinel free text, and
* ``Application.log`` carries sentinel lines.

The agent publishes to the real backend app (in-process, through a recording
transport) and delivers a callback to a mock Magic endpoint. After a graceful stop,
every surface that can carry data off the host, or that echoes what the backend
received, is scanned for the sentinels in several encodings:

1. every request body sent to the backend,
2. every callback body (and header),
3. the agent's own log output (logging, stdout, stderr),
4. every file in the agent state directory,
5. ``/metrics`` (the agent has no ``/metrics`` of its own; the backend does) plus
   the backend's alert, event, health and metrics query responses.

The allowlist below is copied from the spec, not imported from the code. If someone
widens the code's allowlist the sweep then plants a sentinel in a tag the code now
extracts, and the leak is caught. ADR 0004: widening the allowlist needs an ADR.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import gzip
import io
import json
import logging
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import httpx
import pytest
from telemetry_agent.config import load_agent_config
from telemetry_agent.main import build_agent, run_agent
from telemetry_agent.parser.fix.fields import _ALLOWLIST, _HASHED_TAGS
from telemetry_agent.parser.fix.identifiers import hash_identifier
from telemetry_backend.main import create_app

AGENT_ID = "magic-agent-leak-137"
HASH_KEY = "leak-test-hash-key"
CALLBACK_SECRET = "leak-test-callback-secret"
SUFFIX = "9c1f"

# Spec 003 §4: the only tags the agent may extract. 11/41/37/17 are emitted only as
# hashes; 58 only as a bounded label.
SPEC_ALLOWED_TAGS = frozenset(
    {8, 35, 34, 49, 56, 52, 60, 11, 41, 37, 17, 150, 39, 55, 54, 40, 38, 32, 14}
    | {151, 103, 58, 45, 372, 373}
)
# Framing tags carry a length and a checksum, not content.
FRAMING_TAGS = frozenset({9, 10})
SWEEP_TAGS = [
    t for t in range(1, 1000) if t not in SPEC_ALLOWED_TAGS and t not in FRAMING_TAGS
]

TAG_58_TEXT = f"SENTINEL_TAG58_{SUFFIX}"
CL_ORD_IDS = [f"SENTINEL_TAG11_ORD{i}_{SUFFIX}" for i in range(3)]
ORDER_IDS = [f"SENTINEL_TAG37_ORD{i}_{SUFFIX}" for i in range(3)]
EXEC_IDS = [f"SENTINEL_TAG17_EXE{i}_{SUFFIX}" for i in range(3)]
ORIG_CL_ORD_ID = f"SENTINEL_TAG41_{SUFFIX}"
APP_LOG_SENTINELS = [
    f"SENTINEL_APPLOG_OOM_{SUFFIX}",
    f"SENTINEL_APPLOG_TIMEOUT_{SUFFIX}",
    f"SENTINEL_APPLOG_INFO_{SUFFIX}",
]

IDENTIFIER_VALUES = [*CL_ORD_IDS, *ORDER_IDS, *EXEC_IDS, ORIG_CL_ORD_ID]
SWEEP_SENTINELS = [f"SENTINEL_TAG{t}_{SUFFIX}" for t in SWEEP_TAGS]
ALL_SENTINELS = [
    *SWEEP_SENTINELS,
    TAG_58_TEXT,
    *IDENTIFIER_VALUES,
    *APP_LOG_SENTINELS,
]

SURFACES = (
    "backend_requests",
    "callbacks",
    "agent_logs",
    "state_files",
    "backend_metrics",
    "backend_queries",
)

_CONFIG = """
agent:
  id: {agent_id}
  instanceIds: [magic-leak-01]
logs:
  paths: [{log_dir}/Application.log, {log_dir}/Fix.log]
  stateDir: {state_dir}
  appLogPatterns:
    - '^\\d{{2}}:\\d{{2}}:\\d{{2}}\\.\\d+ <\\d+> \\[[NWEIF]+\\]'
parsing:
  errorSignatures:
    - label: out_of_memory
      match: "OutOfMemoryError|std::bad_alloc"
    - label: connection_timeout
      match: "timed out after"
pipeline:
  evaluationInterval: 200ms
rules:
  path: rules.yaml
publish:
  endpoint: https://backend.example/telemetry/batch
  interval: 1s
callbacks:
  endpoint: https://magic.example/magic/callbacks/telemetry-alerts
"""

# Three rejects in the corpus trip this, so a callback body exists to be scanned.
_RULES = """
rules:
  - name: RejectSpike
    kind: threshold
    source: counter
    metric: orders_rejected
    operator: ">"
    tiers: [{severity: warning, threshold: 2}]
    window: 1m
    for: 0s
"""


# --- corpus ------------------------------------------------------------------------


def _sweep() -> str:
    return "|".join(f"{t}=SENTINEL_TAG{t}_{SUFFIX}" for t in SWEEP_TAGS)


def _fix(stamp: str, seq: int, msg_type: str, body: str) -> str:
    """One pipe-delimited FIX line: allowlisted tags with benign values, then a
    sentinel in every non-allowlisted tag."""
    return (
        f"8=FIX.4.2|9=99|35={msg_type}|34={seq}|49=MAGIC|56=EXCH1|52={stamp}"
        f"|{body}|{_sweep()}|10=000|"
    )


def build_fix_corpus(stamp: str) -> list[str]:
    lines = [_fix(stamp, 1, "A", "98=0")]
    seq = 2
    for i in range(3):
        lines.append(
            _fix(
                stamp,
                seq,
                "D",
                f"11={CL_ORD_IDS[i]}|55=AAPL|54=1|40=2|38=100",
            )
        )
        lines.append(
            _fix(
                stamp,
                seq + 1,
                "8",
                f"11={CL_ORD_IDS[i]}|37={ORDER_IDS[i]}|17={EXEC_IDS[i]}|55=AAPL"
                f"|54=1|150=8|39=8|103=3|58={TAG_58_TEXT}",
            )
        )
        seq += 2
    lines.append(
        _fix(
            stamp,
            seq,
            "8",
            f"11={CL_ORD_IDS[0]}|37={ORDER_IDS[0]}|17={EXEC_IDS[0]}|55=AAPL|54=1"
            "|150=F|39=2|32=100|14=100|151=0",
        )
    )
    lines.append(
        _fix(
            stamp,
            seq + 1,
            "F",
            f"11={CL_ORD_IDS[1]}|41={ORIG_CL_ORD_ID}|55=AAPL|54=1|38=100",
        )
    )
    return lines


def build_app_log_corpus() -> list[str]:
    return [
        f"01:00:00.000001 <123456> [F] MAIN: OutOfMemoryError {APP_LOG_SENTINELS[0]}",
        f"01:00:00.000002 <123456> [E] VS_788: timed out after 00:00:30 "
        f"{APP_LOG_SENTINELS[1]}",
        f"01:00:00.000003 <123456> [I] MAIN: {APP_LOG_SENTINELS[2]}",
    ]


# --- scanning ----------------------------------------------------------------------


def encodings(sentinel: str) -> set[str]:
    """Forms a leak might take. Everything is compared as lower-case text."""
    raw = sentinel.encode()
    forms = {
        sentinel,
        quote(sentinel, safe=""),
        raw.hex(),
        base64.b64encode(raw).decode(),
        base64.urlsafe_b64encode(raw).decode(),
        json.dumps(sentinel)[1:-1],
    }
    return {f.lower() for f in forms} | {f for f in forms if f.lower() != f}


_PARTIAL = re.compile(r"sentinel|tag\d+_" + SUFFIX, re.IGNORECASE)


def find_leaks(
    surfaces: Mapping[str, list[str]],
    sentinels: list[str] = ALL_SENTINELS,
    *,
    partial: bool = True,
) -> list[str]:
    """Every (surface, sentinel) hit. With `partial`, also flags a partial sentinel
    (the marker prefix, or `TAGnn_<suffix>`) so a truncated leak is not missed."""
    forms = {s: encodings(s) for s in sentinels}
    leaks: list[str] = []
    for surface, texts in surfaces.items():
        for text in texts:
            lowered = text.lower()
            for sentinel, variants in forms.items():
                if any(v in text or v in lowered for v in variants):
                    leaks.append(f"{surface}: {sentinel}")
            if partial and (match := _PARTIAL.search(text)):
                leaks.append(f"{surface}: partial sentinel {match.group(0)!r}")
    return leaks


# --- the run -----------------------------------------------------------------------


class RecordingTransport(httpx.AsyncBaseTransport):
    """The real backend app behind an in-process transport that records every
    request body the agent sends (gzip-decompressed, as the backend sees it)."""

    def __init__(self, app: object) -> None:
        self._inner = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
        self.requests: list[str] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        body = await request.aread()
        if request.headers.get("content-encoding") == "gzip":
            body = gzip.decompress(body)
        headers = " ".join(f"{k}: {v}" for k, v in request.headers.items())
        self.requests.append(
            f"{request.url}\n{headers}\n{body.decode('utf-8', 'replace')}"
        )
        return await self._inner.handle_async_request(request)


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        # `format` includes the traceback, which is also output.
        self.messages.append(self.format(record))


@dataclass
class Run:
    surfaces: dict[str, list[str]] = field(default_factory=dict)
    alerts: list[dict[str, object]] = field(default_factory=list)
    callbacks: int = 0
    reject_events: list[dict[str, object]] = field(default_factory=list)
    state_file_names: list[str] = field(default_factory=list)


@contextlib.contextmanager
def _capture_logs() -> Iterator[tuple[_ListHandler, io.StringIO, io.StringIO]]:
    handler = _ListHandler()
    handler.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    previous = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            yield handler, out, err
    finally:
        root.removeHandler(handler)
        root.setLevel(previous)


async def _scenario(tmp_path: Path, handler: _ListHandler) -> Run:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    state_dir = tmp_path / "state"
    (tmp_path / "rules.yaml").write_text(_RULES, encoding="utf-8")
    config_path = tmp_path / "agent.yaml"
    config_path.write_text(
        _CONFIG.format(
            agent_id=AGENT_ID,
            log_dir=log_dir.as_posix(),
            state_dir=state_dir.as_posix(),
        ),
        encoding="utf-8",
    )
    cfg = load_agent_config(config_path)

    callback_records: list[str] = []

    def magic(request: httpx.Request) -> httpx.Response:
        headers = " ".join(f"{k}: {v}" for k, v in request.headers.items())
        callback_records.append(
            f"{request.url}\n{headers}\n{request.content.decode('utf-8', 'replace')}"
        )
        return httpx.Response(200, json={})

    app = create_app()
    recorder = RecordingTransport(app)
    agent = build_agent(
        cfg,
        publish_transport=recorder,
        callback_transport=httpx.MockTransport(magic),
        started_at=datetime.now(UTC) - timedelta(hours=1),  # past startup grace
        env={
            "MAGIC_TELEMETRY_ID_HASH_KEY": HASH_KEY,
            "MAGIC_TELEMETRY_PUBLISH_TOKEN": "leak-test-token",
            "MAGIC_TELEMETRY_CALLBACK_SECRET": CALLBACK_SECRET,
        },
    )

    # ASGITransport skips the backend lifespan: run its ingestion worker here.
    worker = asyncio.create_task(app.state.ingestion.run())
    stop = asyncio.Event()
    running = asyncio.create_task(run_agent(agent, stop))
    backend = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://backend"
    )
    run = Run()
    try:
        await asyncio.sleep(0.3)  # agent is tailing before the corpus lands
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
        with (log_dir / "Application.log").open(
            "a", encoding="utf-8", newline="\n"
        ) as f:
            f.write("\n".join(build_app_log_corpus()) + "\n")
        with (log_dir / "Fix.log").open("a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(build_fix_corpus(stamp)) + "\n")

        for _ in range(200):  # up to ~20s
            await asyncio.sleep(0.1)
            alerts = (await backend.get("/telemetry/alerts")).json()["alerts"]
            published = "\n".join(recorder.requests)
            if (
                alerts
                and callback_records
                and "fix.order_reject" in published
                and "app.error_signature" in published
            ):
                break
    finally:
        stop.set()
        await asyncio.wait_for(running, 15)  # graceful stop flushes the state files
        await asyncio.wait_for(app.state.ingestion._queue.join(), 5)

    query_bodies: list[str] = []
    for path in (
        "/telemetry/alerts",
        "/telemetry/events",
        "/telemetry/health/agents",
        f"/telemetry/health/agents/{AGENT_ID}",
    ):
        response = await backend.get(path)
        assert response.status_code == 200, path
        query_bodies.append(response.text)
    response = await backend.post(
        "/telemetry/query/metrics",
        json={"timeRange": {"last": "30m"}, "metrics": ["orders", "rejections"]},
    )
    assert response.status_code == 200
    query_bodies.append(response.text)
    metrics_text = (await backend.get("/metrics")).text
    events = (await backend.get("/telemetry/events")).json()["events"]

    worker.cancel()
    await backend.aclose()

    run.alerts = json.loads(query_bodies[0])["alerts"]
    run.callbacks = len(callback_records)
    run.reject_events = [e for e in events if e["eventType"] == "fix.order_reject"]
    state_files = sorted(p for p in state_dir.rglob("*") if p.is_file())
    run.state_file_names = [p.name for p in state_files]
    run.surfaces = {
        "backend_requests": list(recorder.requests),
        "callbacks": callback_records,
        "agent_logs": list(handler.messages),
        "state_files": [p.read_bytes().decode("utf-8", "replace") for p in state_files]
        + [p.name for p in state_files],
        "backend_metrics": [metrics_text],
        "backend_queries": query_bodies,
    }
    return run


@pytest.fixture(scope="module")
def run(tmp_path_factory: pytest.TempPathFactory) -> Run:
    with _capture_logs() as (handler, out, err):
        result = asyncio.run(_scenario(tmp_path_factory.mktemp("ubs137"), handler))
    result.surfaces["agent_logs"] += [out.getvalue(), err.getvalue()]
    return result


# --- tests -------------------------------------------------------------------------


def test_FR_TST_005_every_surface_was_populated(run: Run) -> None:
    """A scan of an empty surface proves nothing, so prove each one has content."""
    assert run.alerts, "RejectSpike did not fire"
    assert run.callbacks >= 1, "no callback reached the mock Magic endpoint"
    assert run.reject_events, "no fix.order_reject event reached the backend"
    assert "offsets.json" in run.state_file_names
    for surface in SURFACES:
        assert any(text.strip() for text in run.surfaces[surface]), surface
    assert any("fix.order_reject" in b for b in run.surfaces["backend_requests"])
    assert any("app.error_signature" in b for b in run.surfaces["backend_requests"])
    assert any(
        "orders" in b
        for b in run.surfaces["backend_metrics"] + run.surfaces["backend_requests"]
    )
    assert any(m for m in run.surfaces["agent_logs"][:-2]), "agent logged nothing"


@pytest.mark.parametrize("surface", SURFACES)
def test_FR_TST_005_NFR_SEC_002_no_sentinel_on_any_surface(
    run: Run, surface: str
) -> None:
    """`FR-TST-005`: no sentinel, in any encoding, on the surface."""
    leaks = find_leaks({surface: run.surfaces[surface]})
    assert leaks == [], f"data leaked on {surface}: {leaks[:5]}"


def test_FR_TST_005_NFR_SEC_012_identifiers_only_hashed(run: Run) -> None:
    """ClOrdID/OrderID/ExecID/OrigClOrdID never appear in plaintext on any surface,
    and what the backend received is exactly their HMAC (FR-PRS-021, 16 hex)."""
    assert find_leaks(run.surfaces, IDENTIFIER_VALUES, partial=False) == []
    published = "\n".join(run.surfaces["backend_requests"])
    key = HASH_KEY.encode()
    for plaintext in (*CL_ORD_IDS, *ORDER_IDS, *EXEC_IDS):
        digest = hash_identifier(plaintext, key)
        assert len(digest) == 16
        assert digest in published, f"hash of {plaintext} was not published"
    # The hash input is the whole identifier, so hashing alone cannot hide a
    # sentinel: a partial copy of one would be caught by the surface scans above.


def test_FR_TST_005_tag_58_text_never_emitted(run: Run) -> None:
    """Tag 58 text never appears in any form. Reject events carry only the bounded
    label mapped from tag 103, never anything derived from the free text."""
    assert find_leaks(run.surfaces, [TAG_58_TEXT], partial=False) == []
    assert not any("TAG58" in text for t in run.surfaces.values() for text in t)
    reasons = {
        e["dimensions"]["rejectReason"]  # type: ignore[index]
        for e in run.reject_events
    }
    assert reasons == {"OrderExceedsLimit"}  # tag 103=3, not the tag 58 text


def test_FR_TST_005_state_dir_holds_only_offsets(run: Run) -> None:
    """`NFR-SEC-003`: offsets, file identities and alert state only."""
    assert set(run.state_file_names) <= {"offsets.json", "offsets.tmp"}


def test_FR_TST_005_scanner_negative_control() -> None:
    """The scan is not vacuous: planting a sentinel on a surface is flagged there,
    in every encoding it checks for, and a truncated sentinel is flagged too."""
    clean = {s: ["nothing to see here"] for s in SURFACES}
    assert find_leaks(clean) == []
    sample = SWEEP_SENTINELS[0]
    planted = [
        sample,
        sample.lower(),
        quote(sample, safe=""),
        sample.encode().hex(),
        base64.b64encode(sample.encode()).decode(),
        f'{{"fields": {{"x": "{sample}"}}}}',
    ]
    for surface in SURFACES:
        for text in planted:
            leaks = find_leaks({**clean, surface: [f"prefix {text} suffix"]})
            assert leaks, (surface, text)
            assert all(entry.startswith(f"{surface}:") for entry in leaks)
    assert find_leaks({"agent_logs": ["SENTINEL_TAG44_"]}), "truncated leak missed"
    assert find_leaks({"agent_logs": [f"x TAG44_{SUFFIX} y"]}), "tag suffix missed"


def test_FR_TST_005_sentinel_corpus_covers_the_spec_exclusions() -> None:
    """The sweep includes every tag spec 003 §4 names as explicitly excluded."""
    for tag in (44, 31, 6, 1, 448, 447, 452, 21, 528, 529, 581):
        assert tag in SWEEP_TAGS
    assert 58 not in SWEEP_TAGS


def test_FR_TST_005_code_allowlist_matches_spec_003() -> None:
    """Widening the code allowlist needs an ADR (ADR 0004), so make it loud."""
    code_tags = {int(t) for t in _ALLOWLIST} | {int(t) for t in _HASHED_TAGS}
    assert code_tags == SPEC_ALLOWED_TAGS, (
        "the field allowlist differs from spec 003 §4; extending it requires an ADR "
        f"(added: {sorted(code_tags - SPEC_ALLOWED_TAGS)}, "
        f"removed: {sorted(SPEC_ALLOWED_TAGS - code_tags)})"
    )
