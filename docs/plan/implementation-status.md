# Implementation Status

Status: Live document · Last updated: 2026-09-17

Specs state the target; this document states what exists. Where the two differ, the difference
is recorded here rather than by quietly editing the spec.

## Milestones

| Milestone | Scope | Status |
| --- | --- | --- |
| M0 | Repository foundation, CI gates, shared models | Partial — uv workspace, Makefile, `packages/telemetry_shared/` exist; CI and requirement-coverage reporter do not |
| M1 | Log monitor and configuration | **Not started** — `apps/agent/src/telemetry_agent/logs/` does not exist yet |
| M1.5 | Pipeline bridge (monitor → parser) | **Not started** — `apps/agent/src/telemetry_agent/pipeline/` does not exist yet |
| **M2** | **FIX parser (UBS-40–47)** | **Partial** — classify, frame, allowlist extraction, enums, rejection labels, timestamps, seq gaps, parse-error handling implemented; CLI demo with FIX + Magic corpora; not wired through pipeline |
| **M3** | **Metrics aggregation** | **Partial** — aggregator, counters, correlation, and calculated indicators/snapshot output (MA-01–04) implemented and tested; demo sink in `metrics/demo_sink.py` for parser CLI; blocked on real events by M1 (Log Monitor) and M1.5 (pipeline bridge) |
| **M4** | **Backend ingestion, store, query** | **Partial** — Stream Processor and Metric Store (window alignment, cross-agent merge semantics, per-instance locking, memory estimation/shedding) implemented and tested; `/healthz`/`/readyz` implemented; ingestion (auth/validation/dedupe), the agent's own Backend Publisher, and the query engine/HTTP layer are not started |
| **M5** | **Rules, alerts, callbacks** | **Partial** — Rule Engine and alert lifecycle (RE-01–04) implemented and tested; callback dispatch (HTTP/HMAC) not started |
| M6 | Natural language layer | Not started |
| M7 | Operability hardening | Not started |

## M2 requirement coverage (UBS-40–42)

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| UBS-40 | Parser plugin interface and registry | `FR-PRS-030`–`032`, `FR-PRS-003` | Done | `tests/unit/agent/parser/test_FR_PRS_030_registry.py` |
| UBS-41 | Classify log lines before FIX parsing | `FR-PRS-010`, `FR-PRS-011` | Done | `tests/unit/agent/parser/test_FR_PRS_010_classify.py` |
| UBS-42 | Frame FIX messages from log lines | `FR-PRS-012`–`016` | Done | `tests/unit/agent/parser/test_FR_PRS_012_frame.py`, `apps/agent/testdata/fix/` |
| UBS-43 | Allowlisted field extraction | `FR-PRS-020` | Done | `tests/unit/agent/parser/test_FR_PRS_020_fields.py`, `parser/fix/fields.py` |
| UBS-44 | Identifier hashing | `FR-PRS-021` | Done | `tests/unit/agent/parser/test_FR_PRS_021_identifiers.py`, `parser/fix/identifiers.py` |
| UBS-45 | Enum mapping + tag-58 rejection labels | `FR-PRS-022`–`024` | Done | `test_FR_PRS_022_normalize.py`, `test_FR_PRS_023_enums.py`, `test_FR_PRS_024_rejection.py`, `test_UBS45_integration.py` |
| UBS-46 | FIX timestamps + sequence gaps | `FR-PRS-025`–`027` | Done | `test_FR_PRS_025_timestamps.py`, `test_FR_PRS_027_seq_tracker.py` |
| UBS-47 | Parse errors without stopping agent | `FR-PRS-017`–`019` | Done | `test_FR_PRS_017_019_errors.py` |

### Magic applog demo (not UBS-45–47)

| Area | Status | Notes |
| --- | --- | --- |
| Magic line classification | Done | `test_FR_PRS_010_magic_venue_lines.py`, config in `apps/agent/testdata/magic/demo_config.yaml` |
| `%` template error signatures | Done | `parser/applog/signatures.py`, `test_applog_signature_templates.py` |
| Full AppLogParser plugin | Not started | Demo uses FixParser classification + CLI signature matcher |

### Remaining M2 gaps

| Area | Requirements | Notes |
| --- | --- | --- |
| Leak sentinel | `FR-TST-005` | Lands with full corpus gate |
| Parser → MA-01 event bridge | spec 004 | ParsedMessageEvent construction from FixTelemetry not wired |

## Planned: pipeline bridge (M1.5)

Spec: [002-agent.md §1.1](../specs/002-agent.md), ADR [0006](../adr/0006-agent-in-python.md).

| ID | Requirement | Status |
| --- | --- | --- |
| `FR-PIP-001` | Non-blocking monitor enqueue; drop-oldest on full line queue | Not started |
| `FR-PIP-002` | Asymmetric queue sizing (line queue 2048 > event queue 256) | Not started |
| `FR-PIP-003` | Parser worker pool (`min(2, cpu_count)`) | Not started |
| `FR-PIP-004` | Bounded event queue to aggregator | Not started |
| `FR-PIP-005` | Queue depth + drop counters on heartbeat/metrics | Not started |

Target modules: `apps/agent/src/telemetry_agent/pipeline/line_queue.py`, `workers.py`,
`supervisor.py`.

## M3 requirement coverage (MA-01–04)

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| MA-01 | Bucketed counter/histogram store | `FR-MET-024`–`030` | Done | `test_MA_01_aggregator.py` |
| MA-02 | Order/execution/reject counters | spec 004 §4.1 | Done | `test_MA_02_counters.py` |
| MA-03 | Order correlation and latency | spec 004 §4.4 | Done | `test_MA_03_correlation.py`, `test_histogram.py` |
| MA-04 | Calculated indicators and snapshot output | `FR-QRY-007`, `FR-QRY-010`, `FR-QRY-012` | Done | `test_MA_04_snapshot.py` |

Full detail and an alert-readiness mapping: `docs/plan/ma-epic-implementation-summary.md`.
Not yet wired: real events into MA-01–04 depend on M1 (Log Monitor) and M1.5 (pipeline
bridge) — field extraction itself is done (UBS-43–47); `parseErrorRate` is
formula-ready but has no producer yet.

## M4 requirement coverage (Stream Processor & Metric Store)

Renumbered since this table was first written: the original single ticket for this
work (UBS-79/UBS-88 in earlier drafts) split into UBS-89 (cross-agent merge
correctness — the rows below) and UBS-90 (store memory & concurrency — its own
table beneath). UBS-93 (Alert Store) is a separate, later epic.

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| UBS-89 | Window alignment, staleness, and agent reconciliation | `FR-STM-001`, `FR-ING-005`, `FR-STM-005`, `FR-STM-006` | Done | `test_STM_01_window_alignment.py`, `test_STM_03_warmup.py` |
| UBS-89 | Cross-agent merge semantics (counters/ratios/histograms) | `FR-STM-002`–`004` | Done | `test_STM_02_merge_semantics.py` |
| UBS-89 | Per-bucket series cardinality cap (cross-agent) | `FR-MET-030`-equivalent, `NFR-REL-009` | Done | `test_STM_02_merge_semantics.py::test_series_over_the_cardinality_cap_are_dropped_and_counted` |

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| UBS-90 | Per-instance ring buffer, bounded memory | `FR-QRY-001`, `FR-QRY-002` | Partial | Ring buffer + `FR-QRY-002` bounding done; `FR-QRY-001`'s pre-rolled 1m/5m rollups deferred — see note below |
| UBS-90 | Memory estimation, warn/shed thresholds | `FR-QRY-003`, `NFR-SCA-006` | Done | `test_QRY_03_memory.py` |
| UBS-90 | Per-instance lock, not one global lock | `FR-QRY-004` | Done | `test_QRY_04_concurrency.py` |
| UBS-90 | `/readyz` warming state | `FR-QRY-005` | Done | `test_health_endpoints.py`, `main.py` |

**Design notes:**

- **Pre-rolled 1m/5m rollups (`FR-QRY-001`) are deferred.** `read()` sums whatever 10s
  canonical buckets fall in the requested range on every query; `test_STM_04_efficiency.py`
  proves this indexes only the requested span, not the whole ring, so a 6h query costs at
  most ~2160 bucket reads rather than scanning the full ring unconditionally. This keeps
  query cost bounded without a second, incrementally-updated rollup structure to keep
  consistent with the 10s tier. Revisit if profiling under real load shows the on-demand
  sum is too expensive.
- **`estimated_memory_bytes()`** is a documented fixed-bytes-per-bucket/series estimate
  (`_BYTES_PER_SERIES_CONTRIBUTION` / `_BYTES_PER_BUCKET_SHELL` /
  `_BYTES_PER_OCCUPIED_BUCKET_EXTRA` in `metric_store.py`), not `sys.getsizeof`
  introspection, per `NFR-SCA-006`'s "documented as bytes-per-series-per-bucket". It counts
  every allocated ring bucket (occupied or not — an instance's ring is allocated at full
  `capacity` the moment it's first touched, regardless of how much data it ever sends), with
  occupied buckets costing extra on top.
- **`_shed_oldest_tier`** evicts the older half of every instance's retained buckets
  uniformly, as a cheap approximation of "the oldest retention tier" — not a cross-instance
  LRU, which would need globally comparable bucket ages this store doesn't track.
  `keep_count` is floored at 1 so shedding at `capacity < 2` is a no-op rather than a
  self-destructive full wipe.

**Fixes from a post-implementation review pass** (all closed in this same change; see
`git log` for the original vs. fixed diffs):

| Issue found | Fix | Verified by |
| --- | --- | --- |
| Memory warn/shed only reachable via `MetricStore.tick()`, which nothing calls on a schedule — the mechanism was correct but structurally unreachable from the real write path | `merge()` self-triggers a throttled check (`_maybe_check_memory_pressure`, ≤1 per `_MEMORY_CHECK_INTERVAL_SECONDS`, run *after* releasing the writing instance's own lock to avoid deadlocking with `_shed_oldest_tier`) | `test_merge_alone_can_trigger_shedding_without_an_external_tick` |
| `/readyz` could flip to `ready` from elapsed time alone, even with zero data ever merged (ingestion down/misconfigured) — exactly the "empty store misread as zero activity" case `FR-QRY-005` exists to prevent | `StreamProcessor.is_ready()` also requires `MetricStore.has_data` (sticky: set once, never unset by a later quiet period) | `test_is_ready_stays_false_past_warmup_window_if_no_data_ever_arrived`, `test_is_ready_stays_true_once_data_has_arrived_even_if_it_later_ages_out` |
| `estimated_memory_bytes()` undercounted lightly-used instances — only occupied buckets were counted, missing the full ring shell allocated on first touch | Gauge now counts every allocated bucket's shell cost, plus extra for occupied ones | `test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell` |
| `_shed_oldest_tier`'s cutoff degenerated at `capacity < 2` (`capacity // 2 == 0`), could evict a bucket in the same cycle it was written | `keep_count` floored at 1 | `test_shedding_never_evicts_a_bucket_written_in_the_same_cycle_at_small_capacity` |
| Self-metric counters (`MetricStore`'s `dropped_after_retention_total`, `dropped_series_over_cap_total`, `shed_buckets_total`, and `StreamProcessor.dropped_buckets_total`) incremented via bare `+= 1` — concurrent writes to different instances/requests could lose an increment | Dedicated `_counters_lock` / `_counter_lock`, held only for the increment itself | `test_concurrent_drops_across_many_instances_are_all_counted`, `test_concurrent_stale_rejections_across_many_instances_are_all_counted` |
| `_existing_instance` and `_shed_oldest_tier` indexed `_instance_locks` directly; `_get_or_create_instance` sets `_rings[id]` before `_instance_locks[id]` (both inside one guarded section), so a call landing in that window would raise `KeyError` instead of the graceful "nothing here yet" every other unknown-instance path returns | Both now use `.get()`, treating a missing lock the same as a missing ring | `test_existing_instance_does_not_raise_on_a_half_created_instance`, `test_shed_oldest_tier_does_not_raise_on_a_half_created_instance` |
| `max_series_per_bucket` had no lower-bound validation — a misconfigured `0` would silently drop every series as over-cap while `merge()` still set `has_data = True` | `StreamProcessorConfig.__post_init__` now rejects values below 1 | `test_config_rejects_a_non_positive_max_series_per_bucket` |

UBS-89 note: views are keyed by `instanceId` only, not `(application, instanceId,
agentId, window)` — `application` is carried on the wire `Snapshot` but not read by
`MetricStore`. This follows ADR 0005's assumption that cross-replica routing
(consistent-hash on `instanceId`) already requires `instanceId` to be globally
unique; `agentId` and window are handled inside reads (contribution keys, range
queries) rather than as separate top-level store keys. Flagged for confirmation,
not changed unilaterally.

Known gap, not closed here: the merge-associativity test
(`test_STM_01_window_alignment.py::test_merge_is_associative_regardless_of_arrival_order`)
is a hand-picked example, not the `hypothesis` property test spec 012 names for this
case — `hypothesis` isn't a repo dependency yet.

Full detail and remaining known gaps: [`ma-epic-implementation-summary.md`](./ma-epic-implementation-summary.md)
§7. Not yet wired: nothing calls `StreamProcessor.process_snapshot()` with real
data — no agent Backend Publisher and no backend Ingestion Service exist yet (both
separate, later work). `main.py` exposes `/healthz` and `/readyz` only; ingestion
and query routes are out of scope for UBS-89/90.

## M5 requirement coverage (RE-01–04)

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| RE-01 | Rule and alert lifecycle types, multi-tier schema | `FR-RUL-001`–`003`, `FR-RUL-015` | Done | `test_RE_01_fsm.py` |
| RE-02 | Rule evaluation and the alert lifecycle FSM | `FR-RUL-004`–`007`, `012`–`014`, `016`–`022` | Done | `test_RE_01_fsm.py`, `test_RE_02_evaluators.py`, `test_RE_03_safety.py` |
| RE-03 | The 14 default rules | `FR-RUL-010` | Done | `test_RE_04_default_rules.py` |

Full detail and the alert-readiness table: `docs/plan/re-epic-implementation-summary.md`.
Not yet wired: consecutive-failure streak tracking (no rule kind or
producer), session-message counters (`logouts`, `heartbeat_timeouts`,
`seq_gaps`, `clock_skew_events`), Callback Dispatcher and Backend Publisher
(so their self-health rules have no data). `config/rules.yaml` loading and
SIGHUP reload are implemented (`config_loader.py`); only the call to
`SighupRuleReloader.install()` from a real running process is unwired,
since no agent supervisor loop exists yet (M1).

## Code locations

| Component | Path |
| --- | --- |
| Parser protocol + registry | `apps/agent/src/telemetry_agent/parser/protocol.py`, `registry.py` |
| FIX classification | `apps/agent/src/telemetry_agent/parser/fix/classify.py` |
| FIX framing | `apps/agent/src/telemetry_agent/parser/fix/frame.py` |
| FIX field extraction + hashing | `apps/agent/src/telemetry_agent/parser/fix/fields.py`, `identifiers.py` |
| FIX enums, rejection, timestamps, seq gaps | `apps/agent/src/telemetry_agent/parser/fix/enums.py`, `normalize.py`, `rejection.py`, `timestamps.py`, `seq_tracker.py`, `enrich.py`, `telemetry.py` |
| FIX parser plugin | `apps/agent/src/telemetry_agent/parser/fix/parser.py` |
| Applog signature matcher (demo) | `apps/agent/src/telemetry_agent/parser/applog/signatures.py` |
| Parser CLI + visual display | `apps/agent/src/telemetry_agent/parser/cli.py`, `display.py` |
| Demo config loader | `apps/agent/src/telemetry_agent/parser/config.py` |
| Demo metrics sink | `apps/agent/src/telemetry_agent/metrics/demo_sink.py` |
| Synthetic FIX corpus | `apps/agent/testdata/fix/demo_logs.txt` |
| Magic applog corpus + config | `apps/agent/testdata/magic/` |
| Unit tests (parser) | `tests/unit/agent/parser/` |
| Metrics aggregator, counters, correlation, histogram | `apps/agent/src/telemetry_agent/metrics/` |
| Calculated indicators and snapshot output | `apps/agent/src/telemetry_agent/metrics/snapshot.py` |
| Shared snapshot contract | `packages/telemetry_shared/src/telemetry_shared/models/metrics.py` |
| Unit tests (metrics) | `tests/unit/agent/metrics/` |
| Shared histogram, ratios, latency summary | `packages/telemetry_shared/src/telemetry_shared/metrics/` |
| Shared wire-format snapshot contract | `packages/telemetry_shared/src/telemetry_shared/models/snapshot.py` |
| Stream Processor (window alignment, staleness) | `apps/backend/src/telemetry_backend/services/stream_processor.py` |
| Metric Store (cross-agent merge, ring buffer) | `apps/backend/src/telemetry_backend/services/metric_store.py` |
| Stream Processor / Metric Store config | `apps/backend/src/telemetry_backend/config.py` |
| Backend HTTP entrypoint (`/healthz`, `/readyz`) | `apps/backend/src/telemetry_backend/main.py` |
| Unit tests (backend services) | `tests/unit/backend/services/` |
| Unit tests (shared metrics/snapshot model) | `tests/unit/telemetry_shared/metrics/`, `tests/unit/telemetry_shared/models/` |
| Rule types, FSM, default rules | `apps/agent/src/telemetry_agent/rules/` |
| Rule config loading, SIGHUP reload | `apps/agent/src/telemetry_agent/rules/config_loader.py`, `config/rules.yaml` |
| Shared alert contract | `packages/telemetry_shared/src/telemetry_shared/models/alerts.py` |
| Unit tests (rules) | `tests/unit/agent/rules/` |
| Unit tests (shared models) | `tests/unit/telemetry_shared/` |
| Cross-component integration tests | `tests/integration/agent/` |

## How to verify

```bash
uv sync                  # or: make sync
make parser-test
make parser-demo
make stream-processor-quickstart          # UBS-89/90 walkthrough, two agents
uv run pytest tests/ -v                   # full suite, agent + backend + shared
make lint                                 # ruff (repo-wide) + mypy on agent source
uv run mypy apps/backend/src packages/telemetry_shared/src   # mypy on backend (not yet in `make lint`)
```

## Open risks

| Risk | Mitigation |
| --- | --- |
| [Q-8](../plan/open-questions.md#q-8--what-do-magics-logs-actually-look-like-highest-technical-risk): real Magic log shape unknown | Synthetic corpus per spec 012 §3 subset; revisit after sanitised samples |
| Python agent footprint unproven at load | Load test in spec 012 §5 once M1+M3 exist; ADR 0006 reversal conditions apply |
