"""UBS-117: bounded, sanitised observations using the existing batch publisher.

One emitter per instance. Call under the ingestor lock: both the pipeline
thread and periodic evaluator contribute. No I/O or alert decisions live here.
"""

from __future__ import annotations

import time
from collections import OrderedDict, deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid7

from telemetry_shared.events import allowed_event_fields
from telemetry_shared.metrics.dimensions import ALLOWED_DIMENSION_KEYS
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import TelemetryEvent

from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_agent.parser.fix.session_tracker import SessionTimeout
from telemetry_agent.parser.fix.telemetry import session_id_for
from telemetry_agent.parser.metrics_event import parser_counter_dims
from telemetry_agent.parser.protocol import ParseResult, SourceMeta
from telemetry_agent.publishing.publisher import BackendPublisher

PARSE_REASONS = frozenset(
    {
        "no_begin_string",
        "no_msg_type",
        "malformed_field",
        "incomplete_message",
        "unknown_msg_type",
        "bad_timestamp",
        "checksum_mismatch",
        "line_truncated",
        "internal_error",
    }
)

# Observation severity preserves the log level; alert severity belongs to rules.
APP_EVENT_SEVERITY = {
    "N": "info",
    "I": "info",
    "W": "warning",
    "E": "warning",
    "F": "critical",
}


class EventEmitter:
    def __init__(
        self,
        publisher: BackendPublisher,
        *,
        agent_id: str,
        application: str,
        instance_id: str,
        max_events_per_minute: int = 600,
        execution_sample_every: int = 100,
        bucket_seconds: int = 10,
        monotonic: Callable[[], float] = time.monotonic,
        on_drop: Callable[[], None] | None = None,
    ) -> None:
        if min(max_events_per_minute, execution_sample_every, bucket_seconds) < 1:
            raise ValueError("event limits must be positive")
        self.publisher = publisher
        self.agent_id = agent_id
        self.application = application
        self.instance_id = instance_id
        self.limit = max_events_per_minute
        self.sample_every = execution_sample_every
        self.bucket_seconds = bucket_seconds
        self.monotonic = monotonic
        self.on_drop = on_drop
        self.counters = CounterRegistry()
        self._rates: dict[str, deque[float]] = {}
        self._executions = 0
        self._bucket: int | None = None
        self._counts: dict[tuple[str, str], int] = {}
        self._alert_states: OrderedDict[str, tuple[str, str]] = OrderedDict()

    def log_lifecycle(self, event_type: str, source_index: int) -> None:
        if event_type not in {"log.rotated", "log.truncated", "log.stalled"}:
            return
        self.emit(
            event_type,
            at=datetime.now(UTC),
            severity="warning" if event_type == "log.stalled" else "info",
            fields={"sourceIndex": source_index},
        )

    def state_reset(self, reason: str) -> None:
        if reason in {"missing", "corrupt", "unreadable"}:
            self.emit(
                "agent.state_reset",
                at=datetime.now(UTC),
                severity="warning",
                fields={"reason": reason},
            )

    def callback_failed(
        self, alert: AlertEvent, reason: str, attempts: int, status: int | None
    ) -> None:
        if (
            alert.agent_id != self.agent_id
            or alert.application != self.application
            or alert.instance_id != self.instance_id
            or reason
            not in {"payload_too_large", "permanent_http_failure", "retries_exhausted"}
        ):
            return
        fields: dict[str, Any] = {
            "alertId": alert.alert_id,
            "reason": reason,
            "attempts": attempts,
        }
        if status is not None:
            fields["httpStatus"] = status
        self.emit(
            "callback.failed", at=datetime.now(UTC), severity="warning", fields=fields
        )

    def emit(
        self,
        event_type: str,
        *,
        at: datetime,
        severity: str = "info",
        time_source: str = "agent",
        dimensions: dict[str, str] | None = None,
        fields: dict[str, Any] | None = None,
    ) -> bool:
        """Failure/drop never interrupts metrics, rules or callback delivery."""
        try:
            dims, values = dimensions or {}, fields or {}
            if set(dims) - ALLOWED_DIMENSION_KEYS or set(values) - allowed_event_fields(
                event_type
            ):
                raise ValueError("non-allowlisted event field")
            now = self.monotonic()
            recent = self._rates.setdefault(event_type, deque())
            while recent and recent[0] <= now - 60:
                recent.popleft()
            if len(recent) >= self.limit:
                self.counters.increment("events_rate_limited")
                if self.on_drop is not None:
                    self.on_drop()
                return False
            recent.append(now)
            self.publisher.enqueue_event(
                TelemetryEvent(
                    schema_version=1,
                    event_id=uuid7(),
                    agent_id=self.agent_id,
                    application=self.application,
                    instance_id=self.instance_id,
                    event_type=event_type,
                    timestamp_utc=at,
                    time_source=time_source,
                    severity=severity,
                    dimensions=dict(dims),
                    fields=dict(values),
                )
            )
            self.counters.increment("events_enqueued")
            return True
        except Exception:
            # Exception text can contain source values; count without logging it.
            self.counters.increment("event_emit_errors")
            return False

    def observe(self, result: ParseResult, meta: SourceMeta) -> None:
        if meta.instance_id != self.instance_id:
            self.counters.increment("events_rejected_identity")
            return
        self.flush(meta.read_at)
        reason = parser_counter_dims(result, instance_id=meta.instance_id)["reason"]
        if reason != "none":
            self._count(
                "parse.error", reason if reason in PARSE_REASONS else "internal_error"
            )
        app = result.app_log_telemetry
        if app is not None:
            if app.level in {"E", "F"}:
                self._count("app.error", app.level)
            if app.error_signature:
                self.emit(
                    "app.error_signature",
                    at=meta.read_at,
                    time_source="agent",
                    severity=APP_EVENT_SEVERITY.get(app.level, "info"),
                    dimensions={
                        "level": app.level,
                        "errorSignature": app.error_signature,
                    },
                )
        tel, fix = result.telemetry, result.fields
        if tel is None or fix is None or not result.framed or result.internal_error:
            return
        dims = {"session": session_id_for(fix.sender_comp_id, fix.target_comp_id)}
        at = tel.event_time_utc or meta.read_at
        fields: dict[str, Any] = {"msgType": tel.normalized_msg_type or "unspecified"}
        if fix.seq_num is not None and fix.seq_num.isascii() and fix.seq_num.isdigit():
            fields["seqNum"] = int(fix.seq_num)
        msg = tel.normalized_msg_type
        if msg in {"Logon", "Logout"}:
            self.emit(
                "fix.session_state",
                at=at,
                time_source=tel.time_source,
                dimensions=dims,
                fields=fields | {"state": msg.lower()},
            )
        if tel.seq_gap is not None:
            gap = tel.seq_gap
            self.emit(
                "fix.seq_gap",
                at=at,
                severity="warning",
                time_source=tel.time_source,
                dimensions=dims,
                fields=fields
                | {
                    "expectedSeqNum": gap.expected,
                    "gapSize": gap.gap_size,
                    "isRegression": gap.is_regression,
                },
            )
        event_type: str | None = None
        if msg == "Reject":
            event_type = "fix.session_reject"
            dims["sessionRejectReason"] = (
                tel.normalized_session_reject_reason or "unspecified"
            )
        elif msg == "OrderCancelReject" or (
            msg == "ExecutionReport"
            and (
                tel.normalized_exec_type == "Rejected"
                or tel.normalized_ord_status == "Rejected"
            )
        ):
            event_type = "fix.order_reject"
            dims["rejectReason"] = tel.effective_reject_reason or "unspecified"
        elif msg == "ExecutionReport" and tel.normalized_exec_type == "Trade":
            self._executions = (self._executions + 1) % self.sample_every
            if self._executions == 0:
                event_type = "fix.execution"
                fields["sampleEvery"] = self.sample_every
            else:
                self.counters.increment("executions_sampled_out")
        if event_type is not None:
            # Select explicitly; never serialise FixFields/AppLogTelemetry wholesale.
            for key, value in (
                ("clOrdIdHash", fix.cl_ord_id_hash),
                ("origClOrdIdHash", fix.orig_cl_ord_id_hash),
                ("orderIdHash", fix.order_id_hash),
                ("execIdHash", fix.exec_id_hash),
                ("execType", tel.normalized_exec_type),
                ("ordStatus", tel.normalized_ord_status),
            ):
                if value is not None:
                    fields[key] = value
            self.emit(
                event_type,
                at=at,
                time_source=tel.time_source,
                dimensions=dims,
                fields=fields,
                severity="info" if event_type == "fix.execution" else "warning",
            )

    def _count(self, event_type: str, label: str) -> None:
        key = (event_type, label)
        self._counts[key] = self._counts.get(key, 0) + 1

    def flush(self, now: datetime, *, force: bool = False) -> None:
        bucket = int(now.timestamp()) // self.bucket_seconds * self.bucket_seconds
        if self._bucket is not None and (bucket > self._bucket or force):
            for (kind, label), count in self._counts.items():
                self.emit(
                    kind,
                    at=datetime.fromtimestamp(self._bucket, UTC),
                    severity="critical" if label == "F" else "warning",
                    time_source="agent",
                    dimensions={"level" if kind == "app.error" else "reason": label},
                    fields={"count": count, "bucketSeconds": self.bucket_seconds},
                )
            self._counts.clear()
        if self._bucket is None or bucket > self._bucket:
            self._bucket = bucket

    def session_timeout(self, timeout: SessionTimeout, now: datetime) -> None:
        self.emit(
            "fix.session_state",
            at=now,
            severity="critical",
            dimensions={"session": timeout.session_id},
            fields={
                "state": "heartbeat_timeout",
                "silentSeconds": timeout.silent_seconds,
            },
        )

    def alert(self, alert: AlertEvent) -> None:
        if (alert.agent_id, alert.application, alert.instance_id) != (
            self.agent_id,
            self.application,
            self.instance_id,
        ):
            self.counters.increment("events_rejected_identity")
            return
        if alert.status not in {"firing", "resolved"}:
            return
        state = (alert.status, alert.severity)
        if self._alert_states.get(alert.alert_id) == state:
            return  # cooldown re-notification is not a new transition
        if self.emit(
            "alert.resolved" if alert.status == "resolved" else "alert.fired",
            at=alert.resolved_at_utc or alert.last_observed_utc,
            severity=alert.severity,
            fields={
                "alertId": alert.alert_id,
                "ruleName": alert.rule_name,
                "status": alert.status,
            },
        ):
            self._alert_states[alert.alert_id] = state
            self._alert_states.move_to_end(alert.alert_id)
            if len(self._alert_states) > 4096:
                self._alert_states.popitem(last=False)
