# Graph Report - avengers-fyp-is484  (2026-10-22)

## Corpus Check
- 400 files · ~217,600 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: (none) 11, .example 1, .typed 1)

## Summary
- 5110 nodes · 13973 edges · 299 communities (176 shown, 123 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 2464 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `33c78a3e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- IngestionService
- test_FR_PRS_012_frame.py
- test_metrics_event.py
- RuleEngine
- make_snapshot
- load_agent_config
- HealthReporter
- AppLogParser
- RetryPolicy
- LatencyCorrelator
- derive_counters
- test_RE_publish_integration.py
- AgentHeartbeat
- LogMonitor
- PublishBuffer
- SourceMeta
- LlmConfig
- PublishResult
- MetricsAggregator
- deps.py
- make_alert
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- test_bot_replies.py
- factory.py
- CounterRegistry
- build_agent
- DeliveryStatus
- HeartbeatConfig
- test_MA_05_agent_counters.py
- AggregatorConfig
- test_ING_004_008_ingest_guard.py
- _Stack
- test_MA_03_correlation.py
- Stack
- config/rules.yaml live rule set
- create_app
- EventEmitter
- MetricsAggregator ring buffer
- AgentRegistry
- MetricsIngestor
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- heartbeat_json
- CallbackDispatcher
- test_UBS_35_36_reload_and_draft.py
- telemetry_agent_callbacks_config
- ParseResult
- metric_store.py
- parse_publish_config
- QueryEngine
- Histogram
- LineClassification
- from_alert_event
- test_RE_session_integration.py
- AlertEvent
- Registry
- test_queue_depth.py
- RuleEvaluator
- service.py
- test_UBS_116_app_log_counters.py
- enrich.py
- test_UBS_117_events.py
- _Demo
- Telemetry Agent (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- ActionRunner
- test_agent_registry.py
- http
- 009 — Non-Functional Requirements and Security
- StreamProcessorConfig
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- test_UBS_36_backtest_cli.py
- run_slow_parser_backpressure
- HeartbeatMonitor
- datetime
- services/demo_quickstart.py
- make_alert_event
- End-to-End Acceptance Scenario (FR-TST-010)
- HttpsPublishSink
- test_ING_004_008_routes.py
- make_snapshot
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- build_batch
- MultiLogMonitor
- telemetry_agent_callbacks_backoff
- Snapshot
- test_STM_04_efficiency.py
- parsed_message.py
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- test_QRY_04_concurrency.py
- BackendPublisher
- Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- cards.py
- telemetry_backend/config.py
- backtest.py
- test_RE_integration.py
- manifest.json
- telemetry_shared shared schema package
- telemetry_agent/config.py
- Requirement ID Scheme (FR-<AREA>-<NNN>)
- _Harness
- test_UBS_115_snapshot_to_metricstore.py
- test_UBS_109_rule_engine_to_backend.py
- frame.py
- test_readyz_shared_processor.py
- test_backend_self_metrics.py
- test_UBS_115_snapshot_bridge.py
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- services/self_metrics.py
- telemetry_agent_parser_applog_signatures
- snapshot
- ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server
- ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- rules/demo_quickstart.py
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
- _load
- teams_agent/__init__.py
- PublishAction
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
- TeamsBotConfig
- teams/fixtures.py
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
- AlertStore
- telemetry_agent_parser_fix_telemetry
- telemetry_agent_callbacks_retry
- telemetry_agent_parser_registry
- telemetry_agent_callbacks_self_metrics
- telemetry_agent_callbacks_signing
- metrics_event.py
- telemetry_shared_metrics
- telemetry_shared_metrics_histogram
- parse_fix_timestamp
- telemetry_agent_common_backoff
- rule_matcher.py
- Rule Engine
- decimal
- classify_http_status
- OffsetTracker
- fix/normalize.py
- http_server
- publishing/demo_quickstart.py
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
- FixParser
- effective_reject_reason
- Issue tracker: Jira
- test_log_monitor_status.py
- Metrics Query API (UBS-68, UBS-91, UBS-92)
- .__init__
- test_reporter.py
- Rule Engine demo runbook
- Sponsor email — deployment and storage clarifications (Q-13)
- internal.py
- actions/__init__.py
- .__init__
- Teams bot
- test_degraded_status_flows_into_heartbeat_payload
- _wire
- test_UBS_100_teams_bot_to_backend.py
- test_UBS_104_offline_buffering.py
- publishing/__init__.py
- UBS-100 — Teams bot with Adaptive Card answers (spec)
- _error_card_text
- health-reporter-overview.md
- _Agent
- test_llm_fallback.py
- api/health.py
- test_callback_event_failure_does_not_break_terminal_delivery_tracking
- text_blocks
- PipelineStats
- IngestionConfig
- ._serialize_counters
- build.sh

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 120 edges
2. `AlertEvent` - 105 edges
3. `create_app()` - 100 edges
4. `HealthReporter` - 89 edges
5. `BackendPublisher` - 85 edges
6. `MetricStore` - 84 edges
7. `StreamProcessorConfig` - 82 edges
8. `SourceMeta` - 80 edges
9. `FixParser` - 74 edges
10. `CamelModel` - 73 edges

## Surprising Connections (you probably didn't know these)
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py
- `Multi-replica mode (UBS-92)` --references--> `QueryConfig`  [INFERRED]
  docs/plan/metrics-query-api.md → apps/backend/src/telemetry_backend/config.py
- `Consequences` --references--> `build_reply()`  [INFERRED]
  docs/adr/0009-m365-agents-sdk-for-teams-bot.md → apps/teams/src/teams_agent/bot.py

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

## Communities (299 total, 123 thin omitted)

### Community 0 - "IngestionService"
Cohesion: 0.14
Nodes (30): BatchAccepted, IngestionService, Keep store work off FastAPI's request path. A single consumer preserves the…, Owns a bounded queue and one background consumer., fastapi_routing, EventsRequest, model_validator, Convenience endpoint request for events. (+22 more)

### Community 1 - "test_FR_PRS_012_frame.py"
Cohesion: 0.11
Nodes (24): frame_message(), FrameOptions, Framer, FrameResult, LineJoiner, Joins split FIX messages across log lines., Frame a single complete log line., Per file-set framing configuration. (+16 more)

### Community 2 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (40): build_parsed_message_event(), Construct the Metrics Aggregator's event from one framed FIX line. Returns None…, _meta(), _parse(), _parser_counters(), datetime, Decimal, parametrize (+32 more)

### Community 3 - "RuleEngine"
Cohesion: 0.10
Nodes (40): _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _matched_tier(), _metric_context(), datetime (+32 more)

### Community 4 - "make_snapshot"
Cohesion: 0.11
Nodes (55): make_gauges(), make_indicator(), make_indicators(), make_latency(), make_snapshot(), datetime, Decimal, Shared test support for the rules package: builds `MetricsSnapshot` fixtures… (+47 more)

### Community 5 - "load_agent_config"
Cohesion: 0.05
Nodes (85): ActionConfigError, ActionDef, _ActionYaml, _command_key(), _is_rooted(), load_action_catalogue(), _parse_action(), parse_actions() (+77 more)

### Community 6 - "HealthReporter"
Cohesion: 0.06
Nodes (46): AgentStatus, HealthThresholds, FR-HLT-002 thresholds. Only the read-lag one has a producer on UBS-58; the rest…, HealthReporter, HealthSignals, is_parse_error(), datetime, Per-file read health, keyed by the same name `monitors` was built with. (+38 more)

### Community 7 - "AppLogParser"
Cohesion: 0.08
Nodes (26): AppLogParser, Parser plugin for configured application log patterns (Magic format)., compile_signature_rules(), First-match-wins signature rules with dynamic label templates., resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule (+18 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.06
Nodes (40): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, main(), format_fix_line(), generate_application_log() (+32 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.07
Nodes (31): default_resolve_reject_reason(), Fallback reject_reason resolver: no normalisation map, just the raw value.…, CorrelatorStats, LatencyCorrelator, OrderContext, Clock, datetime, Decimal (+23 more)

### Community 10 - "derive_counters"
Cohesion: 0.11
Nodes (34): derive_counters(), All four counter families in one event walk., Config-driven raw-reason -> canonical-label mapping. Backs MetricsAggregator's…, ReasonNormalizer, _banner(), _implementation(), _line(), main() (+26 more)

### Community 11 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (22): _aggregator(), _engine(), _fail_n_times(), _publisher(), UBS-75 integration: BackendPublisher -> consecutive_publish_failures gauge ->…, The whole reason this is a gauge: recovery is observable. A windowed failure…, FR-MET-031. An agent with no publisher must not look like an agent that is…, Regression guard on spec 005 §1.2's withdrawn approximation.… (+14 more)

### Community 12 - "AgentHeartbeat"
Cohesion: 0.07
Nodes (35): HeartbeatEmitter, LoggingHeartbeatSink, PrintHeartbeatSink, datetime, Event, Logger, Write one JSON line per heartbeat to stdout (demo)., Build and send one heartbeat. Sink failures are counted, not raised: a dead… (+27 more)

### Community 13 - "LogMonitor"
Cohesion: 0.07
Nodes (22): Harvester, LogMonitor, Path, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, Find retained rotations that were created while the agent was down. This…, Keep a rotated descriptor alive to collect its final writes., Persist progress even when a continuously busy file never reaches EOF. (+14 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (25): PublishBuffer, datetime, Remove and return up to `max_items` from the front., Put previously-`take`n items back at the front, in original order -- they are…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both…, Drop items older than `max_age_seconds`. The deque is strictly insertion-…, _item(), FR-PUB-004: the byte-and-age-bounded `PublishBuffer` (UBS-104's replacement for… (+17 more)

### Community 15 - "SourceMeta"
Cohesion: 0.05
Nodes (37): Metadata attached to each log line by the monitor., SourceMeta, QueueSnapshot, PipelineCommitter, Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)., Consumes ParsedEvent objects and commits file offsets after ingest., LinePosition, ProcessedLineDeduper (+29 more)

### Community 16 - "LlmConfig"
Cohesion: 0.13
Nodes (30): ensure_nl_llm_credentials(), LlmConfig, NlConfig, Apply provider-specific defaults after YAML merge., resolve_llm_config(), build_llm_filler(), build_nl_service(), AsyncClient (+22 more)

### Community 17 - "PublishResult"
Cohesion: 0.08
Nodes (18): Stands in for the backend: returns responses from a fixed script, one per call,…, _ScriptedSink, classify_publish_response(), PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, _alerts_to_backend_act(), _FlakyBackendSink, UBS-109. Every act above raised its alert locally and stopped there —… (+10 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.12
Nodes (17): _Bucket, _dimension_value(), MetricRow, MetricsAggregator, Clock, datetime, Decimal, One time slot in the ring. `start` is None when the slot is empty. Storage is… (+9 more)

### Community 19 - "deps.py"
Cohesion: 0.08
Nodes (36): EventStoreConfig, Event store retention (UBS-118; spec 010 `store.recentAlertLimit` default)., datetime, Shared service instances the routers reach through `request.app.state`. One…, _utc_now(), EventStore, _InstanceEvents, datetime (+28 more)

### Community 20 - "make_alert"
Cohesion: 0.05
Nodes (57): load_callback_secret(), `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), MockTransport, _burst(), Path, Request (+49 more)

### Community 21 - "MetricStore"
Cohesion: 0.10
Nodes (19): _CanonicalBucket, MetricStore, datetime, Lock, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a…, Evict buckets that have aged out of retention within *one* instance's ring —…, Evict stale buckets across every instance's ring and check memory pressure. For… (+11 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.08
Nodes (35): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+27 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.07
Nodes (50): Per-session MsgSeqNum tracking., SeqTracker, Sessions that have *just* crossed the threshold, each latched so one silence is…, Stop tracking a session. Called on `Logout`, and the reason this exists: a…, Introspection for demos/debug; not used by the detection path., Flags FIX sessions quiet for longer than `timeout_seconds`. Stateful across…, Internal tracking key, identical in format to `SeqTracker.session_key`.…, Record that a session was heard from at `at`. Any message counts, not just… (+42 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (32): health: threshold config block, heartbeat: interval config, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry (+24 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "test_bot_replies.py"
Cohesion: 0.21
Nodes (40): Handler, QueryGroup, answer(), clarification(), converse(), group(), json_ok(), message() (+32 more)

### Community 27 - "factory.py"
Cohesion: 0.14
Nodes (22): Construct NL services from backend configuration., AzureOpenAiSlotFiller, Azure OpenAI structured slot filling (FR-NLQ-007)., LLM slot-filling fallback (FR-NLQ-007)., default_mock_responses(), MockLlmSlotFiller, Deterministic LLM mock for tests (FR-TST-009)., _JsonModeRejected (+14 more)

### Community 28 - "CounterRegistry"
Cohesion: 0.08
Nodes (15): CounterRegistry, Plain dict of named counters behind a lock -- increments happen from both async…, Self-observability, same shape as `BackendPublisher.counters` and…, AbstractContextManager, Any, Logger, datetime, UBS-123: publishes every completed wire bucket once, oldest first. (+7 more)

### Community 29 - "build_agent"
Cohesion: 0.05
Nodes (54): AbstractEventLoop, AgentConfig, Agent, build_agent(), check_action_secret(), stage_actions(), _build_parser(), _install_signals() (+46 more)

### Community 30 - "DeliveryStatus"
Cohesion: 0.09
Nodes (28): DeliveryRecord, DeliveryStatus, DeliveryTracker, datetime, StrEnum, UBS-34: per-alert-occurrence callback delivery status, timestamped at each…, UBS-34 AC: every dispatched callback has exactly one of these five states at…, One alert's current delivery state. `attempt_count` and `last_error` are… (+20 more)

### Community 31 - "HeartbeatConfig"
Cohesion: 0.11
Nodes (33): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, HeartbeatConfig, _HeartbeatYaml, load_health_config() (+25 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.14
Nodes (24): AgentCounterSampler, datetime, Turns monotonic since-startup counters into per-bucket deltas. Stateful across…, Ingest the increase in each tracked counter since the last call. The first call…, _aggregator(), Decimal, UBS-74: `MetricsAggregator.ingest_agent_counters` and the `AgentCounterSampler`…, A restarted dispatcher's registry drops back to 0. That is a new baseline, not… (+16 more)

### Community 33 - "AggregatorConfig"
Cohesion: 0.19
Nodes (22): AggregatorConfig, Bucket granularity, retained windows, and the per-metric dimension table (FR-…, FakeClock, A `Clock` (`() -> float`) that only advances when told to — lets a test assert…, make_event(), minimal_aggregator(), Decimal, test_10k_events_in_60s_window_returns_correct_count() (+14 more)

### Community 34 - "test_ING_004_008_ingest_guard.py"
Cohesion: 0.09
Nodes (34): IngestGuardConfig, UBS-85: batch dedupe (FR-ING-004) and per-agent rate limiting (FR-ING-008).…, Accept, Duplicate, IngestGuard, Clock, datetime, RateLimited (+26 more)

### Community 35 - "_Stack"
Cohesion: 0.10
Nodes (36): _Stack, _names(), Path, Write counters straight into the store, labelled with placeholder dimension…, RejectSpike reads 1m, HighRejectRate reads 5m: one tick, both., The tracker latches each silence: many ticks after the timeout still put…, A rules file the loader accepts, from the shipped config's own entries, so the…, _rule() (+28 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "Stack"
Cohesion: 0.09
Nodes (18): committed_offsets(), FakeClock, fix_lines(), datetime, FastAPI, fixture, MonkeyPatch, Path (+10 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.14
Nodes (21): BackendUnreachable rule, CallbackFailing rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule, PendingOrderTimeout rule (+13 more)

### Community 39 - "create_app"
Cohesion: 0.05
Nodes (61): HTTP routers, one file per concern (spec 007). `health.py` (UBS-69) serves the…, AlertsQueryParams, _counts(), create_app(), enqueue_or_full(), get_alert(), get_event(), ingest_batch() (+53 more)

### Community 40 - "EventEmitter"
Cohesion: 0.29
Nodes (4): EventEmitter, Any, datetime, Failure/drop never interrupts metrics, rules or callback delivery.

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.13
Nodes (20): AckLatencyBreach rule, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent), Histogram (fixed buckets, merge, percentile), MA-epic known gaps (ExecID dedup, timestamp_source) (+12 more)

### Community 42 - "AgentRegistry"
Cohesion: 0.11
Nodes (14): AgentRecord, AgentRegistry, Clock, datetime, Agent Registry (spec 006 FR-ING-010; UBS-69 read side, UBS-87 write side). One…, `missing` if stale, otherwise whatever the agent last reported., Agent IDs past the threshold - the `dataCompleteness.staleAgents` input (FR-…, Thread-safe map of known agents. Memory-only by design (FR-QRY-005). (+6 more)

### Community 43 - "MetricsIngestor"
Cohesion: 0.14
Nodes (25): MetricsIngestor, Logger, The production set: an aggregator that accepts every counter and latency…, _now_sending_time(), MonkeyPatch, Path, test_tailed_fix_lines_reach_the_real_aggregator(), _counters() (+17 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (18): bad(), FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides() (+10 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.13
Nodes (21): Clock, datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, telemetry_agent_health_window (+13 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.11
Nodes (24): Problem P-1: Limited visibility into live trading activity and health, Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), Consistent-Hash Routing on instanceId, 001 — Architecture, Failure Degradation Order (queries → freshness → callbacks → alerting), Ingestion Service (component) (+16 more)

### Community 47 - "CamelModel"
Cohesion: 0.06
Nodes (57): Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, build_intents_response(), 4.1 Wire contract — `packages/telemetry_shared/models/health.py`, AlertCounts, AlertDelivery, AlertDetailResponse, AlertRecord, AlertsListResponse (+49 more)

### Community 48 - "heartbeat_json"
Cohesion: 0.09
Nodes (31): heartbeat_json(), Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat(), telemetry_agent_health_heartbeat, FakeClock, datetime, UBS-104: publish buffer bytes and dropped-event rate in the heartbeat. Mirrors… (+23 more)

### Community 49 - "CallbackDispatcher"
Cohesion: 0.06
Nodes (39): main(), _make_alert(), _print_counters(), Minimal walkthrough of the Callback Dispatcher (UBS-32/33). uv run python -m…, Stands in for Magic: keys its canned response off the alert ID inside the…, _run_one(), _ScriptedSink, _step() (+31 more)

### Community 50 - "test_UBS_35_36_reload_and_draft.py"
Cohesion: 0.12
Nodes (27): datetime, Logger, Reloads `config/rules.yaml` into a live `RuleEngine`, on SIGHUP or (UBS-35, so…, True when the file's mtime differs from the one last loaded (or last rejected,…, Returns the `resolved` events `apply_rules()` emits for alerts whose rule was…, Standalone use only: this reloads inside the signal handler and drops the…, SighupRuleReloader, ReloadStage (+19 more)

### Community 52 - "ParseResult"
Cohesion: 0.11
Nodes (41): DemoMetricsSink, extract_log_level(), Extract [N/E/W/F/I] level from Magic-style log lines., _corpus_files(), _fields_dict(), _format_line_result(), _load_config(), main() (+33 more)

### Community 53 - "metric_store.py"
Cohesion: 0.13
Nodes (20): _dim_key(), DimKey, Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, _SeriesContribution, build_latency_summary(), Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004). Shared by the…, compute_indicators(), compute_ratio() (+12 more)

### Community 54 - "parse_publish_config"
Cohesion: 0.13
Nodes (27): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfigError, Any, Exception, Path, Parses an already-loaded `publish:` YAML section. Pure — no file I/O — so it's… (+19 more)

### Community 55 - "QueryEngine"
Cohesion: 0.06
Nodes (38): QueryConfig, Query engine limits (spec 006 §5, spec 010 `query.*`)., _AccumulatedGroup, datetime, Decimal, DimKey, Exception, timedelta (+30 more)

### Community 56 - "Histogram"
Cohesion: 0.10
Nodes (30): _bridge_to_snapshot(), The conversion a real Backend Publisher would do: turn one agent's raw MA-01…, Histogram, Decimal, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, HistogramPayload (+22 more)

### Community 57 - "LineClassification"
Cohesion: 0.14
Nodes (23): classify_line(), compile_app_log_patterns(), _looks_like_fix(), Pattern, Line classification (FR-PRS-010, FR-PRS-011)., Classify a log line before parsing (FR-PRS-010). Order: fix → app_log →…, True when 8=FIX/8=FIXT is followed by a delimiter and 35= within the window.…, Compile configured app-log regexes for use after FIX detection fails. (+15 more)

### Community 58 - "from_alert_event"
Cohesion: 0.21
Nodes (15): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, deliver(), make_alert_event(), FR-CBK-001/002/003 callback payload shape tests. (+7 more)

### Community 59 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (29): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), Decimal, UBS-73 integration: raw FIX log bytes -> FixParser -> metrics_event bridge ->…, A tracker that has watched `lines` go past, so it knows which sessions exist… (+21 more)

### Community 60 - "AlertEvent"
Cohesion: 0.07
Nodes (15): Sync and non-blocking, called from `AlertRouter.route`. Returns how many action…, Drain the queue one run at a time until cancelled., Run one action for one alert and return its outcome. Never raises (except…, Signs and sends `alert`, retrying transient failures with backoff (`FR-…, Sync, non-blocking — the entry point a future wiring step calls from the same…, Deliver one alert now, bypassing the queue and the workers, and return its…, Spawns `maxInflight` workers pulling from the queue. Runs until cancelled by…, datetime (+7 more)

### Community 61 - "Registry"
Cohesion: 0.05
Nodes (38): Confidence, Parser, Enum, Protocol, str, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'. (+30 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.11
Nodes (22): BufferingHeartbeatSink, Bounded retry buffer in front of another sink (UBS-60 demo stand-in). Not the…, Missing downstream / upstream (what this branch cannot prove), HeartbeatSink, FakeQueue, Flaky, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend. (+14 more)

### Community 63 - "RuleEvaluator"
Cohesion: 0.16
Nodes (10): datetime, Event, Signal-safe: only sets a flag. Register it with…, One tick. Returns every alert routed, in routing order., Tick every `interval_seconds` until `stop` is set; the first tick is immediate.…, Cheap (one `stat`), but still rate-limited to `reload_check_seconds`; 0…, UBS-123: runs after aging so retention matches the aggregator., Runs the Rule Engine every `interval_seconds` and routes its alerts. Shared… (+2 more)

### Community 64 - "service.py"
Cohesion: 0.08
Nodes (39): build_default_filters(), default_time_range(), IntentDefinition, Day-1 intent catalogue and slot defaults (FR-NLQ-003, FR-NLQ-004)., merge_interpreted_query(), Compile interpreted NL slots into metrics query requests., to_metrics_query(), Natural language query interpretation (spec 008, UBS-97/98). (+31 more)

### Community 65 - "test_UBS_116_app_log_counters.py"
Cohesion: 0.12
Nodes (28): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MA-02: order / execution / reject counters and reject-reason normalisation.…, fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not OrdStatus —… (+20 more)

### Community 66 - "enrich.py"
Cohesion: 0.27
Nodes (15): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+7 more)

### Community 67 - "test_UBS_117_events.py"
Cohesion: 0.16
Nodes (25): parse(), app(), meta(), FR-MET-020/021/022/023: bounded events, independently of alert decisions., sent(), Sink, stack(), test_alert_mirror_suppresses_reminders_but_keeps_escalation_and_resolution() (+17 more)

### Community 68 - "_Demo"
Cohesion: 0.05
Nodes (38): _alert_storm_act(), _backend_unreachable_act(), attempt(), _dedup_act(), _Demo, _heartbeat_timeout_act(), main(), _no_log_activity_act() (+30 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.11
Nodes (22): Agent processing pipeline (monitor to health reporter), Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Magic simulator for development, Do not overengineer (development principle), Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores (+14 more)

### Community 70 - "AppDeps"
Cohesion: 0.21
Nodes (23): AppDeps, env(), FakeClock, heartbeat(), post(), datetime, fixture, TestClient (+15 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.10
Nodes (13): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+5 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (20): env(), FakeClock, heartbeat(), post_heartbeat(), datetime, fixture, TestClient, UBS-96: /healthz, /readyz, /metrics on the internal app (FR-HLT-010/012). (+12 more)

### Community 73 - "ActionRunner"
Cohesion: 0.06
Nodes (26): ActionType, StrEnum, ActionRunner, ActionCatalogue, AsyncBaseTransport, datetime, Logger, Swap in a reloaded catalogue. A callback action whose definition is unchanged… (+18 more)

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.14
Nodes (16): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), Resource Discipline (§9), Compliance and Operability Constraints (§7), 009 — Non-Functional Requirements and Security, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-REL-003: Backend Outage Must Not Affect Alerting, NFR-SCA-001: Agent Independence/Statelessness (+8 more)

### Community 77 - "StreamProcessorConfig"
Cohesion: 0.07
Nodes (45): StreamProcessorConfig, datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep…, _snapshot() (+37 more)

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

### Community 82 - "test_UBS_36_backtest_cli.py"
Cohesion: 0.48
Nodes (6): subprocess, Path, UBS-36: test mode over real simulator output, through the real CLI. The…, _simulate(), test_a_draft_rule_replayed_over_simulator_logs(), _test_rule()

### Community 83 - "run_slow_parser_backpressure"
Cohesion: 0.15
Nodes (18): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), OverflowPolicy, Path, Hands back the `FixParser` alongside the registry it went into. Callers need… (+10 more)

### Community 84 - "HeartbeatMonitor"
Cohesion: 0.11
Nodes (17): AlertingConfig, Backend-owned alerting rules (spec 005 `FR-RUL-030`)., backend_alert_id(), HeartbeatMonitor, datetime, Backend-owned `AgentHeartbeatMissing` rule (`FR-QRY-018`, `FR-RUL-030`)., Resolve a backend alert immediately when a fresh heartbeat arrives., Periodically evaluates agent heartbeat staleness. (+9 more)

### Community 85 - "datetime"
Cohesion: 0.07
Nodes (47): End-to-end demo: LogMonitor → queue → parse → output → commit., FR-CBK-005: request signing so Magic can verify a callback originated from this…, Log monitoring, rotation and truncation handling., One complete log line with stable byte identity for idempotent ingest., ReadLine, Multi-file polling and lifecycle management for the Log Monitor., FileReadStatus, Value objects published by the Log Monitor. (+39 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.31
Nodes (13): _accept_and_fill(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact…, The exact 3-order story from the Metrics Aggregator quickstart: two accepted…, Same shape, busier day: 98 accepted and filled, 1 rejected. (+5 more)

### Community 87 - "make_alert_event"
Cohesion: 0.15
Nodes (24): _app_with_store(), UBS-94: alert query API list + detail endpoints., test_UBS_94_batch_ingestion_makes_alerts_queryable(), test_UBS_94_detail_returns_transition_history_and_unknown_is_404(), test_UBS_94_list_filters_by_status_instance_and_since(), test_UBS_94_list_reports_truncation_when_limit_is_exceeded(), test_UBS_94_unknown_query_parameter_returns_invalid_field(), End-to-end NL service tests. (+16 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.12
Nodes (17): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Text Field Normalisation (FR-PRS-022), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025) (+9 more)

### Community 89 - "HttpsPublishSink"
Cohesion: 0.09
Nodes (23): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), AsyncBaseTransport, `FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the compressed…, `FR-PUB-001`/`002`: HTTPS POST with a bearer token, gzip above…, gzip, Headers (+15 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (9): batch(), deps(), FakeClock, metrics(), datetime, UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)., test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() (+1 more)

### Community 91 - "make_snapshot"
Cohesion: 0.14
Nodes (25): starlette_testclient, _client_with_data(), TestClient, UBS-68: HTTP contract for POST /telemetry/query/metrics., test_UBS_68_http_query_returns_totals(), test_UBS_68_unknown_field_returns_400(), _aligned_now(), make_snapshot() (+17 more)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.12
Nodes (20): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009), Configurability NFRs (§5), NFR-CFG-004: Documented Config Defaults Must Match Code (+12 more)

### Community 94 - "build_batch"
Cohesion: 0.09
Nodes (26): BatchSequencer, build_batch(), datetime, UUID, Create a monotonically increasing `batchSeq` and UUIDv7 `batchId`. The current…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, concurrent_futures, inspect (+18 more)

### Community 95 - "MultiLogMonitor"
Cohesion: 0.07
Nodes (30): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+22 more)

### Community 97 - "Snapshot"
Cohesion: 0.08
Nodes (35): align_to_canonical(), datetime, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., Aligns, age-checks, and merges snapshots into a `MetricStore`. Non-blocking and…, FR-QRY-005: `False` ("warming") until `warmupWindow` has elapsed since this…, SnapshotOutcome, StreamProcessor (+27 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (10): _CountingRing, datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in…, The old `tick()` swept every instance's ring on every merge — O(instances x…, A query over one 10s bucket on a 6h-capacity (2160-bucket) ring must not touch…, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to() (+2 more)

### Community 99 - "parsed_message.py"
Cohesion: 0.10
Nodes (30): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, model_validator, Contract between the Parser Engine and the Metrics Aggregator. Spec 003 §4… (+22 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.10
Nodes (30): extract_allowlisted_fields(), FixFields, _hash_or_none(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, Fixed-shape allowlisted field set. No attribute here may hold a raw, non-…, FR-PRS-020: extract only the tags in the compile-time allowlist above.…, hash_identifier(), load_hash_key() (+22 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (13): _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any…, _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved() (+5 more)

### Community 103 - "test_QRY_04_concurrency.py"
Cohesion: 0.13
Nodes (18): FR-QRY-004: the store MUST be safe under concurrent read/write via a per-…, A per-instance lock must still serialise writes *within* one instance — safety…, `dropped_after_retention_total` is a single store-wide counter incremented from…, `StreamProcessor.dropped_buckets_total` is incremented outside any per-instance…, `_get_or_create_instance` sets `_rings[instance_id]` before…, `_shed_oldest_tier` iterates `_rings.items()` and indexed `_instance_locks`…, _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another() (+10 more)

### Community 104 - "BackendPublisher"
Cohesion: 0.11
Nodes (16): make_pending_item(), Measured once at insert and cached on the `PendingItem` -- re-measuring on…, _size_of(), BackendPublisher, datetime, Event, UBS-75 / `FR-MET-031`: failed attempts in a row since the last successful…, Sync, non-blocking (`FR-PUB-007`) — never awaits, never blocks on a full buffer… (+8 more)

### Community 105 - "Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)"
Cohesion: 0.10
Nodes (16): Clock, Register (or remove) the Publisher's queue-depth callback., Register (or remove) the Publisher's buffer-bytes callback…, datetime, Offset + read lag for this file (UBS-30). See docs/plan/ubs30-notes.md., BufferBytesProvider, 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence (+8 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.12
Nodes (34): _alert(), _publisher(), LogCaptureFixture, Logger, parametrize, UBS-109: AlertRouter — the seam from Rule Engine output to the Backend…, Buffering is not publishing — this follows the alert all the way out through…, The containment that matters: the bad alert is dropped, the good ones are… (+26 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "cards.py"
Cohesion: 0.18
Nodes (24): _alert_badge(), _breakdown(), _breakdown_rows(), build_answer_card(), build_clarification_card(), build_error_card(), _card(), _format_value() (+16 more)

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.11
Nodes (31): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), _IngestYaml, _Lenient (+23 more)

### Community 110 - "backtest.py"
Cohesion: 0.11
Nodes (30): _app_log_time(), backtest(), tick(), BacktestReport, _DiscardRouter, _first_dated_time(), _first_time(), _fix_time() (+22 more)

### Community 111 - "test_RE_integration.py"
Cohesion: 0.22
Nodes (9): _ack(), _Clock, _new_order(), RE-05: Metrics Aggregator -> snapshot() -> Rule Engine, using real…, Mutable clock shared by the aggregator and correlator, same pattern as…, _rejected(), _session_reject(), test_real_snapshot_output_drives_the_rule_engine_correctly() (+1 more)

### Community 112 - "manifest.json"
Cohesion: 0.09
Nodes (22): accentColor, bots, description, full, short, developer, name, privacyUrl (+14 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "telemetry_agent/config.py"
Cohesion: 0.08
Nodes (36): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+28 more)

### Community 115 - "Requirement ID Scheme (FR-<AREA>-<NNN>)"
Cohesion: 0.18
Nodes (12): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Requirement ID Scheme (FR-<AREA>-<NNN>), Health Reporter (component), Health Reporter Heartbeat Requirement (FR-HLT-001), Backend Configuration and Secrets (§9), NFR-SEC-004: Secrets from Environment Only (+4 more)

### Community 116 - "_Harness"
Cohesion: 0.17
Nodes (8): _Harness, _orders(), Decimal, parametrize, At t=1200 only [1150,1200) is fully retained; 1000-1140 are skipped., Real aggregator (1s buckets, 60s retention) and publisher behind the emitter., _starts(), TestSnapshotEmitter

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.22
Nodes (19): _aggregator(), _drain_backend(), _evaluator(), _ingest_three_orders(), _publish_and_drain(), _publisher(), Decimal, FastAPI (+11 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.12
Nodes (34): _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _order(), _publish_and_drain(), _publisher(), UBS-109 integration: raw FIX bytes -> FixParser -> MetricsAggregator ->… (+26 more)

### Community 119 - "frame.py"
Cohesion: 0.18
Nodes (18): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), FramedMessage, _has_checksum_field() (+10 more)

### Community 120 - "test_readyz_shared_processor.py"
Cohesion: 0.13
Nodes (16): fastapi_testclient, HTTP routes for NL query., test_nl_query_disabled_returns_503(), _batch_with_snapshot(), datetime, FR-QRY-005: `/readyz` probes the same StreamProcessor that ingestion feeds.…, test_create_app_probes_the_supplied_services_own_processor(), test_create_app_rejects_a_processor_the_service_does_not_feed() (+8 more)

### Community 121 - "test_backend_self_metrics.py"
Cohesion: 0.15
Nodes (18): Prometheus exposition for the backend's own internals (FR-HLT-010)., Recompute per-agent gauges from the registry. Called per scrape so the exporter…, (body, content-type) for `GET /metrics`., SelfMetrics, body(), heartbeat(), datetime, UBS-96: SelfMetrics without HTTP. (+10 more)

### Community 122 - "test_UBS_115_snapshot_bridge.py"
Cohesion: 0.18
Nodes (15): build_snapshot(), Rename each internal dim to its wire name and drop anything not allowlisted…, One `Snapshot` for the closed interval `[bucket_start, bucket_start +…, _to_payload(), _to_wire_dimensions(), _aggregator(), _app_log_aggregator(), UBS-115: `snapshot_bridge.build_snapshot` unit tests. `build_snapshot` is the… (+7 more)

### Community 123 - "Implementation Status live document"
Cohesion: 0.14
Nodes (20): ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, Implementation Status live document, M1.5 Pipeline bridge (UBS-48/49), M1 Log monitor and configuration (not started) (+12 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "services/self_metrics.py"
Cohesion: 0.13
Nodes (16): _BoundSourcesCollector, _counter(), _gauge(), Clock, datetime, Backend self-metrics (UBS-96; FR-HLT-010, spec 006 s7). `SelfMetrics` owns a…, Reads ingestion / stream processor / store state at scrape time., _utc_now() (+8 more)

### Community 127 - "snapshot"
Cohesion: 0.22
Nodes (19): _fire(), _rate(), Needs a failure mode that errors once per line — see `_NO_MSG_TYPE`. The…, test_a_clean_log_never_fires(), test_a_mostly_unparseable_log_escalates_to_critical(), test_unparseable_lines_fire_parse_error_rate(), hand_labelled_events(), Shared test support for the metrics package: a hand-labelled synthetic FIX-… (+11 more)

### Community 128 - "ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server"
Cohesion: 0.20
Nodes (9): ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server, Consequences, Context, Decision, Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents), NL Intent Catalogue (FR-NLQ-003/004) (+1 more)

### Community 129 - "ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell"
Cohesion: 0.33
Nodes (6): ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell, Consequences, Context, Decision, Rationale, callback()

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "rules/demo_quickstart.py"
Cohesion: 0.08
Nodes (46): UBS-35: runs a rule's actions when its alert fires (spec 005 §5). `AlertRouter`…, FR-CBK-*: the `callbacks:` YAML config section (spec 010), following the same…, UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, FR-CBK-007: bounded pending queue, drop-oldest on overflow., Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, FR-CBK-001/011: the swappable Callback transport boundary (spec 005 §3).…, UBS-104: lightweight in-process counters, shared between the Callback…, Heartbeat emitter (UBS-58, FR-HLT-001). Ticks on a fixed interval regardless of… (+38 more)

### Community 133 - "data_completeness.py"
Cohesion: 0.47
Nodes (5): build(), DataCompleteness, datetime, `dataCompleteness` block for query responses (spec 006 s4.1, FR-QRY-015).…, Derive completeness from the registry at `at`. `expected_agent_ids` is the set…

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 138 - "test_UBS_36_backtest.py"
Cohesion: 0.20
Nodes (22): Telemetry Agent — lightweight sidecar for Magic instances., CaptureFixture, _fix_log(), _nothing_may_be_dispatched(), fixture, MonkeyPatch, Path, UBS-36: test mode replays log files through one rule and reports whether, when… (+14 more)

### Community 143 - "_load"
Cohesion: 0.60
Nodes (5): _load(), Path, test_a_label_on_a_non_signature_rule_is_rejected(), test_a_signature_rule_loads_with_its_label(), test_a_signature_rule_without_a_label_is_rejected()

### Community 145 - "PublishAction"
Cohesion: 0.30
Nodes (18): PublishAction, StrEnum, make_snapshot(), _FakeSink, _publisher(), LogCaptureFixture, UBS-103: `BackendPublisher.publish_once()` against the full spec 007 §2.1…, Two separate batches both getting 400'd (e.g. a persistent schema bug)… (+10 more)

### Community 157 - ".validate_and_reserve"
Cohesion: 0.14
Nodes (10): IngestionValidationIssue, Undo an admission reservation when the bounded queue is full., Bound an attacker-controlled key before including it in an error path., One safe, field-level reason an ingestion request was rejected., Apply the backend-side allowlists and bucket cardinality cap. Pydantic has…, _safe_key(), _CardinalityBucketKey, allowed_event_fields() (+2 more)

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 160 - "TeamsBotConfig"
Cohesion: 0.11
Nodes (18): Application, _number(), T, Teams bot settings, read from the environment. Microsoft app credentials…, TeamsBotConfig, _authorize(), create_app(), main() (+10 more)

### Community 161 - "teams/fixtures.py"
Cohesion: 0.09
Nodes (32): AgentApplication, aiohttp, Read-only configuration shared with the ingestion boundary., BackendError, NlBackendClient, _parse(), AsyncClient, Response (+24 more)

### Community 195 - "test_RE_callback_integration.py"
Cohesion: 0.24
Nodes (15): _aggregator(), _alert(), _dispatch(), _drain(), _fire(), UBS-74 integration: CallbackDispatcher -> CounterRegistry ->…, The registry is monotonic, so re-ingesting its absolute value on every tick…, `secondsSinceLastEvent` must stay untouched by the agent's own counters —… (+7 more)

### Community 201 - "AlertStore"
Cohesion: 0.16
Nodes (11): AlertStoreConfig, Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)., AlertStore, _InstanceAlerts, _is_active_status(), datetime, Lock, In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`). (+3 more)

### Community 207 - "metrics_event.py"
Cohesion: 0.09
Nodes (34): _fixed_now(), main(), Minimal walkthrough of parser/metrics_event.py: the same three-order story as…, _step(), One session that has just gone quiet for too long. Carries both identifiers on…, SessionTimeout, FixTelemetry, Sanitized telemetry derived from a framed FIX message. (+26 more)

### Community 210 - "parse_fix_timestamp"
Cohesion: 0.27
Nodes (9): parse_fix_timestamp(), datetime, timedelta, Parse FIX SendingTime/TransactTime as UTC., TimestampResult, FR-PRS-025/026 timestamp tests., test_FR_PRS_025_bad_timestamp_falls_back_to_log(), test_FR_PRS_025_parses_fix_timestamp_utc() (+1 more)

### Community 212 - "rule_matcher.py"
Cohesion: 0.12
Nodes (27): _extract_filters(), _extract_instance(), _extract_symbol(), _IntentPattern, match_rules(), Pattern, Deterministic rule-first intent matcher (FR-NLQ-006)., rule_match_to_interpreted() (+19 more)

### Community 213 - "Rule Engine"
Cohesion: 0.15
Nodes (16): NoLogActivity rule, Multi-tier severity rule shape, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Dependent suppression (FR-RUL-021), Rule Engine, Safety and suppression (silences, grace, storm cap) (+8 more)

### Community 214 - "decimal"
Cohesion: 0.09
Nodes (31): BaseModel, field_validator, model_validator, RE-05: `config/rules.yaml` loading and live reload (`FR-RUL-008`/`009`).…, _RuleYaml, _TierYaml, _to_rule_config(), RE-03: the 16 default rules (spec 005 §1.2). Concrete `RuleConfig` values, used… (+23 more)

### Community 215 - "classify_http_status"
Cohesion: 0.27
Nodes (12): classify_http_status(), StrEnum, FR-CBK-006: HTTP outcome -> retry decision classification., `FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent failure., RetryDecision, parametrize, FR-CBK-006 HTTP status -> retry decision classification tests., 1xx/3xx aren't expected from Magic's ack, but must classify to something rather… (+4 more)

### Community 216 - "OffsetTracker"
Cohesion: 0.09
Nodes (24): Path, OffsetTracker, Path, Deprecated alias for commit_offset., Persists the current state registry to disk using atomic rename., Registrar subsystem for tracking offsets of log files. Stores file offsets…, Generates internal state ID format (e.g., 'native::16777232-1048201')., Loads state registry into memory Supports Filebeat's native list schema with… (+16 more)

### Community 217 - "fix/normalize.py"
Cohesion: 0.28
Nodes (11): compile_reject_patterns(), match_reject_label(), normalize_reject_text(), Steps 1–2 of FR-PRS-022 (matching input only, not emitted)., Return (label, is_unclassified). On no match returns (None, True) — caller…, RejectPattern, FR-PRS-022 tag 58 normalisation tests., test_FR_PRS_022_cardinality_overflow() (+3 more)

### Community 219 - "publishing/demo_quickstart.py"
Cohesion: 0.43
Nodes (7): _drain(), main(), _make_snapshot(), _print_state(), datetime, Minimal walkthrough of the Backend Publisher (UBS-103/104). uv run python -m…, _step()

### Community 226 - "UBS-117: event publication and integration boundary"
Cohesion: 0.18
Nodes (10): Architecture comparison, Config, Current: implemented UBS-117 baseline, Implemented in this change, Intended to-be: same services, with planned additions, Other work remains separate, Sponsor review baseline (proposed; not yet approved), UBS-117: event publication and integration boundary (+2 more)

### Community 234 - "test_a_logged_reject_burst_reaches_the_backend_alert_store"
Cohesion: 0.08
Nodes (27): connect_reporter_to_publisher(), drop_hook(), heartbeat_provider(), provide(), AbstractContextManager, Any, The publisher's `heartbeat_provider`: a fresh, wire-shaped heartbeat on every…, The publisher's `on_drop`: one item evicted from a full outbox counts towards… (+19 more)

### Community 268 - "FixParser"
Cohesion: 0.10
Nodes (23): demo_log_lines(), Path, Return parsed corpus lines, optionally filtered to one source file label., FixParser, Remove raw tag 58 text from egress (FR-PRS-022)., _strip_sensitive_fields(), ParseError, Closed-set parse failure (FR-PRS-018 subset for framing stage). (+15 more)

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

### Community 273 - ".__init__"
Cohesion: 0.22
Nodes (4): _Clock, datetime, Lock, One wall clock for the aggregator (epoch floats) and the evaluator (datetimes),…

### Community 274 - "test_reporter.py"
Cohesion: 0.61
Nodes (7): make_monitor(), Path, test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 275 - "Rule Engine demo runbook"
Cohesion: 0.15
Nodes (12): 1. `make rules-test`, 2. `make rules-quickstart`, 3. `make rules-reload-demo`, Going deeper, if asked, If someone asks, Pre-flight, Rule Engine demo runbook, make rules-quickstart (17-act demo) (+4 more)

### Community 276 - "Sponsor email — deployment and storage clarifications (Q-13)"
Cohesion: 0.40
Nodes (4): Our current design (for context), Our proposed alignment (pending your confirmation), Questions we'd like your help confirming, Sponsor email — deployment and storage clarifications (Q-13)

### Community 277 - "internal.py"
Cohesion: 0.21
Nodes (11): healthz(), metrics(), get, Response, Operator probes (UBS-96; FR-HLT-010, FR-HLT-012; spec 007 s5.3). Mounted on the…, Liveness only: the process is up and serving. No dependency checks, so a broken…, Readiness incl. warm-up (FR-QRY-005), from the same…, readyz() (+3 more)

### Community 279 - ".__init__"
Cohesion: 0.18
Nodes (9): on_drop(), _on_buffer_drop(), Logger, PublishSink, Protocol, The transport boundary. `HttpsPublishSink` is the Day-1 default (ADR 0003);…, BackendUnreachableCallback, DropCallback (+1 more)

### Community 280 - "Teams bot"
Cohesion: 0.18
Nodes (9): Configuration, Questions to try, Real Teams (later, not tested against a real tenant), Run it locally (5 terminals, all from the repo root), Teams bot, ADR 0009 — Build the Teams bot on the Microsoft 365 Agents SDK, Consequences, Context (+1 more)

### Community 281 - "test_degraded_status_flows_into_heartbeat_payload"
Cohesion: 0.18
Nodes (11): Path, Offset survives a clean shutdown + fresh process, but read-lag knowledge does…, FR-HLT-001: degraded read lag has to survive the actual heartbeat wire format., One file being deleted out from under the agent must not crash the health…, Simulates logrotate: old file renamed away, new file created at the same path., Same inode, smaller size in place - e.g. a logger truncates instead of rotating., test_degraded_status_flows_into_heartbeat_payload(), test_health_reporter_handles_truncation() (+3 more)

### Community 282 - "_wire"
Cohesion: 0.22
Nodes (9): datetime, Each tick is one second later, so pending -> firing happens on tick 2 without…, An order with no ack, its age read off the correlator each tick., _rule(), _run_ticks(), _stepping_clock(), test_the_loop_delivers_a_real_reject_spike_to_both_paths(), test_the_loop_feeds_the_correlator_gauge_to_pending_order_timeout() (+1 more)

### Community 283 - "test_UBS_100_teams_bot_to_backend.py"
Cohesion: 0.40
Nodes (10): _ask(), _backend(), _card(), Activity, Any, FastAPI, UBS-100: the Teams bot against the real backend app (mock LLM), in-process.…, test_alert_question_shows_the_alert_badge_from_real_citations() (+2 more)

### Community 284 - "test_UBS_104_offline_buffering.py"
Cohesion: 0.35
Nodes (9): _config(), _FakeSink, UBS-104: offline buffering and backoff on publish failure. - Real exponential…, test_age_eviction_runs_on_each_publish_tick(), test_backoff_delay_grows_with_consecutive_failures_and_gates_retries(), test_backoff_resets_after_a_successful_commit(), test_buffer_overflow_counts_on_both_the_internal_counter_and_the_hook(), on_drop() (+1 more)

### Community 285 - "publishing/__init__.py"
Cohesion: 0.29
Nodes (6): FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, PendingItem, FR-PUB-004: a pending-item buffer bounded by both total bytes and maximum age,…, PublishOutcome, UBS-103: HTTP response -> publish action classification (spec 007 §2.1's…, enum

### Community 286 - "UBS-100 — Teams bot with Adaptive Card answers (spec)"
Cohesion: 0.20
Nodes (9): As Built, Further Notes, Implementation Decisions, Out of Scope, Problem Statement, Solution, Testing Decisions, UBS-100 — Teams bot with Adaptive Card answers (spec) (+1 more)

### Community 287 - "_error_card_text"
Cohesion: 0.22
Nodes (9): _error_card_text(), test_bad_request_gets_a_rephrase_card(), test_connection_failure_hides_the_exception_text(), test_disabled_nl_gets_a_clear_card(), test_gateway_timeout_gets_the_try_again_card(), test_server_error_says_the_service_is_unreachable_without_internals(), test_timeout_gets_a_try_again_card(), boom() (+1 more)

### Community 288 - "health-reporter-overview.md"
Cohesion: 0.25
Nodes (7): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration

### Community 289 - "_Agent"
Cohesion: 0.22
Nodes (7): _Agent, `for: 0s` still means pending on the first tick and firing on the next (only…, Only Application.log is talking — no FIX at all — and the agent must not page…, The shipped config, wired the way main.build_agent wires it, minus the file…, _signature_alerts(), test_app_log_lines_keep_no_log_activity_quiet_end_to_end(), test_shipped_signature_rules_fire_on_their_own_patterns_only()

### Community 290 - "test_llm_fallback.py"
Cohesion: 0.43
Nodes (6): LLM fallback behaviour (UBS-98)., _service(), test_llm_timeout_returns_clarification(), test_mock_llm_fills_slots_for_unknown_phrasing(), test_mock_llm_missing_mapping_raises_and_clarifies(), _TimeoutLlm

### Community 291 - "api/health.py"
Cohesion: 0.43
Nodes (6): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary()

### Community 292 - "test_callback_event_failure_does_not_break_terminal_delivery_tracking"
Cohesion: 0.29
Nodes (4): CallbackSink, test_callback_event_failure_does_not_break_terminal_delivery_tracking(), test_event_hook_failure_does_not_interrupt_monitor(), fail()

### Community 293 - "text_blocks"
Cohesion: 0.29
Nodes (5): Exchange, Any, What the bot sent to the backend, and the reply it produced., Every TextBlock in a card, depth first., text_blocks()

### Community 294 - "PipelineStats"
Cohesion: 0.33
Nodes (3): PipelineStats, Queue depths and drop counters for heartbeat/metrics (FR-PIP-005)., test_pipeline_stats_expose_prometheus_metric_names()

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **247 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `IntentDefinition`, `_IntentPattern`, `telemetry-simulator` (+242 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1663 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **123 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `Implementation Status live document` to `MetricsAggregator ring buffer`, `Rule Engine`, `snapshot`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `Telemetry System Documentation Index` connect `Telemetry System Documentation Index` to `ADR 0004: Raw log content is never persisted or transmitted`, `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1`, `Telemetry Agent (architecture constraint)`, `ADR 0001: Telemetry Agent written in Go (Superseded)`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `Spec 004: Telemetry data model` connect `Telemetry Agent (architecture constraint)` to `Telemetry System Documentation Index`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 81 INFERRED edges - model-reasoned connections that need verification._