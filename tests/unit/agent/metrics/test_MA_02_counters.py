from datetime import UTC, datetime
from decimal import Decimal

from fixtures import (
    EXPECTED_REJECT_REASON_TOTALS,
    EXPECTED_TOTALS,
    EXPECTED_UNMAPPED_REASONS,
    hand_labelled_events,
)
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import (
    COUNTER_DIMENSIONS,
    ReasonNormalizer,
    derive_counters,
    top_reject_reasons,
)
from telemetry_shared.models.parsed_message import (
    ExecutionReportEvent,
    ParsedMessageEvent,
)


def build_aggregator() -> tuple[MetricsAggregator, ReasonNormalizer]:
    reasons = ReasonNormalizer()
    config = AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS))
    aggregator = MetricsAggregator(
        config=config,
        clock=lambda: 1_749_700_800.0,
        resolve_reject_reason=reasons.resolve,
    )
    return aggregator, reasons


def ingest_fixture(aggregator: MetricsAggregator) -> None:
    for event in hand_labelled_events():
        aggregator.ingest_counters(event, derive_counters(event))


def test_counts_match_the_hand_labelled_fixture() -> None:
    aggregator, _ = build_aggregator()
    ingest_fixture(aggregator)

    row = aggregator.snapshot("1m", group_by=())[()]
    for metric, expected in EXPECTED_TOTALS.items():
        actual = row.counters.get(metric, Decimal(0))
        assert actual == expected, f"{metric}: expected {expected}, got {actual}"


def test_unrecognised_msg_type_is_counted_not_dropped() -> None:
    aggregator, _ = build_aggregator()
    ingest_fixture(aggregator)

    totals = aggregator.snapshot("1m", group_by=())[()].counters
    assert totals["unclassified_messages"] == Decimal(1)
    # and it still contributes to messages_total, i.e. it wasn't dropped
    # silently before reaching the counters
    assert totals["messages_total"] == EXPECTED_TOTALS["messages_total"]


def test_business_cancel_and_session_rejects_stay_separate_but_sum_to_total() -> None:
    aggregator, _ = build_aggregator()
    ingest_fixture(aggregator)

    totals = aggregator.snapshot("1m", group_by=())[()].counters
    assert totals["orders_rejected"] == Decimal(1)
    assert totals["cancel_rejects"] == Decimal(1)
    assert totals["session_rejects"] == Decimal(1)
    assert (
        totals["orders_rejected"] + totals["cancel_rejects"] + totals["session_rejects"]
        == totals["rejects_total"]
    )


def test_reject_reasons_are_normalised_and_grouped() -> None:
    aggregator, _ = build_aggregator()
    ingest_fixture(aggregator)

    grouped = aggregator.snapshot("1m", group_by=("reject_reason",))
    reason_totals = {
        label[0]: row.counters["rejects_total"] for label, row in grouped.items()
    }
    assert reason_totals == EXPECTED_REJECT_REASON_TOTALS


def test_unmapped_reasons_fold_to_other_and_are_recorded_bounded() -> None:
    aggregator, reasons = build_aggregator()
    ingest_fixture(aggregator)

    assert reasons.unmapped_seen == EXPECTED_UNMAPPED_REASONS


def test_top_reject_reasons_respects_n() -> None:
    aggregator, _ = build_aggregator()
    ingest_fixture(aggregator)

    top = top_reject_reasons(aggregator, "1m", n=2)
    assert len(top) == 2
    assert all(count == Decimal(1) for _, count in top)  # all three reasons tie at 1


def test_every_counter_is_broken_down_by_symbol() -> None:
    aggregator, _ = build_aggregator()
    ingest_fixture(aggregator)

    grouped = aggregator.snapshot("1m", group_by=("symbol",))
    assert grouped[("AAPL",)].counters["orders_submitted"] == Decimal(1)
    assert grouped[("MSFT",)].counters["orders_submitted"] == Decimal(1)
    assert grouped[("GOOG",)].counters["orders_submitted"] == Decimal(1)
    assert grouped[("AAPL",)].counters["fills_full"] == Decimal(1)
    assert grouped[("MSFT",)].counters["fills_partial"] == Decimal(1)


def _reject_event(reject_reason_text: str) -> ParsedMessageEvent:
    return ParsedMessageEvent(
        event_time_utc=datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC),
        instance_id="magic-prod-01",
        session_id="MAGIC->EXCH1",
        msg_type="Reject",
        reject_reason_text=reject_reason_text,
    )


def test_reason_normalizer_max_unmapped_is_bounded() -> None:
    normalizer = ReasonNormalizer(max_unmapped=2)
    for text in ("reason a", "reason b", "reason c", "reason d"):
        assert normalizer.resolve(_reject_event(text)) == "Other"
    assert normalizer.unmapped_seen == ("reason a", "reason b")


def test_reason_normalizer_truncates_before_storing() -> None:
    normalizer = ReasonNormalizer(max_text_length=5)
    normalizer.resolve(_reject_event("this text is much longer than five characters"))
    assert normalizer.unmapped_seen == ("this ",)


def test_reason_normalizer_does_not_duplicate_the_same_unmapped_reason() -> None:
    normalizer = ReasonNormalizer(max_unmapped=5)
    for _ in range(3):
        normalizer.resolve(_reject_event("repeated reason"))
    assert normalizer.unmapped_seen == ("repeated reason",)


def _exec_report_event(**overrides: object) -> ParsedMessageEvent:
    fields: dict[str, object] = dict(
        event_time_utc=datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC),
        instance_id="magic-prod-01",
        session_id="MAGIC->EXCH1",
        cl_ord_id="ORD-1",
        order_id="OID-1",
        exec_id="EXEC-1",
        exec_type="Trade",
        symbol="AAPL",
        side="buy",
        last_qty=Decimal(10),
    )
    fields.update(overrides)
    return ExecutionReportEvent(**fields)  # type: ignore[arg-type]


def test_fill_split_uses_leaves_qty_over_ord_status_when_both_present() -> None:
    # spec 004 §4.1: fills_full/fills_partial key on LeavesQty, not OrdStatus.
    # OrdStatus says "PartiallyFilled" here, but LeavesQty=0 is the
    # authoritative signal that this specific execution completed the order.
    event = _exec_report_event(ord_status="PartiallyFilled", leaves_qty=Decimal(0))
    counters = derive_counters(event)
    assert counters.get("fills_full") == Decimal(1)
    assert "fills_partial" not in counters


def test_fill_split_falls_back_to_ord_status_when_leaves_qty_missing() -> None:
    event = _exec_report_event(ord_status="Filled")  # no leaves_qty
    counters = derive_counters(event)
    assert counters.get("fills_full") == Decimal(1)
    assert "fills_partial" not in counters


def test_reason_normalizer_unspecified_matches_the_aggregators_default_casing() -> None:
    # FR-PRS-024: "...else unspecified" — the aggregator's own built-in
    # resolve_reject_reason default uses lowercase; ReasonNormalizer must
    # agree, or grouping by reject_reason would split "no reason at all"
    # across two different-looking labels depending on which resolver ran.
    normalizer = ReasonNormalizer()
    no_reason_event = ParsedMessageEvent(
        event_time_utc=datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC),
        instance_id="magic-prod-01",
        session_id="MAGIC->EXCH1",
        msg_type="Reject",
    )
    assert normalizer.resolve(no_reason_event) == "unspecified"


def test_orders_rejected_fires_when_only_ord_status_says_rejected() -> None:
    # spec 004: "either signal counts" — isolate ord_status alone. The
    # fixture's own reject event sets both signals together, so neither was
    # independently exercised before.
    event = _exec_report_event(exec_type="New", ord_status="Rejected")
    counters = derive_counters(event)
    assert counters.get("orders_rejected") == Decimal(1)
    assert counters.get("rejects_total") == Decimal(1)


def test_orders_rejected_fires_when_only_exec_type_says_rejected() -> None:
    event = _exec_report_event(exec_type="Rejected", ord_status="New")
    counters = derive_counters(event)
    assert counters.get("orders_rejected") == Decimal(1)
    assert counters.get("rejects_total") == Decimal(1)


def test_session_reject_reason_code_path_is_exercised_not_just_text() -> None:
    # The schema reuses one reject_reason_code slot for three different
    # source tags depending on msg_type (103/102/373); fixtures.py's own
    # session-reject event only ever sets reject_reason_text, so the
    # 373-sourced-code path (ReasonNormalizer.resolve's `code or text`
    # precedence) had zero coverage.
    aggregator, _ = build_aggregator()
    event = ParsedMessageEvent(
        event_time_utc=datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC),
        instance_id="magic-prod-01",
        session_id="MAGIC->EXCH1",
        msg_type="Reject",
        reject_reason_code="CompIdProblem",
    )
    aggregator.ingest_counters(event, derive_counters(event))

    grouped = aggregator.snapshot("1m", group_by=("reject_reason",))
    assert grouped[("CompIdProblem",)].counters["session_rejects"] == Decimal(1)
