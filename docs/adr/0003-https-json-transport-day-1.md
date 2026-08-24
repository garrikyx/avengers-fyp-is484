# ADR 0003 — Agent → backend transport is HTTPS/JSON batches on Day-1

Status: Accepted · Date: 2026-07-31 · Deciders: TBD

## Context

The original design sketch shows "HTTPS / gRPC" between agent and backend. A choice is needed
for Day-1. The traffic profile is:

- One batch per agent every 10 seconds (`FR-PUB-001`), not a per-message stream.
- Batch size dominated by metric snapshots, which are small and highly compressible.
- Traffic crosses from a trading host to central infrastructure, likely through corporate
  network controls.

At 50 agents and 10-second batching, this is roughly 5 requests/sec in aggregate. Transport
efficiency is not the constraint; operability is.

## Decision

Day-1 uses **HTTPS/1.1 with JSON bodies, gzip-compressed above 4 KiB**, batched every 10
seconds, behind a `Publisher` interface. **gRPC is deferred**, not rejected.

## Rationale

- **Batching already solved the efficiency problem.** Per-message streaming would make protocol
  efficiency matter; a 10-second snapshot batch makes it irrelevant. Derived metrics are orders
  of magnitude smaller than the log volume they summarise.
- **Operability on a locked-down host.** HTTPS traverses corporate proxies, TLS-inspecting
  middleboxes and firewall policies that gRPC/HTTP2 frequently does not. Debugging with `curl`
  and a request log matters during a production incident at 4am.
- **Debuggability of the contract.** A JSON batch can be read by a human, replayed by hand,
  captured in a bug report (after redaction), and validated against a JSON Schema shared by
  both languages (`FR-ING-022`).
- **Idempotency, not streaming, is what reliability needs here.** `batchId` deduplication
  (`FR-PUB-003`, `FR-ING-004`) plus delta counters (`FR-MET-024`) give safe retries. A
  streaming transport would add reconnection and partial-batch semantics without removing the
  need for idempotency.

## Consequences

- JSON is 3–5× larger than protobuf on the wire; gzip recovers most of it, and the absolute
  volume is small. Bandwidth is accepted as a non-issue at Day-1 scale.
- Publishing MUST go through an interface (`Publisher`) so gRPC is a swap, not a rewrite. The
  `/contracts` schemas MUST stay transport-neutral for the same reason.
- No server push. The backend cannot send configuration or commands to the agent over this
  path. That is a deliberate simplification for Day-1: config is local and reloaded by SIGHUP
  (`NFR-CFG-003`). Central config distribution is a Day-2 discussion, and if it is adopted it
  is a strong argument for gRPC.
- HTTP status codes carry the retry semantics (spec 007 §2.1), so the agent's retry logic is
  driven by a small, testable table.

## Reversal conditions

Move to gRPC (or HTTP/2 streaming) if any of: agents must publish more often than every 2
seconds; per-message events become necessary (Day-2 binary protocols with high event value);
central push configuration or backend→agent commands are adopted; or aggregate ingestion
bandwidth exceeds the network budget agreed in [Q-1](../plan/open-questions.md).
