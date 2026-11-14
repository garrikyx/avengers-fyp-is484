# ADR 0010 — Timely, revisioned metric publication for Day-1

Status: Accepted · Date: 2026-11-14 · Scope: UBS-140

## Context

Spec 000 §7 and NFR-PERF-002 require five-second log-to-query visibility, while
FR-MET-001/024 and ADR 0003 specified completed ten-second buckets. Those settings
cannot satisfy that deadline. UBS-140 also exposed loss of late data after a bucket
was emitted and loss/overwrite of an open bucket across a graceful restart.

This decision supersedes ADR 0003's fixed ten-second cadence and its automatic
transport-reversal condition for publication more frequent than two seconds.
It retains HTTPS/JSON batching: one request per second is still batched derived
telemetry, not per-message network traffic. No evidence justifies a gRPC migration.

## Decision

- Keep the five-second visibility and 5,000 sustained synthetic lines/s targets.
  Day-1 acceptance uses one-second wire buckets, one-second publication and 100ms
  evaluation. General library defaults remain ten-second publication/buckets for
  compatibility. Backend canonical storage remains ten seconds and sums native
  one-second contributions. Configure the acceptance backend for 120 batches/minute
  per agent, allowing 60 normal publishes plus recovery/retry headroom.
- Snapshot schema v2 adds a random per-process `runId` and monotonically increasing
  `revision`. A snapshot contains the complete counters/histograms for that run's
  contribution to that native bucket, not a lifetime total or incremental revision.
  Later revisions replace earlier ones; retries and older revisions cannot regress
  or duplicate data. Different runs contribute separately, including when restart
  falls inside the same native bucket. Batch/event/heartbeat envelopes remain v1.
- Dirty retained buckets are republished when late events arrive. Graceful shutdown
  stops reading, drains queued work within the shutdown grace, exports the open
  bucket, and drains publication within the remaining deadline. Committed offsets
  advance only after successful ingestion, in source order and for the original
  file identity. Unfinished lines remain in the original log for restart.
- Restart metadata marks the checkpoint replay interval and startup bucket,
  including late revisions. It must not imply that memory-only buffers survived a
  crash or that duplicated checkpoint replay has been deduplicated across runs.
- ADR 0004, ADR 0005 and FR-PUB-008 remain in force: no raw data egress, database or
  disk spool. Graceful restart with a reachable backend is tested for exact counts.
  Abrupt restart or restart during an outage may lose unpublished in-memory
  telemetry; queries must annotate restart-affected buckets. This is telemetry,
  not an exactly-once audit trail.
- UBS-140's five-minute outage is a connectivity outage with backend memory
  preserved. Backend process destruction loses its cache under FR-QRY-005 and is
  a distinct scenario. Short tests may compress outage duration; the full acceptance
  command must run 300 real seconds. No throughput reduction or loss tolerance is
  used to make the acceptance test pass.

## Compatibility and bounds

The backend accepts legacy snapshot v1 and v2. Deploy the backend before the v2
agent; an old backend is not a compatible receiver for v2. `/contracts` is generated
from the shared models. Snapshot run/revision metadata contains no log content.
Dirty-bucket tracking is bounded by agent retention. Backend contribution/revision
tracking is capped at 4,096 run/native-bucket keys per canonical bucket, in addition
to existing series and memory limits; excess contributions are counted as dropped.
These metadata allocations are included in the store's memory estimate.

## Validation

Requirement-ID tests cover late revisions and retry ordering, same-bucket restart,
source-order/rotation acknowledgements, bounded shutdown, and the combined UBS-140
run. See `docs/plan/ubs140-day1-acceptance.md` for measured acceptance results.
