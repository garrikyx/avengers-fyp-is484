# Implementation Status

Status: Live document · Last updated: 2026-11-08

Specs state the target; this document states what exists. Where the two differ, the
difference is recorded here rather than by quietly editing the spec.

Which requirement IDs have a referencing test is generated, not hand-written: run
`make requirement-coverage`
([`scripts/requirement_coverage.py`](../../scripts/requirement_coverage.py),
`FR-TST-001`, UBS-146) and see [Requirement coverage](#requirement-coverage-generated)
below. Per-epic tables further down record stories and their tests; where they disagree
with the script, trust the script and fix the table.

## Milestones

| Milestone | Scope                                          | Status                                                                                                                                                                                                                                                                                                                                                                                                                                |
| --------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M0        | Repository foundation, CI gates, shared models | Partial — uv workspace, Makefile, `packages/telemetry_shared/`, CI (`.github/workflows/ci.yml`, UBS-138: ruff, mypy, pytest on Linux and Windows) and the requirement-coverage report (`scripts/requirement_coverage.py`, UBS-146; report-only) exist. Not yet: data-leak sentinel (`FR-TST-005`, UBS-137), branch protection, `main` green on both runners (UBS-139)                                                                 |
| M1        | Log monitor and configuration                  | **Implemented, thinly traced** — `apps/agent/src/telemetry_agent/logs/` (LogMonitor, MultiLogMonitor, offset tracker, status); Windows rotation lock fixed (UBS-124). Only 1 of 14 `FR-LOG-*` IDs is cited by a test and `FR-TST-004` (rotation/truncation harness on Linux and Windows) has none                                                                                                                                     |
| M1.5      | Pipeline bridge (monitor → parser)             | **Done** — UBS-48 library and UBS-49 integration (supervisor, MA-01 ingest, heartbeat) landed via UBS-112/114; all 7 `FR-PIP-*` IDs cited by tests                                                                                                                                                                                                                                                                                    |
| **M2**    | **FIX parser (UBS-40–47)**                     | **Done** — classify, frame, allowlist extraction, enums, rejection labels, timestamps, seq gaps, parse-error handling; wired through the pipeline; Magic applog parser and the `magic-binary` detector (`FR-PRS-040`–`046`, frame layout still `TBD(vendor)`). 28 of 30 `FR-PRS-*` IDs cited by tests (missing `001`, `002`)                                                                                                          |
| **M3**    | **Metrics aggregation**                        | **Done** — aggregator, counters, correlation, calculated indicators and snapshot output (MA-01–04), fed by live events through the pipeline (UBS-112); `parseErrorRate` has a producer. 7 of 20 `FR-MET-*` IDs cited by tests                                                                                                                                                                                                         |
| **M4**    | **Backend ingestion, store, query**            | **Done for Day 1 (in-memory)** — Stream Processor and Metric Store, ingestion API and bounded hand-off, allowlists and cardinality enforcement, alert and metrics query APIs, Event Store (UBS-118), Publisher to backend (UBS-103/115), health read API and `AgentHeartbeatMissing`. Persistence (`persistence/`) is empty: Day-2. Authentication of the ingestion path is not covered by tests (`FR-ING-001`–`003`, `NFR-SEC-003`+) |
| **M5**    | **Rules, alerts, callbacks**                   | **Done** — Rule Engine and alert lifecycle (RE-01–04), HTTP/HMAC callback dispatch with retry and delivery status (`FR-CBK-*`, 14 of 18 cited), rule actions and test mode (UBS-35/36), anomaly rules (UBS-25–29). Only 8 of 30 `FR-RUL-*` IDs cited by tests                                                                                                                                                                         |
| M6        | Natural language layer                         | **Partial** — rule-path matcher (UBS-99/101/102), LLM fallback (UBS-97/98), Teams bot (UBS-100), MCP server (ADR 0007), `reject_reason_trend` intent (UBS-143). 8 of 25 `FR-NLQ-*` IDs cited by tests; securing the NL API is in review (UBS-135)                                                                                                                                                                                     |
| M7        | Operability hardening                          | **Not started** — `deployment/` holds only `.gitkeep`; `NFR-OBS-*`, `NFR-OPS-*` and `NFR-SCA-*` have no citing tests; local stack is `compose.yaml` only. Load/footprint test is UBS-144                                                                                                                                                                                                                                              |

## Requirement coverage (generated)

Snapshot of `make requirement-coverage` on 2026-11-08, counting IDs a spec _defines_
against IDs any file under `tests/` names (hyphen or underscore style, short ranges
expanded). It proves a test mentions an ID, not that the test is sufficient. CI prints
the same report on every run and does not fail on gaps yet.

| Area                                                  | Cited by tests | Uncited IDs                                                     |
| ----------------------------------------------------- | -------------- | --------------------------------------------------------------- |
| `FR-PIP`                                              | 7/7            | —                                                               |
| `FR-STM`                                              | 6/6            | —                                                               |
| `FR-PRS`                                              | 28/30          | 001, 002                                                        |
| `FR-PUB`                                              | 6/8            | 003, 008                                                        |
| `FR-CBK`                                              | 14/18          | 008, 010, 012, 018                                              |
| `FR-HLT`                                              | 6/10           | 013–016                                                         |
| `FR-NLQ`                                              | 8/25           | 001, 002, 010–014, 016–020, 022–024, 027, 031                   |
| `FR-MET`                                              | 7/20           | 001–004, 010, 021–023, 025–027, 032, 034                        |
| `FR-RUL`                                              | 8/30           | 001–003, 007, 009–011, 013–016, 018, 021, 022, 031–033, 040–044 |
| `FR-QRY`                                              | 9/30           | 001, 006–014, 019, 020, 030–033, 035–039                        |
| `FR-ING`                                              | 4/13           | 001–003, 006, 007, 009, 020–022                                 |
| `FR-TST`                                              | 3/9            | 002–004, 006, 009, 011                                          |
| `FR-LOG`                                              | 1/14           | all but 010                                                     |
| `FR-CFG`                                              | 0/8            | all                                                             |
| `NFR-PERF`                                            | 2/10           | 002, 003, 005–010 (UBS-144, UBS-140)                            |
| `NFR-SEC`                                             | 2/20           | 003–020                                                         |
| `NFR-REL`, `NFR-CFG`, `NFR-OBS`, `NFR-OPS`, `NFR-SCA` | 2/28           | nearly all                                                      |

Some of these are tested without citing the ID (the report cannot see that); the fix is
to add the ID to the test name or a comment. The known real gaps are tracked as UBS-137
(`FR-TST-005` leak sentinel), UBS-140 (acceptance run) and UBS-144 (load and footprint).

## M2 requirement coverage (UBS-40–42)

| ID     | Story                                  | Requirement                      | Status | Verified by                                                                                                             |
| ------ | -------------------------------------- | -------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| UBS-40 | Parser plugin interface and registry   | `FR-PRS-030`–`032`, `FR-PRS-003` | Done   | `tests/unit/agent/parser/test_FR_PRS_030_registry.py`                                                                   |
| UBS-41 | Classify log lines before FIX parsing  | `FR-PRS-010`, `FR-PRS-011`       | Done   | `tests/unit/agent/parser/test_FR_PRS_010_classify.py`                                                                   |
| UBS-42 | Frame FIX messages from log lines      | `FR-PRS-012`–`016`               | Done   | `tests/unit/agent/parser/test_FR_PRS_012_frame.py`, `apps/agent/testdata/fix/`                                          |
| UBS-43 | Allowlisted field extraction           | `FR-PRS-020`                     | Done   | `tests/unit/agent/parser/test_FR_PRS_020_fields.py`, `parser/fix/fields.py`                                             |
| UBS-44 | Identifier hashing                     | `FR-PRS-021`                     | Done   | `tests/unit/agent/parser/test_FR_PRS_021_identifiers.py`, `parser/fix/identifiers.py`                                   |
| UBS-45 | Enum mapping + tag-58 rejection labels | `FR-PRS-022`–`024`               | Done   | `test_FR_PRS_022_normalize.py`, `test_FR_PRS_023_enums.py`, `test_FR_PRS_024_rejection.py`, `test_UBS45_integration.py` |
| UBS-46 | FIX timestamps + sequence gaps         | `FR-PRS-025`–`027`               | Done   | `test_FR_PRS_025_timestamps.py`, `test_FR_PRS_027_seq_tracker.py`                                                       |
| UBS-47 | Parse errors without stopping agent    | `FR-PRS-017`–`019`               | Done   | `test_FR_PRS_017_019_errors.py`                                                                                         |

### Magic applog demo (not UBS-45–47)

| Area                          | Status | Notes                                                                                          |
| ----------------------------- | ------ | ---------------------------------------------------------------------------------------------- |
| Magic line classification     | Done   | `test_FR_PRS_010_magic_venue_lines.py`, config in `apps/agent/testdata/magic/demo_config.yaml` |
| `%` template error signatures | Done   | `parser/applog/signatures.py`, `test_applog_signature_templates.py`                            |
| Full AppLogParser plugin      | Done   | `parser/applog/parser.py`; chain `[fix, applog]` when `appLogPatterns` configured              |

### Remaining M2 gaps

| Area                        | Requirements | Notes                                                       |
| --------------------------- | ------------ | ----------------------------------------------------------- |
| Leak sentinel               | `FR-TST-005` | Lands with full corpus gate                                 |
| Parser → MA-01 event bridge | spec 004     | ParsedMessageEvent construction from FixTelemetry not wired |

## Pipeline bridge (M1.5)

Spec: [002-agent.md §1.1](../specs/002-agent.md), ADR
[0006](../adr/0006-agent-in-python.md).

| ID           | Requirement                                                            | Status                                                                                                           |
| ------------ | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| UBS-48       | Pipeline bridge **library** — queues, workers, commit, dedupe, demo    | `FR-PIP-001`–`007` (library) — **Done** — `tests/unit/agent/pipeline/`, `make pipeline-demo`                     |
| UBS-49       | Pipeline bridge **integration** — live agent, MA-01, heartbeat, config | `FR-PIP-004`–`005` (operational), `FR-CFG-*` — **Not started** — `docs/plan/ubs49-pipeline-integration-story.md` |
| `FR-PIP-001` | Blocking enqueue (default); optional drop_oldest                       | Done (UBS-48)                                                                                                    |
| `FR-PIP-002` | Asymmetric queue sizing (line queue 2048 > event queue 256)            | Done (UBS-48)                                                                                                    |
| `FR-PIP-003` | Parser worker pool (`min(2, cpu_count)`)                               | Done (UBS-48)                                                                                                    |
| `FR-PIP-004` | Bounded event queue → aggregator                                       | Done (UBS-48; MA-01 ingest UBS-112)                                                                              |
| `FR-PIP-005` | Queue depth + drop counters on heartbeat/metrics                       | Done (UBS-48 `PipelineStats`; heartbeat via UBS-114)                                                             |
| `FR-PIP-006` | Commit offset after parse+ingest                                       | Done (UBS-48)                                                                                                    |
| `FR-PIP-007` | Dedupe by `(dev, inode, byte_offset)`                                  | Done (UBS-48)                                                                                                    |

UBS-48 modules: `pipeline/bounded_queue.py`, `line_queue.py`, `event_queue.py`,
`workers.py`, `committer.py`, `deduper.py`, `supervisor.py`, `monitor_adapter.py`.

UBS-49 landed as `main.py`, `config.py`, `pipeline/ingest.py` and `health/reporter.py`;
there is no separate `event_bridge.py`.

## M3 requirement coverage (MA-01–04)

| ID    | Story                                     | Requirement                              | Status | Verified by                                      |
| ----- | ----------------------------------------- | ---------------------------------------- | ------ | ------------------------------------------------ |
| MA-01 | Bucketed counter/histogram store          | `FR-MET-024`–`030`                       | Done   | `test_MA_01_aggregator.py`                       |
| MA-02 | Order/execution/reject counters           | spec 004 §4.1                            | Done   | `test_MA_02_counters.py`                         |
| MA-03 | Order correlation and latency             | spec 004 §4.4                            | Done   | `test_MA_03_correlation.py`, `test_histogram.py` |
| MA-04 | Calculated indicators and snapshot output | `FR-QRY-007`, `FR-QRY-010`, `FR-QRY-012` | Done   | `test_MA_04_snapshot.py`                         |

Full detail and an alert-readiness mapping:
`docs/plan/ma-epic-implementation-summary.md`. Real events reach MA-01–04 through the
pipeline (UBS-112, UBS-114).

UBS-73/74 added two counter producers on top of MA-02's order counters:
`parser.metrics_event.derive_session_counters` (session health — `logouts`, `seq_gaps`,
`clock_skew_events` — on `counters.SESSION_DIMS`) and
`metrics.agent_counters.AgentCounterSampler` (the agent's own callback counters on
`counters.AGENT_DIMS`, via the new `MetricsAggregator.ingest_agent_counters` write path,
which deliberately leaves `secondsSinceLastEvent` alone). See
`docs/plan/re-epic-implementation-summary.md` §7.

## M4 requirement coverage (Stream Processor & Metric Store)

Renumbered since this table was first written: the original single ticket for this work
(UBS-79/UBS-88 in earlier drafts) split into UBS-89 (cross-agent merge correctness — the
rows below) and UBS-90 (store memory & concurrency — its own table beneath). UBS-93–95
(Alert Store epic) are now implemented.

| ID     | Story                                                            | Requirement                                                                                 | Status | Verified by                                                   |
| ------ | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------- |
| UBS-88 | Window alignment, staleness, and agent reconciliation            | `FR-STM-001`, `FR-ING-005`, `FR-STM-005`, `FR-STM-006`                                      | Done   | `test_STM_01_window_alignment.py`, `test_STM_03_warmup.py`    |
| UBS-88 | Cross-agent merge semantics (counters/ratios/histograms)         | `FR-STM-002`–`004`                                                                          | Done   | `test_STM_02_merge_semantics.py`                              |
| UBS-66 | Ingestion API and payload contract                               | `POST /telemetry/batch`, `/events`, `/heartbeat`; basic schema validation; bounded hand-off | Done   | `tests/unit/backend/api/test_ingestion.py`                    |
| UBS-86 | Dimension/field allowlists and cardinality enforcement at ingest | `FR-ING-006`, `FR-ING-007`, `NFR-SEC-002`                                                   | Done   | `tests/unit/backend/api/test_ingestion.py`                    |
| UBS-93 | Alert state storage and merge by `alertId`                       | `FR-QRY-016`, `FR-QRY-017`                                                                  | Done   | `test_FR_QRY_016_017_alert_store.py`                          |
| UBS-94 | Alert query API (list + detail)                                  | `GET /telemetry/alerts`, `GET /telemetry/alerts/{alertId}` (spec 007 §4)                    | Done   | `test_UBS_94_alerts_query.py`                                 |
| UBS-95 | Backend-owned `AgentHeartbeatMissing`                            | `FR-QRY-018`, `FR-RUL-030`                                                                  | Done   | `test_FR_QRY_018_heartbeat_missing.py`                        |
| UBS-68 | Metrics query API (shape, filters, grouping)                     | `POST /telemetry/query/metrics`, `FR-QRY-006`–`010`, spec 007 §3                            | Done   | `test_UBS_68_query_engine.py`, `test_UBS_68_metrics_query.py` |
| UBS-91 | Query clamping, timeouts, `dataCompleteness`                     | `FR-QRY-011`, `013`–`015`                                                                   | Done   | `test_UBS_91_query_limits.py`                                 |
| UBS-92 | Multi-replica scatter-gather                                     | `NFR-SCA-003`–`004`, `queryMode: fanout \| colocated`                                       | Done   | `test_UBS_92_replica_fanout.py`                               |

UBS-68's original alert-query AC is satisfied by UBS-94 (split per epic scope). API
examples: [`metrics-query-api.md`](./metrics-query-api.md).

Full detail and known gaps:
[`ma-epic-implementation-summary.md`](./ma-epic-implementation-summary.md) §7. The
backend's bounded ingestion worker now calls `StreamProcessor.process_batch()` for
accepted snapshots and `AlertStore.merge()` for alerts. Heartbeats update the Agent
Registry (UBS-69/87) and feed `AgentHeartbeatMissing` (UBS-95). Events are kept in the
Event Store (`services/event_store.py`, UBS-118). Alert query responses carry
placeholder `delivery.status: unknown` until the agent publishes a callback outcome.
Since the agent republishes each alert once its callback settles, queries show the real
delivery state: tracked per notification (`FR-CBK-018`, `callbacks/status.py`) and
merged by the Alert Store, which ignores a stale non-resolved update for a resolved
alert (`FR-QRY-019`). Request body-size limits (`services/request_body.py`), dedupe/rate
limiting (UBS-85) and the health read API (UBS-69) are done. Authentication of the
ingestion path has no citing tests yet (`FR-ING-001`–`003`).

## M5 requirement coverage (RE-01–04)

| ID    | Story                                             | Requirement                                  | Status | Verified by                                                             |
| ----- | ------------------------------------------------- | -------------------------------------------- | ------ | ----------------------------------------------------------------------- |
| RE-01 | Rule and alert lifecycle types, multi-tier schema | `FR-RUL-001`–`003`, `FR-RUL-015`             | Done   | `test_RE_01_fsm.py`                                                     |
| RE-02 | Rule evaluation and the alert lifecycle FSM       | `FR-RUL-004`–`007`, `012`–`014`, `016`–`022` | Done   | `test_RE_01_fsm.py`, `test_RE_02_evaluators.py`, `test_RE_03_safety.py` |
| RE-03 | The 17 default rules                              | `FR-RUL-010`                                 | Done   | `test_RE_04_default_rules.py`                                           |

Full detail and the alert-readiness table:
`docs/plan/re-epic-implementation-summary.md`. Consecutive-failure streak tracking is
not a general rule kind (`BackendUnreachable` gets the effect from a
publisher-maintained gauge, FR-MET-031). Session-message counters (`logouts`,
`seq_gaps`, `clock_skew_events`) landed with UBS-73 and `heartbeat_timeouts` with
UBS-106 (FR-MET-032). `config/rules.yaml` loading and SIGHUP reload are implemented
(`config_loader.py`) and wired into the running agent by `RuleEvaluator` (UBS-113), with
an mtime trigger since UBS-35.

## Rule actions and test mode (UBS-35, UBS-36)

| ID     | Story                                           | Requirement                                                 | Status                 | Verified by                                                                                                                                     |
| ------ | ----------------------------------------------- | ----------------------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| UBS-35 | Custom conditions bound to configurable actions | `FR-CBK-013`–`017` (spec 005 §5), `FR-RUL-008`/`009` reload | Done, pending ADR 0008 | `tests/unit/agent/actions/`, `tests/unit/agent/rules/test_UBS_35_36_reload_and_draft.py`, `tests/integration/test_UBS_35_actions_end_to_end.py` |
| UBS-36 | Validate a condition before activation          | `FR-RUL-031`–`033` (spec 005 §6)                            | Done on branch         | `tests/unit/agent/pipeline/test_UBS_36_backtest.py`, `tests/integration/test_UBS_36_backtest_cli.py`                                            |

Code: `apps/agent/src/telemetry_agent/actions/` (catalogue + runner),
`pipeline/backtest.py` (test mode), `--test-rule` in `main.py`. The `disk-cleanup`
example action is still unbound; `HostDiskFull` exists since UBS-129 but binding it is a
rule-file decision (ADR 0008). The reload now runs in the real agent: on SIGHUP, and on
a `rules.yaml` mtime change.

## D2 anomaly detection (UBS-25–29)

| ID     | Story                                 | Requirement                      | Status                                                             | Verified by                                                                                                                           |
| ------ | ------------------------------------- | -------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| UBS-25 | Alert on abnormal reject rate         | `FR-RUL-040`–`044` (spec 005 §7) | Done                                                               | `tests/unit/agent/rules/test_UBS_25_29_anomaly.py`                                                                                    |
| UBS-26 | Alert on abnormal processing latency  | `FR-RUL-040`–`044`               | Done                                                               | same                                                                                                                                  |
| UBS-27 | Identify increasing rejection reasons | `FR-QRY-040` (spec 007 §3.1)     | Done; NL intent `reject_reason_trend` (UBS-143)                    | `tests/unit/backend/services/test_UBS_27_reject_reason_trends.py`, `tests/unit/backend/nl/test_UBS_143_reject_reason_trend_intent.py` |
| UBS-28 | Alert on abnormal execution issues    | `FR-RUL-040`–`044`               | Done, definition of "execution issue" pending sponsor confirmation | same                                                                                                                                  |
| UBS-29 | Alert on abnormal parser failures     | `FR-RUL-040`–`044`               | Done                                                               | same                                                                                                                                  |

Code: `rules/baseline.py` (baseline tracker, explanation text), `anomaly` kind in
`rules/engine.py`, `load_anomaly_rules` in `rules/config_loader.py`,
`config/anomaly.yaml`; backend `services/reject_reason_trends.py` and
`models/trends.py`. Notes on the ticket wording problems: `docs/plan/ubs25-29-notes.md`.

## Application.log failure alert (UBS-128)

| ID      | Story                                 | Requirement                                                | Status | Verified by                                             |
| ------- | ------------------------------------- | ---------------------------------------------------------- | ------ | ------------------------------------------------------- |
| UBS-128 | Alert on Application.log [F] failures | `FR-RUL-023` (spec 005 §1.2), `FR-MET-033` (spec 004 §4.6) | Done   | `tests/unit/agent/pipeline/test_UBS_128_level_rules.py` |

Code: optional `level:` on `threshold` rules (`rules/types.py`,
`rules/config_loader.py`, read from a `level`-grouped snapshot in `rules/engine.py` and
`pipeline/evaluator.py`), `AppLogFailure` in `rules/defaults.py` and
`config/rules.yaml`, and the `level` dimension on `app_log_errors`
(`metrics/counters.py`). `[E]` lines are counted but do not fire it. Known limit: series
admission is first-come under `maxSeriesPerBucket`, so if a bucket is already full when
the first `[F]` line arrives it folds to `__other__` and the rule does not match;
`cardinality_folded` is the signal.

## Host Monitor (UBS-129)

| ID      | Story                                                                               | Requirement                                                                            | Status         | Verified by                                                                                                                                                                                                     |
| ------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UBS-129 | Host disk/memory gauges, `HostDiskFull`/`HostMemoryHigh`, heartbeat `resourceUsage` | `FR-HLT-013`/`015`/`016` (spec 002 §7.1), `FR-MET-034` (spec 004 §4.7), `NFR-PERF-003` | Done on branch | `tests/unit/agent/health/test_UBS_129_*.py`, `tests/unit/agent/rules/test_UBS_129_host_rules.py`, `tests/integration/agent/test_UBS_129_host_alerts.py`, `tests/integration/test_UBS_129_agent_host_monitor.py` |

Code: `health/host_monitor.py` (`HostMonitor`, `HostSampler` protocol, `PsutilSampler`),
`host:` in `config.py` and `config/agent.yaml`, `HostDiskFull` and `HostMemoryHigh` in
`rules/defaults.py` and `config/rules.yaml`, `Gauges.host_*` fields, `host_gauges`
plumbing in `metrics/snapshot.py`, `pipeline/evaluator.py` and
`publishing/snapshot_bridge.py`, `HealthReporter.set_resource_usage_provider`. `psutil`
is now an agent dependency (`types-psutil` for mypy). Decisions and limits:

- **Flat gauges, `mount` in the key.** `Gauges` and the wire `Snapshot.gauges` are flat
  `dict[str, float]`, so `host_disk_used_ratio` is the worst (maximum) mount over the
  readable `host.diskPaths` (what `HostDiskFull` reads), and each readable mount also
  rides the wire as `host_disk_used_ratio:<mount>` (`<mount>` verbatim; everything after
  the first `:`), like `action_runs:<action>:<outcome>`. Names live in
  `telemetry_shared/metrics/host.py`. A mount that cannot be read has no per-mount key,
  is left out of the maximum and is counted, so the maximum is known to be over the
  readable mounts only; a partly unreadable disk is visible, not silently healthy.
- **Spec holds, not the engine default.** `HostDiskFull` holds 1m, `HostMemoryHigh` 2m
  (spec 005 §1.2). Both set `dependsOnLogActivity: false` so `NoLogActivity` does not
  silence them.
- **Host rules load only when enabled** (spec 005 §1.2): `config.host_rule_filter` drops
  a rule reading `host_disk_used_ratio` / `host_memory_used_ratio` / `magic_process_up`
  unless `host.enabled` and the matching setting (`diskPaths` non-empty, `memory`,
  `process.name`) is on. `load_agent_config` and the rules reloader both apply it, so a
  reload cannot bring one back. A rule that is loaded still stays inactive while its
  gauge is unreadable.
- **Omit, never zero.** A failed read drops that gauge (and the previous value) and
  counts `host_sample_errors`, which the evaluator bridges into the aggregator like the
  other agent counters (`AGENT_DIMS`, windowed series, on the wire in `series`), so it
  is queryable; it is still logged at shutdown too. A firing alert on a host gauge that
  becomes unreadable is **held** (`rules/engine.py`: no auto-resolve, no new
  notification; a resolving alert goes back to firing so the resolve window restarts
  when data returns). This applies only to the three host gauges: for
  `oldest_pending_age_seconds` a missing value genuinely means "clear". A pending alert
  on a missing gauge is dropped, not held.
- **`diskPaths` default.** The shipped `config/agent.yaml` uses `["."]` so dev machines
  (incl. Windows) can read it; set it to Magic's log filesystem on the host. When the
  key is omitted the model default is spec 010's `/var/log/magic` on POSIX and the
  system drive root on Windows (`default_disk_paths`), where that path cannot exist. The
  disk ratio is `1 - free / total` (space the agent's user can still write;
  `used / total` under-reads on APFS), recorded in spec 004 `FR-MET-034`; memory is
  `(total - available) / total`.
- **Heartbeat `resourceUsage`** carries the agent's RSS (MB), CPU and the event loop's
  task count (`activeTasks`, read on the loop by `HostMonitor.run`). With
  `host.enabled: false` or a failed read it is **omitted**, not sent as zeros: the
  shared ingestion `ResourceUsage.activeTasks` and `Heartbeat.resourceUsage` are now
  optional, and the backend health API returns `null` (spec 004 §6 and spec 007 §5.2
  updated).
- **Alert `metricContext`** for gauge rules carries the gauge value instead of a
  fabricated `0.0` counter (also `BackendUnreachable`, `PendingOrderTimeout`), and no
  longer depends on a group having been ingested (Magic down means silent logs).
  Regression tests: `tests/unit/agent/rules/test_UBS_129_gauge_rules_engine.py`.
- **`NFR-PERF-003`:** sampling every 30s in a worker thread with one immutable sample as
  its only state. `test_nfr_perf_003_memory_does_not_grow_with_the_number_of_samples`
  asserts with `tracemalloc` that allocations do not scale with run length; a load test
  with an RSS assertion at target throughput remains a separate item (an RSS reading
  from a unit test is machine-dependent, so it is not asserted).

## Magic process liveness (UBS-130)

| ID      | Story                                       | Requirement                                                                                 | Status         | Verified by                                                                                                                                                                              |
| ------- | ------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UBS-130 | `magic_process_up` gauge, `ApplicationDown` | `FR-HLT-014` (spec 002 §7.1), `FR-MET-034` (spec 004 §4.7), spec 005 §1.2 `ApplicationDown` | Done on branch | `tests/unit/agent/health/test_UBS_130_process_liveness.py`, `tests/unit/agent/rules/test_UBS_130_application_down.py`, `tests/integration/agent/test_UBS_130_application_down_alerts.py` |

Builds on the UBS-129 Host Monitor: `HostSampler.process_running(name)` (+
`PsutilSampler`, see "Process matching" below), a step in `HostMonitor.sample_once`,
`Gauges.magic_process_up`, and `ApplicationDown` in `rules/defaults.py` and
`config/rules.yaml` (critical, `== 0`, 30s hold, `dependsOnLogActivity: false`, so
`NoLogActivity` does not silence it). Decisions and limits:

- **Exact name, no case folding.** `host.process.name` must equal a running process's
  name exactly (`magic.exe` does not match `magic.exe.bak` or `notmagic.exe`). Command
  lines and arguments are never read. On Windows, set the name with the casing the OS
  reports.
- **Process matching never reads a command line.** psutil's `Process.name()` does, on
  POSIX, for names of 15 or more characters (verified against psutil 7.2.2; its `exe()`
  also falls back to `cmdline()` when denied). So `PsutilSampler.process_running` reads
  Linux `/proc/<pid>/comm`, and psutil's `name` only on Windows (which never reads a
  command line). On Linux `comm` holds 15 characters, so a configured name longer than
  that is compared by its first 15; two executables sharing that prefix are not told
  apart. On macOS/BSD the process list is not read at all (unreadable, so the gauge is
  omitted): there is no public psutil call that is safe there, and Magic's host is Linux
  or Windows.
- **An empty or wholly unreadable process list is "no data".** If no process name could
  be read, `process_running` raises, so `magic_process_up` is omitted and the error
  counted; it is never reported as 0.
- **Empty name = off.** No gauge, no process-list read, no error counted, rule inactive.
  The shipped `agent.yaml` leaves it empty (the name is UBS-specific).
- **Limitation: an unreadable process list omits the gauge (no alert).** The sampler
  raising (permissions, platform) counts `host_sample_errors` and drops
  `magic_process_up` rather than reporting 0, so a host where the agent cannot list
  processes never raises `ApplicationDown`. A firing `ApplicationDown` whose gauge turns
  unreadable is held, not auto-resolved (see the UBS-129 decisions).
- **`ApplicationDown` is not loaded while `process.name` is empty** (spec 005 §1.2,
  `host_rule_filter`), rather than loaded and inactive.
- **Timing.** With the 30s default `sampleInterval` and the 30s hold, the alert fires on
  the second consecutive 0 sample. Resolution uses the default `resolveAfter` of 300s;
  the spec is silent on a shorter value.
- **Only the process list is checked**, not that Magic is healthy; a hung but running
  process is still `up`.

## Health Reporter coverage (UBS-30, UBS-58, UBS-59, UBS-60)

| ID     | Story                                    | Requirement                                                                                                                                         | Status                                                   | Verified by                                                                                            |
| ------ | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| UBS-30 | Per-file read lag in the Health Reporter | `FR-LOG-010`, `FR-HLT-001` (read-lag slice)                                                                                                         | Done                                                     | `tests/unit/agent/health/test_reporter.py`, `tests/integration/agent/test_ubs30_health_integration.py` |
| UBS-58 | Emit periodic heartbeat                  | `FR-HLT-001` (interval, idle emission), `FR-HLT-002`/`003` (status + reasons, read-lag rule), `FR-HLT-004` (gaps as `null`), spec 004 s6 wire shape | Done (agent side)                                        | `tests/unit/agent/health/test_heartbeat.py`, `test_status.py`, `test_health_config.py`                 |
| UBS-59 | Parse error rate in heartbeat            | `FR-HLT-001`/`002` (parse-error slice), spec 004 s4.5 `parseErrorRate`                                                                              | Done (agent side; no production producer until M1.5)     | `tests/unit/agent/health/test_window.py`, `test_parse_errors.py`                                       |
| UBS-60 | Publish queue depth in heartbeat         | `FR-HLT-001`/`002` (queue slice); `FR-PIP-005` pipeline queues still pending M1.5                                                                   | Done (agent side; provider hook, Publisher itself is M4) | `tests/unit/agent/health/test_queue_depth.py`                                                          |

Decisions and the missing-downstream list: `docs/plan/ubs58-60-notes.md`. Heartbeats
reach the backend only through the Backend Publisher, inside `TelemetryBatch.heartbeat`
(`health/publishing.py`; the direct `HttpHeartbeatSink` and the stub receiver were
retired 2026-10-07). The UBS-58 ticket's two backend-side criteria (`lastHeartbeatUtc`,
`unresponsive`) are delivered by UBS-69.

## Code locations

| Component                                                                                        | Path                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Parser protocol + registry                                                                       | `apps/agent/src/telemetry_agent/parser/protocol.py`, `registry.py`                                                                                   |
| FIX classification                                                                               | `apps/agent/src/telemetry_agent/parser/fix/classify.py`                                                                                              |
| FIX framing                                                                                      | `apps/agent/src/telemetry_agent/parser/fix/frame.py`                                                                                                 |
| FIX field extraction + hashing                                                                   | `apps/agent/src/telemetry_agent/parser/fix/fields.py`, `identifiers.py`                                                                              |
| FIX enums, rejection, timestamps, seq gaps                                                       | `apps/agent/src/telemetry_agent/parser/fix/enums.py`, `normalize.py`, `rejection.py`, `timestamps.py`, `seq_tracker.py`, `enrich.py`, `telemetry.py` |
| FIX parser plugin                                                                                | `apps/agent/src/telemetry_agent/parser/fix/parser.py`                                                                                                |
| Applog signature matcher (demo)                                                                  | `apps/agent/src/telemetry_agent/parser/applog/signatures.py`                                                                                         |
| Parser CLI + visual display                                                                      | `apps/agent/src/telemetry_agent/parser/cli.py`, `display.py`                                                                                         |
| Demo config loader                                                                               | `apps/agent/src/telemetry_agent/parser/config.py`                                                                                                    |
| Demo metrics sink                                                                                | `apps/agent/src/telemetry_agent/metrics/demo_sink.py`                                                                                                |
| Synthetic FIX corpus                                                                             | `apps/agent/testdata/fix/demo_logs.txt`                                                                                                              |
| Magic applog corpus + config                                                                     | `apps/agent/testdata/magic/`                                                                                                                         |
| Unit tests (parser)                                                                              | `tests/unit/agent/parser/`                                                                                                                           |
| Metrics aggregator, counters, correlation, histogram                                             | `apps/agent/src/telemetry_agent/metrics/`                                                                                                            |
| Calculated indicators and snapshot output                                                        | `apps/agent/src/telemetry_agent/metrics/snapshot.py`                                                                                                 |
| Shared snapshot contract                                                                         | `packages/telemetry_shared/src/telemetry_shared/models/metrics.py`                                                                                   |
| Unit tests (metrics)                                                                             | `tests/unit/agent/metrics/`                                                                                                                          |
| Shared histogram, ratios, latency summary                                                        | `packages/telemetry_shared/src/telemetry_shared/metrics/`                                                                                            |
| Shared wire-format snapshot contract                                                             | `packages/telemetry_shared/src/telemetry_shared/models/snapshot.py`                                                                                  |
| Stream Processor (window alignment, staleness)                                                   | `apps/backend/src/telemetry_backend/services/stream_processor.py`                                                                                    |
| Metric Store (cross-agent merge, ring buffer)                                                    | `apps/backend/src/telemetry_backend/services/metric_store.py`                                                                                        |
| Stream Processor / Metric Store config                                                           | `apps/backend/src/telemetry_backend/config.py`                                                                                                       |
| Backend HTTP entrypoint (`/healthz`, `/readyz`, `/telemetry/alerts`, `/telemetry/query/metrics`) | `apps/backend/src/telemetry_backend/main.py`                                                                                                         |
| Metrics Query Engine                                                                             | `apps/backend/src/telemetry_backend/services/query_engine.py`                                                                                        |
| Replica fan-out (UBS-92)                                                                         | `apps/backend/src/telemetry_backend/services/replica_fanout.py`                                                                                      |
| Shared metrics query models                                                                      | `packages/telemetry_shared/src/telemetry_shared/models/metrics_query.py`                                                                             |
| Query alias tables                                                                               | `packages/telemetry_shared/src/telemetry_shared/query/aliases.py`                                                                                    |
| Alert Store (active + resolved history)                                                          | `apps/backend/src/telemetry_backend/services/alert_store.py`                                                                                         |
| Minimal agent heartbeat registry                                                                 | `apps/backend/src/telemetry_backend/services/agent_registry.py`                                                                                      |
| Backend `AgentHeartbeatMissing` monitor                                                          | `apps/backend/src/telemetry_backend/services/heartbeat_monitor.py`                                                                                   |
| Shared alert query response models                                                               | `packages/telemetry_shared/src/telemetry_shared/models/alerts_query.py`                                                                              |
| Unit tests (backend services)                                                                    | `tests/unit/backend/services/`                                                                                                                       |
| Unit tests (shared metrics/snapshot model)                                                       | `tests/unit/telemetry_shared/metrics/`, `tests/unit/telemetry_shared/models/`                                                                        |
| Rule types, FSM, default rules                                                                   | `apps/agent/src/telemetry_agent/rules/`                                                                                                              |
| Rule config loading, SIGHUP reload                                                               | `apps/agent/src/telemetry_agent/rules/config_loader.py`, `config/rules.yaml`                                                                         |
| Shared alert contract                                                                            | `packages/telemetry_shared/src/telemetry_shared/models/alerts.py`                                                                                    |
| Unit tests (rules)                                                                               | `tests/unit/agent/rules/`                                                                                                                            |
| Unit tests (shared models)                                                                       | `tests/unit/telemetry_shared/`                                                                                                                       |
| Cross-component integration tests                                                                | `tests/integration/agent/`                                                                                                                           |
| Health Reporter, heartbeat emitter, health config                                                | `apps/agent/src/telemetry_agent/health/`                                                                                                             |
| Shared heartbeat contract                                                                        | `packages/telemetry_shared/src/telemetry_shared/models/health.py`                                                                                    |
| Agent entrypoint                                                                                 | `telemetry-agent` (`apps/agent/src/telemetry_agent/main.py`, config `config/agent.yaml`)                                                             |
| Unit tests (health)                                                                              | `tests/unit/agent/health/`                                                                                                                           |

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

| Risk                                                                                                                                                                                                                           | Mitigation                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| [Q-8](../plan/open-questions.md#q-8--what-do-magics-logs-actually-look-like-highest-technical-risk): real Magic log shape unknown                                                                                              | Synthetic corpus per spec 012 §3 subset; revisit after sanitised samples                                    |
| `AppLogFailure` misses an `[F]` line if its bucket already holds `maxSeriesPerBucket` series (admission is first-come; signature rules share this)                                                                             | Watch `cardinality_folded`; raise the cap or reserve budget for level and signature series if it ever trips |
| Python agent footprint unproven at load                                                                                                                                                                                        | Load test in spec 012 §5 once M1+M3 exist; ADR 0006 reversal conditions apply                               |
| CI is red on `main` until UBS-139 lands (anti-fabrication month check, Teams tests need `tzdata` on Windows, mypy platform errors); every PR shows red meanwhile                                                               | Merge UBS-139 first, then enable branch protection so `main` needs a green run                              |
| Day-1 acceptance proof is missing: no leak sentinel through the full pipeline (UBS-137), no 5-second visibility plus rotation/outage/restart run (UBS-140), no CPU/RSS load test (UBS-144), no real Teams tenant run (UBS-142) | Sprint 6; the coverage report shows `FR-TST-*`, `NFR-PERF-*` and `FR-LOG-*` as uncited until then           |
| Open correctness bugs: `AgentHeartbeatMissing` fires once per agent (UBS-136), reject summary mixes denominators (UBS-141); `AppLogFailure` bucket-budget miss above is UBS-145                                                | Sprint 6 bug tickets                                                                                        |
| Alert push and API security are still in review (UBS-120 Teams notification, UBS-135 NL API security); Day-2 host monitor and process liveness (UBS-129, UBS-130) too                                                          | Review and merge; until then those paths are not on `main`                                                  |
| Requirement coverage is by citation only; 173 of 286 requirement IDs had no citing test on 2026-11-08                                                                                                                          | Cite IDs in tests that already cover them; the CI report keeps the list visible                             |
