# Implementation Status

Status: Live document · Last updated: 2026-09-07

Specs state the target; this document states what exists. Where the two differ, the difference
is recorded here rather than by quietly editing the spec.

## Milestones

| Milestone | Scope | Status |
| --- | --- | --- |
| M0 | Repository foundation, CI gates, shared models | Partial — uv workspace, Makefile, `packages/telemetry_shared/` exist; CI and requirement-coverage reporter do not |
| M1 | Log monitor and configuration | **Not started** — `apps/agent/src/telemetry_agent/logs/` is stub only |
| **M2** | **FIX parser (UBS-40–42)** | **Partial** — plugin interface, classification, framing implemented; field extraction (UBS-43+) not started |
| **M3** | **Metrics aggregation** | **Partial** — aggregator, counters, correlation, and calculated indicators/snapshot output (MA-01–04) implemented and tested; blocked on real events by M1 (Log Monitor) and field extraction (UBS-43+) |
| M4 | Backend ingestion, store, query | Not started |
| **M5** | **Rules, alerts, callbacks** | **Partial** — Rule Engine and alert lifecycle (RE-01–04) implemented and tested; callback dispatch (HTTP/HMAC) not started |
| M6 | Natural language layer | Not started |
| M7 | Operability hardening | Not started |

## M2 requirement coverage (UBS-40–42)

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| UBS-40 | Parser plugin interface and registry | `FR-PRS-030`–`032`, `FR-PRS-003` | Done | `tests/unit/agent/parser/test_FR_PRS_030_registry.py` |
| UBS-41 | Classify log lines before FIX parsing | `FR-PRS-010`, `FR-PRS-011` | Done | `tests/unit/agent/parser/test_FR_PRS_010_classify.py` |
| UBS-42 | Frame FIX messages from log lines | `FR-PRS-012`–`016` | Done | `tests/unit/agent/parser/test_FR_PRS_012_frame.py`, `apps/agent/testdata/fix/` |

### Deferred within M2 (UBS-43+)

| Area | Requirements | Notes |
| --- | --- | --- |
| Field allowlist extraction | `FR-PRS-020` | Compile-time allowlist table — next story |
| Hashing and enums | `FR-PRS-021`–`024` | Security-critical emission rules |
| Timestamps and seq gaps | `FR-PRS-025`–`027` | Needed before metrics bucketing |
| Leak sentinel | `FR-TST-005` | Lands with allowlist extraction |
| Full spec 012 §3 corpus | `FR-TST-002` | Subset corpus exists for framing; lifecycle/reject paths pending |

## M3 requirement coverage (MA-01–04)

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| MA-01 | Bucketed counter/histogram store | `FR-MET-024`–`030` | Done | `test_MA_01_aggregator.py` |
| MA-02 | Order/execution/reject counters | spec 004 §4.1 | Done | `test_MA_02_counters.py` |
| MA-03 | Order correlation and latency | spec 004 §4.4 | Done | `test_MA_03_correlation.py`, `test_histogram.py` |
| MA-04 | Calculated indicators and snapshot output | `FR-QRY-007`, `FR-QRY-010`, `FR-QRY-012` | Done | `test_MA_04_snapshot.py` |

Full detail and an alert-readiness mapping: `docs/plan/ma-epic-implementation-summary.md`.
Not yet wired: real events into MA-01–04 depend on M1 (Log Monitor) and field
extraction (UBS-43+); `parseErrorRate` is formula-ready but has no producer yet.

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
(so their self-health rules have no data), `config/rules.yaml` YAML
loading/SIGHUP reload.

## Code locations

| Component | Path |
| --- | --- |
| Parser protocol + registry | `apps/agent/src/telemetry_agent/parser/protocol.py`, `registry.py` |
| FIX classification | `apps/agent/src/telemetry_agent/parser/fix/classify.py` |
| FIX framing | `apps/agent/src/telemetry_agent/parser/fix/frame.py` |
| FIX parser plugin | `apps/agent/src/telemetry_agent/parser/fix/parser.py` |
| Demo CLI | `apps/agent/src/telemetry_agent/parser/cli.py` |
| Synthetic corpus | `apps/agent/testdata/fix/` |
| Unit tests (parser) | `tests/unit/agent/parser/` |
| Metrics aggregator, counters, correlation, histogram | `apps/agent/src/telemetry_agent/metrics/` |
| Calculated indicators and snapshot output | `apps/agent/src/telemetry_agent/metrics/snapshot.py` |
| Shared snapshot contract | `packages/telemetry_shared/src/telemetry_shared/models/metrics.py` |
| Unit tests (metrics) | `tests/unit/agent/metrics/` |
| Rule types, FSM, default rules | `apps/agent/src/telemetry_agent/rules/` |
| Shared alert contract | `packages/telemetry_shared/src/telemetry_shared/models/alerts.py` |
| Unit tests (rules) | `tests/unit/agent/rules/` |
| Unit tests (shared models) | `tests/unit/telemetry_shared/` |
| Cross-component integration tests | `tests/integration/agent/` |

## How to verify

```bash
uv sync                  # or: make sync
make parser-test         # 29 UBS-40–42 unit tests
make parser-demo         # corpus walk — expect framed > 0, errors = 0 on valid fixtures
make lint                # ruff + mypy on agent source
```

Expected demo output (approximate):

```
pipe_delimited.txt: classification=fix framed=true msgType=D
split_message.txt: classification=fix framed=true msgType=D (joined 2 lines)
SUMMARY: N lines | fix=X unsupported=Y framed=Z errors=0
```

## Open risks

| Risk | Mitigation |
| --- | --- |
| [Q-8](../plan/open-questions.md#q-8--what-do-magics-logs-actually-look-like-highest-technical-risk): real Magic log shape unknown | Synthetic corpus per spec 012 §3 subset; revisit after sanitised samples |
| Python agent footprint unproven at load | Load test in spec 012 §5 once M1+M3 exist; ADR 0006 reversal conditions apply |
