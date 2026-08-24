# Implementation Status

Status: Live document · Last updated: 2026-07-31

Specs state the target; this document states what exists. Where the two differ, the difference
is recorded here rather than by quietly editing the spec.

## Milestones

| Milestone | Scope | Status |
| --- | --- | --- |
| M0 | Repository foundation, CI gates, contracts | Partial — Makefile and module layout exist; CI, `contracts/` and the requirement-coverage reporter do not |
| **M1** | **Log monitor and configuration** | **Implemented** — `agent/internal/logmon`, `agent/internal/config`, `agent/cmd/telemetry-agent` |
| M2 | FIX parser | Not started |
| M3 | Metrics aggregation | Not started |
| M4 | Backend ingestion, store, query | Not started |
| M5 | Rules, alerts, callbacks | Not started |
| M6 | Natural language layer | Not started |
| M7 | Operability hardening | Not started |

## M1 requirement coverage

| ID | Requirement | Status | Verified by |
| --- | --- | --- | --- |
| `FR-LOG-001` | Configurable paths and globs, tagged per instance | Done | `TestAppendedLinesAreRead`, `TestMultipleFilesInOneSet` |
| `FR-LOG-002` | Tail and interval read modes | **Partial** — both modes work, but tail mode polls rather than using filesystem notifications (see §4.1) | `TestIntervalModeReadsContent`, `TestRunReadsAppendsDiscoversAndCheckpoints` |
| `FR-LOG-003` | Byte offset per file, resumed after restart | Done | `TestRestartResumesFromCheckpoint`, `TestRunResumesAfterRestart` |
| `FR-LOG-004` | Identify files by identity, not path | Done — `os.SameFile` while open, head fingerprint across restarts (`FR-LOG-023`) | `TestRotationWithIdenticalHeaderReadsNewFileFromStart`, `TestFingerprintStableAsFileGrows` |
| `FR-LOG-005` | Detect rotation and drain the rotated file first | Done for rename-and-create and copy-truncate | `TestRotationRenameAndCreateDrainsOldFile` |
| `FR-LOG-006` | Detect truncation and reset the offset | Done | `TestCopyTruncateRotation`, `TestRestartAfterTruncationDoesNotReplay` |
| `FR-LOG-007` | Emit complete lines; hold fragments until newline or timeout | Done | `TestPartialLineHeldUntilNewline`, `TestPartialLineFlushedAfterTimeout`, `TestLineSplitAcrossWritesJoins` |
| `FR-LOG-008` | Cap line length, count and flag once | Done | `TestOverLongLineTruncatedOnce` |
| `FR-LOG-009` | Read-only, no locking that blocks Magic | Done on POSIX | `TestRotationRenameAndCreateDrainsOldFile` (rename succeeds while open) |
| `FR-LOG-010` | Report read lag and offset progress | Done | `TestFileStatusReportsOffsetAndLag` |
| `FR-LOG-011` | Discover new files; close vanished ones without error | Done | `TestFileDiscoveredMidRunIsReadFromStart`, `TestVanishedFileIsClosedCleanly` |
| `FR-LOG-012` | First-ever start begins at EOF unless configured otherwise | Done | `TestStartAtEndSkipsExistingContent` |
| `FR-LOG-020` | Atomic offset checkpointing | Done | `TestStateStoreRoundTrip`, `TestFlushLeavesNoTemporaryFiles`, `TestFlushDoesNotLoseConcurrentUpdate` |
| `FR-LOG-021` | Bounded re-read after restart | Done | `TestRestartResumesFromCheckpoint` |
| `FR-LOG-022` | Missing or corrupt state starts cleanly and reports a reset | Done | `TestCorruptStateFileResetsCleanly`, `TestUnknownStateVersionResets` |
| `FR-PUB-004` | Bounded queues, drop oldest, count drops | Done for the monitor's output channels | `TestBoundedQueueDropsAndCounts` |
| `FR-CFG-002` | Unknown configuration keys are a startup error | Done | `TestUnknownKeyIsRejected` |
| `FR-CFG-003` | Unique names, per-set validation, overlap detection | Done — overlap detection compares identical patterns only, not general glob intersection | `TestValidationFailures` |
| `FR-CFG-004` | Duration and bound validation | Done | `TestValidationFailures` |
| `FR-CFG-020` | `--check-config` prints the effective configuration | Done | `TestRedactedRoundTrips`, `agent/scripts/m1-demo.sh` |
| `NFR-CFG-002` | Refuse to start on invalid configuration | Done | `TestValidationFailures` |
| `NFR-CFG-004` | Code defaults match documented defaults | Done | `TestDefaultsMatchSpecifiedValues` |
| `NFR-OPS-003` | `--check-config` and `--dry-run` modes | Done | `agent/scripts/m1-demo.sh` |
| `NFR-OPS-004` | Version reported in `--version` and logs | Done | manual, `--version` |
| `NFR-REL-008` | A configured file that does not exist yet is not an error | Done | `TestMissingFileIsNotAnError` |
| `NFR-SEC-001` | No raw log content persisted, transmitted or logged | Done for M1's surfaces | `TestStateFileHoldsNoLogContent`, demo sentinel check |
| `NFR-SEC-003` | State file holds only offsets and identities | Done | `TestStateFileHoldsNoLogContent` |
| `NFR-SEC-015` | Configured paths confined to `allowedRoots`, symlinks resolved first | Done | `TestSymlinkOutsideAllowedRootsIsRefused` |
| `NFR-OBS-002` | Every discard has a counter | Done | `TestBoundedQueueDropsAndCounts`, `Stats` |
| `NFR-OBS-003` | Structured JSON logs | Done | demo output |

Deferred within M1's area: `FR-LOG-023` covers the persisted-identity mechanism and is
implemented; `NFR-PERF-010` (Windows share flags) and the Windows half of the rotation harness
are untested because CI does not yet run on Windows.

## New requirements added while implementing

| ID | Requirement | Why it was needed |
| --- | --- | --- |
| `FR-LOG-023` | Persisted file identity MUST be a digest of a recorded-length prefix of the file head, and MUST be invalidated when the head changes | `os.SameFile` cannot be serialised into the state file, so restart-time identity needs its own mechanism. See spec 002 §2.2. |

## Deviations from the specs

### 4.1 Tail mode polls instead of using filesystem notifications

`FR-LOG-002` specifies tail mode as event-driven via `fsnotify` with a polling fallback. M1
implements the polling path only, at `pollInterval` (default 1s for tail mode).

Why this is acceptable for now: the read path is identical either way, notifications only change
*when* a read is triggered, and the resulting latency (up to `pollInterval`) is well inside the
5-second end-to-end target of `NFR-PERF-002`. Polling also avoids a dependency and the
platform-specific failure modes of watch descriptors on rotated files.

What it costs: one `stat` per file per interval, and up to one poll interval of extra latency.
Adding `fsnotify` later is a change to the trigger only, not to the reader, so it does not
affect the wire contract or any test above.

### 4.2 Glob overlap detection is exact-match only

`FR-CFG-003` requires overlapping globs across file sets to be reported. The implementation
detects identical patterns. Two different patterns that match the same file (`fix*.log` and
`*.log`) are not detected, and would cause that file to be read twice under two file set names.
Deciding glob intersection in general is not worth the complexity; a better approximation is to
warn when two sets resolve to the same canonical path at discovery time, which M3 should add
once double-counting has a visible cost in metrics.

## Defects found and fixed during M1

Recorded because each one is a silent-data-corruption class of bug, and each now has a
regression test.

| Defect | Symptom it would have caused | Found by | Test |
| --- | --- | --- | --- |
| Line-length cap applied only to buffered fragments | A long line arriving whole in one read was emitted uncapped, defeating `FR-LOG-008` | Unit test | `TestOverLongLineTruncatedOnce` |
| Checkpoint used a boolean dirty flag | A `Put` during an in-flight flush was marked written but never persisted, so offsets silently went stale and files were re-read after restart | Integration test | `TestFlushDoesNotLoseConcurrentUpdate` |
| Fingerprint digested "whatever is there now" | A file shorter than 256 bytes changed identity as it grew, so every restart re-read it from the beginning | Integration test | `TestFingerprintStableAsFileGrows` |
| Fingerprint not invalidated on truncation | After an in-place truncation the checkpoint described content that no longer existed; the next start failed to recognise the file and re-read it | Demo script | `TestRestartAfterTruncationDoesNotReplay` |
| Rotation consulted the checkpoint for the new file | A replacement file sharing the old one's first bytes would resume at the old offset and skip its beginning | Reasoning during review | `TestRotationWithIdenticalHeaderReadsNewFileFromStart` |
| Path refusal counted and reported every discovery pass | A permanently misconfigured path emitted an event every interval, an event storm against `NFR-OBS-004` | Demo script | `TestSymlinkOutsideAllowedRootsIsRefused` |

## Measurements

`go test ./internal/logmon/ -bench . -benchmem` on darwin/arm64 (Apple silicon, warm page
cache, so treat as an upper bound):

| Benchmark | Result | Interpretation |
| --- | --- | --- |
| `BenchmarkReadThroughput` | 3.12 ms per 20 000 lines, 1 069 MB/s | ≈ 6.4 M lines/sec through the full read path |
| `BenchmarkConsumeOnly` | 39.7 µs per 512 lines, 2 153 MB/s | ≈ 12.9 M lines/sec for splitting alone |
| Allocations | 20 007 per 20 000 lines | Exactly one allocation per line |

Against `NFR-PERF-001` (5 000 lines/sec sustained on under one core), the read path has roughly
three orders of magnitude of headroom, so the parser and aggregator in M2 and M3 will dominate
cost. The single allocation per line is the copy made when handing a line to the consumer, which
is required because the read buffer is reused; if it ever matters it becomes a buffer pool, but
it should not be optimised before the parser exists.

These figures are not a substitute for the load test in spec 012 §5, which must run against
`tools/fixgen` on representative hardware once [Q-1](./open-questions.md) is answered.

## How to verify

```bash
make test    # unit and integration tests
make race    # the same suite under the race detector
make bench   # throughput and allocation figures
make demo    # end-to-end run: rotation, truncation, restart, security assertions
```
