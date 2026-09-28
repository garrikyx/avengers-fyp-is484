"""In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`)."""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.alerts_query import (
    AlertCounts,
    AlertDelivery,
    AlertDetailResponse,
    AlertRecord,
    AlertsListResponse,
    AlertTransition,
)

from telemetry_backend.config import AlertStoreConfig

_ACTIVE_STATUSES = frozenset({"pending", "firing", "resolving"})
_RESOLVED_STATUS = "resolved"
_DEFAULT_DELIVERY = AlertDelivery(status="unknown", attempts=0)


def _is_active_status(status: str) -> bool:
    return status in _ACTIVE_STATUSES


@dataclass(slots=True)
class _StoredAlert:
    record: AlertRecord
    transitions: deque[AlertTransition] = field(default_factory=deque)
    synthetic: bool = False


@dataclass(slots=True)
class _InstanceAlerts:
    active: dict[str, _StoredAlert] = field(default_factory=dict)
    resolved: deque[str] = field(default_factory=deque)
    resolved_map: dict[str, _StoredAlert] = field(default_factory=dict)


class AlertStore:
    """Per-instance active alerts and a bounded resolved history."""

    def __init__(self, config: AlertStoreConfig | None = None) -> None:
        self._config = config or AlertStoreConfig()
        self._instances: dict[str, _InstanceAlerts] = {}
        self._instance_locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _get_instance(self, instance_id: str) -> tuple[_InstanceAlerts, threading.Lock]:
        with self._locks_guard:
            if instance_id not in self._instances:
                self._instances[instance_id] = _InstanceAlerts()
                self._instance_locks[instance_id] = threading.Lock()
            return self._instances[instance_id], self._instance_locks[instance_id]

    @staticmethod
    def _transition_from_event(event: AlertEvent) -> AlertTransition:
        return AlertTransition(
            status=event.status,
            severity=event.severity,
            observed_value=event.observed_value,
            threshold=event.threshold,
            timestamp_utc=event.last_observed_utc,
            notification_count=event.notification_count,
            matched_condition=event.matched_condition,
        )

    @staticmethod
    def _record_from_event(
        event: AlertEvent,
        *,
        source: Literal["agent", "backend"],
        synthetic: bool,
        delivery: AlertDelivery | None = None,
    ) -> AlertRecord:
        return AlertRecord(
            alert_id=event.alert_id,
            source=source,
            synthetic=synthetic,
            agent_id=event.agent_id,
            application=event.application,
            instance_id=event.instance_id,
            rule_name=event.rule_name,
            severity=event.severity,
            status=event.status,
            matched_condition=event.matched_condition,
            observed_value=event.observed_value,
            threshold=event.threshold,
            first_observed_utc=event.first_observed_utc,
            last_observed_utc=event.last_observed_utc,
            resolved_at_utc=event.resolved_at_utc,
            notification_count=event.notification_count,
            delivery=delivery or _DEFAULT_DELIVERY,
            group_by=dict(event.group_by),
            metric_context=dict(event.metric_context),
            runbook_url=None,
        )

    def _append_transition(self, stored: _StoredAlert, event: AlertEvent) -> None:
        stored.transitions.append(self._transition_from_event(event))
        while len(stored.transitions) > self._config.max_transitions:
            stored.transitions.popleft()

    def _evict_resolved_if_needed(self, instance: _InstanceAlerts) -> None:
        while len(instance.resolved) > self._config.recent_alert_limit:
            oldest_id = instance.resolved.popleft()
            instance.resolved_map.pop(oldest_id, None)

    def _place_alert(
        self,
        instance: _InstanceAlerts,
        stored: _StoredAlert,
        *,
        active: bool,
    ) -> None:
        alert_id = stored.record.alert_id
        instance.active.pop(alert_id, None)
        if alert_id in instance.resolved_map:
            instance.resolved_map.pop(alert_id, None)
            try:
                instance.resolved.remove(alert_id)
            except ValueError:
                pass

        if active:
            instance.active[alert_id] = stored
        else:
            instance.resolved.append(alert_id)
            instance.resolved_map[alert_id] = stored
            self._evict_resolved_if_needed(instance)

    def merge(
        self,
        event: AlertEvent,
        *,
        source: Literal["agent", "backend"] = "agent",
        now: datetime | None = None,
    ) -> None:
        """Merge one alert update (`FR-QRY-016`, `FR-QRY-017`)."""
        _ = now
        instance, lock = self._get_instance(event.instance_id)
        with lock:
            existing = instance.active.get(event.alert_id)
            if existing is None:
                existing = instance.resolved_map.get(event.alert_id)

            if existing is None and event.status == _RESOLVED_STATUS:
                stored = _StoredAlert(
                    record=self._record_from_event(
                        event, source=source, synthetic=True
                    ),
                    synthetic=True,
                )
                self._append_transition(stored, event)
                self._place_alert(instance, stored, active=False)
                return

            if existing is None:
                stored = _StoredAlert(
                    record=self._record_from_event(
                        event, source=source, synthetic=False
                    ),
                    synthetic=False,
                )
                self._append_transition(stored, event)
                self._place_alert(
                    instance, stored, active=_is_active_status(event.status)
                )
                return

            synthetic = existing.synthetic
            stored = _StoredAlert(
                record=self._record_from_event(
                    event,
                    source=source,
                    synthetic=synthetic,
                    delivery=existing.record.delivery,
                ),
                transitions=existing.transitions,
                synthetic=synthetic,
            )
            self._append_transition(stored, event)
            self._place_alert(
                instance, stored, active=_is_active_status(event.status)
            )

    def _iter_all_records(
        self, *, include_active: bool, include_resolved: bool
    ) -> Iterable[AlertRecord]:
        for instance_id in list(self._instances):
            instance, lock = self._get_instance(instance_id)
            with lock:
                if include_active:
                    yield from (s.record for s in instance.active.values())
                if include_resolved:
                    for alert_id in instance.resolved:
                        stored = instance.resolved_map.get(alert_id)
                        if stored is not None:
                            yield stored.record

    def _matches_filters(
        self,
        record: AlertRecord,
        *,
        application: str | None,
        instance_id: str | None,
        rule_name: str | None,
        severity: str | None,
        since: datetime | None,
    ) -> bool:
        if application is not None and record.application != application:
            return False
        if instance_id is not None and record.instance_id != instance_id:
            return False
        if rule_name is not None and record.rule_name != rule_name:
            return False
        if severity is not None and record.severity != severity:
            return False
        if since is not None and record.last_observed_utc < since:
            return False
        return True

    @staticmethod
    def _is_query_active(record: AlertRecord) -> bool:
        return _is_active_status(record.status)

    def list_alerts(
        self,
        *,
        status: Literal["active", "resolved", "all"] = "active",
        application: str | None = None,
        instance_id: str | None = None,
        rule_name: str | None = None,
        severity: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> AlertsListResponse:
        include_active = status in {"active", "all"}
        include_resolved = status in {"resolved", "all"}
        candidates: list[AlertRecord] = []
        for record in self._iter_all_records(
            include_active=include_active, include_resolved=include_resolved
        ):
            if status == "active" and not self._is_query_active(record):
                continue
            if status == "resolved" and record.status != _RESOLVED_STATUS:
                continue
            if not self._matches_filters(
                record,
                application=application,
                instance_id=instance_id,
                rule_name=rule_name,
                severity=severity,
                since=since,
            ):
                continue
            candidates.append(record)

        candidates.sort(key=lambda r: r.last_observed_utc, reverse=True)
        truncated = len(candidates) > limit
        alerts = candidates[:limit]

        all_active = list(
            self._iter_all_records(include_active=True, include_resolved=False)
        )
        counts = AlertCounts(
            active=sum(1 for r in all_active if self._is_query_active(r)),
            critical=sum(
                1
                for r in all_active
                if self._is_query_active(r) and r.severity == "critical"
            ),
            warning=sum(
                1
                for r in all_active
                if self._is_query_active(r) and r.severity == "warning"
            ),
        )
        return AlertsListResponse(
            alerts=alerts, counts=counts, truncated=truncated
        )

    def get_alert(self, alert_id: str) -> AlertDetailResponse | None:
        for instance_id in list(self._instances):
            instance, lock = self._get_instance(instance_id)
            with lock:
                stored = instance.active.get(alert_id)
                if stored is None:
                    stored = instance.resolved_map.get(alert_id)
                if stored is not None:
                    return AlertDetailResponse(
                        alert=stored.record,
                        transitions=list(stored.transitions),
                    )
        return None
