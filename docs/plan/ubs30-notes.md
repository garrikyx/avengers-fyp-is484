# UBS-30 implementation notes

Working notes for the `UBS-30-Ingestion-Health-Read-Lag-Metrics` branch. Code comments
point back here instead of repeating this reasoning inline — this doc is where the
"why", the code is where the "what".

## Ticket vs. spec conflict (read first)

UBS-30's Jira description says `log_read_lag_bytes` (a byte count: `st_size - offset`).
The repo's own spec docs disagree and are internally consistent with each other:
`docs/specs/002-agent.md` (`FR-LOG-010`), `docs/specs/004-telemetry-data-model.md`
(`gauges.read_lag_ms`), and `docs/specs/011-observability-and-runbooks.md`
(">5s sustained = degraded") all define read lag as **time since the last line was
read**, not bytes unread. Decision: built to the spec docs (`log_read_lag_ms`). The
Jira ticket text still says bytes and should be updated to match — not done yet.

## `apps/agent/src/telemetry_agent/logs/log_monitor.py`

This is Mitch's file (UBS-22/23/24); UBS-30 only adds to it because the read
timestamp it needs doesn't exist anywhere else.

- **`Harvester.last_read_at`**: stamped every time a line is actually read. Starts
  as `None`, not `0`/epoch, so a file that's never produced a line is distinguishable
  from one that's genuinely fresh. This matters because of `FR-HLT-004`: a data gap
  must never be presented as a zero — a lag of "0ms" would misreport an unread file
  as perfectly healthy.
- **`FileReadStatus`**: the plain-data snapshot spec 011's health signals table asks
  for (`files[].offset`, plus lag). One dataclass per file, per call.
- **`LogMonitor.get_status(now=None)`**: computes `read_lag_ms = now - last_read_at`.
  Takes `now` as a parameter (default real clock) specifically so tests can control
  time without sleeping. Offset comes from the live harvester if one exists,
  otherwise falls back to the `OffsetTracker`'s last saved value.

## `apps/agent/src/telemetry_agent/health/reporter.py`

New module — this is what the ticket calls "the internal health reporter module,"
which didn't exist before.

- **Scope boundary**: spec 011's `FR-HLT-002` derives a single
  `healthy`/`degraded`/`unhealthy` rollup from read lag *and* parse error rate *and*
  publish buffer *and* RSS. Only read lag exists yet (M1) — Parser Engine (M2) and
  Metrics/Publisher (M3/M4) don't. `degraded_reasons()` is only the read-lag slice
  of that rollup; whoever builds M2+ should fold their signals in rather than
  replace this.
- **`monitors: dict[str, LogMonitor]`**: keyed by name purely for legible output
  (`"Fix.log: read lag ..."`). The reporter never touches file content or identity
  itself, only whatever each `LogMonitor.get_status()` returns.
- **`overall_read_lag_ms()`**: worst-case (max) lag across files that have actually
  produced a line. Files with no reads yet are excluded from the max — again per
  `FR-HLT-004` — rather than either dragging the max down or getting silently
  counted as caught up. If every file is unread, this returns `None`.
- **`degraded_reasons()` / `is_degraded()`**: flags files whose lag crosses
  `degraded_threshold_ms` (default 5000, spec 011's ">5s sustained" line). An unread
  file is never flagged degraded — it has no signal yet either way.

## `packages/telemetry_shared/src/telemetry_shared/models/health.py`

Shared wire-format models (was a broken empty stub before UBS-30 — no prior owner).

- **`FileReadHealth`**: transport shape for `LogMonitor.get_status()`, same
  None-not-zero rule on `read_lag_ms`.
- **`AgentHeartbeat.files` / `.read_lag_ms`**: added, both optional/defaulted so
  nothing that already used this model breaks. Matches the heartbeat shape spec 011
  describes (`files[].offset`). Parse-error and callback-failure fields aren't added
  yet since nothing produces those signals (M2/M5).

## Also touched, and why (not UBS-30-owned content)

- `apps/agent/pyproject.toml`: `packages = ["src/agent"]` pointed at a directory
  that doesn't exist; real package is `src/telemetry_agent`. Blocked importing the
  package at all - Mitch's code too, not just this ticket's.
- `.gitignore`: bare `logs/` matched any directory named "logs" anywhere, which
  silently blocked adding `tests/unit/agent/logs/`. Anchored to `/logs/` and
  `/demo_logs/` instead of removing it.
- Everything else broken in the repo (the other `telemetry_shared` models, etc.) was
  left alone deliberately - not this ticket's files to fix.

## Known gaps / follow-ups

- `apps/agent/src/telemetry_agent/logs/multi_log_monitor.py` is a local, uncommitted
  stopgap (round-robin, not real concurrent tailing) so `demo_suite.py` /
  `run_streamer.py` can run while Mitch's real UBS-22 multi-file class is missing
  from every branch. Delete/replace once he pushes the real one.
- `scripts/ubs30_integration_demo.py`: live demo wiring `LogMonitor` +
  `OffsetTracker` (Mitch's) through `HealthReporter` (ours). Automated coverage for
  the same wiring is `tests/unit/agent/health/test_reporter.py`.
- Mitch's `demo_suite.py` Scenario 2 (rotation) throws `FileNotFoundError` on this
  machine's setup - suspected open-handle-during-rename quirk specific to testing
  against a remote-mounted drive, unconfirmed, not chased down further.
