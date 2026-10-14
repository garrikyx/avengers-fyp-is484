"""`dataCompleteness` block for query responses (spec 006 s4.1, FR-QRY-015).

UBS-69 owns the agent-staleness inputs (`agentsExpected`, `agentsReporting`,
`staleAgents`) so a query over a dead agent's instance does not report zero
activity as healthy. UBS-91 (query envelope) calls `build()` and fills the
bucket-level fields (`restartedBuckets`, `droppedBatchesReported`) from the
Metric Store. Nothing here produces a query response on its own.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from telemetry_shared.models._base import CamelModel

from telemetry_backend.services.agent_registry import AgentRegistry

Confidence = Literal["complete", "partial", "degraded"]


class DataCompleteness(CamelModel):
    agents_expected: int
    agents_reporting: int
    stale_agents: list[str]
    restarted_buckets: int = 0
    dropped_batches_reported: int = 0
    confidence: Confidence


def build(
    registry: AgentRegistry,
    at: datetime,
    *,
    expected_agent_ids: list[str] | None = None,
    restarted_buckets: int = 0,
    dropped_batches_reported: int = 0,
) -> DataCompleteness:
    """Derive completeness from the registry at `at`.

    `expected_agent_ids` is the set the query covers (e.g. every agent whose
    instance matched the filter); default is every agent the registry knows.
    An agent that has *never* reported is counted as expected-but-stale, so a
    filter for an instance nobody serves is not `complete`.
    """
    known = {r.agent_id: r for r in registry.all()}
    expected = (
        list(expected_agent_ids) if expected_agent_ids is not None else list(known)
    )
    stale = [
        agent_id
        for agent_id in expected
        if agent_id not in known or registry.is_stale(known[agent_id], at)
    ]
    reporting = len(expected) - len(stale)

    if not expected or reporting == len(expected):
        confidence: Confidence = "complete"
    elif reporting == 0:
        confidence = "degraded"
    else:
        confidence = "partial"
    if confidence == "complete" and (restarted_buckets or dropped_batches_reported):
        # Every agent is talking but some of what they said is known to be
        # incomplete (FR-HLT-004: a gap is never a zero).
        confidence = "partial"

    return DataCompleteness(
        agents_expected=len(expected),
        agents_reporting=reporting,
        stale_agents=stale,
        restarted_buckets=restarted_buckets,
        dropped_batches_reported=dropped_batches_reported,
        confidence=confidence,
    )
