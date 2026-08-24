# Open Questions and Decisions Required

Status: Live document · Last updated: 2026-07-31

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

## Resolved

*(none yet — record answers here with the date, the decision, and the specs updated)*
