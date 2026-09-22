"""Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).

UBS-66 landed `telemetry_shared.models.ingestion.Heartbeat` in parallel with
our `models.health.AgentHeartbeat`: both implement spec 004 §6, but his makes
every signal field required and non-negative, while ours leaves a signal
`null` when nothing produces it (FR-HLT-004: a gap must never be reported as
a zero).

**Decision (2026-09-22): the agent adapts.** Downstream consumers are waiting
on a working `POST /telemetry/heartbeat`, and only one of the two shapes can
be on the wire. `AgentHeartbeat` stays the agent's internal truth - the
reporter keeps its `None`s, so no status rule ever fires on a fabricated zero
- and this module flattens it to the ingestion shape at the last moment,
inside the sink.

**What that costs, and how to reverse it** - see docs/plan/ubs58-60-notes.md
("Wire compatibility with UBS-66"):

1. `statusReasons` (FR-HLT-003) has no field in the ingestion model, which is
   `extra="forbid"`, so the operator-facing reasons are dropped on the wire.
   The status itself survives.
2. Unmeasured signals are sent as `0`, which the backend cannot distinguish
   from a measured zero.
3. `resourceUsage` is required there and unmeasured here, so it is sent as
   zeros rather than omitted.

Reversing is a one-line change once the team settles the contract: make the
optional fields `| None = None` in `ingestion.Heartbeat` and pass
`wire="health"` to `HttpHeartbeatSink` (or delete this module and send
`AgentHeartbeat` directly).
"""

from __future__ import annotations

from telemetry_shared.models.health import AgentHeartbeat
from telemetry_shared.models.ingestion import Heartbeat, HeartbeatFile, ResourceUsage

# Signals the ingestion contract requires but the agent may not measure yet.
# Sent as 0; see the module docstring for what that loses.
_UNMEASURED = 0


def to_ingestion_heartbeat(
    heartbeat: AgentHeartbeat, *, default_instance_id: str | None = None
) -> Heartbeat:
    """Flatten our heartbeat into UBS-66's ingestion contract.

    `default_instance_id` fills `files[].instanceId`, which is required there
    and unknown per-file here (the Log Monitor has no file -> instance map);
    it defaults to the agent's first configured instance.
    """
    instance_ids = list(heartbeat.instance_ids)
    fallback_instance = default_instance_id or (
        instance_ids[0] if instance_ids else heartbeat.agent_id
    )

    files = [
        HeartbeatFile(
            path=file.path,
            instance_id=file.instance_id or fallback_instance,
            offset=file.offset,
            read_lag_ms=file.read_lag_ms,
            last_line_at_utc=file.last_line_at_utc,
            rotations_detected=file.rotations_detected,
            state=file.state,
        )
        for file in heartbeat.files
    ]

    usage = heartbeat.resource_usage
    resource_usage = ResourceUsage(
        rss_mb=usage.rss_mb if usage and usage.rss_mb is not None else 0.0,
        cpu_percent=usage.cpu_percent
        if usage and usage.cpu_percent is not None
        else 0.0,
        active_tasks=usage.active_tasks
        if usage and usage.active_tasks is not None
        else 0,
    )

    return Heartbeat(
        schema_version=1,
        agent_id=heartbeat.agent_id,
        instance_ids=instance_ids,
        sent_at_utc=heartbeat.sent_at_utc,
        agent_version=heartbeat.agent_version,
        # int there, float here: truncate rather than round so uptime never
        # reports a second the agent has not actually been up.
        uptime_seconds=int(heartbeat.uptime_seconds),
        status=heartbeat.status,
        files=files,
        parse_error_count_last5_min=(
            heartbeat.parse_error_count_last5_min
            if heartbeat.parse_error_count_last5_min is not None
            else _UNMEASURED
        ),
        callback_failures_last5_min=(
            heartbeat.callback_failures_last5_min
            if heartbeat.callback_failures_last5_min is not None
            else _UNMEASURED
        ),
        publish_queue_depth=(
            heartbeat.publish_queue_depth
            if heartbeat.publish_queue_depth is not None
            else _UNMEASURED
        ),
        publish_buffer_bytes=(
            heartbeat.publish_buffer_bytes
            if heartbeat.publish_buffer_bytes is not None
            else _UNMEASURED
        ),
        dropped_events_last5_min=(
            heartbeat.dropped_events_last5_min
            if heartbeat.dropped_events_last5_min is not None
            else _UNMEASURED
        ),
        active_alert_count=(
            heartbeat.active_alert_count
            if heartbeat.active_alert_count is not None
            else _UNMEASURED
        ),
        resource_usage=resource_usage,
    )
