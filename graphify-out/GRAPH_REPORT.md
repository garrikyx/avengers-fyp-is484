# Graph Report - avengers-fyp-is484  (2026-10-05)

## Corpus Check
- 279 files · ~153,716 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 12, .example 1, .typed 1)

## Summary
- 3569 nodes · 8770 edges · 220 communities (136 shown, 84 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 1527 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fa4ff081`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- telemetry_backend/main.py
- frame.py
- models/ingestion.py
- RuleEngine
- make_snapshot
- test_RE_05_config_loader.py
- HealthReporter
- FixParser
- RetryPolicy
- LatencyCorrelator
- derive_counters
- AgentHeartbeat
- test_heartbeat.py
- LogMonitor
- PublishBuffer
- Registry
- test_STM_02_merge_semantics.py
- PublishResult
- MetricsAggregator
- PipelineCommitter
- datetime
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- to_ingestion_heartbeat
- telemetry_backend/config.py
- parse_publish_config
- test_ING_004_008_ingest_guard.py
- DeliveryTracker
- load_health_config
- test_MA_05_agent_counters.py
- FakeClock
- LineClassification
- publishing/sink.py
- test_MA_03_correlation.py
- OffsetTracker
- config/rules.yaml live rule set
- test_health_monitor_e2e.py
- BoundedQueue
- MetricsAggregator ring buffer
- _Clock
- metrics_event.py
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- test_metrics_event.py
- callbacks/config.py
- callbacks/demo_quickstart.py
- telemetry_agent_parser_applog_parser
- ParseResult
- decimal
- StreamProcessorConfig
- MultiLogMonitor
- StreamProcessor
- health/demo.py
- from_alert_event
- test_FR_CBK_004_006_007_dispatcher.py
- snapshot
- models/__init__.py
- test_queue_depth.py
- AgentRegistry
- dispatcher.py
- pathlib
- dataclasses
- BackendPublisher
- _Demo
- Telemetry Agent (architecture constraint)
- AppDeps
- test_RE_session_integration.py
- test_internal_api.py
- test_RE_publish_integration.py
- Snapshot
- heartbeat_receiver_stub.py
- 009 — Non-Functional Requirements and Security
- Histogram
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- AlertEvent
- pipeline_demo.py
- test_FR_CBK_005_signing.py
- mock_logger.py
- services/demo_quickstart.py
- Rule Engine demo runbook
- Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing)
- test_degraded_status_flows_into_heartbeat_payload
- internal.py
- Heartbeat
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- publisher.py
- heartbeat_json
- classify_http_status
- CallbackDispatcher
- test_STM_04_efficiency.py
- ParsedMessageEvent
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- test_QRY_04_concurrency.py
- test_agent_registry.py
- ingest_guard.py
- demo_reload.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- health-reporter-overview.md
- services/self_metrics.py
- Requirement ID Scheme (FR-<AREA>-<NNN>)
- .validate_and_reserve
- test_ING_004_008_routes.py
- telemetry_shared shared schema package
- parse_fix_timestamp
- BackendConfigError
- End-to-End Acceptance Scenario (FR-TST-010)
- test_reporter.py
- BackendHealthConfig
- data_completeness.py
- .__init__
- Stream Processor (component)
- Query Engine Requirements (FR-QRY-006–014)
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- test_UBS_104_outage_isolation.py
- telemetry_agent_parser_applog_signatures
- Rule Engine
- test_log_monitor_status.py
- effective_reject_reason
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- 008 — Natural Language Query Layer (Copilot/Teams)
- NFR-REL-003: Backend Outage Must Not Affect Alerting
- telemetry-shared
- telemetry_agent_parser_applog_telemetry
- telemetry_agent_parser_config
- PipelineStats
- telemetry_agent/__init__.py
- telemetry_agent_parser_corpus
- telemetry_agent_parser_display
- telemetry_backend/__init__.py
- Auditability & Compliance rationale (deterministic order audit trails)
- simulator/__init__.py
- teams_agent/__init__.py
- CLAUDE.md
- ADR 0002: Backend in Python/FastAPI
- ADR 0003: HTTPS/JSON Transport Day-1
- ADR 0005: In-Memory Metric Store
- ADR 0006: Agent in Python
- Parser Test Obligations (§10)
- Message Validation and Parse Error Reason Codes (FR-PRS-017–019)
- Data Completeness Block (FR-QRY-015)
- Backend Health and Self-Metrics (FR-HLT-010)
- telemetry_shared/__init__.py
- telemetry_agent_parser_fix_classify
- FakeClock
- test_data_completeness.py
- reject_rate anomaly baseline config (baseline_window_minutes=60, minimum_samples=100)
- 000 — Overview, Scope and Conventions
- Problem P-3: Reactive troubleshooting via manual log inspection
- Telemetry System (streaming-first, no raw log storage)
- Latency Measurement via ClOrdID Correlation (FR-MET-010–013)
- Metrics Aggregator Agent-Level Contract (FR-MET-001–004)
- Agent Process Model (asyncio per file + bounded queues)
- Rule Engine Ticker-Driven Evaluation (FR-RUL-002)
- Framing and Delimiters (FR-PRS-012–016)
- Line Classification (FR-PRS-010/011)
- Sequence Gap Detection (FR-PRS-027)
- FIX Timestamp Handling (FR-PRS-025/026)
- Alert Store Requirements (FR-QRY-016–018)
- Metric Store Requirements (FR-QRY-001–005)
- Alerts Endpoints (GET /telemetry/alerts[/{alertId}])
- API Conventions (§1)
- Health Endpoints (§5)
- Ingestion Endpoints (POST /telemetry/batch, /events, /heartbeat)
- API Versioning (FR-QRY-039)
- NL Integration Surfaces (Copilot/Teams/Direct API)
- Time Expression Handling (FR-NLQ-011–014)
- Agent Health Signals (§1.1)
- Deployment Operations (§4)
- Derived Agent Status Rules (FR-HLT-002–004)
- Runbook: Agent Heartbeat Missing
- Runbook: Callback Failures
- Runbook: High Reject Rate
- Runbook: No Log Activity
- High-Consequence Risk Test Matrix (§2)
- Test Levels (§1)
- Latency Histograms (ack/exec/cancel_latency_ms, scope correction)
- Internal Contract Schema Evolution (no version negotiation, Pydantic extra=forbid)
- telemetry_agent_parser_fix_identifiers
- IngestionService
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- IngestionConfig
- telemetry_agent_parser_fix_telemetry
- Any
- telemetry_agent_parser_registry
- telemetry_agent_pipeline_config
- telemetry_agent_pipeline_monitor_adapter
- telemetry_agent_pipeline_supervisor
- telemetry_shared_metrics
- telemetry_shared_metrics_histogram
- rules/demo_quickstart.py
- telemetry_shared_models_base
- BaseModel
- Exception
- ArgumentParser
- Event
- HeartbeatSink
- Namespace
- Protocol
- parametrize

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 77 edges
2. `HealthReporter` - 74 edges
3. `StreamProcessorConfig` - 62 edges
4. `FixParser` - 61 edges
5. `MetricStore` - 59 edges
6. `LogMonitor` - 58 edges
7. `make_snapshot()` - 58 edges
8. `SourceMeta` - 57 edges
9. `ParseResult` - 53 edges
10. `create_app()` - 49 edges

## Surprising Connections (you probably didn't know these)
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py
- `4.2 Configuration — `health/config.py`` --references--> `HealthConfigError`  [INFERRED]
  docs/plan/health-reporter-overview.md → apps/agent/src/telemetry_agent/health/config.py
- `Module map (`apps/agent/src/telemetry_agent/health/`)` --references--> `HealthConfigError`  [INFERRED]
  docs/plan/ubs58-60-notes.md → apps/agent/src/telemetry_agent/health/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Day-1 Acceptance Definition Validated by the E2E Scenario** — docs_specs_000_overview_day1_acceptance_definition, docs_specs_012_e2e_acceptance_scenario, docs_specs_002_agent_restart_sequence, docs_specs_012_data_leak_sentinel_test [EXTRACTED 0.90]
- **Alert & Callback Flow participants** — docs_assets_architecture_overview_rule_engine, docs_assets_architecture_overview_callback_dispatcher, docs_assets_architecture_overview_magic_callback_endpoint, docs_assets_architecture_overview_alert_event_store [EXTRACTED 1.00]
- **The 14 configured rules implementing spec 005 §1.2** — config_rules_highrejectrate, config_rules_rejectspike, config_rules_cancelrejectspike, config_rules_sessionrejects, config_rules_pendingordertimeout, config_rules_acklatencybreach, config_rules_parseerrorrate, config_rules_nologactivity, config_rules_noexecutions, config_rules_fixsessiondown, config_rules_seqgapdetected, config_rules_clockskew, config_rules_callbackfailing, config_rules_backendunreachable [EXTRACTED 1.00]
- **One heartbeat tick: sample, judge, package, deliver** — docs_plan_health_reporter_overview_heartbeat_emitter, docs_plan_health_reporter_overview_snapshot, docs_plan_health_reporter_overview_derive_status, docs_plan_health_reporter_overview_build_heartbeat, docs_plan_health_reporter_overview_agentheartbeat, docs_plan_health_reporter_overview_bufferingheartbeatsink, docs_plan_health_reporter_overview_httpheartbeatsink, docs_plan_health_reporter_overview_heartbeat_receiver_stub [EXTRACTED 1.00]
- **Log Ingestion & Metric Publication Flow participants** — docs_assets_architecture_overview_log_files, docs_assets_architecture_overview_log_monitor, docs_assets_architecture_overview_parser_engine, docs_assets_architecture_overview_metrics_aggregator, docs_assets_architecture_overview_ingestion_service [EXTRACTED 1.00]
- **Natural Language Query Flow participants** — docs_assets_architecture_overview_copilot, docs_assets_architecture_overview_microsoft_teams, docs_assets_architecture_overview_query_api_service, docs_assets_architecture_overview_integration_service [EXTRACTED 1.00]
- **Telemetry Agent processing pipeline: log monitor to health reporter** — readme_logs_module, readme_pipeline_module, readme_parser_module, readme_metrics_module, readme_rules_module, readme_callbacks_module, readme_publishing_module, readme_health_module [EXTRACTED 1.00]
- **Unified Python monorepo stack sharing telemetry_shared** — docs_adr_0002_backend_in_python_fastapi_decision, docs_adr_0006_agent_in_python_decision, readme_telemetry_shared [EXTRACTED 1.00]
- **Provisional-Numbers Open Risk Cluster (Q-1, Q-5, Q-8)** — docs_plan_open_questions_q1, docs_plan_open_questions_q5, docs_plan_open_questions_q8, docs_plan_scaffold [INFERRED 0.75]
- **Agent language decision evolution constrained by NFR-PERF-003 (Go to Python)** — docs_adr_0001_agent_in_go_decision, docs_adr_0006_agent_in_python_decision, requirements_nfr_perf_003 [INFERRED 0.85]
- **Agent Telemetry Pipeline (Log Monitor → Pipeline Bridge → Parser Engine → Metrics Aggregator → Rule Engine → Callback Dispatcher → Backend Publisher)** — docs_specs_001_architecture_log_monitor, docs_specs_001_architecture_pipeline_bridge, docs_specs_001_architecture_parser_engine, docs_specs_001_architecture_metrics_aggregator, docs_specs_001_architecture_rule_engine, docs_specs_001_architecture_callback_dispatcher, docs_specs_001_architecture_backend_publisher [INFERRED 0.85]
- **Parsed event to fired alert: the agent metrics-to-rules path** — docs_plan_ma_epic_implementation_summary_derive_counters, docs_plan_ma_epic_implementation_summary_latencycorrelator, docs_plan_ma_epic_implementation_summary_metricsaggregator, docs_plan_ma_epic_implementation_summary_aggregator_snapshot, tests_unit_agent_metrics_test_ma_04_snapshot_rationale_1, docs_plan_re_epic_implementation_summary_rule_engine, docs_plan_re_epic_implementation_summary_alert_lifecycle_fsm [INFERRED 0.95]

## Communities (220 total, 84 thin omitted)

### Community 0 - "telemetry_backend/main.py"
Cohesion: 0.07
Nodes (42): HTTP routers, one file per concern (spec 007). `health.py` (UBS-69) serves the…, _counts(), create_app(), enqueue_or_full(), ingest_batch(), ingest_events(), ingest_heartbeat(), invalid_payload() (+34 more)

### Community 1 - "frame.py"
Cohesion: 0.08
Nodes (42): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+34 more)

### Community 2 - "models/ingestion.py"
Cohesion: 0.09
Nodes (30): BatchSequencer, build_batch(), datetime, FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, `FR-PUB-003`: a monotonically increasing `batchSeq` per agent, and a stable…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, inspect, NoReturn (+22 more)

### Community 3 - "RuleEngine"
Cohesion: 0.10
Nodes (35): AlertStatus, _AlertState, AlwaysActive, _decimal_or_none(), _matched_condition(), _matched_tier(), _metric_context(), AlertEvent (+27 more)

### Community 4 - "make_snapshot"
Cohesion: 0.15
Nodes (38): make_gauges(), make_indicator(), make_indicators(), make_latency(), make_snapshot(), datetime, Decimal, Shared test support for the rules package: builds `MetricsSnapshot` fixtures… (+30 more)

### Community 5 - "test_RE_05_config_loader.py"
Cohesion: 0.13
Nodes (24): load_rules(), load_rules_from_yaml(), _parse_duration_seconds(), Any, Exception, Logger, Path, Parses and validates `path` fully; raises `RuleConfigError` naming the… (+16 more)

### Community 6 - "HealthReporter"
Cohesion: 0.06
Nodes (48): AgentStatus, HealthThresholds, FR-HLT-002 thresholds. Only the read-lag one has a producer on UBS-58; the rest…, HealthReporter, HealthSignals, is_parse_error(), datetime, Health Reporter: per-file read lag (UBS-30), status rollup and heartbeat… (+40 more)

### Community 7 - "FixParser"
Cohesion: 0.08
Nodes (24): demo_log_lines(), Path, Return parsed corpus lines, optionally filtered to one source file label., FixParser, ParseError, Metadata attached to each log line by the monitor., Closed-set parse failure (FR-PRS-018 subset for framing stage)., SourceMeta (+16 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.07
Nodes (26): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, CounterRegistry, UBS-104: lightweight in-process counters, shared between the Callback… (+18 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.07
Nodes (31): CorrelatorStats, LatencyCorrelator, OrderContext, datetime, Decimal, timedelta, MA-03: order correlation and latency. Standalone producer into the shared…, Recorded so consumers of a snapshot know what a latency number means (MA-03 AC)… (+23 more)

### Community 10 - "derive_counters"
Cohesion: 0.09
Nodes (44): derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MetricsAggregator, ParsedMessageEvent, MA-02: order / execution / reject counters and reject-reason normalisation.…, All four counter families in one event walk. (+36 more)

### Community 11 - "AgentHeartbeat"
Cohesion: 0.05
Nodes (45): _make_sink(), BufferingHeartbeatSink, HttpHeartbeatSink, LoggingHeartbeatSink, PrintHeartbeatSink, datetime, Logger, Heartbeat emitter (UBS-58, FR-HLT-001). Ticks on a fixed interval regardless of… (+37 more)

### Community 12 - "test_heartbeat.py"
Cohesion: 0.09
Nodes (24): HeartbeatEmitter, Event, HeartbeatSink, Tick every `interval_seconds` until `stop` is set. First tick is immediate so a…, Collect, FakeClock, datetime, LogCaptureFixture (+16 more)

### Community 13 - "LogMonitor"
Cohesion: 0.07
Nodes (23): Harvester, LogMonitor, Path, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, One complete log line with stable byte identity for idempotent ingest., Find retained rotations that were created while the agent was down. This…, Keep a rotated descriptor alive to collect its final writes. (+15 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.11
Nodes (23): PublishBuffer, Put previously-`take`n items back at the front, in original order -- they are…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both…, Drop items older than `max_age_seconds`. The deque is strictly insertion-…, _item(), FR-PUB-004: the byte-and-age-bounded `PublishBuffer` (UBS-104's replacement for…, Drop-oldest still holds after a requeue: the items just put back are the oldest…, A distinguishable pending item -- `payload` carries `tag` so tests can assert… (+15 more)

### Community 15 - "Registry"
Cohesion: 0.08
Nodes (29): Confidence, Parser, Enum, Protocol, str, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'. (+21 more)

### Community 16 - "test_STM_02_merge_semantics.py"
Cohesion: 0.23
Nodes (16): HistogramPayload, Wire shape of one histogram (`FR-MET-025`/`FR-MET-026`): fixed boundaries…, _histogram_payload(), FR-STM-002/003/004: counters merge by summation; ratios are recomputed from…, Two agents of unequal volume (FR-STM-003's required test shape): agent A:…, FR-MET-030-equivalent guard: cross-agent merge is exactly the case where per-…, A retried publish that misses batchId-level dedupe (a different ticket's…, _read_one_group() (+8 more)

### Community 17 - "PublishResult"
Cohesion: 0.13
Nodes (34): PublishAction, StrEnum, PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, pytest, make_snapshot(), parametrize, test_429_carries_retry_after_seconds() (+26 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.13
Nodes (17): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator, datetime, Decimal, Shared metrics store (spec 004 §3): a time-bucketed ring buffer holding both… (+9 more)

### Community 19 - "PipelineCommitter"
Cohesion: 0.18
Nodes (4): PipelineCommitter, Consumes ParsedEvent objects and commits file offsets after ingest., Path, test_committed_offset_advances_only_after_committer_ingest()

### Community 20 - "datetime"
Cohesion: 0.04
Nodes (58): Demo metrics sink for parser CLI (mirrors spec 004 counter names)., QueueSnapshot, Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)., PipelineConfig, Pipeline bridge sizing (spec 010 §pipeline, FR-PIP-002–004)., Idempotent ingest dedupe by file byte position (FR-PIP-007)., EventQueue, Parser → aggregator bounded event queue (FR-PIP-004). (+50 more)

### Community 21 - "MetricStore"
Cohesion: 0.09
Nodes (24): _CanonicalBucket, _dim_key(), MetricStore, datetime, Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a…, Evict buckets that have aged out of retention within *one* instance's ring —… (+16 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.08
Nodes (35): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+27 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.15
Nodes (32): telemetry_agent_parser_fix_seq_tracker, _key(), _keys(), _observe(), UBS-106: SessionHeartbeatTracker — the `heartbeat_timeouts` producer. A…, A logged-out session is silent forever. Counting that as a timeout would…, SeqTracker accepts both normalized names and raw tag values ("Logon"/"A");…, FIX only requires a Heartbeat when the session is otherwise idle, so a session… (+24 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (32): health: threshold config block, heartbeat: interval config, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry (+24 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "to_ingestion_heartbeat"
Cohesion: 0.16
Nodes (18): Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat(), telemetry_agent_health_heartbeat, make(), UBS-58/66 wire compatibility: our heartbeat flattened to the Ingestion…, The whole point: the Ingestion Service must accept what we send., The ingestion contract has no null for these; the cost is recorded in the notes… (+10 more)

### Community 27 - "telemetry_backend/config.py"
Cohesion: 0.26
Nodes (13): _AlertingYaml, _BackendConfigYaml, _BackendYaml, _drop_none(), _IngestYaml, _Lenient, load_backend_health_config(), parse_duration_seconds() (+5 more)

### Community 28 - "parse_publish_config"
Cohesion: 0.12
Nodes (31): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, _PublishYaml, Any, BaseModel (+23 more)

### Community 29 - "test_ING_004_008_ingest_guard.py"
Cohesion: 0.23
Nodes (17): Accept, Duplicate, RateLimited, guard(), UBS-85: IngestGuard dedupe (FR-ING-004) and rate limiting (FR-ING-008)., A batch refused downstream (503 queue_full) must be accepted on retry., A retry of a batch we already hold costs no quota and gets 202., test_batch_ids_are_scoped_per_agent() (+9 more)

### Community 30 - "DeliveryTracker"
Cohesion: 0.11
Nodes (26): DeliveryRecord, DeliveryStatus, DeliveryTracker, datetime, StrEnum, UBS-34: per-alert-occurrence callback delivery status, timestamped at each…, UBS-34 AC: every dispatched callback has exactly one of these five states at…, One alert's current delivery state. `attempt_count` and `last_error` are… (+18 more)

### Community 31 - "load_health_config"
Cohesion: 0.10
Nodes (35): Any, _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, HeartbeatConfig, _HeartbeatYaml (+27 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.13
Nodes (26): AgentCounterSampler, datetime, UBS-74: bridges the agent's own since-startup counters into the windowed…, Turns monotonic since-startup counters into per-bucket deltas. Stateful across…, Ingest the increase in each tracked counter since the last call. The first call…, telemetry_agent_metrics_aggregator, _aggregator(), Decimal (+18 more)

### Community 33 - "FakeClock"
Cohesion: 0.17
Nodes (23): AggregatorConfig, Bucket granularity, retained windows, and the per-metric dimension table (FR-…, Path, FakeClock, A `Clock` (`() -> float`) that only advances when told to — lets a test assert…, make_event(), minimal_aggregator(), Decimal (+15 more)

### Community 34 - "LineClassification"
Cohesion: 0.09
Nodes (31): AppLogParser, Parser plugin for configured application log patterns (Magic format)., AppLogTelemetry, Structured fields extracted from Magic-style application log lines., classify_line(), compile_app_log_patterns(), _looks_like_fix(), Pattern (+23 more)

### Community 35 - "publishing/sink.py"
Cohesion: 0.10
Nodes (20): DryRunPublishSink, HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), AsyncBaseTransport, Logger, UBS-103: the swappable Publisher transport boundary (spec 002 §6). Mirrors…, Log the intended publish, never open a socket. Use this while there's no real… (+12 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "OffsetTracker"
Cohesion: 0.09
Nodes (24): Path, OffsetTracker, Path, Registrar subsystem for tracking offsets of log files. Stores file offsets…, Generates internal state ID format (e.g., 'native::16777232-1048201')., Loads state registry into memory Supports Filebeat's native JSON list array…, Retrieves the last known offset for a given (device, inode) pair., Persist committed offset after parse+ingest (FR-PIP-006). (+16 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.11
Nodes (28): Agent processing pipeline (monitor to health reporter), publish: Backend Publisher config block, BackendUnreachable rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule (+20 more)

### Community 39 - "test_health_monitor_e2e.py"
Cohesion: 0.10
Nodes (19): MonkeyPatch, committed_offsets(), FakeClock, fix_lines(), datetime, FastAPI, fixture, Path (+11 more)

### Community 40 - "BoundedQueue"
Cohesion: 0.10
Nodes (13): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+5 more)

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.12
Nodes (21): AckLatencyBreach rule, is_parse_error() definition, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent), Histogram (fixed buckets, merge, percentile) (+13 more)

### Community 42 - "_Clock"
Cohesion: 0.22
Nodes (3): IngestionSource, _Clock, Mutable clock shared by the aggregator and correlator, same pattern as…

### Community 43 - "metrics_event.py"
Cohesion: 0.08
Nodes (44): _fixed_now(), main(), Minimal walkthrough of parser/metrics_event.py: the same three-order story as…, _step(), One session that has just gone quiet for too long. Carries both identifiers on…, SessionTimeout, derive_heartbeat_timeout_counters(), derive_parser_counters() (+36 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (18): bad(), FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides() (+10 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.14
Nodes (20): datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, drive(), at() (+12 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.19
Nodes (13): Backend Publisher (component), Callback Dispatcher (component), Consistent-Hash Routing on instanceId, 001 — Architecture, Failure Degradation Order (queries → freshness → callbacks → alerting), Log Monitor (component), Metrics Aggregator (component), Pipeline Bridge (component) (+5 more)

### Community 47 - "CamelModel"
Cohesion: 0.16
Nodes (20): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary(), CamelModel, BaseModel (+12 more)

### Community 48 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (42): build_parsed_message_event(), ParsedMessageEvent, Construct the Metrics Aggregator's event from one framed FIX line. Returns None…, SourceMeta, _meta(), _parse(), _parser_counters(), datetime (+34 more)

### Community 49 - "callbacks/config.py"
Cohesion: 0.13
Nodes (24): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+16 more)

### Community 50 - "callbacks/demo_quickstart.py"
Cohesion: 0.11
Nodes (20): main(), _make_alert(), _print_counters(), Minimal walkthrough of the Callback Dispatcher (UBS-32/33). uv run python -m…, Stands in for Magic: keys its canned response off the alert ID inside the…, _run_one(), _ScriptedSink, _step() (+12 more)

### Community 52 - "ParseResult"
Cohesion: 0.08
Nodes (54): main(), Telemetry Agent entrypoint., DemoMetricsSink, compile_signature_rules(), extract_log_level(), First-match-wins signature rules with dynamic label templates., Extract [N/E/W/F/I] level from Magic-style log lines., resolve_label_template() (+46 more)

### Community 53 - "decimal"
Cohesion: 0.08
Nodes (49): BaseModel, field_validator, RE-05: `config/rules.yaml` loading and SIGHUP reload (`FR-RUL-008`/`009`).…, _RuleYaml, _TierYaml, _to_rule_config(), RE-03: the 14 default rules (spec 005 §1.2). Concrete `RuleConfig` values, used…, _tier() (+41 more)

### Community 54 - "StreamProcessorConfig"
Cohesion: 0.08
Nodes (38): StreamProcessorConfig, datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep…, _snapshot() (+30 more)

### Community 55 - "MultiLogMonitor"
Cohesion: 0.11
Nodes (20): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+12 more)

### Community 56 - "StreamProcessor"
Cohesion: 0.08
Nodes (31): Bounded asynchronous hand-off for HTTP ingestion., align_to_canonical(), datetime, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., Aligns, age-checks, and merges snapshots into a `MetricStore`. Non-blocking and…, Read-only configuration shared with the ingestion boundary., FR-QRY-005: `False` ("warming") until `warmupWindow` has elapsed since this… (+23 more)

### Community 57 - "health/demo.py"
Cohesion: 0.06
Nodes (31): _build_parser(), _detect_session_timeouts(), main(), _poll_forever(), Live heartbeat demo (UBS-58): tail files, emit heartbeats on an interval. uv…, UBS-106: the periodic half of heartbeat-timeout detection. A timeout is the…, Drain each tailed file every 250ms so read lag / offsets stay honest, and feed…, UBS-106: per-session heartbeat-timeout detection. A heartbeat timeout is the… (+23 more)

### Community 58 - "from_alert_event"
Cohesion: 0.20
Nodes (15): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, make_alert_event(), Shared test support for the callbacks package: builds `AlertEvent` fixtures…, FR-CBK-001/002/003 callback payload shape tests. (+7 more)

### Community 59 - "test_FR_CBK_004_006_007_dispatcher.py"
Cohesion: 0.20
Nodes (13): HttpsCallbackSink, AsyncBaseTransport, `FR-CBK-001`: HTTPS POST to the configured Magic endpoint. Rejects plain HTTP…, _make_alert(), UBS-32/33 integration test: dispatch and retry against a mock Magic endpoint.…, _run_one(), test_FR_CBK_001_success_marks_delivered(), handler() (+5 more)

### Community 60 - "snapshot"
Cohesion: 0.36
Nodes (13): hand_labelled_events(), Shared test support for the metrics package: a hand-labelled synthetic FIX-…, _ingest_all(), _shared_config(), test_gauges_are_empty_without_a_correlator(), test_gauges_reflect_pending_orders_and_event_staleness(), test_grouped_breakdown_by_symbol(), test_indicators_computed_from_hand_labelled_fixture() (+5 more)

### Community 61 - "models/__init__.py"
Cohesion: 0.15
Nodes (20): build_latency_summary(), Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004). Shared by the…, compute_indicators(), compute_ratio(), Decimal, RatioDef, Derived-ratio computation (spec 004 §4.5, FR-QRY-010, FR-STM-003). Shared by…, `value` is None when `denominator` is 0 (never fabricate a rate from no data).… (+12 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.17
Nodes (18): FakeQueue, Flaky, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend., test_at_critical_watermark_is_unhealthy(), test_at_high_watermark_is_degraded_with_reason_and_trend(), test_below_high_watermark_is_healthy(), test_buffer_drops_oldest_when_full() (+10 more)

### Community 63 - "AgentRegistry"
Cohesion: 0.11
Nodes (24): get_deps(), datetime, Request, Shared service instances the routers reach through `request.app.state`. One…, _utc_now(), AgentRegistry, Thread-safe map of known agents. Memory-only by design (FR-QRY-005)., Decommission (spec 011 runbook) so `missing` does not fire forever. (+16 more)

### Community 64 - "dispatcher.py"
Cohesion: 0.15
Nodes (11): UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, DropOldestQueue, T, FR-CBK-007: bounded pending queue, drop-oldest on overflow., Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow policy (`FR-…, Enqueue `item`, non-blocking. Returns True if an existing item was dropped to…, asyncio, FR-CBK-007 bounded queue, drop-oldest overflow tests. (+3 more)

### Community 65 - "pathlib"
Cohesion: 0.16
Nodes (13): Log monitoring, rotation and truncation handling., datetime, Offset + read lag for this file (UBS-30). See docs/plan/ubs30-notes.md., datetime, Multi-file polling and lifecycle management for the Log Monitor., Return offset and read-lag state for every configured file., FileReadStatus, Value objects published by the Log Monitor. (+5 more)

### Community 66 - "dataclasses"
Cohesion: 0.09
Nodes (40): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+32 more)

### Community 67 - "BackendPublisher"
Cohesion: 0.11
Nodes (17): _drain(), main(), _make_snapshot(), _print_state(), datetime, Minimal walkthrough of the Backend Publisher (UBS-103/104). uv run python -m…, Stands in for the backend: returns responses from a fixed script, one per call,…, _ScriptedSink (+9 more)

### Community 68 - "_Demo"
Cohesion: 0.08
Nodes (15): _Demo, AlertEvent, Decimal, MetricsSnapshot, Holds the one parser/aggregator/engine trio the whole story runs on, so each…, Pretend `by` messages were lost in transit., ExecType/OrdStatus 8 = Rejected, OrdRejReason 3 = ExchangeClosed., 35=3, a session-level Reject — a FIX plumbing problem rather than a trading… (+7 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.13
Nodes (20): Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Magic simulator for development, Do not overengineer (development principle), Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores, Microsoft Teams as the only user interface (+12 more)

### Community 70 - "AppDeps"
Cohesion: 0.21
Nodes (23): AppDeps, env(), FakeClock, heartbeat(), post(), datetime, fixture, TestClient (+15 more)

### Community 71 - "test_RE_session_integration.py"
Cohesion: 0.13
Nodes (32): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), AlertEvent, Decimal, MetricsAggregator (+24 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (21): env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), datetime, fixture, TestClient (+13 more)

### Community 73 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (22): _aggregator(), _engine(), _fail_n_times(), _publisher(), UBS-75 integration: BackendPublisher -> consecutive_publish_failures gauge ->…, The whole reason this is a gauge: recovery is observable. A windowed failure…, FR-MET-031. An agent with no publisher must not look like an agent that is…, Regression guard on spec 005 §1.2's withdrawn approximation.… (+14 more)

### Community 74 - "Snapshot"
Cohesion: 0.14
Nodes (18): One completed `bucketSeconds`-wide bucket from one agent (`FR-MET-024`).…, Snapshot, datetime, FR-STM-006: an agent's post-restart cold-start state is preserved through the…, warmingUp flags incomplete data for the caller to exclude; it does not mean the…, _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up() (+10 more)

### Community 75 - "heartbeat_receiver_stub.py"
Cohesion: 0.15
Nodes (13): BaseHTTPRequestHandler, http, http_server, _AgentRecord, main(), _make_handler(), do_GET(), do_POST() (+5 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.14
Nodes (15): Resource Discipline (§9), Backend Configuration and Secrets (§9), Compliance and Operability Constraints (§7), 009 — Non-Functional Requirements and Security, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-SCA-001: Agent Independence/Statelessness, NFR-SEC-004: Secrets from Environment Only, Observability of the Telemetry System (§6) (+7 more)

### Community 77 - "Histogram"
Cohesion: 0.15
Nodes (13): Histogram, Decimal, Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012). Shared…, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, Reconstruct a mergeable `Histogram`, keyed on the canonical boundary set rather…, test_merge_is_bucket_wise_addition() (+5 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.19
Nodes (20): datetime, Wires `config/rules.yaml` reloading to SIGHUP for a live `RuleEngine`.…, SighupRuleReloader, AlertStatus, _engine(), _fire(), datetime, LogCaptureFixture (+12 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (18): C++ candidate (rejected: worst-case failure modes), ADR 0001: Telemetry Agent written in Go (Superseded), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), ADR 0002: Telemetry stack is Python 3.12 + FastAPI, .NET alternative (rejected) (+10 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.12
Nodes (18): ADR 0004: No-Raw-Persistence Design, Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Parser Engine Agent-Level Contract (FR-PRS-001–003), Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing), Scaffold Document (plan/scaffold.md) (+10 more)

### Community 82 - "AlertEvent"
Cohesion: 0.20
Nodes (18): AlertEvent, One alert transition or re-notification (`FR-RUL-015`). `severity` reflects the…, telemetry_agent_rules_defaults, _aggregator(), _alert(), _dispatch(), _drain(), _fire() (+10 more)

### Community 83 - "pipeline_demo.py"
Cohesion: 0.17
Nodes (19): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), OverflowPolicy, Path, End-to-end demo: LogMonitor → queue → parse → output → commit. (+11 more)

### Community 84 - "test_FR_CBK_005_signing.py"
Cohesion: 0.16
Nodes (16): load_callback_secret(), FR-CBK-005: request signing so Magic can verify a callback originated from this…, `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), hashlib, hmac, FR-CBK-005 request-signing tests. (+8 more)

### Community 85 - "mock_logger.py"
Cohesion: 0.21
Nodes (12): main(), get_timestamps(), Path, Rotate with numbered retained archives, like ``logrotate``.…, rotate_if_needed(), run_harness(), argparse, sys (+4 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (15): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact…, The exact 3-order story from the Metrics Aggregator quickstart: two accepted… (+7 more)

### Community 87 - "Rule Engine demo runbook"
Cohesion: 0.15
Nodes (12): 1. `make rules-test`, 2. `make rules-quickstart`, 3. `make rules-reload-demo`, Going deeper, if asked, If someone asks, Pre-flight, Rule Engine demo runbook, make rules-quickstart (17-act demo) (+4 more)

### Community 88 - "Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing)"
Cohesion: 0.22
Nodes (9): Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Text Field Normalisation (FR-PRS-022), Error Response Shape (§7), Prompt-Injection and Abuse Considerations (FR-NLQ-023/024), NFR-SEC-015: Canonicalised Allowed Roots, Symlinks Refused, Security: Input Handling (§3.4), Agent Configuration Schema (§1) (+1 more)

### Community 89 - "test_degraded_status_flows_into_heartbeat_payload"
Cohesion: 0.15
Nodes (13): Path, Offset survives a clean shutdown + fresh process, but read-lag knowledge does…, FR-HLT-001: degraded read lag has to survive the actual heartbeat wire format., One file being deleted out from under the agent must not crash the health…, HealthReporter wired to a real MultiLogMonitor, not a hand-built dict., Simulates logrotate: old file renamed away, new file created at the same path., Same inode, smaller size in place - e.g. a logger truncates instead of rotating., test_degraded_status_flows_into_heartbeat_payload() (+5 more)

### Community 90 - "internal.py"
Cohesion: 0.27
Nodes (9): healthz(), metrics(), get, Response, Operator probes (UBS-96; FR-HLT-010, FR-HLT-012; spec 007 s5.3). Mounted on the…, Liveness only: the process is up and serving. No dependency checks, so a broken…, Readiness incl. warm-up (FR-QRY-005), from the same…, readyz() (+1 more)

### Community 91 - "Heartbeat"
Cohesion: 0.14
Nodes (10): AgentRecord, datetime, Agent Registry (spec 006 FR-ING-010; UBS-69 read side, UBS-87 write side). One…, `missing` if stale, otherwise whatever the agent last reported., Agent IDs past the threshold - the `dataCompleteness.staleAgents` input (FR-…, Store the latest heartbeat. Returns True on first contact so the caller can…, _utc_now(), Heartbeat (+2 more)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (16): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Configurability NFRs (§5), NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test), NFR-SEC-012: Order Identifier Hashing, Rotatable Key, NFR-SEC-013: No Raw-Log Debug Mode in Release Build (+8 more)

### Community 94 - "publisher.py"
Cohesion: 0.17
Nodes (13): make_pending_item(), PendingItem, datetime, FR-PUB-004: a pending-item buffer bounded by both total bytes and maximum age,…, Measured once at insert and cached on the `PendingItem` -- re-measuring on…, Remove and return up to `max_items` from the front., _size_of(), classify_publish_response() (+5 more)

### Community 95 - "heartbeat_json"
Cohesion: 0.09
Nodes (24): heartbeat_json(), Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, telemetry_agent_health_reporter, FakeClock, datetime, Path, Agent Health Reporter (UBS-58/59/60) -> Ingestion (UBS-66) -> health read side…, Agents publish a heartbeat inside the 10s batch (FR-PUB-001), not only through… (+16 more)

### Community 96 - "classify_http_status"
Cohesion: 0.25
Nodes (13): classify_http_status(), StrEnum, FR-CBK-006: HTTP outcome -> retry decision classification., `FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent failure., RetryDecision, enum, parametrize, FR-CBK-006 HTTP status -> retry decision classification tests. (+5 more)

### Community 97 - "CallbackDispatcher"
Cohesion: 0.14
Nodes (10): CallbackDispatcher, Logger, Sync, non-blocking — the entry point a future wiring step calls from the same…, Spawns `maxInflight` workers pulling from the queue. Runs until cancelled by…, Signs and sends `alert`, retrying transient failures with backoff (`FR-…, CallbackSink, Protocol, The transport boundary. `HttpsCallbackSink` is the Day-1 default;… (+2 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (10): _CountingRing, datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in…, The old `tick()` swept every instance's ring on every merge — O(instances x…, A query over one 10s bucket on a 6h-capacity (2160-bucket) ring must not touch…, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to() (+2 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.09
Nodes (38): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent, BaseModel (+30 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.11
Nodes (27): extract_allowlisted_fields(), _hash_or_none(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, FR-PRS-020: extract only the tags in the compile-time allowlist above.…, hash_identifier(), load_hash_key(), Identifier hashing (FR-PRS-021)., HMAC-SHA256 of `raw` keyed with `key`, truncated to 16 hex chars. (+19 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (13): _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any…, _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved() (+5 more)

### Community 103 - "test_QRY_04_concurrency.py"
Cohesion: 0.13
Nodes (18): FR-QRY-004: the store MUST be safe under concurrent read/write via a per-…, A per-instance lock must still serialise writes *within* one instance — safety…, `dropped_after_retention_total` is a single store-wide counter incremented from…, `StreamProcessor.dropped_buckets_total` is incremented outside any per-instance…, `_get_or_create_instance` sets `_rings[instance_id]` before…, `_shed_oldest_tier` iterates `_rings.items()` and indexed `_instance_locks`…, _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another() (+10 more)

### Community 104 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 105 - "ingest_guard.py"
Cohesion: 0.16
Nodes (12): IngestGuardConfig, UBS-85: batch dedupe (FR-ING-004) and per-agent rate limiting (FR-ING-008).…, IngestGuard, datetime, Batch dedupe and per-agent rate limiting (UBS-85; FR-ING-004, FR-ING-008).…, Record a batch that is now on the ingest queue., _utc_now(), deque (+4 more)

### Community 106 - "demo_reload.py"
Cohesion: 0.26
Nodes (11): _banner(), _instructions(), main(), Path, Live walkthrough of SIGHUP rule reloading (`FR-RUL-008`/`009`). uv run python…, The watched file may be mid-edit or deliberately broken; a failed read here…, _run(), _safe_rule_count() (+3 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "health-reporter-overview.md"
Cohesion: 0.18
Nodes (10): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration, Not in this change (+2 more)

### Community 109 - "services/self_metrics.py"
Cohesion: 0.12
Nodes (16): _BoundSourcesCollector, _counter(), _gauge(), datetime, Backend self-metrics (UBS-96; FR-HLT-010, spec 006 s7). `SelfMetrics` owns a…, Recompute per-agent gauges from the registry. Called per scrape so the exporter…, (body, content-type) for `GET /metrics`., Reads ingestion / stream processor / store state at scrape time. (+8 more)

### Community 110 - "Requirement ID Scheme (FR-<AREA>-<NNN>)"
Cohesion: 0.16
Nodes (15): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Health Reporter (component), Ingestion Service (component) (+7 more)

### Community 111 - ".validate_and_reserve"
Cohesion: 0.18
Nodes (8): IngestionValidationIssue, Apply the backend-side allowlists and bucket cardinality cap. Pydantic has…, Undo an admission reservation when the bounded queue is full., Bound an attacker-controlled key before including it in an error path., One safe, field-level reason an ingestion request was rejected., _safe_key(), _CardinalityBucketKey, _SeriesKey

### Community 112 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (9): batch(), deps(), FakeClock, metrics(), datetime, UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)., test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() (+1 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "parse_fix_timestamp"
Cohesion: 0.27
Nodes (9): parse_fix_timestamp(), datetime, timedelta, Parse FIX SendingTime/TransactTime as UTC., TimestampResult, FR-PRS-025/026 timestamp tests., test_FR_PRS_025_bad_timestamp_falls_back_to_log(), test_FR_PRS_025_parses_fix_timestamp_utc() (+1 more)

### Community 115 - "BackendConfigError"
Cohesion: 0.18
Nodes (9): BackendConfigError, Exception, Raised when `config/backend.yaml` exists but is invalid., _build_parser(), main(), ArgumentParser, `uv run telemetry-backend [--config config/backend.yaml]`. A missing config…, parametrize (+1 more)

### Community 116 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.25
Nodes (8): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Agent Restart Sequence (§8.2), NL Evaluation Requirements (FR-NLQ-025), End-to-End Acceptance Scenario (FR-TST-010), NL Evaluation Harness (FR-TST-007–009), Synthetic Load Generator (tools/fixgen, FR-TST-006), Cardinality Control (per-bucket max_label_sets/max_series_per_bucket)

### Community 117 - "test_reporter.py"
Cohesion: 0.61
Nodes (7): make_monitor(), Path, test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 118 - "BackendHealthConfig"
Cohesion: 0.29
Nodes (7): BackendHealthConfig, Path, test_defaults_follow_spec_010(), test_invalid_values_are_refused(), test_invalid_yaml_is_refused(), test_missing_file_yields_defaults(), test_reads_backend_store_alerting_sections()

### Community 119 - "data_completeness.py"
Cohesion: 0.47
Nodes (5): build(), DataCompleteness, datetime, `dataCompleteness` block for query responses (spec 006 s4.1, FR-QRY-015).…, Derive completeness from the registry at `at`. `expected_agent_ids` is the set…

### Community 120 - ".__init__"
Cohesion: 0.20
Nodes (7): Logger, PublishSink, Protocol, The transport boundary. `HttpsPublishSink` is the Day-1 default (ADR 0003);…, BackendUnreachableCallback, DropCallback, HeartbeatProvider

### Community 121 - "Stream Processor (component)"
Cohesion: 0.50
Nodes (4): Stream Processor (component), architecture-overview.png (client architecture diagram showing Stream Processor box), Ingestion Requirements (FR-ING-001–010), Stream Processing Requirements (FR-STM-001–006)

### Community 122 - "Query Engine Requirements (FR-QRY-006–014)"
Cohesion: 0.50
Nodes (4): Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009)

### Community 123 - "Implementation Status live document"
Cohesion: 0.24
Nodes (10): Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, Implementation Status live document, M1.5 Pipeline bridge (UBS-48/49), M1 Log monitor and configuration (not started), M2 FIX parser (UBS-40-47), M3 Metrics aggregation (MA-01-04) (+2 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "test_UBS_104_outage_isolation.py"
Cohesion: 0.29
Nodes (7): _HangingSink, _make_alert(), _make_snapshot(), UBS-104 integration test: `NFR-REL-003` -- a backend outage must never affect…, Stands in for a backend that never responds -- e.g. a dropped connection to a…, _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher()

### Community 127 - "Rule Engine"
Cohesion: 0.13
Nodes (20): CallbackFailing rule, NoLogActivity rule, Multi-tier severity rule shape, M5 Rules, alerts, callbacks, AgentCounterSampler (UBS-74), Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Dependent suppression (FR-RUL-021) (+12 more)

### Community 128 - "test_log_monitor_status.py"
Cohesion: 0.62
Nodes (6): make_monitor(), Path, test_status_after_read_reports_elapsed_lag(), test_status_before_any_read_has_no_lag(), test_status_missing_file_has_no_size_but_does_not_raise(), test_status_reports_offset_progress_between_polls()

### Community 129 - "effective_reject_reason"
Cohesion: 0.33
Nodes (7): effective_reject_reason(), Single precedence: ordRejReason → rejectReasonText label → unspecified. For…, FR-PRS-024 rejection precedence tests., test_FR_PRS_024_ord_rej_reason_wins(), test_FR_PRS_024_session_reject_for_msg_type_reject(), test_FR_PRS_024_text_label_when_no_ord_rej(), test_FR_PRS_024_unspecified_when_missing()

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "008 — Natural Language Query Layer (Copilot/Teams)"
Cohesion: 0.40
Nodes (5): Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents), NL Intent Catalogue (FR-NLQ-003/004), 008 — Natural Language Query Layer (Copilot/Teams)

### Community 133 - "NFR-REL-003: Backend Outage Must Not Affect Alerting"
Cohesion: 0.50
Nodes (5): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), NFR-REL-003: Backend Outage Must Not Affect Alerting, Reliability NFRs (§2), Runbook: Backend Unreachable

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 137 - "PipelineStats"
Cohesion: 0.33
Nodes (3): PipelineStats, Queue depths and drop counters for heartbeat/metrics (FR-PIP-005)., test_pipeline_stats_expose_prometheus_metric_names()

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 195 - "IngestionService"
Cohesion: 0.14
Nodes (32): BatchAccepted, IngestionService, Keep store work off FastAPI's request path. A single consumer preserves the…, Owns a bounded queue and one background consumer., fastapi_routing, EventsRequest, model_validator, Convenience endpoint request for events. (+24 more)

### Community 210 - "rules/demo_quickstart.py"
Cohesion: 0.09
Nodes (29): _alert_storm_act(), _backend_unreachable_act(), attempt(), _dedup_act(), _FlakyBackendSink, _heartbeat_timeout_act(), main(), _no_log_activity_act() (+21 more)

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **179 isolated node(s):** `1. What the Health Reporter is for`, `2.1 One heartbeat tick, as a sequence`, `5.1 The window — `health/window.py``, `9. How to verify / demo`, `Also touched, and why` (+174 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1182 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **84 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `config/rules.yaml live rule set` to `MetricsAggregator ring buffer`, `Implementation Status live document`, `snapshot`, `Rule Engine`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `Telemetry System Documentation Index` connect `Telemetry System Documentation Index` to `ADR 0004: Raw log content is never persisted or transmitted`, `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1`, `Telemetry Agent (architecture constraint)`, `ADR 0001: Telemetry Agent written in Go (Superseded)`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `Spec 004: Telemetry data model` connect `Telemetry Agent (architecture constraint)` to `Telemetry System Documentation Index`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 49 INFERRED edges - model-reasoned connections that need verification._