# Open Questions and Decisions Required

Status: Live document · Last updated: 2026-09-27

Each question records why it matters, what the specs currently assume so work is not blocked,
and what has to change once it is answered. When a question is resolved, record the answer here,
update the affected specs, and add an ADR if the answer is a design decision rather than a value.

| ID | Question | Blocks | Status |
| --- | --- | --- | --- |
| Q-1 | Expected FIX throughput and peak log volume per instance | Performance targets, buffer sizing | Open |
| Q-2 | Callback protocol Magic will support | Callback dispatcher implementation | Open |
| Q-3 | Auth model for backend APIs and Copilot/Teams | Backend auth, Copilot registration | Open |
| Q-4 | Deployment topology | Packaging, config shape | Open — assumption is safe |
| Q-5 | Initial alert thresholds | Default rule set credibility | Open — provisional values in use |
| Q-6 | Mandatory query dimensions | Cardinality budget | Open — assumption is safe |
| Q-7 | Day-2 retention requirement | ADR 0005 reversal timing | Open — not needed for Day-1 |
| Q-8 | Log format and FIX version reality | Parser correctness | **Open — highest risk** |
| Q-9 | Trading hours and timezone per instance | Absence rules, `today` semantics | Open |
| Q-10 | Who receives alerts besides Magic | Notification design | Open |
| Q-11 | Scope of "Callback audit" under Integration Service | UBS-102, spec 008 §6/§7 shape | Open |
| Q-12 | Config/control push from backend to agent (thresholds, rules) | Day-1 vs Day-2 scope boundary | Open |
| Q-13 | Production deployment topology (local vs cloud, DB requirement) | Hosting plan, persistence design, FYP demo vs production target | **Open — raised 2026-09-23 sponsor call** |

---

## Q-1 — Expected FIX throughput and peak log volume per Magic instance

**Why it matters.** Nearly every provisional number depends on it: `NFR-PERF-001` (5 000
lines/sec), agent memory ceiling, `publish.bufferBytes` (and therefore how long a backend outage
is survivable), `maxSeriesPerBucket`, and backend capacity per replica.

**Current assumption.** 5 000 log lines/sec sustained per host, 20 000/sec peak, average line
250 bytes. Specs mark these provisional.

**What is needed.** Peak messages/sec per session and per instance, average and p99 log line
size, total daily log volume, and number of instances per host.

**On resolution.** Re-run the load test at the real figures; recompute the survivable outage
duration and state it in the runbook (spec 011 §3); adjust `NFR-PERF-001`, `NFR-PERF-003` and
`publish.bufferBytes`. If sustained throughput is above roughly 20 000 lines/sec per host, revisit
ADR 0003 (publish interval and transport).

---

## Q-2 — What callback protocol should Magic support for Day-1?

**Why it matters.** Determines the entire Callback Dispatcher: transport, auth, retry semantics,
and whether delivery is push or pull.

**Current assumption.** HTTPS POST with HMAC-SHA256 request signing, exponential backoff, 5
attempts, idempotency key (spec 005 §3). The dispatcher sits behind a `CallbackSink` interface so
another transport is an implementation, not a rewrite.

**What is needed from Magic's team.** Endpoint URL and path; auth scheme (shared secret HMAC,
mTLS, bearer token, or IP allowlist); expected payload contract and whether ours is acceptable;
acknowledgement semantics; idempotency and deduplication behaviour on their side; whether a
message queue is preferred over HTTP; whether resolution notifications are wanted or only firing.

**On resolution.** Confirm or replace spec 005 §3.3; if a queue is chosen, write an ADR and add a
second `CallbackSink` implementation. Until then, `callbacks.dryRun: true` allows everything else
to be validated.

---

## Q-3 — Which authentication and authorization model for backend APIs and Teams/Copilot access?

**Why it matters.** Agent identity spoofing would let anyone inject telemetry
(`FR-ING-002`); unauthenticated query access would expose trading activity aggregates.

**Current assumption.** Agents use bearer tokens or mTLS; users use Entra ID OAuth 2.0 with scope
`Telemetry.Read`; all access is read-only (`NFR-SEC-009`).

**What is needed.** Tenant and app registration ownership; whether mTLS is available for agents
and how certificates are issued and rotated; whether authorisation must be scoped per
`instanceId` or per team (this changes the query API, so it matters early); token lifetime and
rotation procedure; audit logging requirements.

**On resolution.** If per-instance authorisation is required, add a filter-injection layer to the
query engine and an ADR — retrofitting row-level authorisation later is expensive.

---

## Q-4 — Preferred deployment topology

**Why it matters.** Affects config shape, packaging and failure domains.

**Current assumption.** One agent per host, monitoring multiple instances via per-file-set
`instanceId` (spec 001 §4). The agent supports all three topologies, so this is a deployment
choice rather than a code choice.

**What is needed.** Whether trading hosts permit a shared observer process; whether per-instance
resource isolation is mandated; whether log files are host-local or on a share.

**Risk if wrong.** Low. This is the safest question to leave open.

---

## Q-5 — Which alert thresholds should be configured initially?

**Why it matters.** Wrong thresholds are the fastest way to make the system ignored. Too
sensitive and the alerts are noise; too loose and the system adds nothing.

**Current assumption.** The provisional set in spec 005 §1.2 — reject rate 5% over 5m, p95 ack
latency 500ms/2000ms, parse error rate 1%/25%, no log activity 5m.

**What is needed.** Normal and abnormal reject rates from historical experience; acceptable ack
latency for this venue set; which conditions genuinely warrant paging versus a dashboard.

**On resolution.** Update spec 005 §1.2 defaults. **Recommended approach:** run in
`callbacks.dryRun: true` for one to two weeks first, then set thresholds from the observed
distribution rather than from guesses. Note this explicitly in the M5 exit review.

---

## Q-6 — Which telemetry dimensions are mandatory for filtering and aggregation?

**Why it matters.** Dimensions drive the cardinality budget, and therefore memory in both
components (spec 004 §5). Adding a dimension later is easy; adding a high-cardinality one is not.

**Current assumption.** `application`, `instanceId`, `session`, `symbol` (capped at 200 with
top-N folding), `side`, `ordType`, `msgType`, `rejectReason`, `sessionRejectReason`.

**What is needed.** Confirmation that symbol-level drill-down is required (it is the main
cardinality risk); whether venue/exchange, trader/desk, or strategy dimensions are needed — noting
that trader and account identifiers conflict with ADR 0004 and would need their own ADR.

---

## Q-7 — What data retention approach is required for Day-2 historical analysis?

**Why it matters.** Determines when ADR 0005 is reversed and what replaces the in-memory store.

**Current assumption.** None needed for Day-1; 6h in-memory, 24h maximum.

**What is needed.** Required retention duration for derived metrics; whether alert history must be
retained for audit (this is the most likely near-term need and is a much smaller change than
metric persistence); any regulatory retention obligation. Note that raw log retention is out of
scope permanently unless ADR 0004 is revisited with a data-protection review.

---

## Q-8 — What do Magic's logs actually look like? *(highest technical risk)*

**Why it matters.** The parser is specified against assumptions about FIX version, delimiter,
line prefixes and multi-line behaviour. If those assumptions are wrong, the parser produces either
`unsupported_lines` or, worse, plausible but incorrect metrics. Every downstream number depends
on this being right.

**Current assumption.** FIX 4.2/4.4 tag=value, SOH or pipe delimited, one message per line,
possibly with a log framework prefix, in files that rotate daily or by size.

**What is needed.** Sanitised sample lines from each log file (`Application.log`, `Fix.log`,
`Order.log`, `Execution.log` per the architecture diagram); FIX version and dictionary, including
custom tags; which files contain FIX versus application text; the rotation scheme and naming; the
encoding; whether inbound and outbound messages are distinguishable and how; and whether any
custom tags carry the rejection reason instead of tags 103/58.

**On resolution.** Update spec 003 §§2, 6 and the corpus in spec 012 §3. **This should be answered
before M2 starts**, and ideally before M1. Obtaining samples requires a redaction agreement — do
not accept unredacted production lines.

---

## Q-9 — Trading hours, calendar and timezone per instance

**Why it matters.** Absence rules (`NoLogActivity`, `NoExecutions`) fire on quiet periods, so
without correct schedules they either page every evening or are switched off entirely. Also
determines what `today` means in NL queries (`FR-NLQ-013`).

**Current assumption.** `Asia/Singapore`, Monday–Friday, 08:30–17:30, one schedule for all
instances (spec 010 §1).

**What is needed.** Per-instance or per-venue trading sessions, timezone, holiday calendar source,
and whether pre-open and post-close activity is expected.

---

## Q-10 — Who receives alerts besides Magic?

**Why it matters.** The design pushes callbacks to Magic and exposes alerts via query. If humans
are expected to be paged directly, a notification channel is missing from Day-1 scope.

**Current assumption.** Magic's callback endpoint is the only push destination; humans discover
alerts through Teams or Copilot queries, or through Magic's own onward routing.

**What is needed.** Whether the telemetry system must notify a Teams channel, email, or a paging
tool directly; if so, who owns escalation policy and quiet hours. If direct paging is required,
add a second `CallbackSink` implementation and expand spec 005 §3.

---

## Q-11 — Scope of "Callback audit" under Integration Service

**Why it matters.** The client's own architecture diagram (`docs/assets/architecture-overview.png`)
labels "Callback audit" as part of the Integration Service box, alongside the Copilot/Teams
connector and other external integrations. Specs 006, 007 and 008 don't currently define this as
a requirement anywhere — there is no `FR-ID` for it. UBS-102 was created as a draft placeholder
story referencing this question rather than guessing at scope.

**Current assumption.** Alert query responses already carry a `delivery` block (status, attempts,
last attempt time, `correlationId` — spec 007 §4.1). The open part is whether/how the Integration
Service is expected to additionally surface that delivery status through NL answers and Adaptive
Cards (a UX/audit feature), versus this being satisfied entirely by the existing alert API and
needing no NL/Teams-specific work at all.

**What is needed.** Confirm with the client whether "callback audit" means (a) nothing beyond the
existing per-alert `delivery` block already in spec 007, (b) a dedicated audit view/report
surfaced through Copilot/Teams, or (c) a separate audit log/export feature. Whichever it is,
give it an `FR-ID` in spec 008 (or a new spec) before committing an estimate.

**On resolution.** Update spec 008 with the relevant `FR-NLQ-*` (or new) requirements; replace
UBS-102's draft AC with the confirmed shape; remove the "needs spec clarification" note from that
ticket.

---

## Q-12 — Config/control push from backend to agent (thresholds, rules)

**Why it matters.** The client's architecture diagram shows a dashed "Config / Control
(Thresholds, Rules, etc.)" line running from the backend's Stream Processor box back to the
agent's Parser Engine. This reads as centralized configuration distribution — the backend pushing
threshold/rule changes down to agents at runtime. `docs/plan/scaffold.md` explicitly defers this:
central config distribution is called out as Day-2 scope, with Day-1 agents reading their
thresholds and rules from local config (`config/rules.yaml` and friends) only. This is a direct
Day-1/Day-2 discrepancy between what the client's own diagram depicts and what the team's spec
and milestone plan commit to building first.

**Current assumption.** No backend-to-agent config push exists in any Day-1 spec (001, 002, 003,
005, 006) or in any Jira epic created so far. Agents remain fully local-config-driven through M7.

**What is needed.** Confirm with the client (or by re-reading the requirements docx's Day-1/Day-2
roadmap table, which does not mention this explicitly either) whether the dashed line in the
diagram is: (a) aspirational/Day-2 and safe to leave out of Day-1 scope entirely, (b) a
misunderstanding of the diagram (e.g. it actually represents the agent's own local config file,
not a backend push), or (c) an actual Day-1 requirement that was missed. Do not build a
config-push mechanism speculatively based on the diagram alone.

**On resolution.** If confirmed Day-2 (most likely, per scaffold.md): add an explicit note to
spec 001 §1's diagram caption saying so, so future readers don't assume it's implemented. If
confirmed Day-1: this needs its own epic (agent-side config-fetch/apply, backend-side
config-distribution API) and is a scope addition, not something already covered by the epics
created in this pass.

---

## Q-13 — Production deployment topology (local vs cloud, DB requirement)

**Why it matters.** The team planned a sprint to "host everything to cloud" because no UBS
server is available for FYP development. In the 2026-09-23 sponsor call, Avinash clarified
that cloud is acceptable for test/demo purposes, but **actual client data in production
cannot sit on public cloud** due to sensitive/shared information; **local is preferable**,
with local filesystem or MongoDB/Postgres on a **local/on-prem server** acceptable. This
question separates three things that are easy to conflate: (1) where the **backend service
runs**, (2) whether **derived telemetry** (not raw logs) may be stored centrally, and (3)
whether a **database** is required at all. It also resolves tension between the formal Day-1
design ([ADR 0005](../adr/0005-in-memory-metric-store.md): in-memory ring buffer, no DB) and
stale README/scaffold language that mentions Redis (Day-1) and PostgreSQL (Day-2).

**Current assumption.**

- **Agent:** colocated on the Magic host; read-only log access; never persists or transmits
  raw log content ([ADR 0004](../adr/0004-no-raw-log-persistence.md)).
- **Backend Day-1:** process-local in-memory metric and alert stores, 6h default retention
  (24h max); no database deployed ([ADR 0005](../adr/0005-in-memory-metric-store.md)).
- **FYP/demo:** student-managed cloud or local Docker is acceptable with simulator data only.
- **Production (provisional, from sponsor call):** backend on local/on-prem server; optional
  local MongoDB or Postgres if persistence is needed; public cloud not for client data.

**What is needed from the sponsor.**

1. Confirm the **production target topology**: agent on Magic host + backend on
   **UBS/on-prem local server** (not public cloud)?
2. Confirm whether **public cloud is FYP/demo-only** — i.e. we should not treat cloud
   hosting as the final production architecture.
3. Confirm whether **in-memory backend retention (6–24h)** is acceptable for Day-1/FYP
   delivery, or whether a **local MongoDB/Postgres** is **required** for derived metrics
   and/or alert history.
4. If a local DB is required: **MongoDB vs Postgres preference**, and what must be
   persisted (metrics, alert history, agent registry/audit)?
5. Clarify whether the "no cloud" rule applies to **derived aggregates** (reject rates,
   session metrics, hashed identifiers) or only to raw/sensitive log content — our design
   already excludes raw logs everywhere.
6. Will UBS provide a **local VM/server** for integration/UAT, or should the team
   self-host locally until handover?
7. Is a **single backend instance** acceptable for production/UAT initially, or is
   multi-replica HA/failover in scope for FYP delivery?

**On resolution.**

- Update spec 001 §§3–5 (technology stack, deployment topology, scaling) with the confirmed
  production profile (`fyp-local`, `fyp-cloud-demo`, `ubs-onprem`, etc.).
- If local DB is required: add an ADR reversing or extending ADR 0005 (scope: derived data
  only; no raw logs; local/on-prem placement).
- If cloud is FYP-only: remove or deprioritise "cloud hosting sprint" work; align M7
  `docker-compose` demo path to the production-local model.
- Reconcile stale README/compose Redis/Postgres language with the decided storage model.
- If single-server is confirmed: document that scatter-gather / consistent-hash routing
  (spec 006 `NFR-SCA-003`/`004`) is deferred until HA is required.

**Related:** [Q-4](#q-4--preferred-deployment-topology) (agent placement),
[Q-7](#q-7--what-data-retention-approach-is-required-for-day-2-historical-analysis)
(retention drives DB need). Sponsor email draft:
[sponsor-email-deployment-clarifications.md](./sponsor-email-deployment-clarifications.md).

---

## Resolved


*(none yet — record answers here with the date, the decision, and the specs updated)*
