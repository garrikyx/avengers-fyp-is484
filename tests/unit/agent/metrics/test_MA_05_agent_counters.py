"""UBS-74: `MetricsAggregator.ingest_agent_counters` and the
`AgentCounterSampler` that feeds it.

These are the agent's *own* counters — callback delivery outcomes — which
have no ParsedMessageEvent behind them, so they cannot ride the normal
per-event ingest path.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fixtures import FakeClock
from telemetry_agent.metrics.agent_counters import AgentCounterSampler
from telemetry_agent.metrics.aggregator import (
    OTHER_LABEL,
    AggregatorConfig,
    MetricsAggregator,
)
from telemetry_agent.metrics.counters import AGENT_DIMS, COUNTER_DIMENSIONS
from telemetry_shared.models.parsed_message import ParsedMessageEvent

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_INSTANCE = "magic-prod-01"


def _aggregator(clock: FakeClock | None = None) -> MetricsAggregator:
    config = AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS))
    return MetricsAggregator(
        config=config, clock=clock or FakeClock(_T0.timestamp())
    )


def _total(aggregator: MetricsAggregator, metric: str) -> Decimal:
    row = aggregator.snapshot("5m", group_by=()).get(())
    return Decimal(0) if row is None else row.counters.get(metric, Decimal(0))


def test_callback_counters_are_declared_on_agent_dims() -> None:
    for metric in (
        "callback_failures",
        "callback_delivered",
        "callback_queue_dropped",
    ):
        assert COUNTER_DIMENSIONS[metric] == AGENT_DIMS


def test_ingest_agent_counters_lands_in_the_window() -> None:
    aggregator = _aggregator()
    aggregator.ingest_agent_counters(
        dims={"instance_id": _INSTANCE},
        counters={"callback_failures": Decimal(4)},
        at=_T0,
    )
    assert _total(aggregator, "callback_failures") == Decimal(4)


def test_agent_counters_group_by_instance_only() -> None:
    aggregator = _aggregator()
    aggregator.ingest_agent_counters(
        dims={"instance_id": _INSTANCE},
        counters={"callback_failures": Decimal(1)},
        at=_T0,
    )
    grouped = aggregator.snapshot("5m", group_by=("instance_id",))
    assert grouped[(_INSTANCE,)].counters["callback_failures"] == Decimal(1)
    # AGENT_DIMS doesn't include session_id, so FR-MET-030 drops the metric
    # from a session-scoped query rather than inventing a label for it.
    assert aggregator.snapshot("5m", group_by=("session_id",)) == {}


def test_ingest_agent_counters_does_not_mark_the_agent_as_having_seen_an_event() -> (
    None
):
    """The whole reason this is a separate write path: the dispatcher
    retrying is not evidence Magic is still writing logs. If these counters
    bumped `_last_event_at`, a log-starved agent would look alive through
    the `secondsSinceLastEvent` gauge that NoLogActivity's sibling reads.
    """
    aggregator = _aggregator()
    assert aggregator.seconds_since_last_event() is None
    aggregator.ingest_agent_counters(
        dims={"instance_id": _INSTANCE},
        counters={"callback_failures": Decimal(9)},
        at=_T0,
    )
    assert aggregator.seconds_since_last_event() is None


def test_ordinary_ingest_still_does_mark_it() -> None:
    """Guard on the contrast above — proves the assertion isn't passing
    because `seconds_since_last_event` is broken for everyone.
    """
    aggregator = _aggregator()
    aggregator.ingest_counters(
        ParsedMessageEvent(
            event_time_utc=_T0,
            instance_id=_INSTANCE,
            session_id="MAGIC->EXCH1",
            msg_type="Heartbeat",
        ),
        {"messages_total": Decimal(1)},
    )
    assert aggregator.seconds_since_last_event() == 0.0


def test_missing_declared_dimension_raises_naming_the_dimension() -> None:
    aggregator = _aggregator()
    with pytest.raises(KeyError, match="instance_id"):
        aggregator.ingest_agent_counters(
            dims={"wrong_key": _INSTANCE},
            counters={"callback_failures": Decimal(1)},
            at=_T0,
        )


def test_undeclared_metric_raises_like_the_event_path_does() -> None:
    aggregator = _aggregator()
    with pytest.raises(KeyError, match="FR-MET-030"):
        aggregator.ingest_agent_counters(
            dims={"instance_id": _INSTANCE},
            counters={"not_a_declared_metric": Decimal(1)},
            at=_T0,
        )


def test_sample_older_than_the_retained_window_is_dropped_not_stored() -> None:
    aggregator = _aggregator()
    aggregator.ingest_agent_counters(
        dims={"instance_id": _INSTANCE},
        counters={"callback_failures": Decimal(7)},
        at=_T0 - timedelta(hours=1),
    )
    assert _total(aggregator, "callback_failures") == Decimal(0)


def test_cardinality_cap_folds_agent_labels_like_any_other_metric() -> None:
    config = AggregatorConfig(
        metric_dimensions=dict(COUNTER_DIMENSIONS), max_label_sets=2
    )
    aggregator = MetricsAggregator(config=config, clock=FakeClock(_T0.timestamp()))
    for i in range(5):
        aggregator.ingest_agent_counters(
            dims={"instance_id": f"instance-{i}"},
            counters={"callback_failures": Decimal(1)},
            at=_T0,
        )
    assert aggregator.cardinality_folded == 3
    grouped = aggregator.snapshot("5m", group_by=("instance_id",))
    assert grouped[(OTHER_LABEL,)].counters["callback_failures"] == Decimal(3)


# --- AgentCounterSampler --------------------------------------------------


def test_first_sample_ingests_the_whole_count_from_zero() -> None:
    aggregator = _aggregator()
    sampler = AgentCounterSampler(aggregator, instance_id=_INSTANCE)
    sampler.sample({"callback_failures": 4}, at=_T0)
    assert _total(aggregator, "callback_failures") == Decimal(4)


def test_subsequent_samples_ingest_only_the_delta() -> None:
    aggregator = _aggregator()
    sampler = AgentCounterSampler(aggregator, instance_id=_INSTANCE)
    sampler.sample({"callback_failures": 4}, at=_T0)
    sampler.sample({"callback_failures": 6}, at=_T0)
    # 4 then +2, not 4 then +6 — the registry is monotonic since startup,
    # so re-ingesting its absolute value would double-count every sample.
    assert _total(aggregator, "callback_failures") == Decimal(6)


def test_unchanged_counter_ingests_nothing() -> None:
    aggregator = _aggregator()
    sampler = AgentCounterSampler(aggregator, instance_id=_INSTANCE)
    sampler.sample({"callback_failures": 3}, at=_T0)
    sampler.sample({"callback_failures": 3}, at=_T0)
    assert _total(aggregator, "callback_failures") == Decimal(3)


def test_registry_reset_rebaselines_instead_of_going_negative() -> None:
    """A restarted dispatcher's registry drops back to 0. That is a new
    baseline, not -5 failures.
    """
    aggregator = _aggregator()
    sampler = AgentCounterSampler(aggregator, instance_id=_INSTANCE)
    sampler.sample({"callback_failures": 5}, at=_T0)
    sampler.sample({"callback_failures": 0}, at=_T0)
    assert _total(aggregator, "callback_failures") == Decimal(5)
    # And it counts up again from the new baseline, not from 5.
    sampler.sample({"callback_failures": 2}, at=_T0)
    assert _total(aggregator, "callback_failures") == Decimal(7)


def test_untracked_registry_keys_are_ignored() -> None:
    aggregator = _aggregator()
    sampler = AgentCounterSampler(aggregator, instance_id=_INSTANCE)
    # `callback_queue_dropped` is tracked; `some_other_counter` is not
    # declared in COUNTER_DIMENSIONS and would raise if it were ingested.
    sampler.sample(
        {"callback_queue_dropped": 2, "some_other_counter": 99}, at=_T0
    )
    assert _total(aggregator, "callback_queue_dropped") == Decimal(2)


def test_deltas_land_in_the_bucket_for_their_own_timestamp() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    sampler = AgentCounterSampler(aggregator, instance_id=_INSTANCE)

    sampler.sample({"callback_failures": 2}, at=_T0)
    clock.advance(240)
    sampler.sample({"callback_failures": 5}, at=_T0 + timedelta(seconds=240))
    assert _total(aggregator, "callback_failures") == Decimal(5)

    # Roll past the 5m window from the first sample: only the later delta
    # of 3 is still inside it.
    clock.advance(120)
    assert _total(aggregator, "callback_failures") == Decimal(3)
