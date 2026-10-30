# Graph Report - wtL  (2026-10-30)

## Corpus Check
- 435 files · ~239,415 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 12, .example 1, .typed 1)

## Summary
- 5574 nodes · 15413 edges · 328 communities (200 shown, 128 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 2710 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9f13b398`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- create_app
- frame.py
- metrics_event.py
- RuleConfig
- make_snapshot
- actions/config.py
- HealthReporter
- test_UBS_116_app_log_ingest.py
- RetryPolicy
- LatencyCorrelator
- derive_counters
- test_RE_publish_integration.py
- test_heartbeat.py
- LogMonitor
- PublishBuffer
- SourceMeta
- LlmSlotResult
- _FlakyBackendSink
- MetricsAggregator
- EventStore
- make_alert
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- test_bot_replies.py
- LlmConfig
- CounterRegistry
- telemetry_agent/main.py
- dispatcher.py
- HeartbeatConfig
- test_MA_05_agent_counters.py
- AggregatorConfig
- test_ING_004_008_ingest_guard.py
- test_UBS_113_evaluator.py
- test_MA_03_correlation.py
- test_health_monitor_e2e.py
- config/rules.yaml live rule set
- telemetry_backend/main.py
- EventEmitter
- MetricsAggregator ring buffer
- AgentRecord
- MetricsIngestor
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- heartbeat_json
- runner.py
- test_UBS_35_36_reload_and_draft.py
- telemetry_agent_callbacks_config
- ParseResult
- metrics/__init__.py
- parse_publish_config
- QueryEngine
- Snapshot
- FixParser
- datetime
- test_RE_session_integration.py
- AlertEvent
- Registry
- test_queue_depth.py
- RuleEvaluator
- service.py
- AppLogParser
- enrich.py
- test_UBS_117_events.py
- _Demo
- Telemetry Agent (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- DropOldestQueue
- test_agent_registry.py
- http
- 009 — Non-Functional Requirements and Security
- StreamProcessorConfig
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- json
- run_slow_parser_backpressure
- HeartbeatMonitor
- test_heartbeat_roundtrip.py
- services/demo_quickstart.py
- AlertStore
- End-to-End Acceptance Scenario (FR-TST-010)
- pytest
- test_ING_004_008_routes.py
- make_snapshot
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- publish_fixtures.py
- pathlib
- telemetry_agent_callbacks_backoff
- StreamProcessor
- test_STM_04_efficiency.py
- ParsedMessageEvent
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- decimal
- test_QRY_04_concurrency.py
- BackendPublisher
- UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- cards.py
- telemetry_backend/config.py
- backtest
- test_RE_integration.py
- manifest.json
- telemetry_shared shared schema package
- parse_callbacks_config
- test_tools.py
- _Harness
- test_UBS_115_snapshot_to_metricstore.py
- test_UBS_109_rule_engine_to_backend.py
- test_UBS_27_reject_reason_trends.py
- test_UBS_117_gzip_ingestion.py
- AgentRegistry
- test_UBS_115_snapshot_bridge.py
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- _BoundSourcesCollector
- telemetry_agent_parser_applog_signatures
- snapshot
- ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server
- ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- collections_abc
- data_completeness.py
- telemetry-shared
- telemetry_agent_parser_applog_telemetry
- telemetry_agent_parser_config
- telemetry_agent_callbacks_payload
- test_UBS_36_backtest.py
- telemetry_agent_parser_corpus
- telemetry_agent_parser_display
- telemetry_backend/__init__.py
- Auditability & Compliance rationale (deterministic order audit trails)
- test_UBS_122_signature_rules.py
- teams_agent/__init__.py
- PublishResult
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
- .validate_and_reserve
- test_data_completeness.py
- teams_agent/main.py
- test_UBS_100_teams_bot_to_backend.py
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
- test_RE_callback_integration.py
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- render_answer
- telemetry_agent_parser_fix_telemetry
- telemetry_agent_callbacks_retry
- telemetry_agent_parser_registry
- telemetry_agent_callbacks_self_metrics
- telemetry_agent_callbacks_signing
- SessionHeartbeatTracker
- telemetry_shared_metrics
- telemetry_shared_metrics_histogram
- parse_fix_timestamp
- telemetry_agent_common_backoff
- time.py
- baseline.py
- config_loader.py
- classify_http_status
- OffsetTracker
- fix/normalize.py
- http_server
- AgentHeartbeat
- telemetry_agent_logs_log_monitor
- telemetry_agent_logs_offset_tracker
- telemetry_agent_parser_fix_fields
- telemetry_agent_callbacks_dispatcher
- telemetry_agent_parser_fix_seq_tracker
- telemetry_agent_parser_fix_timestamps
- UBS-117: event publication and integration boundary
- telemetry_agent_callbacks_sink
- telemetry_agent_common_self_metrics
- telemetry_agent_parser_applog_parser
- telemetry_agent_callbacks_status
- telemetry_agent_publishing_batch
- telemetry_shared_models_parsed_message
- telemetry_agent_publishing_buffer
- test_a_logged_reject_burst_reaches_the_backend_alert_store
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
- test_UBS_25_29_anomaly.py
- effective_reject_reason
- Issue tracker: Jira
- test_log_monitor_status.py
- Metrics Query API (UBS-68, UBS-91, UBS-92)
- _Clock
- test_reporter.py
- Rule Engine demo runbook
- test_RE_02_evaluators.py
- api/health.py
- actions/__init__.py
- dataclasses
- Teams bot
- Agent
- test_UBS_113_evaluation_loop.py
- LlmSlotFillError
- OllamaSlotFiller
- load_agent_config
- UBS-100 — Teams bot with Adaptive Card answers (spec)
- NlQueryService
- health-reporter-overview.md
- rules/demo_quickstart.py
- NlQueryContext
- QueryTimeRange
- ActionRunner
- Exchange
- PipelineStats
- load_rules
- ._serialize_counters
- build.sh
- RuleConfigError
- to_ingestion_heartbeat
- test_FR_CBK_017_isolation.py
- test_UBS_35_actions_end_to_end.py
- signing.py
- test_reply_guard.py
- test_FR_CBK_004_006_007_dispatcher.py
- test_RE_parse_error_integration.py
- telemetry_agent/config.py
- test_FR_CBK_013_action_config.py
- test_UBS_110_alert_router_callbacks.py
- test_nl_eval_fixtures.py
- SeqTracker
- NL query manual test plan: Ollama, Teams and Copilot (MCP)
- callbacks/demo_quickstart.py
- demo_reload.py
- .snapshot
- test_UBS_128_level_rules.py
- test_STM_03_warmup.py
- telemetry_agent/demo_suite.py
- test_RE_03_safety.py
- test_UBS_68_metrics_query.py
- .__init__
- UBS-25–29 implementation notes (D2 anomaly detection)
- .__init__
- .counters
- .skip_sequence
- telemetry_mcp/__init__.py

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 120 edges
2. `AlertEvent` - 116 edges
3. `create_app()` - 106 edges
4. `HealthReporter` - 89 edges
5. `MetricStore` - 88 edges
6. `StreamProcessorConfig` - 86 edges
7. `BackendPublisher` - 85 edges
8. `SourceMeta` - 80 edges
9. `CamelModel` - 79 edges
10. `FixParser` - 74 edges

## Surprising Connections (you probably didn't know these)
- `Missing downstream / upstream (what this branch cannot prove)` --references--> `BufferingHeartbeatSink`  [INFERRED]
  docs/plan/ubs58-60-notes.md → apps/agent/src/telemetry_agent/health/heartbeat.py
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py
- `Design decisions` --references--> `load_rules()`  [INFERRED]
  docs/plan/ubs25-29-notes.md → apps/agent/src/telemetry_agent/rules/config_loader.py

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

## Communities (328 total, 128 thin omitted)

### Community 0 - "create_app"
Cohesion: 0.09
Nodes (42): create_app(), nl_intents(), Build an application, allowing tests and deployment to supply a service., build_intents_response(), IngestionService, Keep store work off FastAPI's request path. A single consumer preserves the…, Owns a bounded queue and one background consumer., fastapi_routing (+34 more)

### Community 1 - "frame.py"
Cohesion: 0.08
Nodes (40): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+32 more)

### Community 2 - "metrics_event.py"
Cohesion: 0.06
Nodes (60): _fixed_now(), main(), Minimal walkthrough of parser/metrics_event.py: the same three-order story as…, _step(), build_parsed_message_event(), derive_parser_counters(), derive_session_counters(), _parse_error_reason() (+52 more)

### Community 3 - "RuleConfig"
Cohesion: 0.08
Nodes (45): The rule's `baseline_seconds`; raises `ValueError` at construction time rather…, validate_anomaly_rule(), _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _matched_tier() (+37 more)

### Community 4 - "make_snapshot"
Cohesion: 0.18
Nodes (33): make_gauges(), make_indicator(), make_indicators(), make_latency(), make_snapshot(), datetime, Decimal, Shared test support for the rules package: builds `MetricsSnapshot` fixtures… (+25 more)

### Community 5 - "actions/config.py"
Cohesion: 0.15
Nodes (22): ActionConfigError, _ActionYaml, _command_key(), _is_rooted(), load_action_catalogue(), _parse_action(), parse_actions(), parse_allowed_commands() (+14 more)

### Community 6 - "HealthReporter"
Cohesion: 0.07
Nodes (43): AgentStatus, HealthThresholds, FR-HLT-002 thresholds. Only the read-lag one has a producer on UBS-58; the rest…, HealthReporter, HealthSignals, datetime, Per-file read health, keyed by the same name `monitors` was built with., Worst-case lag across files (heartbeat gauge). None if none have read yet. (+35 more)

### Community 7 - "test_UBS_116_app_log_ingest.py"
Cohesion: 0.39
Nodes (6): _ingested(), _meta(), UBS-116: MetricsIngestor turns parsed Application.log lines into app-log…, test_app_log_counts_appear_in_the_snapshot(), test_app_log_counts_group_by_signature_level_and_component(), test_fix_metrics_do_not_appear_for_app_log_lines()

### Community 8 - "RetryPolicy"
Cohesion: 0.06
Nodes (40): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, main(), format_fix_line(), generate_application_log() (+32 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.07
Nodes (28): CorrelatorStats, LatencyCorrelator, OrderContext, Clock, datetime, Decimal, timedelta, Recorded so consumers of a snapshot know what a latency number means (MA-03 AC)… (+20 more)

### Community 10 - "derive_counters"
Cohesion: 0.09
Nodes (41): derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MA-02: order / execution / reject counters and reject-reason normalisation.…, All four counter families in one event walk., fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not OrdStatus —…, Config-driven raw-reason -> canonical-label mapping. Backs MetricsAggregator's… (+33 more)

### Community 11 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (22): _aggregator(), _engine(), _fail_n_times(), _publisher(), UBS-75 integration: BackendPublisher -> consecutive_publish_failures gauge ->…, The whole reason this is a gauge: recovery is observable. A windowed failure…, FR-MET-031. An agent with no publisher must not look like an agent that is…, Regression guard on spec 005 §1.2's withdrawn approximation.… (+14 more)

### Community 12 - "test_heartbeat.py"
Cohesion: 0.13
Nodes (19): Collect, FakeClock, datetime, LogCaptureFixture, UBS-58 / FR-HLT-001: heartbeat emitter and wire format., AC: an idle agent still heartbeats; N ticks in ~N intervals., A sink stuck in blocking I/O must not starve other coroutines., _reporter() (+11 more)

### Community 13 - "LogMonitor"
Cohesion: 0.06
Nodes (25): Harvester, LogMonitor, datetime, Path, TextIO, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, Find retained rotations that were created while the agent was down. This… (+17 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (25): PublishBuffer, datetime, Remove and return up to `max_items` from the front., Put previously-`take`n items back at the front, in original order -- they are…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both…, Drop items older than `max_age_seconds`. The deque is strictly insertion-…, _item(), FR-PUB-004: the byte-and-age-bounded `PublishBuffer` (UBS-104's replacement for… (+17 more)

### Community 15 - "SourceMeta"
Cohesion: 0.04
Nodes (58): _build_bridge(), OverflowPolicy, End-to-end demo: LogMonitor → queue → parse → output → commit., Metadata attached to each log line by the monitor., SourceMeta, QueueSnapshot, PipelineCommitter, Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007). (+50 more)

### Community 16 - "LlmSlotResult"
Cohesion: 0.11
Nodes (20): _JsonModeRejected, OpenAiCompatibleSlotFiller, AsyncClient, Exception, Server does not support response_format json_object., Nothing to load: OpenAI-compatible servers manage their own models., LlmSlotResult, config() (+12 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.11
Nodes (20): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator, Clock, datetime, Decimal (+12 more)

### Community 19 - "EventStore"
Cohesion: 0.09
Nodes (27): EventStoreConfig, Event store retention (UBS-118; spec 010 `store.recentAlertLimit` default)., EventStore, _InstanceEvents, datetime, Lock, In-memory Event Store (UBS-118)., Per-instance bounded event history. (+19 more)

### Community 20 - "make_alert"
Cohesion: 0.21
Nodes (24): command_action(), make_alert(), Path, Shared test support for `telemetry_agent.actions` (UBS-35). Command actions run…, write_script(), Path, FR-CBK-015/016/017: a `command` action runs a fixed argv with no shell, the…, _runner() (+16 more)

### Community 21 - "MetricStore"
Cohesion: 0.09
Nodes (23): _CanonicalBucket, _dim_key(), MetricStore, datetime, DimKey, Lock, Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped… (+15 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.06
Nodes (39): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+31 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.16
Nodes (31): _key(), _keys(), _observe(), UBS-106: SessionHeartbeatTracker — the `heartbeat_timeouts` producer. A…, A logged-out session is silent forever. Counting that as a timeout would…, SeqTracker accepts both normalized names and raw tag values ("Logon"/"A");…, FIX only requires a Heartbeat when the session is otherwise idle, so a session…, Session keys from a timed_out() result, for terse assertions. (+23 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (32): health: threshold config block, heartbeat: interval config, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry (+24 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "test_bot_replies.py"
Cohesion: 0.14
Nodes (53): Handler, answer(), clarification(), converse(), recording(), run(), group(), json_ok() (+45 more)

### Community 27 - "LlmConfig"
Cohesion: 0.11
Nodes (28): LlmConfig, Apply provider-specific defaults after YAML merge., resolve_llm_config(), build_llm_filler(), build_nl_service(), Construct NL services from backend configuration., AzureOpenAiSlotFiller, AsyncClient (+20 more)

### Community 28 - "CounterRegistry"
Cohesion: 0.08
Nodes (16): Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, CounterRegistry, Plain dict of named counters behind a lock -- increments happen from both async…, Self-observability, same shape as `BackendPublisher.counters` and…, AbstractContextManager, Any, Logger, datetime (+8 more)

### Community 29 - "telemetry_agent/main.py"
Cohesion: 0.05
Nodes (43): AbstractEventLoop, ActionType, StrEnum, AgentConfig, build_agent(), check_action_secret(), stage_actions(), _build_parser() (+35 more)

### Community 30 - "dispatcher.py"
Cohesion: 0.07
Nodes (50): alert_delivery_from_record(), enrich_alert_delivery(), Map callback delivery tracker state to backend wire models (FR-CBK-009)., UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, DeliveryRecord, DeliveryStatus, DeliveryTracker, notification_key() (+42 more)

### Community 31 - "HeartbeatConfig"
Cohesion: 0.10
Nodes (33): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, HeartbeatConfig, _HeartbeatYaml, load_health_config() (+25 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.19
Nodes (20): _aggregator(), Decimal, UBS-74: `MetricsAggregator.ingest_agent_counters` and the `AgentCounterSampler`…, A restarted dispatcher's registry drops back to 0. That is a new baseline, not…, The whole reason this is a separate write path: the dispatcher retrying is not…, Guard on the contrast above — proves the assertion isn't passing because…, test_agent_counters_group_by_instance_only(), test_deltas_land_in_the_bucket_for_their_own_timestamp() (+12 more)

### Community 33 - "AggregatorConfig"
Cohesion: 0.17
Nodes (23): AggregatorConfig, Bucket granularity, retained windows, and the per-metric dimension table (FR-…, FakeClock, Shared test support for the metrics package: a hand-labelled synthetic FIX-…, A `Clock` (`() -> float`) that only advances when told to — lets a test assert…, make_event(), minimal_aggregator(), Decimal (+15 more)

### Community 34 - "test_ING_004_008_ingest_guard.py"
Cohesion: 0.09
Nodes (34): IngestGuardConfig, UBS-85: batch dedupe (FR-ING-004) and per-agent rate limiting (FR-ING-008).…, Accept, Duplicate, IngestGuard, Clock, datetime, deque (+26 more)

### Community 35 - "test_UBS_113_evaluator.py"
Cohesion: 0.13
Nodes (25): _names(), Path, UBS-113: RuleEvaluator — the periodic loop between the metrics store and…, Write counters straight into the store, labelled with placeholder dimension…, Pending on this tick, firing on the next., RejectSpike reads 1m, HighRejectRate reads 5m: one tick, both., The tracker latches each silence: many ticks after the timeout still put…, A rules file the loader accepts, from the shipped config's own entries, so the… (+17 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "test_health_monitor_e2e.py"
Cohesion: 0.11
Nodes (19): committed_offsets(), FakeClock, fix_lines(), datetime, FastAPI, fixture, MonkeyPatch, Path (+11 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.12
Nodes (26): BackendUnreachable rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule, PendingOrderTimeout rule, RejectSpike rule (+18 more)

### Community 39 - "telemetry_backend/main.py"
Cohesion: 0.06
Nodes (48): HTTP routers, one file per concern (spec 007). `health.py` (UBS-69) serves the…, AlertsQueryParams, BatchAccepted, _counts(), enqueue_or_full(), get_alert(), get_event(), ingest_batch() (+40 more)

### Community 40 - "EventEmitter"
Cohesion: 0.18
Nodes (8): One session that has just gone quiet for too long. Carries both identifiers on…, SessionTimeout, EventEmitter, Any, datetime, Failure/drop never interrupts metrics, rules or callback delivery., allowed_event_fields(), Event field allowlists shared by producers and backend validation (FR-MET-022).…

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.08
Nodes (35): callbacks: Callback Dispatcher config block, agent: identity config (id, instanceIds, version), AckLatencyBreach rule, CallbackFailing rule, ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake (+27 more)

### Community 42 - "AgentRecord"
Cohesion: 0.16
Nodes (8): AgentRecord, datetime, `missing` if stale, otherwise whatever the agent last reported., Agent IDs past the threshold - the `dataCompleteness.staleAgents` input (FR-…, Store the latest heartbeat. Returns True on first contact so the caller can…, _utc_now(), Open points for the team, RegistryStatus

### Community 43 - "MetricsIngestor"
Cohesion: 0.14
Nodes (25): MetricsIngestor, Logger, The production set: an aggregator that accepts every counter and latency…, monitors_by_resolved_path(), MonkeyPatch, Path, test_tailed_fix_lines_reach_the_real_aggregator(), _counters() (+17 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (18): bad(), FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides() (+10 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.12
Nodes (22): Clock, datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, drive() (+14 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.09
Nodes (32): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Backend Publisher (component), Callback Dispatcher (component) (+24 more)

### Community 47 - "CamelModel"
Cohesion: 0.07
Nodes (56): Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, AlertCounts, AlertDelivery, AlertDetailResponse, AlertsListResponse, AlertTransition, Alert query response models (spec 007 §4, `FR-QRY-016`)., Callback delivery status surfaced in alert query results. (+48 more)

### Community 48 - "heartbeat_json"
Cohesion: 0.15
Nodes (15): heartbeat_json(), Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, FakeClock, datetime, UBS-104: publish buffer bytes and dropped-event rate in the heartbeat. Mirrors…, A supervisor wiring the Publisher in calls this once at startup so a healthy…, test_buffer_bytes_is_none_without_a_provider(), test_buffer_bytes_is_read_fresh_on_every_snapshot() (+7 more)

### Community 49 - "runner.py"
Cohesion: 0.08
Nodes (20): datetime, UBS-35: runs a rule's actions when its alert fires (spec 005 §5). `AlertRouter`…, _utc_now(), CallbackResult, DryRunCallbackSink, HttpsCallbackSink, AsyncBaseTransport, Logger (+12 more)

### Community 50 - "test_UBS_35_36_reload_and_draft.py"
Cohesion: 0.11
Nodes (30): datetime, Logger, Reloads `config/rules.yaml` into a live `RuleEngine`, on SIGHUP or (UBS-35, so…, (rules.yaml, anomaly.yaml) modification times., True when the file's mtime differs from the one last loaded (or last rejected,…, Returns the `resolved` events `apply_rules()` emits for alerts whose rule was…, Standalone use only: this reloads inside the signal handler and drops the…, SighupRuleReloader (+22 more)

### Community 52 - "ParseResult"
Cohesion: 0.07
Nodes (56): DemoMetricsSink, Demo metrics sink for parser CLI (mirrors spec 004 counter names)., compile_signature_rules(), extract_log_level(), First-match-wins signature rules with dynamic label templates., Extract [N/E/W/F/I] level from Magic-style log lines., resolve_label_template(), _sanitize_capture() (+48 more)

### Community 53 - "metrics/__init__.py"
Cohesion: 0.14
Nodes (17): build_latency_summary(), Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004). Shared by the…, compute_indicators(), compute_ratio(), Decimal, RatioDef, Derived-ratio computation (spec 004 §4.5, FR-QRY-010, FR-STM-003). Shared by…, `value` is None when `denominator` is 0 (never fabricate a rate from no data).… (+9 more)

### Community 54 - "parse_publish_config"
Cohesion: 0.11
Nodes (31): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfigError, _PublishYaml, Any, BaseModel, Exception (+23 more)

### Community 55 - "QueryEngine"
Cohesion: 0.06
Nodes (40): QueryConfig, Query engine limits (spec 006 §5, spec 010 `query.*`)., _AccumulatedGroup, datetime, Decimal, DimKey, Exception, timedelta (+32 more)

### Community 56 - "Snapshot"
Cohesion: 0.07
Nodes (42): _to_payload(), Histogram, Decimal, Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012). Shared…, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, HistogramPayload (+34 more)

### Community 57 - "FixParser"
Cohesion: 0.06
Nodes (47): is_parse_error(), Count one parsed line, and a parse error if `is_parse_error(result)`., What the heartbeat counts as a parse error (UBS-59). Same definition as the…, demo_log_lines(), Path, Return parsed corpus lines, optionally filtered to one source file label., classify_line(), compile_app_log_patterns() (+39 more)

### Community 58 - "datetime"
Cohesion: 0.17
Nodes (17): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, datetime, deliver(), make_alert_event() (+9 more)

### Community 59 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (29): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), Decimal, UBS-73 integration: raw FIX log bytes -> FixParser -> metrics_event bridge ->…, A tracker that has watched `lines` go past, so it knows which sessions exist… (+21 more)

### Community 60 - "AlertEvent"
Cohesion: 0.08
Nodes (24): CallbackDispatcher, Deliver one alert now, bypassing the queue and the workers, and return its…, Spawns `maxInflight` workers pulling from the queue. Runs until cancelled by…, Signs and sends `alert`, retrying transient failures with backoff (`FR-…, Track `status` against this alert's own notification, not the alert as a whole…, Sync, non-blocking — the entry point a future wiring step calls from the same…, AlertRouter, datetime (+16 more)

### Community 61 - "Registry"
Cohesion: 0.06
Nodes (34): Confidence, Parser, Protocol, StrEnum, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'., Report whether this parser claims the input. (+26 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.22
Nodes (13): FakeQueue, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend., test_at_critical_watermark_is_unhealthy(), test_at_high_watermark_is_degraded_with_reason_and_trend(), test_below_high_watermark_is_healthy(), test_depth_is_read_fresh_on_every_snapshot(), test_draining_queue_recovers_to_healthy() (+5 more)

### Community 63 - "RuleEvaluator"
Cohesion: 0.16
Nodes (10): datetime, Event, Signal-safe: only sets a flag. Register it with…, One tick. Returns every alert routed, in routing order., Tick every `interval_seconds` until `stop` is set; the first tick is immediate.…, Cheap (one `stat`), but still rate-limited to `reload_check_seconds`; 0…, UBS-123: runs after aging so retention matches the aggregator., Runs the Rule Engine every `interval_seconds` and routes its alerts. Shared… (+2 more)

### Community 64 - "service.py"
Cohesion: 0.07
Nodes (48): build_default_filters(), default_time_range(), IntentDefinition, Day-1 intent catalogue and slot defaults (FR-NLQ-003, FR-NLQ-004)., _merge_group_by(), merge_interpreted_query(), _merge_metrics(), _merge_step() (+40 more)

### Community 65 - "AppLogParser"
Cohesion: 0.11
Nodes (24): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), UBS-116: the Application.log counters, one dispatch per parsed line.…, Dimension values for `derive_app_log_counters`' output — one mapping covering…, Bounds the free-text `component` dimension of `app_log_errors`. The first…, AppLogParser, Parser plugin for configured application log patterns (Magic format). (+16 more)

### Community 66 - "enrich.py"
Cohesion: 0.23
Nodes (17): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+9 more)

### Community 67 - "test_UBS_117_events.py"
Cohesion: 0.12
Nodes (28): parse(), app(), meta(), FR-MET-020/021/022/023: bounded events, independently of alert decisions., sent(), Sink, stack(), test_alert_mirror_suppresses_reminders_but_keeps_escalation_and_resolution() (+20 more)

### Community 68 - "_Demo"
Cohesion: 0.15
Nodes (8): _Demo, Holds the one parser/aggregator/engine trio the whole story runs on, so each…, ExecType/OrdStatus 8 = Rejected, OrdRejReason 3 = ExchangeClosed., 35=3, a session-level Reject — a FIX plumbing problem rather than a trading…, 35=9, a rejected cancel/replace — counted as `cancel_rejects`, kept apart from…, An ack whose SendingTime is `delay_ms` after its order. Latency is measured…, `count` orders that each get acked — the healthy baseline volume a reject…, Age the open-order book without aging anything else — what…

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.16
Nodes (16): Agent processing pipeline (monitor to health reporter), Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Magic simulator for development, Do not overengineer (development principle), Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores (+8 more)

### Community 70 - "AppDeps"
Cohesion: 0.21
Nodes (23): AppDeps, env(), FakeClock, heartbeat(), post(), datetime, fixture, TestClient (+15 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.10
Nodes (13): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+5 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.12
Nodes (27): create_internal_app(), FastAPI, UBS-96, FR-HLT-012: `/healthz`, `/readyz` and `/metrics` for the internal…, Two uvicorn servers, one process, one `AppDeps` (FR-HLT-012)., _serve(), env(), FakeClock, heartbeat() (+19 more)

### Community 73 - "DropOldestQueue"
Cohesion: 0.16
Nodes (9): DropOldestQueue, T, FR-CBK-007: bounded pending queue, drop-oldest on overflow., Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow policy (`FR-…, Enqueue `item`, non-blocking. Returns True if an existing item was dropped to…, FR-CBK-007 bounded queue, drop-oldest overflow tests., test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped() (+1 more)

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.09
Nodes (24): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), Resource Discipline (§9), Backend Configuration and Secrets (§9), Compliance and Operability Constraints (§7), Configurability NFRs (§5), 009 — Non-Functional Requirements and Security, NFR-CFG-004: Documented Config Defaults Must Match Code (+16 more)

### Community 77 - "StreamProcessorConfig"
Cohesion: 0.09
Nodes (36): StreamProcessorConfig, datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep…, _snapshot() (+28 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.23
Nodes (17): The active rule set, including any `apply_rules()` hot-swap, so a caller can…, _engine(), _fire(), datetime, LogCaptureFixture, Path, skipif, RE-05: `RuleEngine.apply_rules` and `SighupRuleReloader` (`FR-RUL-008`). (+9 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (18): C++ candidate (rejected: worst-case failure modes), ADR 0001: Telemetry Agent written in Go (Superseded), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), ADR 0002: Telemetry stack is Python 3.12 + FastAPI, .NET alternative (rejected) (+10 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.12
Nodes (18): ADR 0004: No-Raw-Persistence Design, Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Parser Engine Agent-Level Contract (FR-PRS-001–003), Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing), Scaffold Document (plan/scaffold.md) (+10 more)

### Community 82 - "json"
Cohesion: 0.17
Nodes (12): json, subprocess, _burst(), Path, UBS-114 / FR-TST-010 slice: the real agent process, end to end. `build_agent` +…, test_the_agent_process_alerts_magic_and_the_backend(), scenario(), Path (+4 more)

### Community 83 - "run_slow_parser_backpressure"
Cohesion: 0.16
Nodes (17): _build_registry(), _load_config(), main(), _print_stage(), Path, Hands back the `FixParser` alongside the registry it went into. Callers need…, run_happy_path(), run_slow_parser_backpressure() (+9 more)

### Community 84 - "HeartbeatMonitor"
Cohesion: 0.19
Nodes (9): backend_alert_id(), HeartbeatMonitor, Resolve a backend alert immediately when a fresh heartbeat arrives., Periodically evaluates agent heartbeat staleness., _heartbeat(), datetime, FR-QRY-018: backend-owned AgentHeartbeatMissing rule., test_FR_QRY_018_fresh_heartbeat_resolves_backend_alert() (+1 more)

### Community 85 - "test_heartbeat_roundtrip.py"
Cohesion: 0.17
Nodes (10): telemetry_agent_health_config, telemetry_agent_health_reporter, _now_sending_time(), UBS-112 integration: a tailed log file -> MultiLogMonitor -> PipelineBridge…, FakeClock, datetime, Path, Agent Health Reporter (UBS-58/59/60) -> Backend Publisher -> Ingestion (UBS-66)… (+2 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (15): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact…, The exact 3-order story from the Metrics Aggregator quickstart: two accepted… (+7 more)

### Community 87 - "AlertStore"
Cohesion: 0.07
Nodes (44): AlertStoreConfig, Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)., AlertStore, _InstanceAlerts, _is_active_status(), datetime, Lock, In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`). (+36 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.12
Nodes (17): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Text Field Normalisation (FR-PRS-022), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025) (+9 more)

### Community 89 - "pytest"
Cohesion: 0.08
Nodes (30): _maybe_gzip(), _parse_retry_after(), UBS-103: the swappable Publisher transport boundary (spec 002 §6). Mirrors…, `FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the compressed…, ASGITransport, asyncio, gzip, Headers (+22 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (9): batch(), deps(), FakeClock, metrics(), datetime, UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)., test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() (+1 more)

### Community 91 - "make_snapshot"
Cohesion: 0.19
Nodes (19): _aligned_now(), make_snapshot(), datetime, Shared fixtures for metrics query tests., _engine(), UBS-68: metrics query engine filters, grouping, and retention errors., _request(), test_UBS_68_application_filter_selects_instances() (+11 more)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (16): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009), NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test) (+8 more)

### Community 94 - "publish_fixtures.py"
Cohesion: 0.13
Nodes (17): concurrent_futures, inspect, NoReturn, make_alert(), make_event(), datetime, Shared test support for the publishing package: builds `Snapshot`,…, _NeverCalledSink (+9 more)

### Community 95 - "pathlib"
Cohesion: 0.07
Nodes (35): print_header(), run_demo(), setup_environment(), main(), Log monitoring, rotation and truncation handling., One complete log line with stable byte identity for idempotent ingest., ReadLine, MultiLogMonitor (+27 more)

### Community 97 - "StreamProcessor"
Cohesion: 0.09
Nodes (30): align_to_canonical(), datetime, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., Aligns, age-checks, and merges snapshots into a `MetricStore`. Non-blocking and…, FR-QRY-005: `False` ("warming") until `warmupWindow` has elapsed since this…, SnapshotOutcome, StreamProcessor (+22 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (10): _CountingRing, datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in…, The old `tick()` swept every instance's ring on every merge — O(instances x…, A query over one 10s bucket on a 6h-capacity (2160-bucket) ring must not touch…, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to() (+2 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.10
Nodes (33): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent, BaseModel (+25 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.09
Nodes (33): extract_allowlisted_fields(), FixFields, _hash_or_none(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, Fixed-shape allowlisted field set. No attribute here may hold a raw, non-…, FR-PRS-020: extract only the tags in the compile-time allowlist above.…, hash_identifier(), load_hash_key() (+25 more)

### Community 102 - "decimal"
Cohesion: 0.19
Nodes (18): RE-03: the 17 default rules (spec 005 §1.2). Concrete `RuleConfig` values, used…, _tier(), RE-01: rule and alert lifecycle types (spec 005 §1-2). Agent-internal…, decimal, telemetry_agent_rules_types, _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any… (+10 more)

### Community 103 - "test_QRY_04_concurrency.py"
Cohesion: 0.13
Nodes (18): FR-QRY-004: the store MUST be safe under concurrent read/write via a per-…, A per-instance lock must still serialise writes *within* one instance — safety…, `dropped_after_retention_total` is a single store-wide counter incremented from…, `StreamProcessor.dropped_buckets_total` is incremented outside any per-instance…, `_get_or_create_instance` sets `_rings[instance_id]` before…, `_shed_oldest_tier` iterates `_rings.items()` and indexed `_instance_locks`…, _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another() (+10 more)

### Community 104 - "BackendPublisher"
Cohesion: 0.07
Nodes (24): _drain(), main(), _make_snapshot(), _print_state(), datetime, Minimal walkthrough of the Backend Publisher (UBS-103/104). uv run python -m…, Stands in for the backend: returns responses from a fixed script, one per call,…, _ScriptedSink (+16 more)

### Community 105 - "UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth"
Cohesion: 0.11
Nodes (17): Register (or remove) the Publisher's queue-depth callback., 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 5.1 The window — `health/window.py`, 5. UBS-59 — parse error rate, 6. UBS-60 — publish queue depth, 8. What is still missing (so nobody is surprised) (+9 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.16
Nodes (23): _alert(), _publisher(), LogCaptureFixture, Logger, parametrize, UBS-109: AlertRouter — the seam from Rule Engine output to the Backend…, The containment that matters: the bad alert is dropped, the good ones are…, A misconfigured agent raises this for every alert it ever fires; the line is… (+15 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "cards.py"
Cohesion: 0.16
Nodes (26): _alert_badge(), _ask_again(), _breakdown(), _breakdown_rows(), build_answer_card(), build_clarification_card(), build_error_card(), _card() (+18 more)

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.13
Nodes (26): _AlertingYaml, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestionConfig, _IngestYaml, _Lenient (+18 more)

### Community 110 - "backtest"
Cohesion: 0.11
Nodes (25): _app_log_time(), backtest(), tick(), BacktestReport, _first_dated_time(), _first_time(), _fix_time(), _iso() (+17 more)

### Community 111 - "test_RE_integration.py"
Cohesion: 0.21
Nodes (10): _ack(), _Clock, _ingest(), _new_order(), RE-05: Metrics Aggregator -> snapshot() -> Rule Engine, using real…, Mutable clock shared by the aggregator and correlator, same pattern as…, _rejected(), _session_reject() (+2 more)

### Community 112 - "manifest.json"
Cohesion: 0.09
Nodes (22): accentColor, bots, description, full, short, developer, name, privacyUrl (+14 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "parse_callbacks_config"
Cohesion: 0.10
Nodes (27): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+19 more)

### Community 115 - "test_tools.py"
Cohesion: 0.06
Nodes (47): _answer_result(), _clarification_result(), _error_kind(), error_result(), _path(), Any, AsyncClient, Audience (+39 more)

### Community 116 - "_Harness"
Cohesion: 0.16
Nodes (8): _Harness, _orders(), Decimal, parametrize, At t=1200 only [1150,1200) is fully retained; 1000-1140 are skipped., Real aggregator (1s buckets, 60s retention) and publisher behind the emitter., _starts(), TestSnapshotEmitter

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.20
Nodes (21): _aggregator(), _drain_backend(), _evaluator(), _ingest_app_log_lines(), _ingest_three_orders(), _publish_and_drain(), _publisher(), Decimal (+13 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.12
Nodes (33): _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _publish_and_drain(), _publisher(), UBS-109 integration: raw FIX bytes -> FixParser -> MetricsAggregator ->…, Run the ingestion consumer until the queued batch is fully processed.… (+25 more)

### Community 119 - "test_UBS_27_reject_reason_trends.py"
Cohesion: 0.10
Nodes (32): _bad_window(), _by_reason(), classify(), datetime, timedelta, Increasing reject reasons (UBS-27): current window vs. the preceding one. Built…, Direction and relative change for one reason's two counts., Raises `QueryValidationError` for a bad window or filter. (+24 more)

### Community 120 - "test_UBS_117_gzip_ingestion.py"
Cohesion: 0.25
Nodes (9): Read-only configuration shared with the ingestion boundary., on_message(), client(), parametrize, FR-PUB-002 / FR-ING-008: compressed real batches and bounded decoding., test_body_limit_is_loaded_from_existing_ingest_config(), test_compressed_events_are_accepted_with_existing_contract(), test_corrupt_compressed_body_returns_safe_error() (+1 more)

### Community 121 - "AgentRegistry"
Cohesion: 0.06
Nodes (40): AlertingConfig, Backend-owned alerting rules (spec 005 `FR-RUL-030`)., datetime, Shared service instances the routers reach through `request.app.state`. One…, _utc_now(), AgentRegistry, Clock, Agent Registry (spec 006 FR-ING-010; UBS-69 read side, UBS-87 write side). One… (+32 more)

### Community 122 - "test_UBS_115_snapshot_bridge.py"
Cohesion: 0.20
Nodes (14): build_snapshot(), Rename each internal dim to its wire name and drop anything not allowlisted…, One `Snapshot` for the closed interval `[bucket_start, bucket_start +…, _to_wire_dimensions(), _aggregator(), _app_log_aggregator(), UBS-115: `snapshot_bridge.build_snapshot` unit tests. `build_snapshot` is the…, Same bucket, called twice: equal output -- a publish retry that rebuilds the… (+6 more)

### Community 123 - "Implementation Status live document"
Cohesion: 0.31
Nodes (9): Implementation Status live document, M1 Log monitor and configuration (not started), M2 FIX parser (UBS-40-47), M3 Metrics aggregation (MA-01-04), Backend Metric Store and cross-agent merge, Ratios are recomputed, never averaged, Backend Stream Processor (UBS-88), Known rough edges (+1 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "_BoundSourcesCollector"
Cohesion: 0.18
Nodes (10): _BoundSourcesCollector, _counter(), _gauge(), Clock, Reads ingestion / stream processor / store state at scrape time., Collector, CounterMetricFamily, GaugeMetricFamily (+2 more)

### Community 127 - "snapshot"
Cohesion: 0.45
Nodes (12): hand_labelled_events(), _ingest_all(), _shared_config(), test_gauges_are_empty_without_a_correlator(), test_gauges_reflect_pending_orders_and_event_staleness(), test_grouped_breakdown_by_symbol(), test_indicators_computed_from_hand_labelled_fixture(), test_latency_summary_present_for_recorded_histograms() (+4 more)

### Community 128 - "ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server"
Cohesion: 0.18
Nodes (10): ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server, Consequences, Context, Decision, Rationale, Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents) (+2 more)

### Community 129 - "ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell"
Cohesion: 0.29
Nodes (6): ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell, Consequences, Context, Decision, Rationale, callback()

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "collections_abc"
Cohesion: 0.10
Nodes (27): UBS-104: lightweight in-process counters, shared between the Callback…, Heartbeat emitter (UBS-58, FR-HLT-001). Ticks on a fixed interval regardless of…, UBS-74: bridges the agent's own since-startup counters into the windowed…, MA-03: order correlation and latency. Standalone producer into the shared…, UBS-109/110: routes Rule Engine alerts to the Backend Publisher and the…, UBS-36: test mode. Replays log files through one rule without dispatching. uv…, UBS-113: the periodic loop that drives the Rule Engine. `RuleEngine.evaluate()`…, Feed each committed parse result into the real metrics and health state… (+19 more)

### Community 133 - "data_completeness.py"
Cohesion: 0.47
Nodes (5): build(), DataCompleteness, datetime, `dataCompleteness` block for query responses (spec 006 s4.1, FR-QRY-015).…, Derive completeness from the registry at `at`. `expected_agent_ids` is the set…

### Community 134 - "telemetry-shared"
Cohesion: 0.33
Nodes (6): telemetry-agent, telemetry-backend, telemetry-mcp, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 138 - "test_UBS_36_backtest.py"
Cohesion: 0.21
Nodes (21): Telemetry Agent — lightweight sidecar for Magic instances., CaptureFixture, _fix_log(), _nothing_may_be_dispatched(), fixture, MonkeyPatch, Path, UBS-36: test mode replays log files through one rule and reports whether, when… (+13 more)

### Community 143 - "test_UBS_122_signature_rules.py"
Cohesion: 0.18
Nodes (18): _load(), Path, _Stack, UBS-122: signature rules count only their own pattern, and app-log lines keep…, A quiet FIX session with a busy Application.log is a live pipeline., The bug this closes: the instance-level snapshot sums every signature, so ten…, The extra grouped snapshot must not hide ordinary rules on the same window from…, _seed_signature() (+10 more)

### Community 145 - "PublishResult"
Cohesion: 0.13
Nodes (34): classify_publish_response(), PublishAction, StrEnum, PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, make_snapshot(), parametrize, test_429_carries_retry_after_seconds() (+26 more)

### Community 157 - ".validate_and_reserve"
Cohesion: 0.28
Nodes (4): Undo an admission reservation when the bounded queue is full., Apply the backend-side allowlists and bucket cardinality cap. Pydantic has…, _CardinalityBucketKey, _SeriesKey

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 160 - "teams_agent/main.py"
Cohesion: 0.08
Nodes (26): AgentApplication, aiohttp, Application, register_handlers(), _number(), T, TeamsBotConfig, _authorize() (+18 more)

### Community 161 - "test_UBS_100_teams_bot_to_backend.py"
Cohesion: 0.11
Nodes (29): BackendError, NlBackendClient, _parse(), AsyncClient, Response, Async client for the backend's natural-language query API., build_reply(), Activity (+21 more)

### Community 195 - "test_RE_callback_integration.py"
Cohesion: 0.16
Nodes (20): AgentCounterSampler, datetime, Turns monotonic since-startup counters into per-bucket deltas. Stateful across…, Ingest the increase in each tracked counter since the last call. The first call…, telemetry_agent_metrics_agent_counters, _aggregator(), _alert(), _dispatch() (+12 more)

### Community 201 - "render_answer"
Cohesion: 0.09
Nodes (39): escape_adaptive_card_text(), Escape dynamic strings for rendered output (FR-NLQ-022)., Escape text embedded in Adaptive Card TextBlock bodies., alert_duration_minutes(), alert_prose(), breakdown_phrase(), chart_rows_from_groups(), compare_delta_phrase() (+31 more)

### Community 207 - "SessionHeartbeatTracker"
Cohesion: 0.10
Nodes (16): UBS-106: per-session heartbeat-timeout detection. A heartbeat timeout is the…, Sessions that have *just* crossed the threshold, each latched so one silence is…, Stop tracking a session. Called on `Logout`, and the reason this exists: a…, Introspection for demos/debug; not used by the detection path., Flags FIX sessions quiet for longer than `timeout_seconds`. Stateful across…, Internal tracking key, identical in format to `SeqTracker.session_key`.…, Record that a session was heard from at `at`. Any message counts, not just…, SessionHeartbeatTracker (+8 more)

### Community 210 - "parse_fix_timestamp"
Cohesion: 0.27
Nodes (9): parse_fix_timestamp(), datetime, timedelta, Parse FIX SendingTime/TransactTime as UTC., TimestampResult, FR-PRS-025/026 timestamp tests., test_FR_PRS_025_bad_timestamp_falls_back_to_log(), test_FR_PRS_025_parses_fix_timestamp_utc() (+1 more)

### Community 212 - "time.py"
Cohesion: 0.23
Nodes (16): baseline_time_range_before(), _local_midnight(), _parse_relative_duration(), _parse_short_datetime(), parse_time_expression(), datetime, timedelta, Time expression parsing for NL queries (FR-NLQ-011–014). (+8 more)

### Community 213 - "baseline.py"
Cohesion: 0.10
Nodes (28): AnomalyMetric, AnomalyReading, _baseline_value(), BaselineTracker, _current_sample(), _current_value(), _minutes(), _percent() (+20 more)

### Community 214 - "config_loader.py"
Cohesion: 0.16
Nodes (11): _AnomalyYaml, BaseModel, field_validator, model_validator, RE-05: `config/rules.yaml` loading and live reload (`FR-RUL-008`/`009`).…, _RuleYaml, _TierYaml, _to_rule_config() (+3 more)

### Community 215 - "classify_http_status"
Cohesion: 0.25
Nodes (13): classify_http_status(), StrEnum, FR-CBK-006: HTTP outcome -> retry decision classification., `FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent failure., RetryDecision, enum, parametrize, FR-CBK-006 HTTP status -> retry decision classification tests. (+5 more)

### Community 216 - "OffsetTracker"
Cohesion: 0.09
Nodes (24): Path, OffsetTracker, Path, Deprecated alias for commit_offset., Persists the current state registry to disk using atomic rename., Registrar subsystem for tracking offsets of log files. Stores file offsets…, Generates internal state ID format (e.g., 'native::16777232-1048201')., Loads state registry into memory Supports Filebeat's native list schema with… (+16 more)

### Community 217 - "fix/normalize.py"
Cohesion: 0.28
Nodes (11): compile_reject_patterns(), match_reject_label(), normalize_reject_text(), Steps 1–2 of FR-PRS-022 (matching input only, not emitted)., Return (label, is_unclassified). On no match returns (None, True) — caller…, RejectPattern, FR-PRS-022 tag 58 normalisation tests., test_FR_PRS_022_cardinality_overflow() (+3 more)

### Community 219 - "AgentHeartbeat"
Cohesion: 0.08
Nodes (22): BufferingHeartbeatSink, HeartbeatEmitter, LoggingHeartbeatSink, PrintHeartbeatSink, datetime, Event, Logger, Write one JSON line per heartbeat to stdout (demo). (+14 more)

### Community 226 - "UBS-117: event publication and integration boundary"
Cohesion: 0.18
Nodes (10): Architecture comparison, Config, Current: implemented UBS-117 baseline, Implemented in this change, Intended to-be: same services, with planned additions, Other work remains separate, Sponsor review baseline (proposed; not yet approved), UBS-117: event publication and integration boundary (+2 more)

### Community 234 - "test_a_logged_reject_burst_reaches_the_backend_alert_store"
Cohesion: 0.09
Nodes (25): connect_reporter_to_publisher(), drop_hook(), on_drop(), heartbeat_provider(), AbstractContextManager, Any, Connect the Health Reporter to the Backend Publisher (UBS-58, UBS-60). The…, The publisher's `heartbeat_provider`: a fresh, wire-shaped heartbeat on every… (+17 more)

### Community 268 - "test_UBS_25_29_anomaly.py"
Cohesion: 0.21
Nodes (33): load_anomaly_rules(), Anomaly rules from `path`; none if the file is absent or empty. Raises…, _engine(), _fire(), datetime, parametrize, _ratio_snapshot(), D2 anomaly rules (UBS-25 reject rate, UBS-26 latency, UBS-28 execution issues,… (+25 more)

### Community 269 - "effective_reject_reason"
Cohesion: 0.33
Nodes (7): effective_reject_reason(), Single precedence: ordRejReason → rejectReasonText label → unspecified. For…, FR-PRS-024 rejection precedence tests., test_FR_PRS_024_ord_rej_reason_wins(), test_FR_PRS_024_session_reject_for_msg_type_reject(), test_FR_PRS_024_text_label_when_no_ord_rej(), test_FR_PRS_024_unspecified_when_missing()

### Community 270 - "Issue tracker: Jira"
Cohesion: 0.12
Nodes (13): graphify, Before exploring, read these, Domain Docs, File structure, Flag ADR and spec conflicts, Use the glossary's vocabulary, Conventions, Issue tracker: Jira (+5 more)

### Community 271 - "test_log_monitor_status.py"
Cohesion: 0.62
Nodes (6): make_monitor(), Path, test_status_after_read_reports_elapsed_lag(), test_status_before_any_read_has_no_lag(), test_status_missing_file_has_no_size_but_does_not_raise(), test_status_reports_offset_progress_between_polls()

### Community 272 - "Metrics Query API (UBS-68, UBS-91, UBS-92)"
Cohesion: 0.22
Nodes (9): Code locations, Endpoint, Example request, Example response, Metric and dimension aliases, Metrics Query API (UBS-68, UBS-91, UBS-92), Multi-replica mode (UBS-92), Operational limits (UBS-91) (+1 more)

### Community 273 - "_Clock"
Cohesion: 0.29
Nodes (3): _Clock, datetime, One wall clock for the aggregator (epoch floats) and the evaluator (datetimes),…

### Community 274 - "test_reporter.py"
Cohesion: 0.61
Nodes (7): make_monitor(), Path, test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 275 - "Rule Engine demo runbook"
Cohesion: 0.09
Nodes (25): NoLogActivity rule, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Dependent suppression (FR-RUL-021), Rule Engine, Safety and suppression (silences, grace, storm cap), SighupRuleReloader (+17 more)

### Community 276 - "test_RE_02_evaluators.py"
Cohesion: 0.16
Nodes (31): _read_observed(), StrEnum, FR-RUL-001: Day-1 supports the first five; `anomaly` is the D2 rolling-baseline…, Where a rule's observed value is read from in a MetricsSnapshot., RuleKind, ValueSource, _absence_rule(), _gauge_rule() (+23 more)

### Community 277 - "api/health.py"
Cohesion: 0.15
Nodes (17): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary(), healthz(), metrics() (+9 more)

### Community 279 - "dataclasses"
Cohesion: 0.08
Nodes (33): BatchSequencer, build_batch(), datetime, UUID, FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, Create a monotonically increasing `batchSeq` and UUIDv7 `batchId`. The current…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, make_pending_item() (+25 more)

### Community 280 - "Teams bot"
Cohesion: 0.12
Nodes (13): Configuration, Connect Copilot, Run it locally, Telemetry MCP server, Configuration, Questions to try, Real Teams (later, not tested against a real tenant), Run it locally (5 terminals, all from the repo root) (+5 more)

### Community 281 - "Agent"
Cohesion: 0.15
Nodes (22): Agent, Magic log simulator — generates configurable FIX send/receive logs., agent(), Exception, fixture, MonkeyPatch, parametrize, Path (+14 more)

### Community 282 - "test_UBS_113_evaluation_loop.py"
Cohesion: 0.23
Nodes (12): _order(), _NullCallbackSink, datetime, UBS-113 integration: raw FIX bytes -> FixParser -> MetricsAggregator /…, Each tick is one second later, so pending -> firing happens on tick 2 without…, An order with no ack, its age read off the correlator each tick., _rule(), _run_ticks() (+4 more)

### Community 283 - "LlmSlotFillError"
Cohesion: 0.13
Nodes (20): _normalize_time_range(), parse_llm_slot_payload(), Any, Parse structured slot JSON from LLM responses (FR-NLQ-007)., JSON Schema for constrained decoding (Ollama `format`); slot schema is the…, _sanitize_filters(), slot_json_schema(), LlmSlotFillError (+12 more)

### Community 284 - "OllamaSlotFiller"
Cohesion: 0.12
Nodes (21): native_base_url(), OllamaSlotFiller, AsyncClient, Load the model into memory. An empty `messages` list only loads it., `http://host:11434/v1` -> `http://host:11434` (the `/v1` route is OpenAI's)., _chat(), Any, parametrize (+13 more)

### Community 285 - "load_agent_config"
Cohesion: 0.25
Nodes (22): AgentConfigError, load_agent_config(), Exception, Path, `agent.yaml` is missing or a section is invalid; the message names it., parametrize, Path, UBS-114: `config/agent.yaml` is read once and each section reaches the loader… (+14 more)

### Community 286 - "UBS-100 — Teams bot with Adaptive Card answers (spec)"
Cohesion: 0.20
Nodes (9): As Built, Further Notes, Implementation Decisions, Out of Scope, Problem Statement, Solution, Testing Decisions, UBS-100 — Teams bot with Adaptive Card answers (spec) (+1 more)

### Community 287 - "NlQueryService"
Cohesion: 0.12
Nodes (16): BackendConfigError, ensure_nl_llm_credentials(), NlConfig, Exception, Raised when `config/backend.yaml` exists but is invalid., _build_parser(), main(), ArgumentParser (+8 more)

### Community 288 - "health-reporter-overview.md"
Cohesion: 0.20
Nodes (9): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration, Not in this change (+1 more)

### Community 289 - "rules/demo_quickstart.py"
Cohesion: 0.16
Nodes (20): derive_heartbeat_timeout_counters(), UBS-106: one `(dims, counters)` pair per session that just timed out. Takes…, _alert_storm_act(), _backend_unreachable_act(), attempt(), _dedup_act(), _heartbeat_timeout_act(), main() (+12 more)

### Community 290 - "NlQueryContext"
Cohesion: 0.24
Nodes (19): MockLlmSlotFiller, NlQueryContext, _ask(), _ForbiddenLlm, LLM fallback behaviour (UBS-98)., _service(), test_FR_NLQ_021_timeout_falls_back_to_weak_rule_match(), test_FR_NLQ_021_unreachable_llm_without_rule_match_is_friendly() (+11 more)

### Community 291 - "QueryTimeRange"
Cohesion: 0.20
Nodes (18): to_metrics_query(), _clamp_time_range(), InterpretedValidationError, datetime, Exception, Validate interpreted queries against metrics API rules (FR-NLQ-002, FR-NLQ-008)., _schema_issues(), validate_interpreted_query() (+10 more)

### Community 292 - "ActionRunner"
Cohesion: 0.15
Nodes (9): ActionDef, ActionRunner, ActionCatalogue, AsyncBaseTransport, Logger, Swap in a reloaded catalogue. A callback action whose definition is unchanged…, Sync and non-blocking, called from `AlertRouter.route`. Returns how many action…, Drain the queue one run at a time until cancelled. (+1 more)

### Community 293 - "Exchange"
Cohesion: 0.40
Nodes (3): Exchange, Any, What the bot sent to the backend, and the reply it produced.

### Community 294 - "PipelineStats"
Cohesion: 0.33
Nodes (3): PipelineStats, Queue depths and drop counters for heartbeat/metrics (FR-PIP-005)., test_pipeline_stats_expose_prometheus_metric_names()

### Community 295 - "load_rules"
Cohesion: 0.14
Nodes (19): How long to keep ticking after the last line, so a condition that was true at…, _tail_seconds(), anomaly_path_for(), load_rules(), _parse_duration_seconds(), `anomaly.yaml` lives beside `rules.yaml` (both under `config/`)., `DEFAULT_RULES` if `path` doesn't exist; otherwise the parsed file (raising…, parametrize (+11 more)

### Community 299 - "RuleConfigError"
Cohesion: 0.19
Nodes (20): _defined_action_names(), load_rules_from_yaml(), _mtime_or_none(), Any, Exception, Path, The parsed top level of a rules file: `rules:` plus, optionally, the `actions:`…, Parses and validates `path` fully; raises `RuleConfigError` naming the… (+12 more)

### Community 300 - "to_ingestion_heartbeat"
Cohesion: 0.17
Nodes (18): provide(), Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat(), telemetry_agent_health_heartbeat, telemetry_agent_health_wire, make(), UBS-58/66 wire compatibility: our heartbeat flattened to the Ingestion…, The whole point: the Ingestion Service must accept what we send. (+10 more)

### Community 301 - "test_FR_CBK_017_isolation.py"
Cohesion: 0.15
Nodes (12): MockTransport, callback_action(), _ExplodingRunner, datetime, FR-CBK-014/017: a callback action reuses the §3 dispatcher, and a failing…, _Recorder, _runner(), test_a_callback_action_is_signed_like_the_magic_callback() (+4 more)

### Community 302 - "test_UBS_35_actions_end_to_end.py"
Cohesion: 0.16
Nodes (10): _burst(), Path, Request, Response, UBS-35 / spec 005 §5: rule actions in the real agent process, end to end.…, _Stack, test_a_bad_edit_is_rejected_and_the_agent_keeps_its_actions(), test_a_firing_rule_runs_each_of_its_actions_once() (+2 more)

### Community 303 - "signing.py"
Cohesion: 0.19
Nodes (14): load_callback_secret(), FR-CBK-005: request signing so Magic can verify a callback originated from this…, `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), FR-CBK-005 request-signing tests., test_FR_CBK_005_different_body_produces_different_signature(), test_FR_CBK_005_different_secret_produces_different_signature() (+6 more)

### Community 304 - "test_reply_guard.py"
Cohesion: 0.18
Nodes (13): guard_reply(), Guard for the LLM's conversational reply (FR-NLQ-030, FR-NLQ-009). The reply is…, The cleaned reply, or None when it must not be shown., match_small_talk(), SmallTalkKind, Deterministic small-talk replies that skip the LLM (FR-NLQ-030). Only whole-…, parametrize, Conversational reply guard and small-talk matcher (FR-NLQ-030). (+5 more)

### Community 305 - "test_FR_CBK_004_006_007_dispatcher.py"
Cohesion: 0.27
Nodes (10): _make_alert(), UBS-32/33 integration test: dispatch and retry against a mock Magic endpoint.…, _run_one(), test_FR_CBK_001_success_marks_delivered(), handler(), test_FR_CBK_004_006_persistent_5xx_retries_then_fails_after_max_attempts(), test_FR_CBK_004_006_retries_then_succeeds(), test_FR_CBK_006_429_is_retried_not_treated_as_permanent() (+2 more)

### Community 306 - "test_RE_parse_error_integration.py"
Cohesion: 0.27
Nodes (13): telemetry_agent_rules_defaults, _fire(), _ingest(), _rate(), UBS-18 integration: raw log bytes -> FixParser -> derive_parser_counters ->…, Needs a failure mode that errors once per line — see `_NO_MSG_TYPE`. The…, Documents the asymptote above as behaviour, not accident: three of every four…, `min_samples` is 20 for this rule. Under that, a single bad line in a handful… (+5 more)

### Community 307 - "telemetry_agent/config.py"
Cohesion: 0.23
Nodes (12): _ActionsYaml, LogsConfig, _LogsYaml, ParsingConfig, _ParsingYaml, _PipelineYaml, Any, BaseModel (+4 more)

### Community 308 - "test_FR_CBK_013_action_config.py"
Cohesion: 0.37
Nodes (12): _agent_yaml(), Path, FR-CBK-013/014/015: the `actions:` block, `rules[].actions` and…, _rules_file(), test_a_command_must_be_on_the_operators_allowlist(), test_a_rule_names_its_actions(), test_agent_config_carries_the_allowlist_and_catalogue(), test_agent_config_refuses_to_start_on_an_unlisted_command() (+4 more)

### Community 309 - "test_UBS_110_alert_router_callbacks.py"
Cohesion: 0.32
Nodes (11): _dispatcher(), _NullCallbackSink, _pending(), UBS-110: AlertRouter fans each alert out to the Callback Dispatcher as well as…, The guard protects the batch; a callback has no batch to poison., _router(), test_a_failing_dispatcher_does_not_cost_the_backend_its_alert(), boom() (+3 more)

### Community 310 - "test_nl_eval_fixtures.py"
Cohesion: 0.26
Nodes (11): assert_answer_numbers_in_data(), _numbers_from_data(), numeric_tokens_in_text(), FR-TST-008: numeric tokens in rendered answers must exist in structured data., _interpret_rule(), _load_fixtures(), Any, parametrize (+3 more)

### Community 311 - "SeqTracker"
Cohesion: 0.27
Nodes (7): Per-session MsgSeqNum tracking., SeqTracker, SeqGapEvent, FR-PRS-027 sequence gap tests., test_FR_PRS_027_detects_gap(), test_FR_PRS_027_detects_regression(), test_FR_PRS_027_logon_resets_without_gap()

### Community 312 - "NL query manual test plan: Ollama, Teams and Copilot (MCP)"
Cohesion: 0.17
Nodes (12): 0. Setup, A. Backend startup, B. Direct API, C. Ollama slow or down, D. Teams (Agents Playground), E. MCP server (MCP Inspector), F. Copilot Studio (optional), G. Safety (+4 more)

### Community 313 - "callbacks/demo_quickstart.py"
Cohesion: 0.27
Nodes (8): main(), _make_alert(), _print_counters(), Minimal walkthrough of the Callback Dispatcher (UBS-32/33). uv run python -m…, Stands in for Magic: keys its canned response off the alert ID inside the…, _run_one(), _ScriptedSink, _step()

### Community 314 - "demo_reload.py"
Cohesion: 0.29
Nodes (10): _banner(), _instructions(), main(), Path, Live walkthrough of SIGHUP rule reloading (`FR-RUL-008`/`009`). uv run python…, The watched file may be mid-edit or deliberately broken; a failed read here…, _run(), _safe_rule_count() (+2 more)

### Community 315 - ".snapshot"
Cohesion: 0.20
Nodes (3): Always with the correlator attached — that's what populates the `latency`…, Evaluate twice: once to move a matched rule to `pending`, then again past its…, One evaluation a moment later — enough for a tier escalation, which takes…

### Community 316 - "test_UBS_128_level_rules.py"
Cohesion: 0.33
Nodes (9): _Stack, UBS-128: a `threshold` rule with `level:` counts only one Application.log level…, _seed_app_errors(), _summary(), test_error_lines_do_not_fire_the_default_level_rule(), test_errors_are_still_counted_in_app_log_errors(), test_instance_rules_still_evaluate_alongside_level_rules(), test_level_rule_is_independent_of_signature_rules() (+1 more)

### Community 317 - "test_STM_03_warmup.py"
Cohesion: 0.33
Nodes (9): datetime, FR-STM-006: an agent's post-restart cold-start state is preserved through the…, warmingUp flags incomplete data for the caller to exclude; it does not mean the…, _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up(), test_data_from_a_restarted_bucket_is_still_merged_not_dropped(), test_restarted_bucket_count_reflects_only_buckets_a_restart_touched() (+1 more)

### Community 318 - "telemetry_agent/demo_suite.py"
Cohesion: 0.33
Nodes (8): main(), poll_available(), print_lines(), print_section(), Path, Deterministic local demo for Log Monitor lifecycle behaviour. Run with ``uv run…, Read every available line without entering the infinite stream loop., run_demo()

### Community 319 - "test_RE_03_safety.py"
Cohesion: 0.36
Nodes (7): _counter_rule(), RE-02: suppression and safety (spec 005 §4) — maxActiveAlerts/AlertStorm,…, test_dependent_suppression_when_no_log_activity_is_firing(), test_max_active_alerts_emits_one_alertstorm_and_suppresses_further(), test_schedule_inactive_skips_rule_entirely(), test_silence_suppresses_notification_but_still_tracks_state(), test_storm_clears_once_under_cap_and_the_suppressed_rule_fires()

### Community 320 - "test_UBS_68_metrics_query.py"
Cohesion: 0.38
Nodes (6): starlette_testclient, _client_with_data(), TestClient, UBS-68: HTTP contract for POST /telemetry/query/metrics., test_UBS_68_http_query_returns_totals(), test_UBS_68_unknown_field_returns_400()

### Community 321 - ".__init__"
Cohesion: 0.33
Nodes (4): Clock, Register (or remove) the Publisher's buffer-bytes callback…, BufferBytesProvider, QueueDepthProvider

### Community 322 - "UBS-25–29 implementation notes (D2 anomaly detection)"
Cohesion: 0.33
Nodes (5): Conflict with spec 000 §3.2, Design decisions, Not done / follow-ups, Ticket wording problems (Jira text not edited), UBS-25–29 implementation notes (D2 anomaly detection)

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements

## Knowledge Gaps
- **263 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `IntentDefinition`, `_IntentPattern`, `telemetry-mcp` (+258 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1791 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **128 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `MetricsAggregator ring buffer` to `config/rules.yaml live rule set`, `Rule Engine demo runbook`, `AgentHeartbeat wire contract`, `Implementation Status live document`, `snapshot`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `AlertEvent` connect `AlertEvent` to `create_app`, `RuleConfig`, `make_snapshot`, `test_RE_publish_integration.py`, `test_UBS_25_29_anomaly.py`, `test_UBS_122_signature_rules.py`, `make_alert`, `dataclasses`, `Agent`, `telemetry_agent/main.py`, `dispatcher.py`, `rules/demo_quickstart.py`, `test_UBS_113_evaluator.py`, `ActionRunner`, `telemetry_backend/main.py`, `EventEmitter`, `MetricsIngestor`, `test_FR_CBK_017_isolation.py`, `CamelModel`, `test_FR_CBK_004_006_007_dispatcher.py`, `test_UBS_35_36_reload_and_draft.py`, `test_RE_parse_error_integration.py`, `test_UBS_110_alert_router_callbacks.py`, `callbacks/demo_quickstart.py`, `datetime`, `.snapshot`, `test_RE_session_integration.py`, `test_UBS_128_level_rules.py`, `RuleEvaluator`, `test_RE_callback_integration.py`, `_Demo`, `render_answer`, `test_RE_06_reload.py`, `HeartbeatMonitor`, `AlertStore`, `pytest`, `publish_fixtures.py`, `BackendPublisher`, `test_UBS_109_alert_router.py`, `backtest`, `parse_callbacks_config`, `test_UBS_109_rule_engine_to_backend.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `CamelModel` connect `CamelModel` to `create_app`, `NlQueryContext`, `RuleConfig`, `QueryTimeRange`, `data_completeness.py`, `HealthReporter`, `telemetry_backend/main.py`, `render_answer`, `cards.py`, `EventStore`, `test_UBS_27_reject_reason_trends.py`, `metrics/__init__.py`, `QueryEngine`, `Snapshot`, `datetime`, `AgentHeartbeat`, `AlertEvent`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 81 INFERRED edges - model-reasoned connections that need verification._