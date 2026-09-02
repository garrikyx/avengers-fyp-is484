# Implementation Status

Status: Live document · Last updated: 2026-08-31

Specs state the target; this document states what exists. Where the two differ, the difference
is recorded here rather than by quietly editing the spec.

## Milestones

| Milestone | Scope | Status |
| --- | --- | --- |
| M0 | Repository foundation, CI gates, shared models | Partial — uv workspace, Makefile, `packages/telemetry_shared/` exist; CI and requirement-coverage reporter do not |
| M1 | Log monitor and configuration | **Not started** — `apps/agent/src/telemetry_agent/logs/` is stub only |
| **M2** | **FIX parser (UBS-40–42)** | **Partial** — plugin interface, classification, framing implemented; field extraction (UBS-43+) not started |
| M3 | Metrics aggregation | Not started |
| M4 | Backend ingestion, store, query | Not started |
| M5 | Rules, alerts, callbacks | Not started |
| M6 | Natural language layer | Not started |
| M7 | Operability hardening | Not started |

## M2 requirement coverage (UBS-40–42)

| ID | Story | Requirement | Status | Verified by |
| --- | --- | --- | --- | --- |
| UBS-40 | Parser plugin interface and registry | `FR-PRS-030`–`032`, `FR-PRS-003` | Done | `tests/unit/parser/test_FR_PRS_030_registry.py` |
| UBS-41 | Classify log lines before FIX parsing | `FR-PRS-010`, `FR-PRS-011` | Done | `tests/unit/parser/test_FR_PRS_010_classify.py` |
| UBS-42 | Frame FIX messages from log lines | `FR-PRS-012`–`016` | Done | `tests/unit/parser/test_FR_PRS_012_frame.py`, `apps/agent/testdata/fix/` |

### Deferred within M2 (UBS-43+)

| Area | Requirements | Notes |
| --- | --- | --- |
| Field allowlist extraction | `FR-PRS-020` | Compile-time allowlist table — next story |
| Hashing and enums | `FR-PRS-021`–`024` | Security-critical emission rules |
| Timestamps and seq gaps | `FR-PRS-025`–`027` | Needed before metrics bucketing |
| Leak sentinel | `FR-TST-005` | Lands with allowlist extraction |
| Full spec 012 §3 corpus | `FR-TST-002` | Subset corpus exists for framing; lifecycle/reject paths pending |

## Code locations

| Component | Path |
| --- | --- |
| Parser protocol + registry | `apps/agent/src/telemetry_agent/parser/protocol.py`, `registry.py` |
| FIX classification | `apps/agent/src/telemetry_agent/parser/fix/classify.py` |
| FIX framing | `apps/agent/src/telemetry_agent/parser/fix/frame.py` |
| FIX parser plugin | `apps/agent/src/telemetry_agent/parser/fix/parser.py` |
| Demo CLI | `apps/agent/src/telemetry_agent/parser/cli.py` |
| Synthetic corpus | `apps/agent/testdata/fix/` |
| Unit tests | `tests/unit/parser/` |

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
