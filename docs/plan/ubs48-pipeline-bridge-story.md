# UBS-48 — Pipeline bridge (zero-loss, idempotent)

Jira story draft for M1.5 **library**: decouple the log monitor from the parser engine with
bounded blocking queues, commit-after-process offsets, and deduplicated ingest.
Spec: [002-agent.md §1.1](../specs/002-agent.md).

**Production integration** (supervisor, MA-01, heartbeat, `main.py`) is **[UBS-49](./ubs49-pipeline-integration-story.md)**.

## Summary

Wire `LogMonitor` output into the existing `Parser` plugins through bounded queues
(default `overflowPolicy: block`) and a CPU-bound worker pool. Persisted file offsets
advance only after parse+ingest succeeds (`FR-PIP-006`). Re-reads after restart are
idempotent via `(device, inode, byte_offset)` dedupe (`FR-PIP-007`).

## User story

As an operator running the telemetry agent on a trading host, I want every log line
processed exactly once with no silent drops, so trading metrics remain complete even
during parse bursts or agent restarts.

## Requirements

| ID | Requirement | Module |
| --- | --- | --- |
| `FR-PIP-001` | Block on full queue (default); optional `drop_oldest` | `pipeline/bounded_queue.py` |
| `FR-PIP-002` | Default line queue size 2048 | `pipeline/config.py` |
| `FR-PIP-003` | Parser worker pool, default `min(2, cpu_count)` | `pipeline/workers.py` |
| `FR-PIP-004` | Bounded event queue (default 256), block on overflow | `pipeline/event_queue.py` |
| `FR-PIP-005` | Queue depth + drop counters on heartbeat/metrics | `pipeline/stats.py` |
| `FR-PIP-006` | Commit offset only after parse+ingest | `logs/log_monitor.py`, `pipeline/committer.py` |
| `FR-PIP-007` | Dedupe re-reads by file position | `pipeline/deduper.py` |

## Acceptance criteria

1. **Zero loss (block mode)** — flooding the line queue while parser is slow blocks the
   producer; `pipeline.lines_dropped` stays 0.
2. **Commit-after-process** — persisted offset does not advance until ingest ack.
3. **Idempotent re-read** — same `(dev, inode, byte_offset)` ingested twice does not
   double-count metrics.
4. **Parser workers** — configured parser chain invoked from thread pool; `ParsedEvent`
   emitted on event queue.
5. **End-to-end demo** — `make pipeline-demo` shows monitor → queue → parse → output → commit.
6. **Spec boundary** — `LogMonitor` does not call `Parser.parse()` directly.

## Test plan

```bash
make pipeline-test
make pipeline-demo
```

## Out of scope (→ UBS-49)

- `main.py` supervisor replacing parser-CLI stub
- `agent.yaml` config loader for `pipeline.*`
- `ParsedMessageEvent` → `MetricsAggregator` (production ingest)
- `AgentHeartbeat` queue depth producer
- Always-on agent process / SIGTERM graceful shutdown

## Branch naming

`UBS-48-Pipeline-Bridge-Bounded-Queues`

## Status

**Done** — library, tests, and `make pipeline-demo`. Do not expand UBS-48 for integration work; use UBS-49.
