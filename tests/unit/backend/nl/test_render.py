"""Template renderer tests (UBS-99, FR-NLQ-009/015/016)."""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_backend.nl.render import RenderInput, render_answer
from telemetry_shared.models.alerts_query import AlertDelivery, AlertRecord
from telemetry_shared.models.metrics_query import (
    DataCompleteness,
    EffectiveTimeRange,
    MetricsQueryResponse,
    QueryGroup,
    QueryInterpretation,
)

_NOW = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_RANGE = EffectiveTimeRange(
    from_utc=datetime(2026, 6, 12, 3, 30, 0, tzinfo=UTC),
    to_utc=_NOW,
)


def _response(**totals: float | int | None) -> MetricsQueryResponse:
    return MetricsQueryResponse(
        query_id="q-1",
        evaluated_at_utc=_NOW,
        effective_time_range=_RANGE,
        interpretation=QueryInterpretation(metrics=[], group_by=[], filters={}),
        totals=dict(totals),
        groups=[
            QueryGroup(
                dimensions={"rejectReason": "OrderExceedsLimit"},
                counters={"orders_rejected": 35},
            ),
            QueryGroup(
                dimensions={"rejectReason": "UnknownSymbol"},
                counters={"orders_rejected": 18},
            ),
        ],
        data_completeness=DataCompleteness(
            agents_expected=3,
            agents_reporting=2,
            confidence="partial",
        ),
    )


def test_rejection_summary_null_rate_wording() -> None:
    data = _response(orders_submitted=0, orders_rejected=0, rejectRate=None)
    out = render_answer(
        RenderInput(intent="rejection_summary", data=data, application="Magic")
    )
    assert "not enough activity" in out.answer
    assert "0%" not in out.answer


def test_rejection_summary_leads_with_counts() -> None:
    data = _response(orders_submitted=1250, orders_rejected=62, rejectRate=0.05)
    out = render_answer(
        RenderInput(intent="rejection_summary", data=data, application="Magic")
    )
    assert out.answer.startswith("Magic recorded 62 rejected")
    assert "5.0%" in out.answer
    assert len(out.chart_rows) >= 1


def test_completeness_caveat_in_answer() -> None:
    data = _response(orders_submitted=10, orders_rejected=1, rejectRate=0.1)
    out = render_answer(
        RenderInput(intent="rejection_summary", data=data, application="Magic")
    )
    assert "1 of 3 agents is not reporting" in out.answer


def test_alert_delivery_phrase_in_technical_mode() -> None:
    data = _response()
    alert = AlertRecord(
        alert_id="alert-1",
        source="agent",
        agent_id="a1",
        application="Magic",
        instance_id="magic-prod-01",
        rule_name="HighRejectRate",
        severity="critical",
        status="firing",
        matched_condition="rejectRate > 0.05",
        observed_value=0.06,
        threshold=0.05,
        first_observed_utc=datetime(2026, 6, 12, 3, 48, 0, tzinfo=UTC),
        last_observed_utc=_NOW,
        notification_count=1,
        delivery=AlertDelivery(status="delivered", attempts=1),
    )
    out = render_answer(
        RenderInput(
            intent="alert_status",
            data=data,
            alerts=(alert,),
            now=_NOW,
        )
    )
    assert "delivered" in out.answer
    assert "alert-1" in out.answer
    assert len(out.alert_summaries) == 1
