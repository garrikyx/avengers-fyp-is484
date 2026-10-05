"""Multi-replica scatter-gather for metrics queries (UBS-92, NFR-SCA-003)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from telemetry_shared.models.metrics_query import (
    DataCompleteness,
    MetricsQueryRequest,
    MetricsQueryResponse,
    QueryGroup,
)

from telemetry_backend.config import QueryConfig
from telemetry_backend.services.query_engine import QueryEngine

REPLICA_QUERY_HEADER = "X-Replica-Query"


class FanoutClient(Protocol):
    async def post_query(
        self, peer: str, request: MetricsQueryRequest
    ) -> MetricsQueryResponse | None: ...


class ReplicaFanout:
    """Fan out a query to peer replicas and merge bucket-wise."""

    def __init__(
        self,
        *,
        local: QueryEngine,
        config: QueryConfig,
        client: FanoutClient,
    ) -> None:
        self._local = local
        self._config = config
        self._client = client

    async def query(
        self, request: MetricsQueryRequest, *, now: datetime | None = None
    ) -> MetricsQueryResponse:
        now = now or datetime.now(UTC)
        local_response = await self._local.query(
            request, now=now, skip_fanout=True
        )

        peer_tasks = [
            asyncio.wait_for(
                self._client.post_query(peer, request),
                timeout=self._config.fanout_timeout_seconds,
            )
            for peer in self._config.replica_registry
        ]
        peer_results: list[MetricsQueryResponse | None] = []
        failed_peers: list[str] = []
        for peer, task in zip(self._config.replica_registry, peer_tasks, strict=True):
            try:
                result = await task
            except TimeoutError:
                failed_peers.append(peer)
                peer_results.append(None)
                continue
            if result is None:
                failed_peers.append(peer)
                continue
            peer_results.append(result)

        responses = [local_response, *[r for r in peer_results if r is not None]]
        return self._merge_responses(
            responses,
            failed_peers=failed_peers,
            partial=bool(failed_peers),
        )

    def _merge_responses(
        self,
        responses: list[MetricsQueryResponse],
        *,
        failed_peers: list[str],
        partial: bool,
    ) -> MetricsQueryResponse:
        if len(responses) == 1:
            base = responses[0]
            if not failed_peers:
                return base
            return base.model_copy(
                update={
                    "data_completeness": base.data_completeness.model_copy(
                        update={
                            "confidence": "partial",
                            "failed_peers": failed_peers,
                        }
                    ),
                    "partial": True,
                }
            )

        base = responses[0]
        merged_totals: dict[str, Decimal] = {}
        merged_groups: dict[tuple[tuple[str, str], ...], QueryGroup] = {}

        for response in responses:
            for metric, value in response.totals.items():
                if value is None:
                    continue
                merged_totals[metric] = merged_totals.get(metric, Decimal(0)) + Decimal(
                    str(value)
                )
            for group in response.groups:
                key = tuple(sorted(group.dimensions.items()))
                existing = merged_groups.get(key)
                if existing is None:
                    merged_groups[key] = group
                else:
                    merged_counters = dict(existing.counters)
                    for metric, value in group.counters.items():
                        merged_counters[metric] = merged_counters.get(metric, 0) + value
                    merged_groups[key] = existing.model_copy(
                        update={"counters": merged_counters}
                    )

        totals_out: dict[str, int | float | None] = {
            k: int(v) if v == v.to_integral_value() else float(v)
            for k, v in merged_totals.items()
        }

        completeness = self._merge_completeness(
            [response.data_completeness for response in responses],
            failed_peers=failed_peers,
            partial=partial,
        )

        return base.model_copy(
            update={
                "totals": totals_out,
                "groups": list(merged_groups.values()),
                "data_completeness": completeness,
                "partial": partial,
            }
        )

    @staticmethod
    def _merge_completeness(
        blocks: list[DataCompleteness],
        *,
        failed_peers: list[str],
        partial: bool,
    ) -> DataCompleteness:
        stale: set[str] = set()
        failed: set[str] = set(failed_peers)
        agents_reporting = 0
        agents_expected = 0
        restarted = 0
        dropped = 0
        for block in blocks:
            stale.update(block.stale_agents)
            failed.update(block.failed_peers)
            agents_reporting = max(agents_reporting, block.agents_reporting)
            agents_expected = max(agents_expected, block.agents_expected)
            restarted += block.restarted_buckets
            dropped += block.dropped_batches_reported

        confidence = "complete"
        if stale or restarted or failed or partial:
            confidence = "partial"

        return DataCompleteness(
            agents_expected=agents_expected,
            agents_reporting=agents_reporting,
            stale_agents=sorted(stale),
            restarted_buckets=restarted,
            dropped_batches_reported=dropped,
            confidence=confidence,  # type: ignore[arg-type]
            failed_peers=sorted(failed),
        )


class HttpxFanoutClient:
    """POST metrics queries to peer replicas."""

    def __init__(self, transport: object | None = None) -> None:
        import httpx

        self._client = httpx.AsyncClient(transport=transport, timeout=5.0)

    async def post_query(
        self, peer: str, request: MetricsQueryRequest
    ) -> MetricsQueryResponse | None:
        url = peer.rstrip("/") + "/telemetry/query/metrics"
        response = await self._client.post(
            url,
            json=request.model_dump(mode="json", by_alias=True),
            headers={REPLICA_QUERY_HEADER: "1"},
        )
        if response.status_code != 200:
            return None
        return MetricsQueryResponse.model_validate(response.json())

    async def aclose(self) -> None:
        await self._client.aclose()
