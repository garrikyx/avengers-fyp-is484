# ADR 0004 — Raw log content is never persisted or transmitted

Status: Accepted · Date: 2026-07-31 · Deciders: TBD

## Context

Magic's logs contain FIX traffic: client order identifiers, accounts, party identifiers,
prices and quantities. Centralising them would create a copy of sensitive trading data in a
new system with a new set of access paths, and would make the telemetry system's blast radius
far larger than its value. The requirement is explicit in the brief: "Raw sensitive log content
is not persisted as part of the core design."

The temptation to violate this is strong and specific: during an incident, someone will want to
see the actual line. Every "just this once" mechanism — a debug flag, a sampled raw event, a
truncated excerpt in an alert — reintroduces the risk, usually in the least reviewed code path.

## Decision

Raw log content MUST NOT be persisted to disk, transmitted off-host, or embedded in any event,
metric label, alert, error message, or log statement. The system transmits **only** derived
data: counters, histograms, and allowlisted field values, with identifiers hashed and free text
normalised to a bounded label set.

This is enforced by four mechanisms, not by policy alone:

1. **A compile-time field allowlist** (spec 003 §4, `FR-PRS-020`) — configuration cannot widen it.
2. **Identifier hashing** with an environment-provided HMAC key (`FR-PRS-021`).
3. **Text normalisation to a bounded label set**, never the normalised string itself
   (`FR-PRS-022`).
4. **A blocking CI sentinel test** (`FR-TST-005`) that proves no non-allowlisted value reaches
   any outbound payload, log, state file or metrics endpoint.

Additionally, `NFR-SEC-013` prohibits a raw-logging mode in release builds: it exists only
behind a build tag that CI asserts is absent from release artefacts.

## Consequences

**Accepted losses.** These are real and must be stated plainly rather than discovered later:

- No log replay, no historical forensics, no "show me the message" during an incident. The
  original log file on the host remains the only place to see it, with existing access controls.
- Root-cause analysis is limited to the dimensions and labels chosen in advance. A rejection
  reason that was never pattern-matched appears as `unclassified` and is only diagnosable by
  someone with host access reading the file.
- Adding a new rejection reason pattern is a config change that only affects **future** traffic;
  yesterday's `unclassified` rejects cannot be retroactively classified.
- Prices, quantities beyond aggregate volume, accounts and party identifiers are simply not
  available for analysis. `NFR-SEC-002` excludes them deliberately.
- Cross-day identifier correlation breaks when the hash key is rotated.

**Gains.** The system holds no sensitive data at rest anywhere, so its compliance surface,
access control requirements and breach impact are all bounded to derived aggregates. This is
what makes central aggregation acceptable at all.

**Design consequences.** Because there is no raw fallback, the derived data must be good enough
to be operationally useful on its own. That is why specs 004 and 011 insist on: every drop being
counted (`NFR-OBS-002`), `dataCompleteness` on every query (`FR-QRY-015`), `unclassified`
counting (`FR-PRS-022`), and `null` rather than `0` for missing data (`FR-QRY-035`). Without raw
logs to reconcile against, silent inaccuracy would be undetectable.

## Reversal conditions

Any change requires a new ADR and an explicit data-protection review, and would need to specify:
which fields, what retention, what encryption at rest, what access control, what audit logging,
and what deletion guarantee. Day-2 "persistence options" in the roadmap refer to **derived
metric** persistence, not raw logs — that is a different and much smaller decision.

Adding a single field to the allowlist (for example tag 44, Price) also requires an ADR, because
the allowlist is the entire boundary.
