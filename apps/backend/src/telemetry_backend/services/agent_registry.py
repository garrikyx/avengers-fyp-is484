"""Agent Registry (spec 006 FR-ING-010; UBS-69 read side, UBS-87 write side).

One in-memory record per `agentId`: the last heartbeat document plus when the
backend received it. Staleness is decided at *read* time from the backend's
own clock (`received_at`), never from the agent's `sentAtUtc` alone - an
agent that has died cannot report its own death, and an agent with a skewed
clock must not look dead or alive because of it (spec 004 s6, UBS-69 scope
note). See docs/plan/ubs69-96-notes.md.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from telemetry_shared.models.health import AgentHeartbeat, RegistryStatus

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True, frozen=True)
class AgentRecord:
    agent_id: str
    first_seen_at: datetime
    received_at: datetime  # backend clock, drives staleness
    heartbeat: AgentHeartbeat  # last document as sent

    @property
    def instance_ids(self) -> list[str]:
        return list(self.heartbeat.instance_ids)

    @property
    def agent_version(self) -> str:
        return self.heartbeat.agent_version

    @property
    def last_heartbeat_utc(self) -> datetime:
        return self.heartbeat.sent_at_utc


class AgentRegistry:
    """Thread-safe map of known agents. Memory-only by design (FR-QRY-005)."""

    def __init__(
        self, missing_threshold_seconds: float = 60.0, clock: Clock | None = None
    ) -> None:
        if missing_threshold_seconds <= 0:
            raise ValueError("missing_threshold_seconds must be > 0")
        self.missing_threshold_seconds = missing_threshold_seconds
        self._clock = clock or _utc_now
        self._lock = threading.Lock()
        self._agents: dict[str, AgentRecord] = {}

    # --- write side (UBS-87 calls this from the batch path) ----------------------

    def record_heartbeat(
        self, heartbeat: AgentHeartbeat, received_at: datetime | None = None
    ) -> bool:
        """Store the latest heartbeat. Returns True on first contact so the
        caller can emit the unknown-agent event FR-ING-010 asks for."""
        received_at = received_at or self._clock()
        with self._lock:
            existing = self._agents.get(heartbeat.agent_id)
            if existing is None:
                self._agents[heartbeat.agent_id] = AgentRecord(
                    agent_id=heartbeat.agent_id,
                    first_seen_at=received_at,
                    received_at=received_at,
                    heartbeat=heartbeat,
                )
                return True
            # A late-delivered older heartbeat must not roll the view backwards.
            if heartbeat.sent_at_utc < existing.heartbeat.sent_at_utc:
                return False
            self._agents[heartbeat.agent_id] = replace(
                existing, received_at=received_at, heartbeat=heartbeat
            )
            return False

    def remove(self, agent_id: str) -> bool:
        """Decommission (spec 011 runbook) so `missing` does not fire forever."""
        with self._lock:
            return self._agents.pop(agent_id, None) is not None

    # --- read side (UBS-69) --------------------------------------------------------

    def get(self, agent_id: str) -> AgentRecord | None:
        with self._lock:
            return self._agents.get(agent_id)

    def all(self) -> list[AgentRecord]:
        with self._lock:
            return sorted(self._agents.values(), key=lambda r: r.agent_id)

    def heartbeat_age_ms(self, record: AgentRecord, at: datetime | None = None) -> int:
        at = at or self._clock()
        return max(0, int((at - record.received_at).total_seconds() * 1000))

    def is_stale(self, record: AgentRecord, at: datetime | None = None) -> bool:
        return self.heartbeat_age_ms(record, at) > self.missing_threshold_seconds * 1000

    def status_of(
        self, record: AgentRecord, at: datetime | None = None
    ) -> RegistryStatus:
        """`missing` if stale, otherwise whatever the agent last reported."""
        if self.is_stale(record, at):
            return "missing"
        return record.heartbeat.status

    def stale_agents(self, at: datetime | None = None) -> list[str]:
        """Agent IDs past the threshold - the `dataCompleteness.staleAgents`
        input (FR-QRY-015) and what UBS-95's AgentHeartbeatMissing reads."""
        at = at or self._clock()
        return [r.agent_id for r in self.all() if self.is_stale(r, at)]

    def __len__(self) -> int:
        with self._lock:
            return len(self._agents)
