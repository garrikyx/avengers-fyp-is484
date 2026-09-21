# UBS-49 — Pipeline bridge integration (live agent path)

Jira story draft for the **production wiring** of the M1.5 pipeline bridge.
Depends on [UBS-48](./ubs48-pipeline-bridge-story.md) (library complete) and partial M1/M2.

Spec: [002-agent.md §1.1](../specs/002-agent.md), [010-configuration.md](../specs/010-configuration.md),
[011-observability-and-runbooks.md](../specs/011-observability-and-runbooks.md).

## Relationship to UBS-48

| Story | Scope | Status |
| --- | --- | --- |
| **UBS-48** | Pipeline **library**: bounded queues, worker pool, committer, deduper, `PipelineBridge` API, `pipeline_demo`, unit/integration tests | Done |
| **UBS-49** (this story) | Pipeline **integration**: always-on agent supervisor, config-driven file sets, MA-01 ingest, heartbeat metrics, graceful lifecycle | Not started |

UBS-48 proves the bridge works in isolation (`make pipeline-demo`). UBS-49 makes it the
default path when the telemetry agent runs on a host.

## Summary

Replace the parser-CLI stub in `main.py` with a supervisor loop that tails configured log
files through `LogMonitor`, enqueues lines on `PipelineBridge`, ingests parsed events into
`MetricsAggregator`, commits offsets on success, and exposes queue depth on the agent
heartbeat.

## User story

As an operator deploying the telemetry agent beside Magic, I want the monitor → parser
pipeline to run continuously from `agent.yaml` configuration, so FIX lines become real
aggregated metrics and health signals without running a separate demo script.

## Requirements

| ID | Requirement | Target |
| --- | --- | --- |
| `FR-PIP-004` (completion) | Parsed events reach **MetricsAggregator**, not only `DemoMetricsSink` | `pipeline/event_bridge.py`, `metrics/` |
| `FR-PIP-005` (completion) | Queue depths + drop counters on heartbeat and `/metrics` | `health/reporter.py`, `packages/telemetry_shared/.../health.py` |
| `FR-PIP-006` (operational) | Periodic offset checkpoint (`checkpointInterval`) + flush on SIGTERM | `pipeline/supervisor.py`, `logs/log_monitor.py` |
| `FR-CFG-*` | Load `pipeline.*` from `agent.yaml` (`lineQueueSize`, `overflowPolicy`, `dedupeCapacity`, …) | `config.py` |
| `FR-LOG-001` | File sets from config drive which paths/chains the adapter polls | Depends on M1 config loader / UBS-22 |
| spec 004 | `ParsedMessageEvent` construction from `ParseResult` / `FixTelemetry` | `pipeline/event_bridge.py` |

## Acceptance criteria

1. **Live agent entrypoint** — `telemetry_agent.main` runs monitor + pipeline + aggregator
   (parser CLI remains available as `telemetry-parser` or `--mode parser-demo`).
2. **Config-driven pipeline** — `pipeline.lineQueueSize`, `eventQueueSize`, `parseWorkers`,
   `overflowPolicy`, `dedupeCapacity`, `dedupeTtl` loaded from `agent.yaml` with spec 010
   defaults.
3. **Real metrics path** — FIX lines from a tailed log file produce non-zero counters in
   `MetricsAggregator` (orders, messages, etc.), verified by integration test — not
   `DemoMetricsSink` alone.
4. **Heartbeat queue metrics** — `AgentHeartbeat` (or equivalent) includes
   `pipeline_line_queue_depth`, `pipeline_events_dropped_total`, etc., from
   `PipelineStats.as_metrics()`.
5. **Health rollup** — sustained high line-queue depth or non-zero drops (in `drop_oldest`
   mode) surface in degraded reasons per spec 011.
6. **Graceful shutdown** — SIGTERM stops workers, drains in-flight events, commits offsets,
   exits 0 within `shutdownGrace`.
7. **Idempotency preserved** — restart integration test: stop mid-file, restart, no
   duplicate counter increments for already-committed lines (`FR-PIP-007`).
8. **No spec violation** — `LogMonitor` still does not call `Parser.parse()` directly;
   all parsing goes through `PipelineBridge`.

## Out of scope

- Full asyncio per-file-set supervisor (can start with `MonitorPipelineAdapter` + thread
  pool until UBS-22 multi-file monitor lands).
- Backend Publisher / rule engine tickers (M4/M5).
- Replacing `MultiLogMonitor` stopgap — wire through it now; swap when UBS-22 merges.
- `drop_oldest` operational runbooks (document only; default remains `block`).

## Implementation map (proposed)

```
apps/agent/src/telemetry_agent/
├── main.py                    # supervisor entry (replace parser-only stub)
├── config.py                  # load agent.yaml including pipeline.*
├── pipeline/
│   ├── supervisor.py          # extend: lifecycle, checkpoint ticker
│   ├── event_bridge.py        # NEW: ParseResult → ParsedMessageEvent → Aggregator
│   └── committer.py           # swap DemoMetricsSink for AggregatorIngestSink
├── health/reporter.py         # fold in PipelineStats + queue depth
└── publishing/                # (stub OK) heartbeat assembly uses reporter
```

### Suggested wiring

```python
# Pseudocode — production loop
bridge = PipelineBridge(config=pipeline_config, registry=registry)
bridge.attach_committer(
    monitors_by_path,
    sink=AggregatorIngestSink(aggregator, deduper, event_bridge),
)
bridge.start()
adapter = MonitorPipelineAdapter(multi_monitor, bridge, parser_chain=...)
while running:
    adapter.poll_once()
    bridge.process_commits()
    maybe_checkpoint_offsets()  # every checkpointInterval
```

## Dependencies

| Dependency | Why |
| --- | --- |
| **UBS-48** (done) | `PipelineBridge`, committer, deduper, blocking queues |
| **M2 parser** (done) | `FixParser`, registry |
| **MA-01–04** (done) | `MetricsAggregator`, `derive_counters`, correlation |
| **M1 config** (partial) | File-set paths, `instanceId`, parser chain — may stub for first PR |
| **UBS-22** (pending) | Production multi-file monitor — stopgap `MultiLogMonitor` OK interim |
| **UBS-30** (done) | Read-lag health — extend with queue depth |

## Test plan

```bash
make pipeline-test                                    # UBS-48 regression
uv run pytest tests/integration/agent/test_UBS49_pipeline_agent.py -v   # NEW
```

| Test | Asserts |
| --- | --- |
| `test_UBS49_config_loads_pipeline_section` | YAML defaults match spec 010 |
| `test_UBS49_live_tail_produces_aggregator_counters` | Tail FIX log → MA-01 counters > 0 |
| `test_UBS49_heartbeat_includes_queue_depth` | `PipelineStats` fields on heartbeat model |
| `test_UBS49_restart_idempotent` | Stop/start mid-file; no double-count |
| `test_UBS49_sigterm_commits_offsets` | Committed offset persisted on clean shutdown |

## Demo / sponsor verification

After UBS-49:

```bash
# Continuous agent (new)
uv run python -m telemetry_agent.main --config config/agent.yaml

# Compare to library demo (UBS-48, unchanged)
make pipeline-demo
```

Sponsor talking point: UBS-48 showed the **pipe**; UBS-49 connects the pipe to the
**running agent** and **real metrics store**.

## Branch naming

`UBS-49-Pipeline-Bridge-Integration`

## Open questions

1. **CLI split** — keep `telemetry-parser` for corpus demos; `telemetry-agent` for live mode?
2. **First PR scope** — accept single-file + `MultiLogMonitor` stopgap before UBS-22?
3. **Event bridge ownership** — new `pipeline/event_bridge.py` vs extend `parser/fix/telemetry.py`?
