"""UBS-122 integration: Magic-format Application.log lines -> AppLogParser
(the error signatures shipped in config/agent.yaml) -> MetricsIngestor ->
RuleEvaluator running the shipped config/rules.yaml -> AlertRouter.

Nothing here is hand-built config: it pins that the shipped signature labels
and the shipped signature rules agree with each other, as well as the
plumbing. One OOM line warns, three escalate, and a lost-DB burst in the same
window trips only its own rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_agent.config import load_agent_config
from telemetry_agent.parser.applog.parser import AppLogParser
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import DryRunPublishSink
from telemetry_agent.rules.engine import RuleEngine
from telemetry_shared.models.alerts import AlertEvent

_REPO_ROOT = Path(__file__).resolve().parents[3]
_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_APP = "Magic"

_OOM = b"10:00:00.000001 <7> [E] VS_788: java.lang.OutOfMemoryError: heap"
_DB_LOST = b"10:00:00.000002 <7> [E] DBPool: connection lost to primary database"
_NOISE = b"10:00:00.000003 <7> [I] VS_788: order book rebuilt"


class _NullCallbackSink:
    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> CallbackResult:
        return CallbackResult(status_code=200, latency_ms=1.0)


class _Agent:
    """The shipped config, wired the way main.build_agent wires it, minus the
    file tailing and the network."""

    def __init__(self) -> None:
        cfg = load_agent_config(_REPO_ROOT / "config" / "agent.yaml")
        self.instance_id = cfg.instance_id
        self.now = _T0
        self.ingestor = MetricsIngestor.build_default(
            clock=lambda: self.now.timestamp(), monotonic=lambda: 0.0
        )
        self.parser = AppLogParser(
            app_log_patterns=list(cfg.logs.app_log_patterns),
            error_signatures=list(cfg.parsing.error_signatures),
        )
        publisher = BackendPublisher(
            DryRunPublishSink(),
            parse_publish_config({"endpoint": "https://backend.example/batch"}),
            agent_id=cfg.agent_id,
            application=_APP,
        )
        dispatcher = CallbackDispatcher(
            _NullCallbackSink(),
            parse_callbacks_config({"endpoint": "https://magic.example/cb"}),
            b"secret",
        )
        self.publisher = publisher
        engine = RuleEngine(
            cfg.rules,
            instance_id=cfg.instance_id,
            application=_APP,
            agent_id=cfg.agent_id,
            started_at=_T0 - timedelta(hours=1),
        )
        self.evaluator = RuleEvaluator(
            engine,
            self.ingestor.aggregator,
            AlertRouter(
                publisher,
                agent_id=cfg.agent_id,
                application=_APP,
                dispatcher=dispatcher,
            ),
            instance_id=cfg.instance_id,
            correlator=self.ingestor.correlator,
            session_tracker=self.ingestor.session_tracker,
            publisher=publisher,
            dispatcher=dispatcher,
            clock=lambda: self.now,
            monotonic=lambda: 0.0,
            lock=self.ingestor.lock,
        )

    def log(self, *lines: bytes) -> None:
        meta = SourceMeta(
            instance_id=self.instance_id,
            path="Application.log",
            log_type="app",
            read_at=self.now,
        )
        for line in lines:
            self.ingestor.ingest(self.parser.parse(line, meta), meta)

    def tick(self, advance: float = 1.0) -> list[AlertEvent]:
        self.now += timedelta(seconds=advance)
        return self.evaluator.evaluate_once()


def _signature_alerts(alerts: list[AlertEvent]) -> list[tuple[str, str]]:
    return [(a.rule_name, a.severity) for a in alerts if a.rule_name.startswith("App")]


def test_shipped_signature_rules_fire_on_their_own_patterns_only() -> None:
    """`for: 0s` still means pending on the first tick and firing on the next
    (only pending -> firing notifies, FR-RUL-012): one evaluation interval of
    latency. An escalation while firing notifies on the very next tick."""
    agent = _Agent()
    agent.log(_OOM, _NOISE)

    assert _signature_alerts(agent.tick()) == []  # pending
    assert _signature_alerts(agent.tick()) == [("AppOutOfMemory", "warning")]

    agent.log(_OOM, _OOM)  # three in the 1m window
    assert _signature_alerts(agent.tick()) == [("AppOutOfMemory", "critical")]

    agent.log(_DB_LOST)
    agent.tick()  # pending
    assert _signature_alerts(agent.tick()) == [("AppDbConnectionLost", "warning")]


def test_app_log_lines_keep_no_log_activity_quiet_end_to_end() -> None:
    """Only Application.log is talking — no FIX at all — and the agent must
    not page that its pipeline is dead."""
    agent = _Agent()
    for _ in range(3):
        agent.log(_NOISE)
        fired = agent.tick()
        assert "NoLogActivity" not in [a.rule_name for a in fired]
