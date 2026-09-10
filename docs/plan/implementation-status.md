# Implementation Status

Status: Live document · Last updated: 2026-09-10

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
| **M4** | **Backend ingestion, store, query** | **Partial** — Stream Processor and Metric Store (window alignment, cross-agent merge semantics) implemented and tested; ingestion (auth/validation/dedupe), the agent's own Backend Publisher, and the query engine/HTTP layer are not started |
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

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| UBS-88 | Window alignment, staleness, and agent reconciliation | `FR-STM-001`, `FR-ING-005`, `FR-STM-005`, `FR-STM-006` | Done | `test_STM_01_window_alignment.py`, `test_STM_03_warmup.py` |
| UBS-88 | Cross-agent merge semantics (counters/ratios/histograms) | `FR-STM-002`–`004` | Done | `test_STM_02_merge_semantics.py` |

Full detail and known gaps: [`ma-epic-implementation-summary.md`](./ma-epic-implementation-summary.md)
§7. Not yet wired: nothing calls `StreamProcessor.process_snapshot()` with real
data — no agent Backend Publisher and no backend Ingestion Service or HTTP
layer exist yet (both separate, later work).

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
make lint                # ruff + mypy on agent source
```

## Open risks

| Risk | Mitigation |
| --- | --- |
| [Q-8](../plan/open-questions.md#q-8--what-do-magics-logs-actually-look-like-highest-technical-risk): real Magic log shape unknown | Synthetic corpus per spec 012 §3 subset; revisit after sanitised samples |
| Python agent footprint unproven at load | Load test in spec 012 §5 once M1+M3 exist; ADR 0006 reversal conditions apply |
