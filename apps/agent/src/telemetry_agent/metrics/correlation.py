"""MA-03: order correlation and latency.

Standalone producer into the shared MetricsAggregator's histograms — it does
not maintain its own query surface. Its own state (the open-order map) is
order-lifecycle-shaped, not bucket-shaped, so it is a separate data
structure from the ring buffer, with its own TTL/cap eviction. Agent-internal
— plain dataclasses, not a telemetry_shared contract.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from telemetry_agent.metrics.aggregator import MetricsAggregator
from telemetry_agent.metrics.counters import BASE_DIMS
from telemetry_shared.models.parsed_message import ParsedMessageEvent

Clock = Callable[[], float]
TimestampSource = Literal["log_observed", "transact_time"]

# FR-MET-030's shared table entry for this module's three histograms.
LATENCY_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "ack_latency_ms": BASE_DIMS,
    "exec_latency_ms": BASE_DIMS,
    "cancel_latency_ms": BASE_DIMS,
}

_NEW_ORDER_MSG_TYPES = frozenset(
    {"NewOrderSingle", "OrderCancelRequest", "OrderCancelReplaceRequest"}
)
_CANCEL_ORIGIN_MSG_TYPES = frozenset(
    {"OrderCancelRequest", "OrderCancelReplaceRequest"}
)

_DEFAULT_TTL_SECONDS = 15 * 60
_DEFAULT_MAX_ENTRIES = 100_000
_DEFAULT_MAX_PLAUSIBLE_MS = Decimal(
    3_600_000
)  # 1 hour; only reachable via a skewed transact_time


def _timedelta_to_ms(delta: timedelta) -> Decimal:
    """Exact, never float: build the millisecond value from integer
    microseconds rather than `Decimal(delta.total_seconds())`, which would
    round-trip through a float.
    """
    total_microseconds = (
        delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds
    )
    return Decimal(total_microseconds) / Decimal(1000)


@dataclass(slots=True)
class OrderContext:
    """One tracked order, keyed by (session_id, cl_ord_id).

    orig_cl_ord_id is retained for lineage/traceability when this entry is a
    cancel/replace of a prior order; latency for *this* cl_ord_id is still
    measured from *this* entry's own first-seen time, not carried forward
    from the original order — a deliberate simplification: the ticket
    specifies the link but not which timestamp a replace's latency should
    use, and propagating the original clock forward would conflate "how long
    since the very first order" with "how long since this specific request",
    which is a different, larger design question than this epic asks for.

    origin_msg_type decides which histogram a response resolves to: spec
    004 §4.4 scopes ack_latency_ms / exec_latency_ms specifically to 35=D
    ("NewOrderSingle → first 35=8"), not to cancel/replace requests, and
    scopes cancel_latency_ms to 35=F ("→ 35=8 Canceled or 35=9"). A
    cancel/replace request is still tracked here (so its response isn't
    misclassified as an orphan) even though spec defines no histogram for a
    replace's own confirmation (ExecType=Replaced) — nothing is recorded for
    that case, deliberately, rather than inventing an unspecified metric.
    """

    first_seen_at: datetime
    orig_cl_ord_id: str | None
    origin_msg_type: str
    ack_recorded: bool = False
    first_fill_recorded: bool = False
    cancel_recorded: bool = False


@dataclass(slots=True)
class CorrelatorStats:
    ttl_evictions: int = 0
    cap_evictions: int = 0
    unmatched_orders: int = 0
    orphan_responses: int = 0
    latency_anomalies: int = 0


class LatencyCorrelator:
    """order -> ack, order -> first-fill, and cancel -> outcome latency, fed
    into a shared MetricsAggregator's histograms.
    """

    def __init__(
        self,
        aggregator: MetricsAggregator,
        *,
        ttl_seconds: float = _DEFAULT_TTL_SECONDS,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        timestamp_source: TimestampSource = "log_observed",
        max_plausible_ms: Decimal = _DEFAULT_MAX_PLAUSIBLE_MS,
        clock: Clock = time.time,
    ) -> None:
        self._aggregator = aggregator
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._timestamp_source = timestamp_source
        self._max_plausible_ms = max_plausible_ms
        self._clock = clock
        self._open: dict[tuple[str, str], OrderContext] = {}
        self.stats = CorrelatorStats()

    @property
    def timestamp_source(self) -> TimestampSource:
        """Recorded so consumers of a snapshot know what a latency number
        means (MA-03 AC) — the correlator's own basis, not per-sample.
        """
        return self._timestamp_source

    def _timestamp_of(self, event: ParsedMessageEvent) -> datetime:
        if (
            self._timestamp_source == "transact_time"
            and event.transact_time_utc is not None
        ):
            return event.transact_time_utc
        return event.event_time_utc

    def tick(self) -> None:
        """Timer-callable expiry sweep, independent of ingest — mirrors
        MetricsAggregator.tick so both can be driven by the same runtime
        scheduler.
        """
        self._evict_expired()

    def ingest(self, event: ParsedMessageEvent) -> None:
        self._evict_expired()

        if event.msg_type in _NEW_ORDER_MSG_TYPES:
            self._track_new_order(event)
        elif event.msg_type == "ExecutionReport":
            self._handle_execution_report(event)
        elif event.msg_type == "OrderCancelReject":
            self._handle_cancel_reject(event)

    def _track_new_order(self, event: ParsedMessageEvent) -> None:
        if event.cl_ord_id is None:
            return
        self._evict_if_at_capacity()
        key = (event.session_id, event.cl_ord_id)
        self._open[key] = OrderContext(
            first_seen_at=self._timestamp_of(event),
            orig_cl_ord_id=event.orig_cl_ord_id,
            origin_msg_type=event.msg_type,
        )

    def _handle_execution_report(self, event: ParsedMessageEvent) -> None:
        if event.cl_ord_id is None:
            return
        key = (event.session_id, event.cl_ord_id)
        context = self._open.get(key)
        if context is None:
            self.stats.orphan_responses += 1
            return

        if context.origin_msg_type == "NewOrderSingle":
            if event.exec_type == "New" and not context.ack_recorded:
                context.ack_recorded = True
                self._record_latency("ack_latency_ms", context.first_seen_at, event)
            elif event.exec_type == "Trade" and not context.first_fill_recorded:
                context.first_fill_recorded = True
                self._record_latency("exec_latency_ms", context.first_seen_at, event)
        elif context.origin_msg_type in _CANCEL_ORIGIN_MSG_TYPES:
            if event.exec_type == "Canceled" and not context.cancel_recorded:
                context.cancel_recorded = True
                self._record_latency("cancel_latency_ms", context.first_seen_at, event)
        # A duplicate ack/fill/cancel (already recorded) is a deliberate
        # no-op: not a second latency sample, and not an anomaly either.

    def _handle_cancel_reject(self, event: ParsedMessageEvent) -> None:
        if event.cl_ord_id is None:
            return
        key = (event.session_id, event.cl_ord_id)
        context = self._open.get(key)
        if context is None:
            self.stats.orphan_responses += 1
            return
        if (
            context.origin_msg_type in _CANCEL_ORIGIN_MSG_TYPES
            and not context.cancel_recorded
        ):
            context.cancel_recorded = True
            self._record_latency("cancel_latency_ms", context.first_seen_at, event)

    def _record_latency(
        self, metric: str, started_at: datetime, response_event: ParsedMessageEvent
    ) -> None:
        responded_at = self._timestamp_of(response_event)
        delta_ms = _timedelta_to_ms(responded_at - started_at)
        if delta_ms < 0 or delta_ms > self._max_plausible_ms:
            self.stats.latency_anomalies += 1
            return
        self._aggregator.observe_latency(
            metric=metric,
            dims_event=response_event,
            value_ms=delta_ms,
            at=response_event.event_time_utc,
        )

    def _evict_if_at_capacity(self) -> None:
        if len(self._open) < self._max_entries:
            return
        oldest_key = min(self._open, key=lambda key: self._open[key].first_seen_at)
        del self._open[oldest_key]
        self.stats.cap_evictions += 1
        self.stats.unmatched_orders += 1

    def _evict_expired(self) -> None:
        cutoff = self._clock() - self._ttl_seconds
        expired = [
            key
            for key, ctx in self._open.items()
            if ctx.first_seen_at.timestamp() < cutoff
        ]
        for key in expired:
            del self._open[key]
            self.stats.ttl_evictions += 1
            self.stats.unmatched_orders += 1
