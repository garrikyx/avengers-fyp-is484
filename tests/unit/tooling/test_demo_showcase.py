"""Demo showcase helper (scripts/demo_showcase.py): the pure parts and the
tamper check against the real Magic stub (FR-CBK-005, spec 000 s7)."""

from __future__ import annotations

import json
import random
import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml
from simulator.mock_logger import format_fix_line, generate_fix_order_messages
from telemetry_agent.rules.config_loader import load_rules_from_yaml

from scripts import demo_showcase as show
from scripts import mock_magic_callback_receiver as receiver

ROOT = Path(__file__).resolve().parents[3]
DEMO_RULES = ROOT / "config" / "demo" / "rules.yaml"


@pytest.fixture
def stub(tmp_path: Path) -> Iterator[tuple[str, Path]]:
    record = tmp_path / "callbacks.jsonl"
    secret = receiver.DEV_SECRET.encode()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), receiver.make_handler(secret, record))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    yield f"http://{host!s}:{port}{receiver.PATH}", record
    httpd.shutdown()
    httpd.server_close()


def test_FR_CBK_005_tamper_is_rejected_by_the_magic_stub(
    stub: tuple[str, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    url, record = stub
    monkeypatch.setattr(show, "RUN", tmp_path)

    assert show.cmd_tamper(url) == 0
    assert not record.exists(), "a forged callback must not be recorded"


def test_rotated_logs_are_listed_oldest_first(tmp_path: Path) -> None:
    for name in ("Fix.log", "Fix.log.1", "Fix.log.10", "Fix.log.2", "Fix.log.bak"):
        (tmp_path / name).write_text("", encoding="utf-8")

    names = [p.name for p in show.rotated_logs(tmp_path, "Fix.log")]

    assert names == ["Fix.log.10", "Fix.log.2", "Fix.log.1", "Fix.log"]


def test_counts_match_the_orders_the_simulator_wrote(tmp_path: Path) -> None:
    random.seed(11)
    rejected = 0
    files = [tmp_path / "Fix.log.1", tmp_path / "Fix.log"]
    for n, path in enumerate(files * 50):
        messages = generate_fix_order_messages(f"ORD{n}", "AAPL", reject_rate=0.3)
        rejected += any("|39=8|" in m for m in messages)
        with path.open("a", encoding="utf-8") as log:
            for message in messages:
                log.write(format_fix_line("2026-11-18 12:00:00.000", message) + "\n")
    with files[1].open("a", encoding="utf-8") as log:  # what `malformed` writes
        log.write("2026-11-18 : 8=FIX.4.2|9=999|35=D|49=CLIENT|BROKEN-NO-CHECKSUM\n")

    assert show.count_fix_orders(files) == (100, rejected)


def test_reload_strict_changes_one_tier_and_still_loads(tmp_path: Path) -> None:
    original = DEMO_RULES.read_text(encoding="utf-8")
    strict = show.set_tier_threshold(
        original, show.STRICT_RULE, show.STRICT_SEVERITY, show.STRICT_THRESHOLD
    )
    path = tmp_path / "rules.yaml"
    path.write_text(strict, encoding="utf-8")

    rule = next(r for r in load_rules_from_yaml(path) if r.name == show.STRICT_RULE)
    tiers = {t.severity: t.threshold for t in rule.tiers}
    assert float(tiers[show.STRICT_SEVERITY]) == show.STRICT_THRESHOLD
    assert len(yaml.safe_load(strict)["rules"]) == len(
        yaml.safe_load(original)["rules"]
    )


def test_reload_rejects_an_unknown_tier() -> None:
    with pytest.raises(show.DemoError):
        show.set_tier_threshold(DEMO_RULES.read_text(encoding="utf-8"), "Nope", "x", 1)


def test_prepare_copies_the_demo_config_into_the_run_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(show, "RUN_CONFIG", tmp_path / "config")

    show.cmd_prepare()

    for name in show.CONFIG_FILES:
        assert (tmp_path / "config" / name).read_bytes() == (
            show.DEMO_CONFIG / name
        ).read_bytes()


def test_leak_check_finds_plaintext_ids_and_tag_58_text_only() -> None:
    assert show.leaks_in('{"clOrdIdHash": "f61935e7f0f1f710"}') == []
    found = show.leaks_in("11=ORD1042|58=Price exceeds limit for symbol AAPL")
    assert found == ["ORD1042", "Price exceeds limit"]


def test_alerts_table_shows_delivery_and_a_short_id() -> None:
    rows = show.alerts_table(
        [
            {
                "alertId": "1234567890abcdef",
                "ruleName": "AgentHeartbeatMissing",
                "severity": "critical",
                "status": "resolved",
                "observedValue": None,
                "threshold": 20,
                "firstObservedUtc": "2026-11-18T04:00:00Z",
                "resolvedAtUtc": "2026-11-18T04:01:00Z",
                "delivery": {"status": "failed", "attempts": 3},
            }
        ]
    )
    assert rows[1].startswith("12345678 AgentHeartbeatMissing")
    assert "failed (3 attempts)" in rows[1]
    assert show.alerts_table([]) == ["No alerts yet."]


def test_backend_alerts_get_distinct_short_ids_and_no_callback_column() -> None:
    """UBS-136: each outage gets its own `backend-<rule>-<hash>` ID; the table
    must show them as different occurrences."""
    first = "backend-agentheartbeatmissing-50ddf53865b360fb"
    second = "backend-agentheartbeatmissing-c7de02db03359e6c"
    assert show.short_id(first) != show.short_id(second)
    rows = show.alerts_table(
        [{"alertId": first, "ruleName": "AgentHeartbeatMissing", "source": "backend"}]
    )
    assert rows[1].startswith("50ddf538 ")
    assert "n/a (raised by the backend)" in rows[1]


def test_answer_lines_show_provenance() -> None:
    lines = show.answer_lines(
        {
            "kind": "answer",
            "answer": "Magic recorded 2 rejected orders out of 218 submitted.",
            "intent": "rejection_summary",
            "source": "rule",
            "dataCompleteness": {
                "confidence": "complete",
                "agentsReporting": 1,
                "agentsExpected": 1,
            },
            "citations": [{"type": "metrics_query", "queryId": "q-1"}],
        }
    )
    text = "\n".join(lines)
    assert "218 submitted" in text
    assert "answered by rule, data complete (1/1 agents)" in text
    assert "cites: metrics_query q-1" in text
    assert show.answer_lines({"error": "unavailable"}) == ["  error: unavailable"]


def test_every_showcase_command_is_offered_by_both_launchers() -> None:
    bat = (ROOT / "scripts" / "demo_windows.bat").read_text(encoding="utf-8")
    mac = (ROOT / "scripts" / "demo_mac" / "demo.sh").read_text(encoding="utf-8")
    for command in (
        "ask",
        "privacy",
        "tamper",
        "replay",
        "reload",
        "outage",
        "malformed",
        "health",
        "mcp-check",
        "stub-stop",
        "stub-start",
        "reconcile",
    ):
        assert f'if /i "%CMD%"=="{command}"' in bat, command
        assert f"\n  {command})" in mac, command
    payload = json.dumps(show.TOUR)
    assert "Why are Magic orders rejecting" in payload
