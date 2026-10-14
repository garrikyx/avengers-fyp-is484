"""Backend-owned `AgentHeartbeatMissing` rule (`FR-QRY-018`, `FR-RUL-030`)."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from telemetry_shared.models.alerts import AlertEvent

from telemetry_backend.config import AlertingConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore

logger = logging.getLogger(__name__)

_RULE_NAME = "AgentHeartbeatMissing"
_DEFAULT_APPLICATION = "Magic"


def backend_alert_id(agent_id: str) -> str:
    digest = hashlib.sha256(f"{_RULE_NAME}:{agent_id}".encode()).hexdigest()
    return f"backend-{_RULE_NAME.lower()}-{digest[:16]}"


class HeartbeatMonitor:
    """Periodically evaluates agent heartbeat staleness."""

    def __init__(
        self,
        *,
        registry: AgentRegistry,
        alert_store: AlertStore,
        config: AlertingConfig | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._registry = registry
        self._alert_store = alert_store
        self._config = config or AlertingConfig()
        self._now_fn = now_fn or (lambda: datetime.now(UTC))
        self._firing: set[str] = set()

    def _build_firing_event(
        self, *, agent_id: str, application: str, instance_id: str, age_seconds: float
    ) -> AlertEvent:
        now = self._now_fn()
        threshold = float(self._config.missing_heartbeat_threshold_seconds)
        return AlertEvent(
            alert_id=backend_alert_id(agent_id),
            rule_name=_RULE_NAME,
            severity="critical",
            status="firing",
            application=application,
            instance_id=instance_id,
            agent_id=agent_id,
            matched_condition=(
                f"no heartbeat for {age_seconds:.0f}s "
                f"(threshold {threshold:.0f}s)"
            ),
            observed_value=age_seconds,
            threshold=threshold,
            first_observed_utc=now,
            last_observed_utc=now,
            notification_count=1,
        )

    def _build_resolved_event(
        self, *, agent_id: str, application: str, instance_id: str
    ) -> AlertEvent:
        now = self._now_fn()
        threshold = float(self._config.missing_heartbeat_threshold_seconds)
        return AlertEvent(
            alert_id=backend_alert_id(agent_id),
            rule_name=_RULE_NAME,
            severity="critical",
            status="resolved",
            application=application,
            instance_id=instance_id,
            agent_id=agent_id,
            matched_condition=(
                f"heartbeat restored within {threshold:.0f}s threshold"
            ),
            observed_value=0.0,
            threshold=threshold,
            first_observed_utc=now,
            last_observed_utc=now,
            resolved_at_utc=now,
            notification_count=1,
        )

    @staticmethod
    def _instance_id(agent_id: str, record_instance_ids: list[str]) -> str:
        return record_instance_ids[0] if record_instance_ids else agent_id

    def evaluate_once(self) -> None:
        now = self._now_fn()
        stale_ids = set(self._registry.stale_agents(at=now))

        for agent_id in stale_ids:
            record = self._registry.get(agent_id)
            if record is None:
                continue
            instance_id = self._instance_id(agent_id, record.instance_ids)
            age = (now - record.received_at).total_seconds()
            event = self._build_firing_event(
                agent_id=agent_id,
                application=_DEFAULT_APPLICATION,
                instance_id=instance_id,
                age_seconds=age,
            )
            self._alert_store.merge(event, source="backend", now=now)
            self._firing.add(agent_id)

        recovered = self._firing - stale_ids
        for agent_id in recovered:
            record = self._registry.get(agent_id)
            if record is None:
                self._firing.discard(agent_id)
                continue
            instance_id = self._instance_id(agent_id, record.instance_ids)
            event = self._build_resolved_event(
                agent_id=agent_id,
                application=_DEFAULT_APPLICATION,
                instance_id=instance_id,
            )
            self._alert_store.merge(event, source="backend", now=now)
            self._firing.discard(agent_id)

    async def run(self) -> None:
        while True:
            await asyncio.to_thread(self.evaluate_once)
            await asyncio.sleep(self._config.monitor_interval_seconds)

    def on_heartbeat(self, agent_id: str) -> None:
        """Resolve a backend alert immediately when a fresh heartbeat arrives."""
        if agent_id not in self._firing:
            return
        record = self._registry.get(agent_id)
        if record is None:
            self._firing.discard(agent_id)
            return
        now = self._now_fn()
        if not self._registry.is_stale(record, at=now):
            instance_id = self._instance_id(agent_id, record.instance_ids)
            event = self._build_resolved_event(
                agent_id=agent_id,
                application=_DEFAULT_APPLICATION,
                instance_id=instance_id,
            )
            self._alert_store.merge(event, source="backend", now=now)
            self._firing.discard(agent_id)
