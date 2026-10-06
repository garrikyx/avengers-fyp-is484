"""UBS-109: routes Rule Engine alerts to the Backend Publisher.

`RuleEngine.evaluate()` returns `AlertEvent`s and `BackendPublisher` accepts
them via `enqueue_alert()`, but nothing joined the two — the publisher's own
docstring notes that "nothing in this repo calls them yet". Alerts fired
locally and the backend never learned they existed.

Lives in `pipeline/` because that is this package's composition layer
(`PipelineBridge` assembles `logs/` + `parser/` + queues + `committer`), and
because `rules/` must not import `publishing/`: the Rule Engine deliberately
knows nothing about transports so a backend outage cannot affect alerting
(`NFR-REL-003`).

Alerts are *also* consumed by the Callback Dispatcher, which has its own
`enqueue()`. Wiring that is UBS-32/33/34's; `route()` is shaped so a second
sink is additive rather than a rewrite.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime

from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_agent.publishing.publisher import BackendPublisher


class AlertRouter:
    """Enqueues alerts for publication, rejecting any that would poison the
    batch they land in.

    The rejection is the reason this is a class and not a two-line loop.
    `TelemetryBatch.identities_match_batch` requires every alert's `agentId`
    and `application` to equal the batch's, and that validator runs inside
    `build_batch`, inside `publish_once`, where nothing catches
    `ValidationError`. Measured against the real publisher, one mismatched
    alert therefore:

    1. raises out of `publish_once` and out of `run()`, killing the publisher
       task for good; and
    2. silently destroys the *other* alerts in that batch — they were already
       `take()`-n off the buffer when the raise happened, so they are never
       sent and never requeued. Three alerts in, one bad: zero sink calls,
       empty buffer, two good alerts gone.

    Catching it at enqueue costs one comparison and contains the damage to
    the one alert that is actually wrong.
    """

    def __init__(
        self,
        publisher: BackendPublisher,
        *,
        agent_id: str,
        application: str,
        counters: CounterRegistry | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._publisher = publisher
        self._agent_id = agent_id
        self._application = application
        self._counters = counters or CounterRegistry()
        self._logger = logger or logging.getLogger(__name__)
        self._logged_identity_mismatch = False

    @property
    def counters(self) -> CounterRegistry:
        """Self-observability, same shape as `BackendPublisher.counters` and
        `CallbackDispatcher.counters` so one sampler can read any of them."""
        return self._counters

    def route(
        self, alerts: Sequence[AlertEvent], *, now: datetime | None = None
    ) -> int:
        """Enqueue every alert whose identity matches the batch's. Returns
        how many were enqueued.

        Non-blocking and never raises: `enqueue_alert` is a synchronous deque
        append (`FR-PUB-007`), so routing can never stall rule evaluation,
        and a rejected alert is counted rather than thrown — the Rule Engine
        has already done its job by the time we are called, and failing here
        would lose the alert from the callback path too.
        """
        routed = 0
        for alert in alerts:
            if not self._identity_matches(alert):
                self._reject(alert)
                continue
            self._publisher.enqueue_alert(alert, now=now)
            routed += 1
        if routed:
            self._counters.increment("alerts_routed", routed)
        return routed

    def _identity_matches(self, alert: AlertEvent) -> bool:
        return (
            alert.agent_id == self._agent_id
            and alert.application == self._application
        )

    def _reject(self, alert: AlertEvent) -> None:
        self._counters.increment("alerts_rejected_identity")
        if self._logged_identity_mismatch:
            # Once per process, like `publisher._logged_schema_error`: a
            # misconfigured agent produces this for every alert it ever
            # raises, and the log line is identical each time.
            return
        self._logged_identity_mismatch = True
        self._logger.error(
            "dropping alert %s (rule %s): identity %s/%s does not match the "
            "publisher's %s/%s, and TelemetryBatch would reject the whole "
            "batch at send time",
            alert.alert_id,
            alert.rule_name,
            alert.agent_id,
            alert.application,
            self._agent_id,
            self._application,
        )
