# ADR 0001 — Telemetry Agent is written in Go

Status: Accepted · Date: 2026-07-31 · Deciders: TBD

## Context

The agent runs on a production trading host, next to the Magic process. Its constraints are
unusually strict for a monitoring component:

- It must not compete with Magic for CPU, and must have a hard, predictable memory ceiling.
- It must be deployable without installing a runtime, a package manager, or dependencies onto
  a locked-down host.
- It must run on both Linux and Windows, since Magic deployments may be either.
- It must handle file tailing, rotation and per-file concurrency, which is fiddly and
  platform-specific.
- It must never be the reason a trading host has a problem, which argues for a small, boring,
  statically linked artefact.

Candidates considered: Go, Rust, Python, .NET, C++.

## Decision

The Telemetry Agent is written in **Go 1.23+**, built with `CGO_ENABLED=0` into a single static
binary per platform.

## Rationale

| Candidate | Assessment |
| --- | --- |
| **Go (chosen)** | Static single binary, trivial cross-compilation to `linux/amd64` and `windows/amd64`, excellent concurrency model for one goroutine pipeline per file, mature file-watching and HTTP libraries, GC pauses irrelevant for a non-latency-critical observer, and a small enough language that a maintenance team can be productive quickly. |
| Rust | Better absolute footprint and no GC, but a materially slower build-out for a first version, and the added safety buys little here because the agent does no unsafe work and holds no critical state. Reconsider only if the memory ceiling proves unreachable in Go. |
| Python | Rejected. Requires a runtime on a locked-down trading host, GIL-bound parsing throughput, and a memory profile that is hard to bound — the opposite of `NFR-PERF-003`. |
| .NET | Viable, especially if Magic is .NET and the team already operates it. Rejected for Day-1 because self-contained deployment artefacts are larger and Linux support is more operational work than Go's. |
| C++ | Rejected. No benefit over Go for I/O-bound work, and the failure modes on a trading host are the worst of any candidate. |

Go also matters for a specific requirement: `NFR-PERF-004` demands parsing without per-message
map allocations. Go makes that straightforward with a fixed struct plus byte-slice scanning,
and `-benchmem` makes it enforceable in CI.

## Consequences

- One language for all agent code; the parser plugin interface is a Go interface
  (`FR-PRS-030`), and Day-2 binary parsers are Go packages, not dynamically loaded modules
  (`FR-PRS-032`).
- Go's GC means memory is bounded but not deterministic; `NFR-PERF-003` is enforced by explicit
  caps and shedding, plus `GOMEMLIMIT` as a soft ceiling, not by trusting the allocator.
- The team maintains two languages overall (Go agent, Python backend). The shared schema in
  `/contracts` (`FR-ING-022`) is what keeps that from becoming a drift problem.
- Windows service and Linux systemd packaging are both required (`NFR-OPS-001`).

## Reversal conditions

Revisit if: the agent cannot hold RSS under 150 MB at target throughput after optimisation
(→ Rust); or Magic's platform team mandates a single .NET runtime estate for host-resident
software (→ .NET).
