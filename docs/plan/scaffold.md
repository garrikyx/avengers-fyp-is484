# Scaffold and Build Plan

Status: Draft · Owner: TBD · Last updated: 2026-09-07

This document defines the target repository layout and build order. See
[implementation-status.md](./implementation-status.md) for what exists today.

## 1. Target repository layout (Python monorepo — ADR 0006)

```
avengers-fyp-is484/
├── README.md
├── Makefile                       # parser-test, parser-demo, lint
├── pyproject.toml                 # uv workspace root
├── compose.yaml
│
├── apps/
│   ├── agent/                     # Telemetry Agent — ADR 0006
│   │   ├── pyproject.toml
│   │   ├── testdata/fix/          # synthetic FIX corpus (FR-TST-002)
│   │   └── src/telemetry_agent/
│   │       ├── main.py            # supervisor: monitors + pipeline + stages
│   │       ├── config.py
│   │       ├── logs/              # M1 log monitor
│   │       ├── pipeline/          # M1.5 bridge: bounded queues + parser worker pool (FR-PIP-*)
│   │       ├── parser/            # M2 FIX parser — UBS-40–42 implemented
│   │       ├── metrics/           # M3
│   │       ├── rules/             # M5
│   │       ├── callbacks/
│   │       ├── health/
│   │       └── publishing/
│   ├── backend/                   # FastAPI — ADR 0002
│   ├── teams/                     # M6 Teams integration
│   └── simulator/                 # synthetic log generator
│
├── packages/
│   └── telemetry_shared/          # shared Pydantic models (FR-ING-022 Day-1)
│
├── tests/
│   ├── unit/parser/               # FR-PRS-* requirement-ID tests
│   ├── integration/
│   └── e2e/
│
├── config/                        # agent.yaml, rules.yaml, anomaly.yaml
├── docs/                          # specs, ADRs, plan
└── deployment/
```

- `packages/telemetry_shared/` is the Day-1 shared schema home (`FR-ING-022`); a `/contracts`
  JSON Schema generator may be added later if needed.
- `apps/agent/src/telemetry_agent/parser/` implements the pluggable parser interface
  (`FR-PRS-030`); Day-2 binary parsers register here without pipeline changes.
- `apps/simulator/` replaces `tools/fixgen` as the synthetic log generator target.

## 2. Milestones

Each milestone lists its requirement IDs and an exit criterion that is demonstrable. Nothing is
"done" without the tests named in its exit criterion.

### M0 — Repository foundation

Scope: `Makefile`, linters (`ruff`, `mypy --strict`), CI workflow with the
blocking gates of spec 012 §8 wired up (initially passing trivially), `contracts/` skeleton with
the envelope and snapshot schemas plus `generate.sh`, `.cursor/rules`, example configs.

Exit: `make lint test` passes on an empty test suite in CI on Linux and Windows runners; the
requirement-coverage reporter runs and lists all IDs as uncovered.

Why first: the requirement-coverage gate and the leak-test gate are the two things that make the
rest of this plan self-enforcing. Adding them after the fact never happens.

### M1 — Log monitor and config (`FR-LOG-*`, `FR-CFG-*`, `NFR-CFG-*`)

Scope: config load/validate/defaults/`--check-config`; tail and interval modes; offset
checkpointing and state file; rotation, truncation, partial line, glob discovery; the rotation
harness of spec 012 §3.2.

Exit: the full log monitor harness passes on Linux and Windows; `--check-config` output matches
the defaults golden file (`NFR-CFG-004`); an agent run against synthetic log output reports
correct line counts and read lag with no parsing yet.

### M1.5 — Pipeline bridge (`FR-PIP-*`)

Scope: bounded line queue per file set with non-blocking monitor enqueue and drop-oldest;
shared parser worker pool (`ThreadPoolExecutor`); bounded event queue to aggregator stub;
queue depth and drop counters on heartbeat/metrics.

Exit: integration test feeds lines faster than parser workers can consume and asserts (a) the
monitor never blocks, (b) `pipeline.lines_dropped` increments only when the line queue is
full, (c) parser workers drain the backlog when input slows, (d) framed `ParseResult` objects
reach the event queue. Wires existing `parser/` modules into a live agent path for the first
time.

Why between M1 and M2 completion: the parser classify+frame code already exists; the bridge is
the missing connection and establishes backpressure before field extraction adds more CPU
load.

### M2 — FIX parser (`FR-PRS-*`)

Scope: classification, framing, delimiters, allowlist extraction, hashing, text normalisation,
enum mapping, timestamps, sequence gaps, parse error reasons, the parser registry, the corpus and
the fuzz target.

Exit: full corpus passes; fuzz target runs clean for 5 minutes; allocation profiling shows
minimal per-message growth (`NFR-PERF-004`); **the data-leak sentinel test (`FR-TST-005`) is
implemented and blocking from this milestone onward.**

Why the leak test lands here: the moment the parser can extract fields is the moment leakage
becomes possible. It must not be possible for a single commit to exist where extraction works and
the gate does not.

### M3 — Metrics aggregation (`FR-MET-*`)

Scope: 10s buckets, dimension sets, counters, histograms with fixed boundaries, gauges,
cardinality caps and folding, late-event handling, ClOrdID latency correlation with bounded LRU
and TTL, local retention.

Exit: property test proves bucket merge is associative and commutative; cardinality test proves
folding to `__other__` under a 5000-symbol input with memory held flat; latency correlation test
covers uncorrelated, implausible and evicted cases; 30-minute soak holds RSS under 150 MB
(`NFR-PERF-003`).

### M4 — Backend ingestion, store and query (`FR-ING-*`, `FR-QRY-*`)

Scope: FastAPI app, auth, strict validation, partial batch acceptance, `batchId` dedupe, bucket
merge, ring buffer plus rollups, memory shedding, query engine with filters/groupBy/topK/series,
KPIs with `minSampleSize`, approximate percentiles, `dataCompleteness`, alert store, agent
registry, `/healthz` `/readyz` `/metrics`, error shape.

Exit: contract tests pass both directions against `contracts/`; `null` vs `0` semantics test
passes (`FR-QRY-035`); agent → backend → query round-trip shows a reject burst within 5 seconds
(`NFR-PERF-002`); ingestion load test hits `NFR-PERF-007`.

At the end of M4 the system is genuinely useful: real metrics, queryable, end to end.

### M5 — Rules, alerts and callbacks (`FR-RUL-*`, `FR-CBK-*`)

Scope: five rule kinds, `for`/`resolveAfter` hysteresis, dedup keys and stable `alertId`,
state persistence across restart, renotification, silences, schedules, startup and dependent
suppression, alert storm cap; callback signing, retry/backoff, delivery tracking, `dryRun`;
`mock-magic` receiver verifying HMAC; the backend-owned `AgentHeartbeatMissing`.

Exit: oscillating-input test proves exactly one notification per occurrence; restart test proves
no duplicate notification (`FR-RUL-020`); mock Magic verifies every signature; backend-outage test
proves alerting and callbacks continue (`NFR-REL-003`).

### M6 — Natural language layer (`FR-NLQ-*`)

Scope: rule-first intent matcher, slot schema and validation, LLM structured-output fallback with
timeout, time expression resolution with timezone, template renderer, `/telemetry/nl/query` and
`/telemetry/nl/intents`, evaluation harness with ≥ 40 fixtures, generated OpenAPI reviewed for
Copilot plugin use.

Exit: intent accuracy ≥ 90% and slot exactness ≥ 80% on the fixture set; the anti-fabrication test
(`FR-TST-008`) passes; every fixture's `interpretedQuery` replayed against the metrics API returns
the same numbers as the prose.

### M7 — Operability and Day-1 hardening

Scope: systemd unit and Windows service, packaging and versioning, structured logging with
rate limiting, agent `/metrics`, derived health status with `statusReasons`, runbook verification,
load and chaos runs, dependency and secret scanning, `docker-compose` demo path.

Exit: the full acceptance scenario of spec 012 §7 passes unattended; every runbook in spec 011 §3
has been walked through against an injected fault; all `NFR-PERF-*` targets measured and recorded.

### Deferred to Day-2

Binary protocol parser behind the existing `Parser` interface; persistent metric store; historical
replay and forensics; anomaly detection and adaptive thresholds; central config distribution
(and with it, reconsidering ADR 0003); richer Teams workflows and dashboards.

## 3. Dependency order

```
M0 ──► M1 ──► M1.5 ──► M2 ──► M3 ──► M4 ──► M5 ──► M7
                             └────► M6 ──┘
```

M1.5 depends on M1 (monitor produces lines) and the existing parser stub (M2 partial). M6
depends only on M4's query engine, so the NL layer can be built in parallel with M5 once the
query API is stable. M2 must not be merged without the leak test. M7 needs M5 for the callback
runbooks.

## 4. Working agreement for implementation

1. **Spec before code.** If an implementation question is not answered by a spec, update the spec
   in the same pull request, or record an ADR if it is a decision rather than a detail.
2. **Reference requirement IDs** in commit messages, PR descriptions and test names. The coverage
   reporter is the check.
3. **One milestone, one branch, small PRs within it.** Each PR should leave `make parser-test` green.
4. **Never widen the field allowlist casually.** It requires an ADR (ADR 0004).
5. **Every new accumulating structure needs a cap and a drop counter** (`NFR-REL-009`), stated in
   the PR description.
6. **Provisional numbers stay marked provisional** until [Q-1](./open-questions.md) and
   [Q-5](./open-questions.md) are answered; do not quietly promote a guess to a default.

## 5. Next concrete tasks

See [implementation-status.md](./implementation-status.md) for current progress. In priority
order:

1. **M1 — Log monitor** — config loader, tail/interval readers, offset checkpointing, rotation
   harness (spec 012 §3.2). Use `apps/simulator/` for synthetic log output until `fixgen` exists.
2. **M1.5 — Pipeline bridge** — `pipeline/line_queue.py`, `pipeline/workers.py`, wire
   `logs/` → `parser/` with bounded queues per spec 002 §1.1 (`FR-PIP-*`). This is the
   critical integration point between I/O-bound reading and CPU-bound parsing.
3. **M0 CI** — Linux and Windows runners with requirement-coverage reporter reading IDs from
   `docs/specs/*.md`.
4. **M2 completion** — allowlist extraction (`FR-PRS-020`+), leak sentinel (`FR-TST-005`).

Before finishing the parser, get sanitised log samples
([Q-8](./open-questions.md#q-8--what-do-magics-logs-actually-look-like-highest-technical-risk)).
The log monitor is deliberately format-agnostic; the parser is not.
