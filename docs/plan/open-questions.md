# Open Questions and Decisions Required

Status: Reconciled with team decisions · Last updated: 2026-10-16

This document distinguishes **settled Day-1 POC scope** from **unconfirmed production
inputs** and **deferred Day-2 decisions**. A POC decision is a team decision, not evidence
of sponsor approval or production compatibility. Resolved scope does not mean implemented
or tested. The original requirements document leaves the authentication model open;
custom backend authentication is not a POC acceptance requirement.

| ID | Question | POC status | Remaining work outside the settled POC scope |
| --- | --- | --- | --- |
| Q-1 | Throughput and log volume | Resolved — synthetic benchmark | Measure production workload before capacity sign-off |
| Q-2 | Magic callback contract | Resolved — mock endpoint | Agree real Magic transport, credentials and acknowledgement contract |
| Q-3 | Authentication and authorisation | Resolved — custom backend auth deferred | Teams/Copilot platform setup is required for the demo; production backend identity/access policy remains open |
| Q-4 | Agent deployment topology | Resolved — co-located, one agent per host | Validate real host access and isolation constraints |
| Q-5 | Initial alert thresholds | Resolved — confirmed tiers plus configurable provisional defaults | Calibrate remaining thresholds for production |
| Q-6 | Query dimensions | Resolved — current spec 004 catalogue | Extra dimensions require an explicit scope change |
| Q-7 | Historical retention | Deferred — Day-2 | Decide retention, durability and store before historical reporting |
| Q-8 | Parser/log formats | Resolved — simulator acceptance and extensible parsers | Validate additional production formats before onboarding |
| Q-9 | Trading calendar | Resolved — demo schedule only | Obtain production schedules/timezones/holidays |
| Q-10 | Human notifications | Resolved — real Teams chat demo | Production routing, quiet hours and escalation remain unconfirmed |
| Q-11 | Callback audit | Resolved — per-alert delivery details | Durable audit/export is separate future scope |
| Q-12 | Central config/control | Deferred — Day-2; local config for Day-1 | Specify distribution only if commissioned |
| Q-13 | Hosting and persistence | Resolved — local Day-1 server, no DB | Day-2 cloud requires client-info masking; production infrastructure/access and HA remain unconfirmed |

## Q-1 — Throughput and log volume

**Decision (team, 2026-10-16).** Use 5,000 lines/sec sustained and 20,000 lines/sec peak
per host as synthetic POC load targets. These are acceptance benchmarks, not measurements
of Magic. The existing 250-byte average line size is a sizing assumption, not a confirmed
production value. Record test hardware, line sizes and achieved rates in the load report.

**Production follow-up.** Measure sustained/peak rates, average/p99 line size, daily volume
and instances per host. Recompute buffer/outage capacity and resource limits before
production capacity sign-off. References: spec 009 §1, spec 012 §5, spec 011 §3.

## Q-2 — Magic callback contract

**Decision (team, 2026-10-16).** A mock Magic endpoint is sufficient for POC acceptance.
Exercise the existing signed HTTP callback contract, retry, idempotency and firing/resolved
handling against that mock. The configurable `CallbackSink` remains the transport seam.
No real Magic endpoint is required to complete the POC.

**Production follow-up.** Agree endpoint ownership, transport, authentication, payload,
acknowledgement/deduplication behaviour and resolution notifications with Magic's team.
The current HTTP/HMAC contract is not yet their confirmed production contract.
References: spec 005 §3, spec 012 POC acceptance.

## Q-3 — Authentication and authorisation

**Decision (team, 2026-10-16).** Custom telemetry-backend authentication, agent identity
binding and per-user Entra token enforcement are outside the local synthetic-data POC.
Separate ingestion/query bearer tokens are not an additional POC requirement.

**Teams/Copilot remains a real integration.** Keep the app registration, credentials and
incoming-message validation required by the selected Microsoft platform connection.
A user can ask in Teams, the adapter can call the local telemetry backend without custom
backend auth, and the adapter can render the result. Platform authentication and backend
authentication are separate. Connectivity to the local service must be demonstrated.

**Production follow-up.** Choose agent credentials/rotation, tenant/app ownership, and
application/instance read permissions. The team accepted restricted production visibility;
the exact grants and implementation remain unconfirmed. Backend request logs in the POC
must not claim an unverified identity is authenticated. Production requirements remain in
specs 006–009, with an explicit POC exception in spec 009 §3.3.

## Q-4 — Agent deployment topology

**Decision (team, 2026-10-16).** Default to one agent on each log host, with per-file-set
`instanceId` for multiple Magic instances. Day-1 reads host-local logs. Remote fetching is
a separate spike, not an already supported POC topology. Backend placement is Q-13.

**Production follow-up.** Validate host permissions, isolation requirements and real file
paths. Sponsor permission to explore remote reading does not waive ADR 0004's prohibition
on transmitting raw logs. References: spec 001 §4, spec 002 §2.

## Q-5 — Initial alert thresholds

**Decision (team, 2026-10-16).** Keep the client-confirmed warning/critical tiers:

- reject rate: >3% / >5%;
- p95 acknowledgement latency: >500 ms / >1,000 ms;
- parse error rate: >1% / >25%.

Use the remaining spec 005 §1.2 values as configurable, provisional demo defaults.
`NoLogActivity` is 60 seconds within the configured schedule, not the stale five-minute
value. Host, application and other unconfirmed thresholds need production calibration;
they are not all sponsor-approved. Do not add automatic paging to the POC.

## Q-6 — Mandatory query dimensions

**Decision (team, 2026-10-16).** Use the current spec 004 §5 catalogue and its per-metric
allowlists/caps: `application`, `instanceId`, `session`, `symbol`, `side`, `ordType`,
`msgType`, `rejectReason`, `sessionRejectReason`, `reason`, `severity`, `level`, `mount`,
`component`, and `errorSignature`. Symbol drilldown is already an intent in spec 008.
Do not add desk/trader/strategy dimensions without a new explicit requirement and any
necessary data-minimisation review. This settles POC scope, not future production needs.

## Q-7 — Historical retention

**Decision (team, 2026-10-16).** Day-1 uses bounded in-memory stores, 6h default and 24h
maximum, with restart loss reported. No durable telemetry database is required for the
POC (ADR 0005). Historical business reporting and end-of-day summaries are Day-2 and
are not final Day-1 POC acceptance criteria.

**Day-2 follow-up.** End-of-day totals, alert summaries and previous-trading-day comparison
are specified in `FR-NLQ-028`. Decide retention duration, restart durability, alert history
and storage technology before implementation. Weekends/holidays mean a previous trading
day cannot be assumed to fit inside a 24h window. Retain only approved derived/sanitised
telemetry; raw-log retention remains prohibited. Cloud placement also depends on Q-13.

## Q-8 — Parser/log formats

**Decision (team, 2026-10-16).** The parser is a configurable module, selected per file
set, with a shared interface and registry so other text or binary formats can be added
without changing the pipeline (`FR-PRS-030`–`032`). POC FIX telemetry uses the simulator's
FIX records; its Application.log records remain the application-health input.

The team confirms the simulator format is based on sponsor samples, extended with
synthetic examples. Its verified application level set is `NWEIF`. The extra-critical-level
interpretation is withdrawn; UBS-127 was withdrawn and UBS-128 narrowed to F-level alerts.
Spec 004 `FR-MET-033` retains E/F error counting and a five-value `level` dimension.

**Production follow-up.** Validate additional files, FIX versions/dictionaries/custom tags,
direction markers, encoding and rotation before onboarding. Simulator compatibility is
POC acceptance, not proof of full production compatibility. References: specs 003, 004,
005 and apps/simulator/log_specifications.md.

## Q-9 — Trading hours, calendar and timezones

**Decision (team, 2026-10-16).** Singapore weekdays 08:30–17:30 are a demo schedule only.
Production inactivity alerts require explicitly configured, verified schedules and
holiday calendars. The schedule configuration example does not prove runtime gating;
calendar enforcement must be verified before claiming schedule-aware alerting works.

NL relative dates use the user's timezone from Teams (default `Asia/Singapore`), which
is separate from an instance's trading calendar (`FR-NLQ-012`–`014`).

**Production follow-up.** Obtain per-instance/venue trading sessions, timezones, holidays,
and pre-open/post-close activity expectations. References: specs 005 and 010.

## Q-10 — Human alert notifications

**Decision (team, 2026-10-16, following sponsor request).** Day-1 demonstrates real queries
and firing/resolved notifications in one configurable, team-controlled Teams group chat.
Only the Magic callback endpoint is mocked. No automated email/pager escalation,
per-team routing or quiet-hours policy is required for the POC. The chat and platform
credentials are setup inputs, not unresolved feature scope.

**Production follow-up.** Agree recipients/routing, quiet hours and escalation ownership.
References: spec 000 §3.1, spec 008 §6, UBS-120.

## Q-11 — Callback audit

**Decision (team, 2026-10-16).** Show the existing per-alert `delivery` data in the technical
Teams/Copilot alert detail view: status, attempts, last attempt time and `correlationId`.
Read it through backend APIs; do not invent success when the data is absent. This is a
visibility feature, not a new durable audit store or export. Spec 008 `FR-NLQ-029` defines
the scope for UBS-102; spec 007 §4.1 defines the existing payload.

**Future follow-up.** Durable attempt history/export requires a separate retention and
storage decision under Q-7.

## Q-12 — Config/control distribution

**Decision (team, 2026-10-16).** Day-1 uses local configuration and the specified reload
mechanism. Backend-to-agent central configuration push is deferred to Day-2. The dashed
control line in the client diagram is not a Day-1 implementation commitment. Configurable
Day-2 remediation hooks are a separate feature and do not imply config distribution.
References: spec 001 §1, spec 010, ADR 0003 and ADR 0008.

## Q-13 — Hosting and persistence

**Decision (team, 2026-10-16).** Day-1 deploys on a local server, with the co-located agent
from Q-4 and bounded in-memory backend storage from Q-7. Cloud deployment is Day-2;
client information must be masked before any cloud upload. Raw Magic logs/full FIX
payloads still cannot leave the host or be uploaded (ADR 0004). Masking is a requirement
for approved derived telemetry, not permission to upload raw logs.

**Still unconfirmed.** Local server ownership/access, availability of a UBS integration/UAT
host, production HA/failover requirements, and the exact masking policy for Day-2 cloud.
The earlier single-backend recommendation was not explicitly confirmed when the team
corrected the hosting choice; do not mark production HA requirements resolved.
No database vendor is selected by this decision. Preserve scalable interfaces and query
completeness requirements; do not silently remove existing multi-replica behaviour.
References: spec 001 §4–5, spec 009 §3.1 and ADR 0005.

## Source evidence and decision history

### 2026-10-16 sponsor call (Avinash Gopal)


- **Q-10 (sponsor evidence; POC policy settled below):** People must be notified, not only Magic. Push events reach end
  users "in the group chat" through Copilot/Teams. This is UBS-120 (Teams notification),
  raised to High. The team subsequently chose no automated escalation or quiet-hours
  policy for the POC. Updated: spec 000 §3.1.
- **Q-8 (corrected by the team on 2026-10-16):** The simulator's sponsor-format samples
  use `NWEIF`. The earlier extra-critical-level interpretation is withdrawn. Spec 004
  `FR-MET-033` keeps E/F error counting and a five-value `level` dimension; spec 005 keeps
  `AppLogFailure`. The parser stays extensible; POC acceptance uses the simulator format.
- **Q-13 (sponsor evidence; deployment decision settled below):** The telemetry server may run remotely and connect to the log
  host, or co-located "if it is within the metrics, not consuming more memory". Day-1 keeps
  the agent co-located; remote fetching is a spike. Updated: spec 002 §2.
- **New scope from the same call:**
  - host/system events (disk, memory, Magic process): spec 002 §7.1, spec 005 §1.2;
  - an MCP server for M365 Copilot: ADR 0007, spec 008 `FR-NLQ-026`;
  - technical vs executive answers by audience: spec 008 `FR-NLQ-027`;
  - end-of-day business summaries: `FR-NLQ-028`, Day-2;
  - configurable action hooks: ADR 0008, spec 005 §5, Day-2.

### 2026-10-16 team scope review

The decisions in Q-1–Q-13 above reconcile the subsequent team discussion. In particular,
they supersede the previous "Magic only" notification assumption, all-provisional
threshold wording, blanket POC Entra/backend-auth requirements, and cloud-first Day-1
hosting questions. The source DOCX remains unmodified. Open production details must not
be reintroduced as blockers to the agreed synthetic-data POC.
