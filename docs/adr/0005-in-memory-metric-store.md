# ADR 0005 — Backend metric store is in-memory time buckets, no database on Day-1

Status: Accepted · Date: 2026-07-31 · Deciders: TBD

## Context

The backend must answer queries over a recent window ("last 30 minutes", "today") with
filtering, grouping and approximate percentiles. Day-1 explicitly excludes historical
forensics and long-term retention. The brief calls for in-memory metric views and states that
raw log persistence is not required for Day-1 operation.

Options: an in-memory bucket store; an embedded time-series database; Prometheus or
VictoriaMetrics; a general-purpose database (PostgreSQL / TimescaleDB); a hosted
observability product.

## Decision

Day-1 uses a **process-local ring buffer of 10-second buckets** per instance, with pre-rolled
1-minute and 5-minute rollups, retaining `retentionWindow` (default 6h, max 24h). No database
is deployed. State is lost on restart, by design.

## Rationale

- **Retention required is hours, not months.** Every query the Day-1 intent catalogue supports
  (spec 008 §2) fits inside the retention window. Deploying a database to serve a 6-hour window
  adds an operational dependency that buys nothing Day-1 needs.
- **The data volume is small.** Derived series per instance per bucket are capped at 2000
  (`FR-MET-030`); at 10-second buckets over 6 hours that is a bounded, computable footprint
  (`NFR-SCA-006` requires it be documented as bytes-per-series-per-bucket).
- **Query shape is fixed and simple.** Filter, group by up to 3 dimensions, sum counters, merge
  histograms. This is a few hundred lines of well-tested code, not a query planner.
- **Delta counters make merging trivial and idempotent** (`FR-MET-024`), so there is no
  read-modify-write correctness problem that a transactional store would solve.
- **Alerting does not depend on it.** Rules run in the agent (spec 005), so losing the store
  loses queryability, not protection. This is what makes the "restart loses everything"
  trade-off tolerable.

Why not Prometheus specifically: it is a good fit for the metric shape, but it would push
`rejectReason`, `symbol` and `session` into label cardinality that needs careful management
anyway, would still require a separate path for events and alert state, and would add an
external dependency to the Day-1 deployment. It is the leading candidate for Day-2 (see
reversal conditions) once retention beyond hours is actually required.

## Consequences

- **A restart empties the store.** Mitigated by `/readyz` reporting `warming` for
  `warmupWindow` (`FR-QRY-005`) so an empty store is never read as "zero activity", and by
  agents' 1-hour local retention (`FR-MET-002`) which lets recent buckets be republished.
- **Replica state is not shared.** This is the significant cost. Query correctness across
  replicas requires either scatter-gather (`NFR-SCA-003`) or consistent-hash routing on
  `instanceId` (`NFR-SCA-004`). Both are specified; `fanout` is the default because it does not
  depend on load balancer capabilities.
- **Memory is the hard limit, so shedding is mandatory.** `FR-QRY-003` requires warning at 75%
  and shedding the oldest tier at 90% rather than being OOM-killed, and shedding must be visible
  through `dataCompleteness`.
- **Percentiles are approximate**, interpolated from fixed histogram buckets, and must be
  labelled as such (`FR-QRY-012`). Exact percentiles would require retaining samples, which
  contradicts both the memory bound and the data-minimisation posture of ADR 0004.
- **No ad-hoc historical analysis.** Anything beyond the retention window does not exist. This
  is the single most likely source of Day-2 pressure.

## Reversal conditions

Introduce a persistent store when any of these becomes true: retention beyond 24 hours is
required; day-over-day comparison (`compare_period` beyond the window) is needed operationally;
restart-induced blind spots become unacceptable; or replica fan-out proves too slow at scale.
The natural progression is Prometheus/VictoriaMetrics for metrics plus a small relational store
for alert history — and critically, that change affects only the store and query engine, not
the agent, the wire contract, or the API surface, provided `FR-QRY-006`–`FR-QRY-015` are honoured
by the replacement.
