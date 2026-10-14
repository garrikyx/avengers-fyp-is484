"""UBS-109/110: routes Rule Engine alerts to the Backend Publisher and the
Callback Dispatcher.

`RuleEngine.evaluate()` returns `AlertEvent`s and `BackendPublisher` accepts
them via `enqueue_alert()`, but nothing joined the two — the publisher's own
docstring notes that "nothing in this repo calls them yet". Alerts fired
locally and the backend never learned they existed.

Lives in `pipeline/` because that is this package's composition layer
(`PipelineBridge` assembles `logs/` + `parser/` + queues + `committer`), and
because `rules/` must not import `publishing/`: the Rule Engine deliberately
knows nothing about transports so a backend outage cannot affect alerting
(`NFR-REL-003`).

UBS-110 adds the second consumer: the Callback Dispatcher (UBS-32/33/34),
which notifies Magic directly. The two paths are isolated from each other
(`NFR-REL-003`): each `enqueue` is guarded separately, so a fault in one never
costs the other its alert.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import datetime

from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
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

    The guard applies to the backend path only. A callback carries one alert,
    not a batch, so there is nothing for a mismatch to poison — Magic still
    gets every alert the engine raised.
    """

    def __init__(
        self,
        publisher: BackendPublisher,
        *,
        agent_id: str,
        application: str,
        dispatcher: CallbackDispatcher | None = None,
        counters: CounterRegistry | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._publisher = publisher
        self._dispatcher = dispatcher
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
        """Hand every alert to the Callback Dispatcher (if configured), and
        every alert whose identity matches the batch's to the publisher.
        Returns how many were enqueued for the backend.

        Non-blocking and never raises: both `enqueue`s are synchronous
        appends (`FR-PUB-007`, `FR-CBK-007`), so routing can never stall rule
        evaluation, and a rejected or failed alert is counted rather than
        thrown — the Rule Engine has already done its job by the time we are
        called.
        """
        routed = 0
        dispatched = 0
        for alert in alerts:
            if self._dispatcher is not None and self._guarded(
                "callback", alert, self._dispatcher.enqueue
            ):
                dispatched += 1
            if not self._identity_matches(alert):
                self._reject(alert)
                continue
            if self._guarded(
                "publish",
                alert,
                lambda a: self._publisher.enqueue_alert(a, now=now),
            ):
                routed += 1
        if routed:
            self._counters.increment("alerts_routed", routed)
        if dispatched:
            self._counters.increment("alerts_dispatched", dispatched)
        return routed

    def _guarded(
        self, path: str, alert: AlertEvent, enqueue: Callable[[AlertEvent], None]
    ) -> bool:
        """Run one path's enqueue so its failure stays on that path."""
        try:
            enqueue(alert)
        except Exception:
            self._counters.increment(f"alerts_{path}_enqueue_failed")
            self._logger.exception(
                "failed to enqueue alert %s on the %s path", alert.alert_id, path
            )
            return False
        return True

    def _identity_matches(self, alert: AlertEvent) -> bool:
        return (
            alert.agent_id == self._agent_id and alert.application == self._application
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
