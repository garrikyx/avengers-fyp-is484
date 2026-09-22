"""UBS-74: bridges the agent's own since-startup counters into the
windowed MetricsAggregator, so a Rule Engine rule can alert on them.

The Callback Dispatcher's `self_metrics.CounterRegistry` counts
monotonically from process start; `CallbackFailing` asks "more than 3
failures *in the last 5 minutes*". Those are different questions, and the
gap between them is a delta: sample the registry periodically, ingest only
what changed since the previous sample, and let the aggregator's ring
buffer do the windowing it already does for every other counter.

Takes a plain `Mapping[str, int]` rather than a `CounterRegistry`, so
`metrics/` never imports `callbacks/` — any counter registry with a
`snapshot()` of that shape works.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from telemetry_agent.metrics.aggregator import MetricsAggregator

# The counters metrics.counters declares on AGENT_DIMS. Kept as the default
# rather than hardcoded inside sample(), so a caller can track a subset (or
# a future producer's own counters) without editing this module.
DEFAULT_AGENT_METRICS: frozenset[str] = frozenset(
    {"callback_failures", "callback_delivered", "callback_queue_dropped"}
)


class AgentCounterSampler:
    """Turns monotonic since-startup counters into per-bucket deltas.

    Stateful across calls: it holds the previous sample as the baseline.
    One sampler per registry — sharing one between two registries would
    diff each against the other's baseline.
    """

    def __init__(
        self,
        aggregator: MetricsAggregator,
        *,
        instance_id: str,
        metrics: frozenset[str] = DEFAULT_AGENT_METRICS,
    ) -> None:
        self._aggregator = aggregator
        self._dims = {"instance_id": instance_id}
        self._metrics = metrics
        self._baseline: dict[str, int] = {}

    def sample(self, snapshot: Mapping[str, int], *, at: datetime) -> None:
        """Ingest the increase in each tracked counter since the last call.

        The first call establishes the baseline from zero, so counters that
        accumulated before the first sample are not lost. A counter that
        went *down* since the last sample means the registry was reset (the
        dispatcher was rebuilt, or the process restarted): that is a new
        baseline, not a negative count, so it contributes nothing to this
        bucket and is simply re-baselined.
        """
        deltas: dict[str, Decimal] = {}
        for metric in self._metrics:
            current = snapshot.get(metric, 0)
            delta = current - self._baseline.get(metric, 0)
            self._baseline[metric] = current
            if delta > 0:
                deltas[metric] = Decimal(delta)
        if not deltas:
            return
        self._aggregator.ingest_agent_counters(
            dims=self._dims, counters=deltas, at=at
        )
