"""Minimal agent registry for heartbeat tracking (subset of `FR-ING-010`)."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime

from telemetry_shared.models.ingestion import Heartbeat


@dataclass(slots=True)
class AgentRecord:
    agent_id: str
    application: str
    instance_ids: list[str] = field(default_factory=list)
    agent_version: str = ""
    last_heartbeat_utc: datetime | None = None


class AgentRegistry:
    """Records the latest heartbeat per known agent."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentRecord] = {}
        self._lock = threading.Lock()

    def record_heartbeat(self, heartbeat: Heartbeat, *, now: datetime) -> None:
        with self._lock:
            existing = self._agents.get(heartbeat.agent_id)
            if existing is None:
                existing = AgentRecord(
                    agent_id=heartbeat.agent_id,
                    application="Magic",
                )
                self._agents[heartbeat.agent_id] = existing
            existing.instance_ids = list(heartbeat.instance_ids)
            existing.agent_version = heartbeat.agent_version
            existing.last_heartbeat_utc = heartbeat.sent_at_utc or now

    def get_record(self, agent_id: str) -> AgentRecord | None:
        with self._lock:
            return self._agents.get(agent_id)

    def get_last_heartbeat(self, agent_id: str) -> datetime | None:
        with self._lock:
            record = self._agents.get(agent_id)
            return None if record is None else record.last_heartbeat_utc

    def agents_exceeding_threshold(
        self, threshold_seconds: float, *, now: datetime
    ) -> list[AgentRecord]:
        stale: list[AgentRecord] = []
        with self._lock:
            for record in self._agents.values():
                if record.last_heartbeat_utc is None:
                    continue
                age = (now - record.last_heartbeat_utc).total_seconds()
                if age > threshold_seconds:
                    stale.append(record)
        return stale

    def all_agent_ids(self) -> list[str]:
        with self._lock:
            return list(self._agents.keys())
