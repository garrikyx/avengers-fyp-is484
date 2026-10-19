# Graph Report - avengers-fyp-is484  (2026-10-16)

## Corpus Check
- 337 files · ~186,108 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 9, .example 1, .typed 1)

## Summary
- 4348 nodes · 11473 edges · 280 communities (156 shown, 124 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 2075 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `edb7142f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Snapshot
- FixParser
- test_metrics_event.py
- RuleConfig
- make_snapshot
- config_loader.py
- Module map (`apps/agent/src/telemetry_agent/health/`)
- test_RE_02_evaluators.py
- RetryPolicy
- LatencyCorrelator
- derive_counters
- test_RE_publish_integration.py
- test_heartbeat.py
- LogMonitor
- PublishBuffer
- SourceMeta
- metrics_event.py
- PublishResult
- MetricsAggregator
- EventStore
- test_RE_session_integration.py
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- heartbeat.py
- telemetry_agent/config.py
- BackendPublisher
- Agent
- DeliveryTracker
- HeartbeatConfig
- test_MA_05_agent_counters.py
- AggregatorConfig
- test_agent_heartbeat_reaches_the_health_endpoint
- test_UBS_113_evaluator.py
- test_MA_03_correlation.py
- test_health_monitor_e2e.py
- config/rules.yaml live rule set
- create_app
- session_tracker.py
- MetricsAggregator ring buffer
- AgentRegistry
- _dispatch
- test_parse_errors.py
- pytest
- 001 — Architecture
- CamelModel
- HealthReporter
- callbacks/config.py
- callbacks/demo_quickstart.py
- telemetry_agent_callbacks_config
- cli.py
- Histogram
- parse_publish_config
- QueryEngine
- test_STM_02_merge_semantics.py
- LineClassification
- from_alert_event
- CallbackDispatcher
- AlertEvent
- Confidence
- test_queue_depth.py
- HeartbeatMonitor
- PipelineBridge
- test_UBS_116_app_log_counters.py
- enrich.py
- publishing/demo_quickstart.py
- _Demo
- Telemetry Backend (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- DropOldestQueue
- test_agent_registry.py
- http
- 009 — Non-Functional Requirements and Security
- rules/demo_quickstart.py
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- 003 — Parser Engine and FIX Parsing
- _Harness
- pipeline_demo.py
- IngestionService
- datetime
- services/demo_quickstart.py
- signing.py
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- HttpsPublishSink
- test_ING_004_008_routes.py
- QueryConfig
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- build_batch
- MultiLogMonitor
- telemetry_agent_callbacks_backoff
- StreamProcessor
- test_STM_04_efficiency.py
- ParsedMessageEvent
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- test_QRY_04_concurrency.py
- StreamProcessorConfig
- AgentHeartbeat
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- MetricsQueryResponse
- telemetry_backend/config.py
- test_backend_self_metrics.py
- test_publishing_helpers.py
- PublishAction
- telemetry_shared shared schema package
- OffsetTracker
- UBS-30 Implementation Notes
- test_UBS_122_signature_rules.py
- test_UBS_115_snapshot_to_metricstore.py
- test_UBS_109_rule_engine_to_backend.py
- MetricsIngestor
- ParseResult
- mock_logger.py
- test_UBS_115_snapshot_bridge.py
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- reporter.py
- telemetry_agent_parser_applog_signatures
- Rule Engine
- ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server
- ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- collections_abc
- _Clock
- telemetry-shared
- telemetry_agent_parser_applog_telemetry
- telemetry_agent_parser_config
- telemetry_agent_callbacks_payload
- telemetry_agent/__init__.py
- telemetry_agent_parser_corpus
- telemetry_agent_parser_display
- telemetry_backend/__init__.py
- Auditability & Compliance rationale (deterministic order audit trails)
- build_parsed_message_event
- teams_agent/__init__.py
- test_RE_integration.py
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
- telemetry_agent_callbacks_queue
- metric_store.py
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
- _BoundSourcesCollector
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- AlertStore
- telemetry_agent_parser_fix_telemetry
- telemetry_agent_callbacks_retry
- telemetry_agent_parser_registry
- telemetry_agent_callbacks_self_metrics
- telemetry_agent_callbacks_signing
- test_RE_parse_error_integration.py
- telemetry_shared_metrics
- telemetry_shared_metrics_histogram
- test_degraded_status_flows_into_heartbeat_payload
- telemetry_agent_common_backoff
- ._serialize_counters
- Rule Engine demo runbook
- decimal
- test_UBS_110_alert_router_callbacks.py
- MA-04: calculated indicators and snapshot output.
- DryRunCallbackSink
- http_server
- publishing/__init__.py
- telemetry_agent_logs_log_monitor
- telemetry_agent_logs_offset_tracker
- telemetry_agent_parser_fix_fields
- telemetry_agent_callbacks_dispatcher
- telemetry_agent_parser_fix_seq_tracker
- telemetry_agent_parser_fix_timestamps
- .__init__
- telemetry_agent_callbacks_sink
- telemetry_agent_common_self_metrics
- telemetry_agent_parser_applog_parser
- telemetry_agent_callbacks_status
- telemetry_agent_publishing_batch
- telemetry_shared_models_parsed_message
- telemetry_agent_publishing_buffer
- telemetry_agent/main.py
- telemetry_agent_publishing_outcome
- telemetry_agent_parser_fix_parser
- telemetry_agent_parser_fix_session_tracker
- telemetry_backend_api
- telemetry_backend_services_ingest_guard
- telemetry_backend_services_ingestion
- telemetry_backend_services_stream_processor
- telemetry_agent_parser_metrics_event
- telemetry_shared_models_alerts_query
- telemetry_shared_models_base
- telemetry_shared_models_ingestion
- telemetry_agent_parser_protocol
- telemetry_shared_models_snapshot
- telemetry_agent_pipeline_alert_router
- telemetry_agent_pipeline_committer
- telemetry_agent_pipeline_config
- telemetry_agent_pipeline_deduper
- telemetry_agent_pipeline_monitor_adapter
- telemetry_agent_pipeline_supervisor
- telemetry_agent_pipeline_types
- telemetry_agent_pipeline_ingest
- telemetry_agent_publishing_config
- telemetry_agent_publishing_publisher
- telemetry_agent_publishing_sink
- telemetry_shared_models_alerts
- urllib_error
- urllib_request
- telemetry_shared_models_metrics
- test_UBS45_integration.py
- Heartbeat
- Issue tracker: Jira
- Telemetry Agent (architecture constraint)
- Metrics Query API (UBS-68, UBS-91, UBS-92)
- End-to-End Acceptance Scenario (FR-TST-010)
- test_reporter.py
- .seed
- services/self_metrics.py
- test_log_monitor_status.py
- data_completeness.py
- .fire

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 119 edges
2. `HealthReporter` - 89 edges
3. `create_app()` - 83 edges
4. `BackendPublisher` - 80 edges
5. `AlertEvent` - 80 edges
6. `MetricStore` - 77 edges
7. `StreamProcessorConfig` - 75 edges
8. `SourceMeta` - 74 edges
9. `FixParser` - 69 edges
10. `CamelModel` - 64 edges

## Surprising Connections (you probably didn't know these)
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py
- `Multi-replica mode (UBS-92)` --references--> `QueryConfig`  [INFERRED]
  docs/plan/metrics-query-api.md → apps/backend/src/telemetry_backend/config.py
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

## Communities (280 total, 124 thin omitted)

### Community 0 - "Snapshot"
Cohesion: 0.13
Nodes (36): attempt(), BatchAccepted, fastapi_routing, EventsRequest, model_validator, Convenience endpoint request for events., Primary ingestion request., Reject accidental cross-agent batches before they enter the queue. (+28 more)

### Community 1 - "FixParser"
Cohesion: 0.06
Nodes (57): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+49 more)

### Community 2 - "test_metrics_event.py"
Cohesion: 0.13
Nodes (26): _meta(), _parser_counters(), datetime, Decimal, parametrize, Tests for parser/metrics_event.py — the ParseResult -> ParsedMessageEvent…, A backwards sequence carries gap_size=0, so counting it as seq_gaps would fire…, A counter the aggregator has no dimension set for raises KeyError at ingest… (+18 more)

### Community 3 - "RuleConfig"
Cohesion: 0.11
Nodes (37): _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _metric_context(), datetime, Decimal (+29 more)

### Community 4 - "make_snapshot"
Cohesion: 0.20
Nodes (29): make_gauges(), make_snapshot(), `empty=True` builds a snapshot with zero groups (nothing ingested this window…, _gauge_rule(), test_gauge_evaluator_none_when_gauge_is_none(), test_gauge_evaluator_reads_gauge_value(), _engine(), _fire() (+21 more)

### Community 5 - "config_loader.py"
Cohesion: 0.08
Nodes (36): load_rules(), load_rules_from_yaml(), _parse_duration_seconds(), Any, BaseModel, datetime, Exception, field_validator (+28 more)

### Community 6 - "Module map (`apps/agent/src/telemetry_agent/health/`)"
Cohesion: 0.11
Nodes (16): datetime, Per-file read health, keyed by the same name `monitors` was built with., Worst-case lag across files (heartbeat gauge). None if none have read yet., Files whose lag exceeds the threshold. Unread files are never flagged., Count one parsed line, and a parse error if `is_parse_error(result)`., Count a parse error from a producer that does not hand over a `ParseResult`…, Count `n` buffer-eviction drops (`droppedEventsLast5Min`, `FR-PUB-004`) at…, (depth, trend) sampled now; trend compares with the previous sample so… (+8 more)

### Community 7 - "test_RE_02_evaluators.py"
Cohesion: 0.16
Nodes (24): make_indicator(), make_indicators(), make_latency(), datetime, Decimal, Shared test support for the rules package: builds `MetricsSnapshot` fixtures…, _absence_rule(), _latency_rule() (+16 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.13
Nodes (17): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, random, FR-CBK-004 exponential backoff with jitter tests., test_FR_CBK_004_delay_doubles_per_attempt_with_factor_2() (+9 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.08
Nodes (27): CorrelatorStats, LatencyCorrelator, OrderContext, Clock, datetime, Decimal, timedelta, MA-03: order correlation and latency. Standalone producer into the shared… (+19 more)

### Community 10 - "derive_counters"
Cohesion: 0.09
Nodes (42): derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MA-02: order / execution / reject counters and reject-reason normalisation.…, All four counter families in one event walk., fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not OrdStatus —…, Config-driven raw-reason -> canonical-label mapping. Backs MetricsAggregator's… (+34 more)

### Community 11 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (22): _aggregator(), _engine(), _fail_n_times(), _publisher(), UBS-75 integration: BackendPublisher -> consecutive_publish_failures gauge ->…, The whole reason this is a gauge: recovery is observable. A windowed failure…, FR-MET-031. An agent with no publisher must not look like an agent that is…, Regression guard on spec 005 §1.2's withdrawn approximation.… (+14 more)

### Community 12 - "test_heartbeat.py"
Cohesion: 0.12
Nodes (19): Collect, FakeClock, datetime, LogCaptureFixture, UBS-58 / FR-HLT-001: heartbeat emitter and wire format., AC: an idle agent still heartbeats; N ticks in ~N intervals., A sink stuck in blocking I/O must not starve other coroutines., _reporter() (+11 more)

### Community 13 - "LogMonitor"
Cohesion: 0.07
Nodes (26): Harvester, LogMonitor, datetime, Path, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, One complete log line with stable byte identity for idempotent ingest., Find retained rotations that were created while the agent was down. This… (+18 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.06
Nodes (38): make_pending_item(), PendingItem, PublishBuffer, datetime, FR-PUB-004: a pending-item buffer bounded by both total bytes and maximum age,…, Put previously-`take`n items back at the front, in original order -- they are…, Measured once at insert and cached on the `PendingItem` -- re-measuring on…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both… (+30 more)

### Community 15 - "SourceMeta"
Cohesion: 0.05
Nodes (40): Demo metrics sink for parser CLI (mirrors spec 004 counter names)., Metadata attached to each log line by the monitor., SourceMeta, QueueSnapshot, PipelineCommitter, Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)., Consumes ParsedEvent objects and commits file offsets after ingest., LinePosition (+32 more)

### Community 16 - "metrics_event.py"
Cohesion: 0.13
Nodes (24): _fixed_now(), main(), Minimal walkthrough of parser/metrics_event.py: the same three-order story as…, _step(), FixTelemetry, Sanitized telemetry derived from a framed FIX message., derive_parser_counters(), derive_session_counters() (+16 more)

### Community 17 - "PublishResult"
Cohesion: 0.12
Nodes (16): PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, _FlakyBackendSink, Backend stand-in for the UBS-75 act: answers whatever `status` currently says,…, _HangingSink, Stands in for a backend that never responds -- e.g. a dropped connection to a…, _StatusSink, _config() (+8 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.10
Nodes (30): _Bucket, _dimension_value(), MetricRow, MetricsAggregator, Clock, datetime, Decimal, Shared metrics store (spec 004 §3): a time-bucketed ring buffer holding both… (+22 more)

### Community 19 - "EventStore"
Cohesion: 0.08
Nodes (35): EventStoreConfig, Event store retention (UBS-118; spec 010 `store.recentAlertLimit` default)., EventStore, _InstanceEvents, datetime, Lock, In-memory Event Store (UBS-118)., Per-instance bounded event history. (+27 more)

### Community 20 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (29): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), Decimal, UBS-73 integration: raw FIX log bytes -> FixParser -> metrics_event bridge ->…, A tracker that has watched `lines` go past, so it knows which sessions exist… (+21 more)

### Community 21 - "MetricStore"
Cohesion: 0.11
Nodes (19): _CanonicalBucket, MetricStore, datetime, Lock, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a…, Evict buckets that have aged out of retention within *one* instance's ring —…, Evict stale buckets across every instance's ring and check memory pressure. For… (+11 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.07
Nodes (36): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+28 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.13
Nodes (35): _key(), _keys(), _observe(), UBS-106: SessionHeartbeatTracker — the `heartbeat_timeouts` producer. A…, A logged-out session is silent forever. Counting that as a timeout would…, SeqTracker accepts both normalized names and raw tag values ("Logon"/"A");…, FIX only requires a Heartbeat when the session is otherwise idle, so a session…, Session keys from a timed_out() result, for terse assertions. (+27 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.13
Nodes (24): AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry, HealthSignals sampled instant, heartbeat_json() serialisation helper (+16 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "heartbeat.py"
Cohesion: 0.13
Nodes (20): datetime, Heartbeat emitter (UBS-58, FR-HLT-001). Ticks on a fixed interval regardless of…, Build and send one heartbeat. Sink failures are counted, not raised: a dead…, Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat(), telemetry_agent_health_heartbeat, telemetry_agent_health_wire, make() (+12 more)

### Community 27 - "telemetry_agent/config.py"
Cohesion: 0.12
Nodes (34): AgentConfigError, load_agent_config(), LogsConfig, _LogsYaml, ParsingConfig, _ParsingYaml, _PipelineYaml, Any (+26 more)

### Community 28 - "BackendPublisher"
Cohesion: 0.08
Nodes (20): CounterRegistry, Plain dict of named counters behind a lock -- increments happen from both async…, Logger, AbstractContextManager, Any, Logger, BackendPublisher, UBS-75 / `FR-MET-031`: failed attempts in a row since the last successful… (+12 more)

### Community 29 - "Agent"
Cohesion: 0.13
Nodes (22): Agent, Magic log simulator — generates configurable FIX send/receive logs., agent(), Exception, fixture, MonkeyPatch, parametrize, Path (+14 more)

### Community 30 - "DeliveryTracker"
Cohesion: 0.07
Nodes (40): classify_http_status(), StrEnum, FR-CBK-006: HTTP outcome -> retry decision classification., `FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent failure., RetryDecision, DeliveryRecord, DeliveryStatus, DeliveryTracker (+32 more)

### Community 31 - "HeartbeatConfig"
Cohesion: 0.10
Nodes (35): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, HeartbeatConfig, _HeartbeatYaml, load_health_config() (+27 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.14
Nodes (24): AgentCounterSampler, datetime, Turns monotonic since-startup counters into per-bucket deltas. Stateful across…, Ingest the increase in each tracked counter since the last call. The first call…, _aggregator(), Decimal, UBS-74: `MetricsAggregator.ingest_agent_counters` and the `AgentCounterSampler`…, A restarted dispatcher's registry drops back to 0. That is a new baseline, not… (+16 more)

### Community 33 - "AggregatorConfig"
Cohesion: 0.17
Nodes (23): AggregatorConfig, Bucket granularity, retained windows, and the per-metric dimension table (FR-…, FakeClock, Shared test support for the metrics package: a hand-labelled synthetic FIX-…, A `Clock` (`() -> float`) that only advances when told to — lets a test assert…, make_event(), minimal_aggregator(), Decimal (+15 more)

### Community 34 - "test_agent_heartbeat_reaches_the_health_endpoint"
Cohesion: 0.25
Nodes (5): FakeClock, datetime, Path, test_agent_heartbeat_reaches_the_health_endpoint(), test_unknown_agent_is_404()

### Community 35 - "test_UBS_113_evaluator.py"
Cohesion: 0.15
Nodes (25): _names(), Path, UBS-113: RuleEvaluator — the periodic loop between the metrics store and…, RejectSpike reads 1m, HighRejectRate reads 5m: one tick, both., The tracker latches each silence: many ticks after the timeout still put…, A rules file the loader accepts, from the shipped config's own entries, so the…, _rule(), _Stack (+17 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "test_health_monitor_e2e.py"
Cohesion: 0.11
Nodes (19): committed_offsets(), FakeClock, fix_lines(), datetime, FastAPI, fixture, MonkeyPatch, Path (+11 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.12
Nodes (25): Agent processing pipeline (monitor to health reporter), publish: Backend Publisher config block, BackendUnreachable rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule (+17 more)

### Community 39 - "create_app"
Cohesion: 0.07
Nodes (45): HTTP routers, one file per concern (spec 007). `health.py` (UBS-69) serves the…, AlertsQueryParams, _build_parser(), _counts(), create_app(), enqueue_or_full(), get_alert(), get_event() (+37 more)

### Community 40 - "session_tracker.py"
Cohesion: 0.18
Nodes (8): UBS-106: per-session heartbeat-timeout detection. A heartbeat timeout is the…, Stop tracking a session. Called on `Logout`, and the reason this exists: a…, Internal tracking key, identical in format to `SeqTracker.session_key`.…, Record that a session was heard from at `at`. Any message counts, not just…, _SessionState, The canonical `session_id` *dimension* value (`FR-MET-030`). Deliberately…, session_id_for(), _session_id()

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.14
Nodes (19): AckLatencyBreach rule, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent), Histogram (fixed buckets, merge, percentile), MA-epic known gaps (ExecID dedup, timestamp_source) (+11 more)

### Community 42 - "AgentRegistry"
Cohesion: 0.13
Nodes (12): AgentRecord, AgentRegistry, Clock, datetime, Agent Registry (spec 006 FR-ING-010; UBS-69 read side, UBS-87 write side). One…, `missing` if stale, otherwise whatever the agent last reported., Agent IDs past the threshold - the `dataCompleteness.staleAgents` input (FR-…, Thread-safe map of known agents. Memory-only by design (FR-QRY-005). (+4 more)

### Community 43 - "_dispatch"
Cohesion: 0.20
Nodes (14): _aggregator(), _alert(), _dispatch(), _drain(), _fire(), The registry is monotonic, so re-ingesting its absolute value on every tick…, `secondsSinceLastEvent` must stay untouched by the agent's own counters —…, Send `count` alerts to a Magic endpoint that always answers `status`, and… (+6 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.17
Nodes (17): FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides(), test_errors_counted_and_reported_in_heartbeat() (+9 more)

### Community 45 - "pytest"
Cohesion: 0.06
Nodes (48): Clock, datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, drive() (+40 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.10
Nodes (28): Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), Consistent-Hash Routing on instanceId, 001 — Architecture, Failure Degradation Order (queries → freshness → callbacks → alerting) (+20 more)

### Community 47 - "CamelModel"
Cohesion: 0.08
Nodes (45): Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, RejectedItem, AlertCounts, AlertDelivery, AlertDetailResponse, AlertRecord, AlertsListResponse (+37 more)

### Community 48 - "HealthReporter"
Cohesion: 0.09
Nodes (24): heartbeat_json(), Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, HealthReporter, Clock, Count successfully parsed lines in bulk (denominator only)., Register (or remove) the Publisher's buffer-bytes callback…, Aggregates agent health signals and derives spec 011 §2 status., BufferBytesProvider (+16 more)

### Community 49 - "callbacks/config.py"
Cohesion: 0.10
Nodes (27): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+19 more)

### Community 50 - "callbacks/demo_quickstart.py"
Cohesion: 0.13
Nodes (14): main(), _make_alert(), _print_counters(), Minimal walkthrough of the Callback Dispatcher (UBS-32/33). uv run python -m…, Stands in for Magic: keys its canned response off the alert ID inside the…, _run_one(), _ScriptedSink, _step() (+6 more)

### Community 52 - "cli.py"
Cohesion: 0.09
Nodes (36): compile_signature_rules(), extract_log_level(), First-match-wins signature rules with dynamic label templates., Extract [N/E/W/F/I] level from Magic-style log lines., resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule (+28 more)

### Community 53 - "Histogram"
Cohesion: 0.09
Nodes (26): spec 004 §5 / FR-ING-007: the dimension-key allowlist shared by both trust-…, Histogram, Decimal, Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012). Shared…, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, build_latency_summary() (+18 more)

### Community 54 - "parse_publish_config"
Cohesion: 0.12
Nodes (31): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, _PublishYaml, Any, BaseModel (+23 more)

### Community 55 - "QueryEngine"
Cohesion: 0.11
Nodes (22): _AccumulatedGroup, datetime, Decimal, DimKey, Exception, timedelta, QueryEngine, QueryTimeoutError (+14 more)

### Community 56 - "test_STM_02_merge_semantics.py"
Cohesion: 0.23
Nodes (15): HistogramPayload, Wire shape of one histogram (`FR-MET-025`/`FR-MET-026`): fixed boundaries…, Reconstruct a mergeable `Histogram`, keyed on the canonical boundary set rather…, _histogram_payload(), FR-STM-002/003/004: counters merge by summation; ratios are recomputed from…, Two agents of unequal volume (FR-STM-003's required test shape): agent A:…, A retried publish that misses batchId-level dedupe (a different ticket's…, _read_one_group() (+7 more)

### Community 57 - "LineClassification"
Cohesion: 0.09
Nodes (31): AppLogParser, Parser plugin for configured application log patterns (Magic format)., _explain_classification(), Pattern, classify_line(), compile_app_log_patterns(), _looks_like_fix(), Pattern (+23 more)

### Community 58 - "from_alert_event"
Cohesion: 0.20
Nodes (15): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, make_alert_event(), Shared test support for the callbacks package: builds `AlertEvent` fixtures…, FR-CBK-001/002/003 callback payload shape tests. (+7 more)

### Community 59 - "CallbackDispatcher"
Cohesion: 0.16
Nodes (16): CallbackDispatcher, Spawns `maxInflight` workers pulling from the queue. Runs until cancelled by…, Signs and sends `alert`, retrying transient failures with backoff (`FR-…, HttpsCallbackSink, AsyncBaseTransport, `FR-CBK-001`: HTTPS POST to the configured Magic endpoint. Rejects plain HTTP…, _make_alert(), UBS-32/33 integration test: dispatch and retry against a mock Magic endpoint.… (+8 more)

### Community 60 - "AlertEvent"
Cohesion: 0.07
Nodes (26): Sync, non-blocking — the entry point a future wiring step calls from the same…, AlertRouter, datetime, Run one path's enqueue so its failure stays on that path., Enqueues alerts for publication, rejecting any that would poison the batch they…, Self-observability, same shape as `BackendPublisher.counters` and…, Hand every alert to the Callback Dispatcher (if configured), and every alert…, datetime (+18 more)

### Community 61 - "Confidence"
Cohesion: 0.06
Nodes (28): Confidence, Parser, Enum, Protocol, str, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'. (+20 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.14
Nodes (21): HeartbeatEmitter, Event, Tick every `interval_seconds` until `stop` is set. First tick is immediate so a…, FakeQueue, Flaky, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend., test_at_critical_watermark_is_unhealthy() (+13 more)

### Community 63 - "HeartbeatMonitor"
Cohesion: 0.14
Nodes (12): AlertingConfig, Backend-owned alerting rules (spec 005 `FR-RUL-030`)., backend_alert_id(), HeartbeatMonitor, datetime, Backend-owned `AgentHeartbeatMissing` rule (`FR-QRY-018`, `FR-RUL-030`)., Resolve a backend alert immediately when a fresh heartbeat arrives., Periodically evaluates agent heartbeat staleness. (+4 more)

### Community 64 - "PipelineBridge"
Cohesion: 0.08
Nodes (18): Selects the first parser in a configured chain with Confidence.HIGH., Return unknown parser names in chain., Registry, PipelineConfig, Pipeline bridge sizing (spec 010 §pipeline, FR-PIP-002–004)., PipelineStats, Queue depths and drop counters for heartbeat/metrics (FR-PIP-005)., PipelineBridge (+10 more)

### Community 65 - "test_UBS_116_app_log_counters.py"
Cohesion: 0.15
Nodes (22): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), UBS-116: the Application.log counters, one dispatch per parsed line.…, Dimension values for `derive_app_log_counters`' output — one mapping covering…, Bounds the free-text `component` dimension of `app_log_errors`. The first…, AppLogTelemetry, Structured fields extracted from Magic-style application log lines. (+14 more)

### Community 66 - "enrich.py"
Cohesion: 0.06
Nodes (49): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+41 more)

### Community 67 - "publishing/demo_quickstart.py"
Cohesion: 0.26
Nodes (9): _drain(), main(), _make_snapshot(), _print_state(), datetime, Minimal walkthrough of the Backend Publisher (UBS-103/104). uv run python -m…, Stands in for the backend: returns responses from a fixed script, one per call,…, _ScriptedSink (+1 more)

### Community 68 - "_Demo"
Cohesion: 0.07
Nodes (23): _Demo, Decimal, Holds the one parser/aggregator/engine trio the whole story runs on, so each…, Pretend `by` messages were lost in transit., ExecType/OrdStatus 8 = Rejected, OrdRejReason 3 = ExchangeClosed., 35=3, a session-level Reject — a FIX plumbing problem rather than a trading…, 35=9, a rejected cancel/replace — counted as `cancel_rejects`, kept apart from…, An ack whose SendingTime is `delay_ms` after its order. Latency is measured… (+15 more)

### Community 69 - "Telemetry Backend (architecture constraint)"
Cohesion: 0.13
Nodes (18): Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores, Microsoft Teams as the only user interface, Telemetry Backend (architecture constraint), callbacks: Callback Dispatcher config block (+10 more)

### Community 70 - "AppDeps"
Cohesion: 0.09
Nodes (43): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary(), healthz(), metrics() (+35 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.09
Nodes (13): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+5 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (21): env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), datetime, fixture, TestClient (+13 more)

### Community 73 - "DropOldestQueue"
Cohesion: 0.16
Nodes (9): DropOldestQueue, T, FR-CBK-007: bounded pending queue, drop-oldest on overflow., Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow policy (`FR-…, Enqueue `item`, non-blocking. Returns True if an existing item was dropped to…, FR-CBK-007 bounded queue, drop-oldest overflow tests., test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped() (+1 more)

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.11
Nodes (20): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), Resource Discipline (§9), Compliance and Operability Constraints (§7), Configurability NFRs (§5), 009 — Non-Functional Requirements and Security, NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed (+12 more)

### Community 77 - "rules/demo_quickstart.py"
Cohesion: 0.08
Nodes (29): Sessions that have *just* crossed the threshold, each latched so one silence is…, Introspection for demos/debug; not used by the detection path., One session that has just gone quiet for too long. Carries both identifiers on…, Flags FIX sessions quiet for longer than `timeout_seconds`. Stateful across…, SessionHeartbeatTracker, SessionTimeout, derive_heartbeat_timeout_counters(), UBS-106: one `(dims, counters)` pair per session that just timed out. Takes… (+21 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.23
Nodes (18): The active rule set, including any `apply_rules()` hot-swap, so a caller can…, AlertStatus, _engine(), _fire(), datetime, LogCaptureFixture, Path, skipif (+10 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (18): C++ candidate (rejected: worst-case failure modes), ADR 0001: Telemetry Agent written in Go (Superseded), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), ADR 0002: Telemetry stack is Python 3.14 + FastAPI, .NET alternative (rejected) (+10 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "003 — Parser Engine and FIX Parsing"
Cohesion: 0.15
Nodes (13): Problem P-2: Rejects/failures/latency spikes slow to identify, Parser Engine (component), Parser Engine Agent-Level Contract (FR-PRS-001–003), Scaffold Document (plan/scaffold.md), 003 — Parser Engine and FIX Parsing, Parser Plugin Interface (Python Protocol, FR-PRS-030–032), UBS-40–42 Milestone (parse() returns framing metadata only), UBS-43+ Milestone (deferred telemetry event emission) (+5 more)

### Community 82 - "_Harness"
Cohesion: 0.16
Nodes (8): _Harness, _orders(), Decimal, parametrize, At t=1200 only [1150,1200) is fully retained; 1000-1140 are skipped., Real aggregator (1s buckets, 60s retention) and publisher behind the emitter., _starts(), TestSnapshotEmitter

### Community 83 - "pipeline_demo.py"
Cohesion: 0.12
Nodes (19): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), OverflowPolicy, Path, End-to-end demo: LogMonitor → queue → parse → output → commit. (+11 more)

### Community 84 - "IngestionService"
Cohesion: 0.09
Nodes (22): AcceptedIngestion, IngestionService, IngestionValidationIssue, datetime, Apply the backend-side allowlists and bucket cardinality cap. Pydantic has…, Undo an admission reservation when the bounded queue is full., Try to hand off without waiting; False means callers return 503., Keep store work off FastAPI's request path. A single consumer preserves the… (+14 more)

### Community 85 - "datetime"
Cohesion: 0.12
Nodes (23): Log monitoring, rotation and truncation handling., datetime, Multi-file polling and lifecycle management for the Log Monitor., Return offset and read-lag state for every configured file., FileReadStatus, Value objects published by the Log Monitor., Offset, size and read lag for one monitored file., Connect MultiLogMonitor reads to PipelineBridge (FR-PIP-001/006). (+15 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (15): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact…, The exact 3-order story from the Metrics Aggregator quickstart: two accepted… (+7 more)

### Community 87 - "signing.py"
Cohesion: 0.12
Nodes (19): load_callback_secret(), FR-CBK-005: request signing so Magic can verify a callback originated from this…, `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), _burst(), Path, UBS-114 / FR-TST-010 slice: the real agent process, end to end. `build_agent` +… (+11 more)

### Community 88 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.15
Nodes (14): ADR 0004: No-Raw-Persistence Design, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Log Ingestion and Metric Publication Sequence (§8.1), Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing), Parser Invocation via Pipeline Bridge (§0), Text Field Normalisation (FR-PRS-022) (+6 more)

### Community 89 - "HttpsPublishSink"
Cohesion: 0.13
Nodes (15): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), AsyncBaseTransport, `FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the compressed…, `FR-PUB-001`/`002`: HTTPS POST with a bearer token, gzip above…, gzip, Headers (+7 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (9): batch(), deps(), FakeClock, metrics(), datetime, UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)., test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() (+1 more)

### Community 91 - "QueryConfig"
Cohesion: 0.14
Nodes (24): QueryConfig, Query engine limits (spec 006 §5, spec 010 `query.*`)., model_validator, QueryTimeRange, Exactly one of absolute or relative bounds., _aligned_now(), make_snapshot(), datetime (+16 more)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (16): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009), NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test) (+8 more)

### Community 94 - "build_batch"
Cohesion: 0.13
Nodes (21): BatchSequencer, build_batch(), datetime, UUID, `FR-PUB-003`: a monotonically increasing `batchSeq` per agent, and a stable…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, inspect, NoReturn (+13 more)

### Community 95 - "MultiLogMonitor"
Cohesion: 0.11
Nodes (19): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+11 more)

### Community 97 - "StreamProcessor"
Cohesion: 0.07
Nodes (37): align_to_canonical(), datetime, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., Aligns, age-checks, and merges snapshots into a `MetricStore`. Non-blocking and…, FR-QRY-005: `False` ("warming") until `warmupWindow` has elapsed since this…, SnapshotOutcome, StreamProcessor (+29 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (10): _CountingRing, datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in…, The old `tick()` swept every instance's ring on every merge — O(instances x…, A query over one 10s bucket on a 6h-capacity (2160-bucket) ring must not touch…, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to() (+2 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.10
Nodes (35): default_resolve_reject_reason(), Fallback reject_reason resolver: no normalisation map, just the raw value.…, CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent (+27 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.10
Nodes (30): extract_allowlisted_fields(), FixFields, _hash_or_none(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, Fixed-shape allowlisted field set. No attribute here may hold a raw, non-…, FR-PRS-020: extract only the tags in the compile-time allowlist above.…, hash_identifier(), load_hash_key() (+22 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (13): _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any…, _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved() (+5 more)

### Community 103 - "test_QRY_04_concurrency.py"
Cohesion: 0.17
Nodes (14): FR-QRY-004: the store MUST be safe under concurrent read/write via a per-…, A per-instance lock must still serialise writes *within* one instance — safety…, `dropped_after_retention_total` is a single store-wide counter incremented from…, `StreamProcessor.dropped_buckets_total` is incremented outside any per-instance…, _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another(), write_a(), test_concurrent_drops_across_many_instances_are_all_counted() (+6 more)

### Community 104 - "StreamProcessorConfig"
Cohesion: 0.07
Nodes (41): StreamProcessorConfig, Read-only configuration shared with the ingestion boundary., datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep… (+33 more)

### Community 105 - "AgentHeartbeat"
Cohesion: 0.06
Nodes (33): BufferingHeartbeatSink, LoggingHeartbeatSink, PrintHeartbeatSink, Logger, Write one JSON line per heartbeat to stdout (demo)., Bounded retry buffer in front of another sink (UBS-60 demo stand-in). Not the…, Emit the wire JSON through `logging` (demo / local runs)., Register (or remove) the Publisher's queue-depth callback. (+25 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.16
Nodes (23): _alert(), _publisher(), LogCaptureFixture, Logger, parametrize, UBS-109: AlertRouter — the seam from Rule Engine output to the Backend…, Buffering is not publishing — this follows the alert all the way out through…, The containment that matters: the bad alert is dropped, the good ones are… (+15 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "MetricsQueryResponse"
Cohesion: 0.14
Nodes (15): FanoutClient, HttpxFanoutClient, datetime, Protocol, Multi-replica scatter-gather for metrics queries (UBS-92, NFR-SCA-003)., POST metrics queries to peer replicas., Fan out a query to peer replicas and merge bucket-wise., ReplicaFanout (+7 more)

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.05
Nodes (59): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestGuardConfig, IngestionConfig (+51 more)

### Community 110 - "test_backend_self_metrics.py"
Cohesion: 0.15
Nodes (17): Prometheus exposition for the backend's own internals (FR-HLT-010)., Recompute per-agent gauges from the registry. Called per scrape so the exporter…, (body, content-type) for `GET /metrics`., SelfMetrics, concurrent_futures, body(), heartbeat(), datetime (+9 more)

### Community 111 - "test_publishing_helpers.py"
Cohesion: 0.29
Nodes (6): FakePublisher, UBS-58/60: the Health Reporter reaches the backend only through the Backend…, _reporter(), test_connect_points_outbox_signals_at_the_publisher(), test_drop_hook_counts_each_evicted_item(), test_provider_returns_a_fresh_wire_heartbeat_each_call()

### Community 112 - "PublishAction"
Cohesion: 0.30
Nodes (18): PublishAction, StrEnum, make_snapshot(), _FakeSink, _publisher(), LogCaptureFixture, UBS-103: `BackendPublisher.publish_once()` against the full spec 007 §2.1…, Two separate batches both getting 400'd (e.g. a persistent schema bug)… (+10 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "OffsetTracker"
Cohesion: 0.09
Nodes (24): Path, OffsetTracker, Path, Registrar subsystem for tracking offsets of log files. Stores file offsets…, Generates internal state ID format (e.g., 'native::16777232-1048201')., Loads state registry into memory Supports Filebeat's native JSON list array…, Retrieves the last known offset for a given (device, inode) pair., Persist committed offset after parse+ingest (FR-PIP-006). (+16 more)

### Community 115 - "UBS-30 Implementation Notes"
Cohesion: 0.14
Nodes (15): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library (+7 more)

### Community 116 - "test_UBS_122_signature_rules.py"
Cohesion: 0.21
Nodes (16): _Stack, _load(), Path, UBS-122: signature rules count only their own pattern, and app-log lines keep…, The bug this closes: the instance-level snapshot sums every signature, so ten…, The extra grouped snapshot must not hide ordinary rules on the same window from…, _seed_signature(), _summary() (+8 more)

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.22
Nodes (19): _aggregator(), _drain_backend(), _evaluator(), _ingest_three_orders(), _publish_and_drain(), _publisher(), Decimal, FastAPI (+11 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.12
Nodes (34): _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _order(), _publish_and_drain(), _publisher(), UBS-109 integration: raw FIX bytes -> FixParser -> MetricsAggregator ->… (+26 more)

### Community 119 - "MetricsIngestor"
Cohesion: 0.21
Nodes (8): MetricsIngestor, `PipelineCommitter(on_event=...)` / `attach_committer(on_event=...)`., _ingested(), _meta(), UBS-116: MetricsIngestor turns parsed Application.log lines into app-log…, test_app_log_counts_appear_in_the_snapshot(), test_app_log_counts_group_by_signature_level_and_component(), test_fix_metrics_do_not_appear_for_app_log_lines()

### Community 120 - "ParseResult"
Cohesion: 0.14
Nodes (26): is_parse_error(), What the heartbeat counts as a parse error (UBS-59). Same definition as the…, DemoMetricsSink, _box_title(), _delimiter_label(), _format_field_row(), _hr(), print_demo_header() (+18 more)

### Community 121 - "mock_logger.py"
Cohesion: 0.20
Nodes (13): main(), generate_application_log(), get_timestamps(), Path, Generate one sponsor-format line for ``Application.log``. Main, client and…, Rotate with numbered retained archives, like ``logrotate``.…, rotate_if_needed(), run_harness() (+5 more)

### Community 122 - "test_UBS_115_snapshot_bridge.py"
Cohesion: 0.18
Nodes (15): build_snapshot(), Rename each internal dim to its wire name and drop anything not allowlisted…, One `Snapshot` for the closed interval `[bucket_start, bucket_start +…, _to_payload(), _to_wire_dimensions(), _aggregator(), _app_log_aggregator(), UBS-115: `snapshot_bridge.build_snapshot` unit tests. `build_snapshot` is the… (+7 more)

### Community 123 - "Implementation Status live document"
Cohesion: 0.24
Nodes (9): health: threshold config block, HeartbeatConfig / HealthThresholds / load_health_config, Implementation Status live document, M1 Log monitor and configuration (not started), M2 FIX parser (UBS-40-47), M3 Metrics aggregation (MA-01-04), Known rough edges, UBS-58/59/60 implementation notes (+1 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "reporter.py"
Cohesion: 0.12
Nodes (21): AgentStatus, HealthThresholds, FR-HLT-002 thresholds. Only the read-lag one has a producer on UBS-58; the rest…, HealthSignals, Health Reporter: per-file read lag (UBS-30), status rollup and heartbeat…, FR-HLT-002 rollup for the signals that exist; FR-HLT-003 reasons. Each rule…, spec 011 s1.1: publish queue depth >= critical watermark unhealthy, >= high…, spec 011 s2: parse error rate > 25% unhealthy, > 1% degraded. (+13 more)

### Community 127 - "Rule Engine"
Cohesion: 0.23
Nodes (12): NoLogActivity rule, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Dependent suppression (FR-RUL-021), Rule Engine, Safety and suppression (silences, grace, storm cap), SighupRuleReloader (+4 more)

### Community 128 - "ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server"
Cohesion: 0.18
Nodes (10): ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server, Consequences, Context, Decision, Rationale, Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents) (+2 more)

### Community 129 - "ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell"
Cohesion: 0.22
Nodes (8): ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell, Consequences, Context, Decision, Rationale, Agent-local alerting beats centrally-hosted, The five Day-1 rule kinds (FR-RUL-001), Spec 005 — Rule Engine, Alerting and Callbacks

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "collections_abc"
Cohesion: 0.08
Nodes (40): UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, FR-CBK-001/011: the swappable Callback transport boundary (spec 005 §3).…, UBS-104: lightweight in-process counters, shared between the Callback…, UBS-74: bridges the agent's own since-startup counters into the windowed…, UBS-109/110: routes Rule Engine alerts to the Backend Publisher and the…, UBS-113: the periodic loop that drives the Rule Engine. `RuleEngine.evaluate()`…, UBS-103/104: batches buffered telemetry, gzip-compresses it, and POSTs it to… (+32 more)

### Community 133 - "_Clock"
Cohesion: 0.29
Nodes (3): _Clock, datetime, One wall clock for the aggregator (epoch floats) and the evaluator (datetimes),…

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 143 - "build_parsed_message_event"
Cohesion: 0.23
Nodes (14): build_parsed_message_event(), Construct the Metrics Aggregator's event from one framed FIX line. Returns None…, _parse(), A NewOrderSingle missing symbol/side/ord_type/order_qty fails NewOrderEvent's…, effective_reject_reason's own "unspecified" fallback must not leak into…, test_execution_report_reject_maps_reason_code(), test_malformed_message_falls_back_to_base_event_instead_of_raising(), test_missing_comp_ids_fall_back_to_unknown_session_id() (+6 more)

### Community 145 - "test_RE_integration.py"
Cohesion: 0.21
Nodes (10): _ack(), _Clock, _ingest(), _new_order(), RE-05: Metrics Aggregator -> snapshot() -> Rule Engine, using real…, Mutable clock shared by the aggregator and correlator, same pattern as…, _rejected(), _session_reject() (+2 more)

### Community 157 - "metric_store.py"
Cohesion: 0.19
Nodes (13): _dim_key(), DimKey, Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, _SeriesContribution, datetime, FR-STM-006: an agent's post-restart cold-start state is preserved through the…, warmingUp flags incomplete data for the caller to exclude; it does not mean the…, _snapshot() (+5 more)

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 195 - "_BoundSourcesCollector"
Cohesion: 0.18
Nodes (10): _BoundSourcesCollector, _counter(), _gauge(), Clock, Reads ingestion / stream processor / store state at scrape time., Collector, CounterMetricFamily, GaugeMetricFamily (+2 more)

### Community 201 - "AlertStore"
Cohesion: 0.09
Nodes (34): AlertStoreConfig, Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)., AlertStore, _InstanceAlerts, _is_active_status(), datetime, Lock, In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`). (+26 more)

### Community 207 - "test_RE_parse_error_integration.py"
Cohesion: 0.31
Nodes (12): _fire(), _ingest(), _rate(), UBS-18 integration: raw log bytes -> FixParser -> derive_parser_counters ->…, Needs a failure mode that errors once per line — see `_NO_MSG_TYPE`. The…, Documents the asymptote above as behaviour, not accident: three of every four…, `min_samples` is 20 for this rule. Under that, a single bad line in a handful…, test_a_clean_log_never_fires() (+4 more)

### Community 210 - "test_degraded_status_flows_into_heartbeat_payload"
Cohesion: 0.15
Nodes (13): Path, Offset survives a clean shutdown + fresh process, but read-lag knowledge does…, FR-HLT-001: degraded read lag has to survive the actual heartbeat wire format., One file being deleted out from under the agent must not crash the health…, HealthReporter wired to a real MultiLogMonitor, not a hand-built dict., Simulates logrotate: old file renamed away, new file created at the same path., Same inode, smaller size in place - e.g. a logger truncates instead of rotating., test_degraded_status_flows_into_heartbeat_payload() (+5 more)

### Community 213 - "Rule Engine demo runbook"
Cohesion: 0.18
Nodes (10): 1. `make rules-test`, 3. `make rules-reload-demo`, Going deeper, if asked, Pre-flight, Rule Engine demo runbook, make rules-quickstart (17-act demo), Spoken script — sponsor demo (~3 min), The 5-minute version (+2 more)

### Community 214 - "decimal"
Cohesion: 0.12
Nodes (21): RE-03: the 16 default rules (spec 005 §1.2). Concrete `RuleConfig` values, used…, _tier(), _matched_tier(), Highest tier whose condition holds — not the first configured. Correct for the…, StrEnum, RE-01: rule and alert lifecycle types (spec 005 §1-2). Agent-internal…, Where a rule's observed value is read from in a MetricsSnapshot., One (severity, threshold) rung. `FR-RUL-022`: the matched tier is whichever,… (+13 more)

### Community 215 - "test_UBS_110_alert_router_callbacks.py"
Cohesion: 0.32
Nodes (11): _dispatcher(), _NullCallbackSink, _pending(), UBS-110: AlertRouter fans each alert out to the Callback Dispatcher as well as…, The guard protects the batch; a callback has no batch to poison., _router(), test_a_failing_dispatcher_does_not_cost_the_backend_its_alert(), boom() (+3 more)

### Community 216 - "MA-04: calculated indicators and snapshot output."
Cohesion: 0.20
Nodes (12): ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, M1.5 Pipeline bridge (UBS-48/49), derive_parser_counters (UBS-18), No-producer rules read as no-fire (+4 more)

### Community 217 - "DryRunCallbackSink"
Cohesion: 0.22
Nodes (8): DryRunCallbackSink, Logger, `FR-CBK-011`: log the intended delivery, never open a socket. Use this while…, FR-CBK-011 dry-run mode tests., DryRunCallbackSink never imports/constructs an httpx client at all — completing…, test_FR_CBK_011_dry_run_logs_delivery_id_and_body(), test_FR_CBK_011_dry_run_never_opens_a_socket(), test_FR_CBK_011_dry_run_returns_synthetic_success()

### Community 219 - "publishing/__init__.py"
Cohesion: 0.31
Nodes (7): classify_publish_response(), PublishOutcome, UBS-103: HTTP response -> publish action classification (spec 007 §2.1's…, parametrize, test_429_carries_retry_after_seconds(), test_status_code_classification(), test_transport_error_is_backoff()

### Community 226 - ".__init__"
Cohesion: 0.18
Nodes (9): on_drop(), _on_buffer_drop(), Logger, PublishSink, Protocol, The transport boundary. `HttpsPublishSink` is the Day-1 default (ADR 0003);…, BackendUnreachableCallback, DropCallback (+1 more)

### Community 234 - "telemetry_agent/main.py"
Cohesion: 0.06
Nodes (46): AbstractEventLoop, AgentConfig, connect_reporter_to_publisher(), drop_hook(), heartbeat_provider(), provide(), AbstractContextManager, Any (+38 more)

### Community 268 - "test_UBS45_integration.py"
Cohesion: 0.28
Nodes (8): demo_log_lines(), Path, Return parsed corpus lines, optionally filtered to one source file label., test_FR_PRS_012_corpus_files_frame_without_errors(), _meta(), Integration-style parser tests for UBS-45 enrich path., test_reject_text_maps_to_label(), test_seq_gap_from_corpus()

### Community 269 - "Heartbeat"
Cohesion: 0.31
Nodes (7): Heartbeat, The standalone and batch heartbeat payload., _heartbeat(), datetime, FR-QRY-018: backend-owned AgentHeartbeatMissing rule., test_FR_QRY_018_fresh_heartbeat_resolves_backend_alert(), test_FR_QRY_018_stale_heartbeat_fires_backend_alert()

### Community 270 - "Issue tracker: Jira"
Cohesion: 0.12
Nodes (13): graphify, Before exploring, read these, Domain Docs, File structure, Flag ADR and spec conflicts, Use the glossary's vocabulary, Conventions, Issue tracker: Jira (+5 more)

### Community 271 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.25
Nodes (9): Magic simulator for development, Do not overengineer (development principle), Telemetry Agent (architecture constraint), Unified Telemetry Intelligence (Magic), heartbeat: interval config, HeartbeatEmitter, Open risks (unknown Magic log shape, unproven footprint), Heartbeat thread/async model (+1 more)

### Community 272 - "Metrics Query API (UBS-68, UBS-91, UBS-92)"
Cohesion: 0.22
Nodes (9): Code locations, Endpoint, Example request, Example response, Metric and dimension aliases, Metrics Query API (UBS-68, UBS-91, UBS-92), Multi-replica mode (UBS-92), Operational limits (UBS-91) (+1 more)

### Community 273 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.25
Nodes (8): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Agent Restart Sequence (§8.2), NL Evaluation Requirements (FR-NLQ-025), End-to-End Acceptance Scenario (FR-TST-010), NL Evaluation Harness (FR-TST-007–009), Synthetic Load Generator (tools/fixgen, FR-TST-006), Cardinality Control (per-bucket max_label_sets/max_series_per_bucket)

### Community 274 - "test_reporter.py"
Cohesion: 0.61
Nodes (7): make_monitor(), Path, test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 276 - "services/self_metrics.py"
Cohesion: 0.33
Nodes (6): datetime, Backend self-metrics (UBS-96; FR-HLT-010, spec 006 s7). `SelfMetrics` owns a…, _utc_now(), prometheus_client, prometheus_client_core, prometheus_client_registry

### Community 277 - "test_log_monitor_status.py"
Cohesion: 0.62
Nodes (6): make_monitor(), Path, test_status_after_read_reports_elapsed_lag(), test_status_before_any_read_has_no_lag(), test_status_missing_file_has_no_size_but_does_not_raise(), test_status_reports_offset_progress_between_polls()

### Community 278 - "data_completeness.py"
Cohesion: 0.47
Nodes (5): build(), DataCompleteness, datetime, `dataCompleteness` block for query responses (spec 006 s4.1, FR-QRY-015).…, Derive completeness from the registry at `at`. `expected_agent_ids` is the set…

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **205 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `telemetry-simulator`, `telemetry-teams`, `avengers-fyp-is484` (+200 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1450 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **124 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `MA-04: calculated indicators and snapshot output.` to `config/rules.yaml live rule set`, `MetricsAggregator ring buffer`, `MetricsAggregator`, `Implementation Status live document`, `Rule Engine`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `HealthReporter` connect `HealthReporter` to `Module map (`apps/agent/src/telemetry_agent/health/`)`, `test_heartbeat.py`, `LogMonitor`, `metrics_event.py`, `test_reporter.py`, `heartbeat.py`, `Agent`, `DeliveryTracker`, `HeartbeatConfig`, `test_agent_heartbeat_reaches_the_health_endpoint`, `test_health_monitor_e2e.py`, `test_parse_errors.py`, `pytest`, `test_queue_depth.py`, `test_UBS_116_app_log_counters.py`, `publishing/demo_quickstart.py`, `test_degraded_status_flows_into_heartbeat_payload`, `datetime`, `AgentHeartbeat`, `telemetry_agent/main.py`, `test_publishing_helpers.py`, `OffsetTracker`, `MetricsIngestor`, `ParseResult`, `reporter.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `MetricsAggregator` connect `MetricsAggregator` to `FixParser`, `collections_abc`, `LatencyCorrelator`, `derive_counters`, `test_RE_publish_integration.py`, `metrics_event.py`, `test_RE_integration.py`, `test_RE_session_integration.py`, `BackendPublisher`, `test_MA_05_agent_counters.py`, `AggregatorConfig`, `test_UBS_113_evaluator.py`, `test_MA_03_correlation.py`, `_dispatch`, `pytest`, `Histogram`, `AlertEvent`, `test_UBS_116_app_log_counters.py`, `_Demo`, `rules/demo_quickstart.py`, `test_RE_parse_error_integration.py`, `_Harness`, `services/demo_quickstart.py`, `ParsedMessageEvent`, `telemetry_agent/main.py`, `test_UBS_115_snapshot_to_metricstore.py`, `test_UBS_109_rule_engine_to_backend.py`, `MetricsIngestor`, `test_UBS_115_snapshot_bridge.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 80 INFERRED edges - model-reasoned connections that need verification._