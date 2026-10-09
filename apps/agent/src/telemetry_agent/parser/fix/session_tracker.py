"""UBS-106: per-session heartbeat-timeout detection.

A heartbeat timeout is the *absence* of a message, so no per-message
derivation can observe it — which is why `heartbeat_timeouts` (spec 004
§4.2) had no producer while every other session counter did. It needs two
things a single parse call cannot provide: a memory of when each session was
last heard from, and a periodic tick to notice the silence has run too long.

This holds the memory; the caller provides the tick. In the agent,
`MetricsIngestor` (UBS-112) calls `observe` for every ingested line, and
`RuleEvaluator` (UBS-113) calls `timed_out` on each evaluation tick.

Deliberately mirrors `seq_tracker.SeqTracker`: same `@dataclass(slots=True)`
shape, same per-session dict, same caller-driven style.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from telemetry_agent.parser.fix.telemetry import session_id_for

# Mirrors the backend's own AgentRegistry.missing_threshold_seconds
# (FR-RUL-030's `missingHeartbeatThreshold`), so the agent and the backend
# agree on what "missing heartbeat" means rather than each picking a number.
# Spec 004 §4.2 names heartbeat_timeouts but never defines the interval, so
# this is a documented default, not a UBS-supplied threshold — override it
# from `health.sessionHeartbeatTimeout`.
DEFAULT_SESSION_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True, slots=True)
class SessionTimeout:
    """One session that has just gone quiet for too long.

    Carries both identifiers on purpose. `session_key` is the internal,
    direction-aware tracking key; `session_id` is the `FR-MET-030`
    dimension label the aggregator groups by, and is the one that must match
    what `logouts`/`seq_gaps`/`clock_skew_events` already emit.
    """

    session_key: str
    session_id: str
    silent_seconds: float


@dataclass(slots=True)
class _SessionState:
    last_seen: float
    session_id: str


@dataclass(slots=True)
class SessionHeartbeatTracker:
    """Flags FIX sessions quiet for longer than `timeout_seconds`.

    Stateful across calls, one instance per agent (not per session) — it
    holds every session it has seen. Times are plain floats supplied by the
    caller (`at`/`now`), never read from a clock here, so tests and demos
    drive it deterministically the way `MetricsAggregator` and
    `BackendPublisher` already are.
    """

    timeout_seconds: float = DEFAULT_SESSION_TIMEOUT_SECONDS
    _sessions: dict[str, _SessionState] = field(default_factory=dict)
    # Sessions already reported. This is the latch: without it a 10s tick
    # against a 60s threshold would re-report the same silent session every
    # tick, posting ~30 heartbeat_timeouts for one five-minute outage into a
    # counter `FixSessionDown` reads at `>= 1` critical.
    _timed_out: set[str] = field(default_factory=set)

    def session_key(
        self,
        sender: str | None,
        target: str | None,
        *,
        direction: str = "out",
    ) -> str:
        """Internal tracking key, identical in format to
        `SeqTracker.session_key`.

        Direction-aware because inbound and outbound are separate heartbeat
        streams: a venue can stop sending while we keep sending fine, and
        that is the failure worth catching. This is *not* the dimension
        label — see `session_id_for` in `fix.telemetry`.
        """
        return f"{sender or '?'}->{target or '?'}:{direction}"

    def observe(
        self,
        *,
        msg_type: str | None,
        sender: str | None,
        target: str | None,
        direction: str = "out",
        at: float,
    ) -> None:
        """Record that a session was heard from at `at`.

        Any message counts, not just `35=0` Heartbeat: a session carrying
        orders is demonstrably alive whether or not a heartbeat is due, and
        FIX only requires a Heartbeat when the session is otherwise idle.
        Counting heartbeats alone would flag the busiest sessions as dead.

        `Logout` is the exception — it ends the session, so it is forgotten
        rather than refreshed. See `forget`.
        """
        key = self.session_key(sender, target, direction=direction)

        if msg_type in ("Logout", "5"):
            self.forget(key)
            return

        self._sessions[key] = _SessionState(
            last_seen=at, session_id=session_id_for(sender, target)
        )
        # Re-arm: a session that was timed out and has now spoken can time
        # out again later, and that later silence is a new incident.
        self._timed_out.discard(key)

    def timed_out(self, now: float) -> tuple[SessionTimeout, ...]:
        """Sessions that have *just* crossed the threshold, each latched so
        one silence is reported exactly once.

        Sorted by session key so a caller ingesting the result produces
        deterministic output.
        """
        newly: list[SessionTimeout] = []
        for key, state in self._sessions.items():
            if key in self._timed_out:
                continue
            silent = now - state.last_seen
            if silent > self.timeout_seconds:
                self._timed_out.add(key)
                newly.append(
                    SessionTimeout(
                        session_key=key,
                        session_id=state.session_id,
                        silent_seconds=silent,
                    )
                )
        return tuple(sorted(newly, key=lambda t: t.session_key))

    def forget(self, session_key: str) -> None:
        """Stop tracking a session.

        Called on `Logout`, and the reason this exists: a cleanly logged-out
        session is silent forever, so without forgetting it, it would trip a
        timeout one interval after every logout and double-count against
        `logouts` inside the very same `FixSessionDown` rule — turning one
        orderly shutdown into two critical signals.
        """
        self._sessions.pop(session_key, None)
        self._timed_out.discard(session_key)

    def is_timed_out(self, session_key: str) -> bool:
        """Introspection for demos/debug; not used by the detection path."""
        return session_key in self._timed_out

    def tracked_sessions(self) -> tuple[str, ...]:
        return tuple(sorted(self._sessions))
