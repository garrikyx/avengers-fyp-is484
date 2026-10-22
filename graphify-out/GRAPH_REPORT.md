# Graph Report - avengers-fyp-is484  (2026-10-22)

## Corpus Check
- 385 files · ~209,442 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: (none) 11, .example 1, .typed 1)

## Summary
- 4896 nodes · 13367 edges · 280 communities (157 shown, 123 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 2391 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `abe73738`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- IngestionService
- frame.py
- ingest.py
- RuleEngine
- make_snapshot
- RuleConfigError
- reporter.py
- test_RE_02_evaluators.py
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
- dataclasses
- make_alert
- MetricStore
- Scaffold and Build Plan
- test_RE_session_integration.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- to_ingestion_heartbeat
- load_agent_config
- test_UBS_104_outage_isolation.py
- build_agent
- DeliveryStatus
- HeartbeatConfig
- test_MA_05_agent_counters.py
- AggregatorConfig
- test_ING_004_008_ingest_guard.py
- test_UBS_113_evaluator.py
- test_MA_03_correlation.py
- test_health_monitor_e2e.py
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
- HealthReporter
- parse_callbacks_config
- test_UBS_35_36_reload_and_draft.py
- telemetry_agent_callbacks_config
- ParseResult
- Histogram
- parse_publish_config
- QueryEngine
- test_STM_02_merge_semantics.py
- LineClassification
- test_UBS_117_event_publication.py
- DryRunCallbackSink
- AlertEvent
- Confidence
- test_queue_depth.py
- RuleEvaluator
- service.py
- test_UBS_116_app_log_counters.py
- fix/parser.py
- pytest
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
- pipeline_demo.py
- HeartbeatMonitor
- datetime
- services/demo_quickstart.py
- sign
- End-to-End Acceptance Scenario (FR-TST-010)
- test_a_logged_reject_burst_reaches_the_backend_alert_store
- test_ING_004_008_routes.py
- query_engine.py
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- buffer.py
- MultiLogMonitor
- telemetry_agent_callbacks_backoff
- Snapshot
- test_STM_04_efficiency.py
- ParsedMessageEvent
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- _snapshot
- test_QRY_03_memory.py
- Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- MetricsQueryRequest
- telemetry_backend/config.py
- backtest.py
- telemetry_agent_metrics_aggregator
- actions/config.py
- telemetry_shared shared schema package
- telemetry_agent/config.py
- health-reporter-overview.md
- _Harness
- test_UBS_115_snapshot_to_metricstore.py
- test_UBS_109_rule_engine_to_backend.py
- QueryTimeRange
- test_readyz_shared_processor.py
- mock_logger.py
- test_UBS_115_snapshot_bridge.py
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- HealthThresholds
- telemetry_agent_parser_applog_signatures
- decimal
- ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server
- ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- telemetry_agent/main.py
- pydantic
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
- demo_reload.py
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
- test_STM_03_warmup.py
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
- test_RE_parse_error_integration.py
- telemetry_shared_metrics
- telemetry_shared_metrics_histogram
- parse_fix_timestamp
- telemetry_agent_common_backoff
- time.py
- Rule Engine demo runbook
- RuleConfig
- test_FR_CBK_013_action_config.py
- test_log_monitor_lifecycle.py
- test_UBS_110_alert_router_callbacks.py
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
- heartbeat_provider
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
- _Clock
- test_reporter.py
- main
- Sponsor email — deployment and storage clarifications (Q-13)
- .fire
- actions/__init__.py
- .seed

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 120 edges
2. `AlertEvent` - 105 edges
3. `create_app()` - 99 edges
4. `HealthReporter` - 89 edges
5. `BackendPublisher` - 85 edges
6. `MetricStore` - 84 edges
7. `StreamProcessorConfig` - 81 edges
8. `SourceMeta` - 80 edges
9. `FixParser` - 73 edges
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
- `4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`` --references--> `AgentHeartbeat`  [INFERRED]
  docs/plan/health-reporter-overview.md → packages/telemetry_shared/src/telemetry_shared/models/health.py

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

## Communities (280 total, 123 thin omitted)

### Community 0 - "IngestionService"
Cohesion: 0.08
Nodes (42): BatchAccepted, IngestionService, IngestionValidationIssue, datetime, Undo an admission reservation when the bounded queue is full., Try to hand off without waiting; False means callers return 503., Keep store work off FastAPI's request path. A single consumer preserves the…, Bound an attacker-controlled key before including it in an error path. (+34 more)

### Community 1 - "frame.py"
Cohesion: 0.08
Nodes (41): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+33 more)

### Community 2 - "ingest.py"
Cohesion: 0.06
Nodes (66): _fixed_now(), main(), Minimal walkthrough of parser/metrics_event.py: the same three-order story as…, _step(), The canonical `session_id` *dimension* value (`FR-MET-030`). Deliberately…, session_id_for(), build_parsed_message_event(), derive_heartbeat_timeout_counters() (+58 more)

### Community 3 - "RuleEngine"
Cohesion: 0.10
Nodes (30): _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _matched_tier(), datetime, Decimal (+22 more)

### Community 4 - "make_snapshot"
Cohesion: 0.17
Nodes (33): Gauges, Instance-wide state, not grouped by dimension — matching spec 004 §3 where…, make_gauges(), make_indicator(), make_indicators(), make_snapshot(), datetime, Decimal (+25 more)

### Community 5 - "RuleConfigError"
Cohesion: 0.12
Nodes (27): _defined_action_names(), load_rules(), load_rules_from_yaml(), Any, Exception, Logger, Path, The parsed top level of a rules file: `rules:` plus, optionally, the `actions:`… (+19 more)

### Community 6 - "reporter.py"
Cohesion: 0.07
Nodes (33): AgentStatus, HealthSignals, is_parse_error(), datetime, Health Reporter: per-file read lag (UBS-30), status rollup and heartbeat…, Per-file read health, keyed by the same name `monitors` was built with., Worst-case lag across files (heartbeat gauge). None if none have read yet., Files whose lag exceeds the threshold. Unread files are never flagged. (+25 more)

### Community 7 - "test_RE_02_evaluators.py"
Cohesion: 0.20
Nodes (23): _read_observed(), make_latency(), _absence_rule(), _latency_rule(), _rate_rule(), RE-02: the per-`RuleKind` evaluators, tested directly against hand-built…, test_absence_evaluator_fires_when_guard_satisfied_and_metric_is_zero(), test_absence_evaluator_guard_unmet_returns_none_not_zero() (+15 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.13
Nodes (17): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, random, FR-CBK-004 exponential backoff with jitter tests., test_FR_CBK_004_delay_doubles_per_attempt_with_factor_2() (+9 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.09
Nodes (19): CorrelatorStats, LatencyCorrelator, OrderContext, Clock, datetime, Decimal, timedelta, MA-03: order correlation and latency. Standalone producer into the shared… (+11 more)

### Community 10 - "derive_counters"
Cohesion: 0.10
Nodes (36): derive_counters(), All four counter families in one event walk., Config-driven raw-reason -> canonical-label mapping. Backs MetricsAggregator's…, Top-N normalised reject reasons by `metric` in `window`, N configurable., ReasonNormalizer, top_reject_reasons(), _banner(), _implementation() (+28 more)

### Community 11 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (22): _aggregator(), _engine(), _fail_n_times(), _publisher(), UBS-75 integration: BackendPublisher -> consecutive_publish_failures gauge ->…, The whole reason this is a gauge: recovery is observable. A windowed failure…, FR-MET-031. An agent with no publisher must not look like an agent that is…, Regression guard on spec 005 §1.2's withdrawn approximation.… (+14 more)

### Community 12 - "AgentHeartbeat"
Cohesion: 0.07
Nodes (33): HeartbeatEmitter, LoggingHeartbeatSink, PrintHeartbeatSink, datetime, Event, Logger, Write one JSON line per heartbeat to stdout (demo)., Build and send one heartbeat. Sink failures are counted, not raised: a dead… (+25 more)

### Community 13 - "LogMonitor"
Cohesion: 0.07
Nodes (25): Harvester, LogMonitor, Path, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, One complete log line with stable byte identity for idempotent ingest., Find retained rotations that were created while the agent was down. This…, Keep a rotated descriptor alive to collect its final writes. (+17 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (24): PublishBuffer, Remove and return up to `max_items` from the front., Put previously-`take`n items back at the front, in original order -- they are…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both…, Drop items older than `max_age_seconds`. The deque is strictly insertion-…, _item(), FR-PUB-004: the byte-and-age-bounded `PublishBuffer` (UBS-104's replacement for…, Drop-oldest still holds after a requeue: the items just put back are the oldest… (+16 more)

### Community 15 - "SourceMeta"
Cohesion: 0.04
Nodes (51): Metadata attached to each log line by the monitor., SourceMeta, QueueSnapshot, PipelineCommitter, Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)., Consumes ParsedEvent objects and commits file offsets after ingest., LinePosition, ProcessedLineDeduper (+43 more)

### Community 16 - "LlmConfig"
Cohesion: 0.07
Nodes (61): ensure_nl_llm_credentials(), LlmConfig, NlConfig, Apply provider-specific defaults after YAML merge., resolve_llm_config(), build_llm_filler(), build_nl_service(), Construct NL services from backend configuration. (+53 more)

### Community 17 - "PublishResult"
Cohesion: 0.08
Nodes (46): classify_publish_response(), PublishAction, PublishOutcome, StrEnum, UBS-103: HTTP response -> publish action classification (spec 007 §2.1's…, PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, _alerts_to_backend_act() (+38 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.11
Nodes (20): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator, Clock, datetime, Decimal (+12 more)

### Community 19 - "dataclasses"
Cohesion: 0.07
Nodes (43): EventStoreConfig, Event store retention (UBS-118; spec 010 `store.recentAlertLimit` default)., In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`)., EventStore, _InstanceEvents, datetime, Lock, In-memory Event Store (UBS-118). (+35 more)

### Community 20 - "make_alert"
Cohesion: 0.10
Nodes (37): MockTransport, callback_action(), command_action(), make_alert(), Path, Shared test support for `telemetry_agent.actions` (UBS-35). Command actions run…, write_script(), Path (+29 more)

### Community 21 - "MetricStore"
Cohesion: 0.08
Nodes (26): _CanonicalBucket, _dim_key(), MetricStore, datetime, DimKey, Lock, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a… (+18 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.08
Nodes (35): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+27 more)

### Community 23 - "test_RE_session_integration.py"
Cohesion: 0.05
Nodes (72): Sessions that have *just* crossed the threshold, each latched so one silence is…, Stop tracking a session. Called on `Logout`, and the reason this exists: a…, Introspection for demos/debug; not used by the detection path., Flags FIX sessions quiet for longer than `timeout_seconds`. Stateful across…, Internal tracking key, identical in format to `SeqTracker.session_key`.…, Record that a session was heard from at `at`. Any message counts, not just…, SessionHeartbeatTracker, _SessionState (+64 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.09
Nodes (35): Agent processing pipeline (monitor to health reporter), health: threshold config block, heartbeat: interval config, publish: Backend Publisher config block, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat() (+27 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "to_ingestion_heartbeat"
Cohesion: 0.17
Nodes (17): Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat(), telemetry_agent_health_heartbeat, make(), UBS-58/66 wire compatibility: our heartbeat flattened to the Ingestion…, The whole point: the Ingestion Service must accept what we send., The ingestion contract has no null for these; the cost is recorded in the notes… (+9 more)

### Community 27 - "load_agent_config"
Cohesion: 0.25
Nodes (22): AgentConfigError, load_agent_config(), Exception, Path, `agent.yaml` is missing or a section is invalid; the message names it., parametrize, Path, UBS-114: `config/agent.yaml` is read once and each section reaches the loader… (+14 more)

### Community 28 - "test_UBS_104_outage_isolation.py"
Cohesion: 0.29
Nodes (7): _HangingSink, _make_alert(), _make_snapshot(), UBS-104 integration test: `NFR-REL-003` -- a backend outage must never affect…, Stands in for a backend that never responds -- e.g. a dropped connection to a…, _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher()

### Community 29 - "build_agent"
Cohesion: 0.05
Nodes (47): AbstractEventLoop, ActionType, StrEnum, AgentConfig, Agent, build_agent(), check_action_secret(), stage_actions() (+39 more)

### Community 30 - "DeliveryStatus"
Cohesion: 0.07
Nodes (40): classify_http_status(), StrEnum, FR-CBK-006: HTTP outcome -> retry decision classification., `FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent failure., RetryDecision, DeliveryRecord, DeliveryStatus, DeliveryTracker (+32 more)

### Community 31 - "HeartbeatConfig"
Cohesion: 0.10
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

### Community 35 - "test_UBS_113_evaluator.py"
Cohesion: 0.15
Nodes (25): _names(), Path, UBS-113: RuleEvaluator — the periodic loop between the metrics store and…, RejectSpike reads 1m, HighRejectRate reads 5m: one tick, both., The tracker latches each silence: many ticks after the timeout still put…, A rules file the loader accepts, from the shipped config's own entries, so the…, _rule(), _Stack (+17 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "test_health_monitor_e2e.py"
Cohesion: 0.10
Nodes (20): fastapi_testclient, committed_offsets(), FakeClock, fix_lines(), datetime, FastAPI, fixture, MonkeyPatch (+12 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.11
Nodes (27): BackendUnreachable rule, CallbackFailing rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule, PendingOrderTimeout rule (+19 more)

### Community 39 - "create_app"
Cohesion: 0.05
Nodes (58): HTTP routers, one file per concern (spec 007). `health.py` (UBS-69) serves the…, _build_parser(), _counts(), create_app(), enqueue_or_full(), get_alert(), get_event(), ingest_batch() (+50 more)

### Community 40 - "EventEmitter"
Cohesion: 0.19
Nodes (8): One session that has just gone quiet for too long. Carries both identifiers on…, SessionTimeout, EventEmitter, Any, datetime, Failure/drop never interrupts metrics, rules or callback delivery., allowed_event_fields(), Event field allowlists shared by producers and backend validation (FR-MET-022).…

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.11
Nodes (26): AckLatencyBreach rule, ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, M1.5 Pipeline bridge (UBS-48/49), MetricsAggregator.snapshot(window, group_by) (+18 more)

### Community 42 - "AgentRegistry"
Cohesion: 0.04
Nodes (55): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary(), AgentRecord, AgentRegistry (+47 more)

### Community 43 - "MetricsIngestor"
Cohesion: 0.10
Nodes (31): MetricsIngestor, The production set: an aggregator that accepts every counter and latency…, `PipelineCommitter(on_event=...)` / `attach_committer(on_event=...)`., _now_sending_time(), MonkeyPatch, Path, test_tailed_fix_lines_reach_the_real_aggregator(), _counters() (+23 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (18): bad(), FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides() (+10 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.13
Nodes (21): Clock, datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, drive() (+13 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.10
Nodes (28): Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), Consistent-Hash Routing on instanceId, 001 — Architecture, Failure Degradation Order (queries → freshness → callbacks → alerting) (+20 more)

### Community 47 - "CamelModel"
Cohesion: 0.09
Nodes (39): AlertsQueryParams, EventsQueryParams, Strict query model for `GET /telemetry/alerts` (`FR-QRY-032`)., Strict query model for `GET /telemetry/events` (`FR-QRY-032`)., RejectedItem, build_intents_response(), CamelModel, BaseModel (+31 more)

### Community 48 - "HealthReporter"
Cohesion: 0.07
Nodes (28): heartbeat_json(), Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, HealthReporter, Clock, Count successfully parsed lines in bulk (denominator only)., Register (or remove) the Publisher's queue-depth callback., Register (or remove) the Publisher's buffer-bytes callback…, Count `n` buffer-eviction drops (`droppedEventsLast5Min`, `FR-PUB-004`) at… (+20 more)

### Community 49 - "parse_callbacks_config"
Cohesion: 0.06
Nodes (39): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+31 more)

### Community 50 - "test_UBS_35_36_reload_and_draft.py"
Cohesion: 0.11
Nodes (28): datetime, Reloads `config/rules.yaml` into a live `RuleEngine`, on SIGHUP or (UBS-35, so…, True when the file's mtime differs from the one last loaded (or last rejected,…, Returns the `resolved` events `apply_rules()` emits for alerts whose rule was…, Standalone use only: this reloads inside the signal handler and drops the…, SighupRuleReloader, UBS-36: a `draft` rule is loaded and fully validated, but the running agent…, RuleState (+20 more)

### Community 52 - "ParseResult"
Cohesion: 0.07
Nodes (55): DemoMetricsSink, Demo metrics sink for parser CLI (mirrors spec 004 counter names)., AppLogParser, Parser plugin for configured application log patterns (Magic format)., compile_signature_rules(), extract_log_level(), First-match-wins signature rules with dynamic label templates., Extract [N/E/W/F/I] level from Magic-style log lines. (+47 more)

### Community 53 - "Histogram"
Cohesion: 0.10
Nodes (25): Histogram, Decimal, Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012). Shared…, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, build_latency_summary(), Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004). Shared by the… (+17 more)

### Community 54 - "parse_publish_config"
Cohesion: 0.11
Nodes (33): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, _PublishYaml, Any, BaseModel (+25 more)

### Community 55 - "QueryEngine"
Cohesion: 0.10
Nodes (22): _AccumulatedGroup, datetime, Decimal, DimKey, timedelta, QueryEngine, QueryValidationError, Validate and resolve the effective UTC window (FR-NLQ-002). (+14 more)

### Community 56 - "test_STM_02_merge_semantics.py"
Cohesion: 0.23
Nodes (15): HistogramPayload, Wire shape of one histogram (`FR-MET-025`/`FR-MET-026`): fixed boundaries…, Reconstruct a mergeable `Histogram`, keyed on the canonical boundary set rather…, _histogram_payload(), FR-STM-002/003/004: counters merge by summation; ratios are recomputed from…, Two agents of unequal volume (FR-STM-003's required test shape): agent A:…, A retried publish that misses batchId-level dedupe (a different ticket's…, _read_one_group() (+7 more)

### Community 57 - "LineClassification"
Cohesion: 0.13
Nodes (24): classify_line(), compile_app_log_patterns(), _looks_like_fix(), Pattern, Line classification (FR-PRS-010, FR-PRS-011)., Classify a log line before parsing (FR-PRS-010). Order: fix → app_log →…, True when 8=FIX/8=FIXT is followed by a delimiter and 35= within the window.…, Compile configured app-log regexes for use after FIX detection fails. (+16 more)

### Community 58 - "test_UBS_117_event_publication.py"
Cohesion: 0.11
Nodes (24): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, CaptureTransport, config(), parametrize (+16 more)

### Community 59 - "DryRunCallbackSink"
Cohesion: 0.22
Nodes (8): DryRunCallbackSink, Logger, `FR-CBK-011`: log the intended delivery, never open a socket. Use this while…, FR-CBK-011 dry-run mode tests., DryRunCallbackSink never imports/constructs an httpx client at all — completing…, test_FR_CBK_011_dry_run_logs_delivery_id_and_body(), test_FR_CBK_011_dry_run_never_opens_a_socket(), test_FR_CBK_011_dry_run_returns_synthetic_success()

### Community 60 - "AlertEvent"
Cohesion: 0.05
Nodes (44): ActionRunner, ActionCatalogue, AsyncBaseTransport, Logger, Swap in a reloaded catalogue. A callback action whose definition is unchanged…, Sync and non-blocking, called from `AlertRouter.route`. Returns how many action…, Drain the queue one run at a time until cancelled., Run one action for one alert and return its outcome. Never raises (except… (+36 more)

### Community 61 - "Confidence"
Cohesion: 0.06
Nodes (31): Confidence, Parser, Enum, Protocol, str, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'. (+23 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.11
Nodes (22): BufferingHeartbeatSink, Bounded retry buffer in front of another sink (UBS-60 demo stand-in). Not the…, Missing downstream / upstream (what this branch cannot prove), HeartbeatSink, FakeQueue, Flaky, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend. (+14 more)

### Community 63 - "RuleEvaluator"
Cohesion: 0.09
Nodes (20): datetime, Event, Signal-safe: only sets a flag. Register it with…, One tick. Returns every alert routed, in routing order., Tick every `interval_seconds` until `stop` is set; the first tick is immediate.…, Cheap (one `stat`), but still rate-limited to `reload_check_seconds`; 0…, UBS-123: runs after aging so retention matches the aggregator., Runs the Rule Engine every `interval_seconds` and routes its alerts. Shared… (+12 more)

### Community 64 - "service.py"
Cohesion: 0.08
Nodes (33): build_default_filters(), default_time_range(), IntentDefinition, Day-1 intent catalogue and slot defaults (FR-NLQ-003, FR-NLQ-004)., merge_interpreted_query(), Compile interpreted NL slots into metrics query requests., Natural language query interpretation (spec 008, UBS-97/98)., catalogue_summary_for_prompt() (+25 more)

### Community 65 - "test_UBS_116_app_log_counters.py"
Cohesion: 0.12
Nodes (25): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MA-02: order / execution / reject counters and reject-reason normalisation.…, fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not OrdStatus —… (+17 more)

### Community 66 - "fix/parser.py"
Cohesion: 0.07
Nodes (52): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+44 more)

### Community 67 - "pytest"
Cohesion: 0.12
Nodes (29): pytest, parse(), app(), meta(), FR-MET-020/021/022/023: bounded events, independently of alert decisions., sent(), Sink, stack() (+21 more)

### Community 68 - "_Demo"
Cohesion: 0.08
Nodes (14): _Demo, Decimal, Holds the one parser/aggregator/engine trio the whole story runs on, so each…, Pretend `by` messages were lost in transit., ExecType/OrdStatus 8 = Rejected, OrdRejReason 3 = ExchangeClosed., 35=3, a session-level Reject — a FIX plumbing problem rather than a trading…, 35=9, a rejected cancel/replace — counted as `cancel_rejects`, kept apart from…, An ack whose SendingTime is `delay_ms` after its order. Latency is measured… (+6 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.12
Nodes (21): Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Magic simulator for development, Do not overengineer (development principle), Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores, Microsoft Teams as the only user interface (+13 more)

### Community 70 - "AppDeps"
Cohesion: 0.11
Nodes (37): healthz(), metrics(), get, Response, Operator probes (UBS-96; FR-HLT-010, FR-HLT-012; spec 007 s5.3). Mounted on the…, Liveness only: the process is up and serving. No dependency checks, so a broken…, Readiness incl. warm-up (FR-QRY-005), from the same…, readyz() (+29 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.10
Nodes (13): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+5 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (20): env(), FakeClock, heartbeat(), post_heartbeat(), datetime, fixture, TestClient, UBS-96: /healthz, /readyz, /metrics on the internal app (FR-HLT-010/012). (+12 more)

### Community 73 - "DropOldestQueue"
Cohesion: 0.18
Nodes (8): DropOldestQueue, T, Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow policy (`FR-…, Enqueue `item`, non-blocking. Returns True if an existing item was dropped to…, FR-CBK-007 bounded queue, drop-oldest overflow tests., test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped(), test_FR_CBK_007_overflow_drops_oldest_and_increments_counter()

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.14
Nodes (16): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), Resource Discipline (§9), Compliance and Operability Constraints (§7), 009 — Non-Functional Requirements and Security, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-REL-003: Backend Outage Must Not Affect Alerting, NFR-SCA-001: Agent Independence/Statelessness (+8 more)

### Community 77 - "StreamProcessorConfig"
Cohesion: 0.13
Nodes (22): StreamProcessorConfig, Read-only configuration shared with the ingestion boundary., datetime, FR-STM-001, FR-ING-005, FR-STM-005: canonical window alignment, rejection of…, FR-ING-005: out-of-order snapshots for the same bucket must still merge to the…, A snapshot the StreamProcessor accepts as within maxBucketAge must still be…, A cap below 1 would drop every series as over-cap while `merge()` still marks…, FR-QRY-003: the shed threshold must be strictly above the warn threshold, or… (+14 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.22
Nodes (18): The active rule set, including any `apply_rules()` hot-swap, so a caller can…, signal, _engine(), _fire(), datetime, LogCaptureFixture, Path, skipif (+10 more)

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

### Community 83 - "pipeline_demo.py"
Cohesion: 0.08
Nodes (34): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), OverflowPolicy, Path, End-to-end demo: LogMonitor → queue → parse → output → commit. (+26 more)

### Community 84 - "HeartbeatMonitor"
Cohesion: 0.14
Nodes (13): AlertingConfig, Backend-owned alerting rules (spec 005 `FR-RUL-030`)., backend_alert_id(), HeartbeatMonitor, datetime, Backend-owned `AgentHeartbeatMissing` rule (`FR-QRY-018`, `FR-RUL-030`)., Resolve a backend alert immediately when a fresh heartbeat arrives., Periodically evaluates agent heartbeat staleness. (+5 more)

### Community 85 - "datetime"
Cohesion: 0.07
Nodes (33): Log monitoring, rotation and truncation handling., datetime, Multi-file polling and lifecycle management for the Log Monitor., Return offset and read-lag state for every configured file., OffsetTracker, Path, Deprecated alias for commit_offset., Persists the current state registry to disk using atomic rename. (+25 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (15): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact…, The exact 3-order story from the Metrics Aggregator quickstart: two accepted… (+7 more)

### Community 87 - "sign"
Cohesion: 0.09
Nodes (22): load_callback_secret(), `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), _burst(), Path, Request, Response (+14 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.12
Nodes (17): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Text Field Normalisation (FR-PRS-022), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025) (+9 more)

### Community 89 - "test_a_logged_reject_burst_reaches_the_backend_alert_store"
Cohesion: 0.10
Nodes (21): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), AsyncBaseTransport, `FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the compressed…, `FR-PUB-001`/`002`: HTTPS POST with a bearer token, gzip above…, Headers, _burst_lines() (+13 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (9): batch(), deps(), FakeClock, metrics(), datetime, UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)., test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() (+1 more)

### Community 91 - "query_engine.py"
Cohesion: 0.08
Nodes (38): QueryConfig, Query engine limits (spec 006 §5, spec 010 `query.*`)., Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, Metrics Query Engine (spec 006 §5, UBS-68/91)., Multi-replica scatter-gather for metrics queries (UBS-92, NFR-SCA-003)., starlette_testclient, HTTP routes for NL query., test_nl_query_disabled_returns_503() (+30 more)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.12
Nodes (20): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009), Configurability NFRs (§5), NFR-CFG-004: Documented Config Defaults Must Match Code (+12 more)

### Community 94 - "buffer.py"
Cohesion: 0.06
Nodes (39): BatchSequencer, build_batch(), datetime, UUID, FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, Create a monotonically increasing `batchSeq` and UUIDv7 `batchId`. The current…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, make_pending_item() (+31 more)

### Community 95 - "MultiLogMonitor"
Cohesion: 0.10
Nodes (20): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+12 more)

### Community 97 - "Snapshot"
Cohesion: 0.07
Nodes (37): align_to_canonical(), datetime, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., Aligns, age-checks, and merges snapshots into a `MetricStore`. Non-blocking and…, FR-QRY-005: `False` ("warming") until `warmupWindow` has elapsed since this…, SnapshotOutcome, StreamProcessor (+29 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (10): _CountingRing, datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in…, The old `tick()` swept every instance's ring on every merge — O(instances x…, A query over one 10s bucket on a 6h-capacity (2160-bucket) ring must not touch…, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to() (+2 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.10
Nodes (33): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent, BaseModel (+25 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.16
Nodes (17): hash_identifier(), load_hash_key(), Identifier hashing (FR-PRS-021)., HMAC-SHA256 of `raw` keyed with `key`, truncated to 16 hex chars., Read the identifier hash key from the environment (NFR-SEC-004). Raises…, hashlib, hmac, FR-PRS-021 identifier hashing tests. (+9 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (13): _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any…, _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved() (+5 more)

### Community 103 - "_snapshot"
Cohesion: 0.15
Nodes (13): A per-instance lock must still serialise writes *within* one instance — safety…, `dropped_after_retention_total` is a single store-wide counter incremented from…, `StreamProcessor.dropped_buckets_total` is incremented outside any per-instance…, _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another(), write_a(), test_concurrent_drops_across_many_instances_are_all_counted(), drop_one() (+5 more)

### Community 104 - "test_QRY_03_memory.py"
Cohesion: 0.17
Nodes (15): datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep…, _snapshot(), test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell() (+7 more)

### Community 105 - "Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)"
Cohesion: 0.12
Nodes (16): datetime, Offset + read lag for this file (UBS-30). See docs/plan/ubs30-notes.md., 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 4.1 Wire contract — `packages/telemetry_shared/models/health.py`, 4.2 Configuration — `health/config.py`, 4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py` (+8 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.16
Nodes (23): _alert(), _publisher(), LogCaptureFixture, Logger, parametrize, UBS-109: AlertRouter — the seam from Rule Engine output to the Backend…, Buffering is not publishing — this follows the alert all the way out through…, The containment that matters: the bad alert is dropped, the good ones are… (+15 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "MetricsQueryRequest"
Cohesion: 0.15
Nodes (15): Exception, QueryTimeoutError, FanoutClient, HttpxFanoutClient, datetime, Protocol, POST metrics queries to peer replicas., Fan out a query to peer replicas and merge bucket-wise. (+7 more)

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.11
Nodes (29): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestionConfig, _IngestYaml (+21 more)

### Community 110 - "backtest.py"
Cohesion: 0.12
Nodes (28): _app_log_time(), backtest(), tick(), BacktestReport, _DiscardRouter, _first_dated_time(), _first_time(), _fix_time() (+20 more)

### Community 111 - "telemetry_agent_metrics_aggregator"
Cohesion: 0.10
Nodes (23): UBS-74: bridges the agent's own since-startup counters into the windowed…, main(), ingest(), Minimal walkthrough of the Metrics Aggregator (MA-01–04). uv run python -m…, _step(), _build_gauges(), datetime, MA-04: calculated indicators and snapshot output. Wraps the already-tested… (+15 more)

### Community 112 - "actions/config.py"
Cohesion: 0.15
Nodes (23): ActionConfigError, ActionDef, _ActionYaml, _command_key(), _is_rooted(), load_action_catalogue(), _parse_action(), parse_actions() (+15 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "telemetry_agent/config.py"
Cohesion: 0.23
Nodes (12): _ActionsYaml, LogsConfig, _LogsYaml, ParsingConfig, _ParsingYaml, _PipelineYaml, Any, BaseModel (+4 more)

### Community 115 - "health-reporter-overview.md"
Cohesion: 0.13
Nodes (15): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library (+7 more)

### Community 116 - "_Harness"
Cohesion: 0.16
Nodes (8): _Harness, _orders(), Decimal, parametrize, At t=1200 only [1150,1200) is fully retained; 1000-1140 are skipped., Real aggregator (1s buckets, 60s retention) and publisher behind the emitter., _starts(), TestSnapshotEmitter

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.20
Nodes (21): _aggregator(), _drain_backend(), _evaluator(), _ingest_app_log_lines(), _ingest_three_orders(), _publish_and_drain(), _publisher(), Decimal (+13 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.12
Nodes (34): _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _order(), _publish_and_drain(), _publisher(), UBS-109 integration: raw FIX bytes -> FixParser -> MetricsAggregator ->… (+26 more)

### Community 119 - "QueryTimeRange"
Cohesion: 0.23
Nodes (16): to_metrics_query(), _clamp_time_range(), InterpretedValidationError, datetime, Exception, Validate interpreted queries against metrics API rules (FR-NLQ-002, FR-NLQ-008)., _schema_issues(), validate_interpreted_query() (+8 more)

### Community 120 - "test_readyz_shared_processor.py"
Cohesion: 0.16
Nodes (16): gzip, _batch_with_snapshot(), datetime, TestClient, FR-QRY-005: `/readyz` probes the same StreamProcessor that ingestion feeds.…, test_create_app_probes_the_supplied_services_own_processor(), test_create_app_rejects_a_processor_the_service_does_not_feed(), test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store() (+8 more)

### Community 121 - "mock_logger.py"
Cohesion: 0.20
Nodes (13): main(), generate_application_log(), get_timestamps(), Path, Generate one sponsor-format line for ``Application.log``. Main, client and…, Rotate with numbered retained archives, like ``logrotate``.…, rotate_if_needed(), run_harness() (+5 more)

### Community 122 - "test_UBS_115_snapshot_bridge.py"
Cohesion: 0.18
Nodes (15): build_snapshot(), Rename each internal dim to its wire name and drop anything not allowlisted…, One `Snapshot` for the closed interval `[bucket_start, bucket_start +…, _to_payload(), _to_wire_dimensions(), _aggregator(), _app_log_aggregator(), UBS-115: `snapshot_bridge.build_snapshot` unit tests. `build_snapshot` is the… (+7 more)

### Community 123 - "Implementation Status live document"
Cohesion: 0.31
Nodes (9): Implementation Status live document, M1 Log monitor and configuration (not started), M2 FIX parser (UBS-40-47), M3 Metrics aggregation (MA-01-04), Backend Metric Store and cross-agent merge, Ratios are recomputed, never averaged, Backend Stream Processor (UBS-88), Known rough edges (+1 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "HealthThresholds"
Cohesion: 0.27
Nodes (11): HealthThresholds, FR-HLT-002 thresholds. Only the read-lag one has a producer on UBS-58; the rest…, _file(), FR-HLT-002/003: status rollup and reasons, using the signals UBS-58 has. Builds…, FR-HLT-004: a file with no reads yet is a gap, not a zero and not a fault., test_every_lagging_file_gets_its_own_reason(), test_legacy_degraded_threshold_kwarg_still_wins(), test_no_signals_is_healthy_with_no_reasons() (+3 more)

### Community 127 - "decimal"
Cohesion: 0.30
Nodes (15): decimal, hand_labelled_events(), Shared test support for the metrics package: a hand-labelled synthetic FIX-…, _ingest_all(), _shared_config(), test_gauges_are_empty_without_a_correlator(), test_gauges_reflect_pending_orders_and_event_staleness(), test_grouped_breakdown_by_symbol() (+7 more)

### Community 128 - "ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server"
Cohesion: 0.17
Nodes (11): nl_query(), ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server, Consequences, Context, Decision, Rationale, Problem P-4: No way to ask questions of live telemetry, NL Adapter (component) (+3 more)

### Community 129 - "ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell"
Cohesion: 0.33
Nodes (6): ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell, Consequences, Context, Decision, Rationale, callback()

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "telemetry_agent/main.py"
Cohesion: 0.05
Nodes (68): datetime, UBS-35: runs a rule's actions when its alert fires (spec 005 §5). `AlertRouter`…, _utc_now(), UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, FR-CBK-007: bounded pending queue, drop-oldest on overflow., Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, FR-CBK-001/011: the swappable Callback transport boundary (spec 005 §3).…, CounterRegistry (+60 more)

### Community 133 - "pydantic"
Cohesion: 0.21
Nodes (9): build(), DataCompleteness, datetime, `dataCompleteness` block for query responses (spec 006 s4.1, FR-QRY-015).…, Derive completeness from the registry at `at`. `expected_agent_ids` is the set…, Alert query response models (spec 007 §4, `FR-QRY-016`)., Shared Pydantic base for telemetry_shared wire-format models. camelCase on the…, pydantic (+1 more)

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 138 - "test_UBS_36_backtest.py"
Cohesion: 0.21
Nodes (21): Telemetry Agent — lightweight sidecar for Magic instances., CaptureFixture, _fix_log(), _nothing_may_be_dispatched(), fixture, MonkeyPatch, Path, UBS-36: test mode replays log files through one rule and reports whether, when… (+13 more)

### Community 143 - "test_UBS_122_signature_rules.py"
Cohesion: 0.21
Nodes (16): _Stack, _load(), Path, UBS-122: signature rules count only their own pattern, and app-log lines keep…, The bug this closes: the instance-level snapshot sums every signature, so ten…, The extra grouped snapshot must not hide ordinary rules on the same window from…, _seed_signature(), _summary() (+8 more)

### Community 145 - "demo_reload.py"
Cohesion: 0.09
Nodes (28): FR-CBK-005: request signing so Magic can verify a callback originated from this…, _alert_storm_act(), _backend_unreachable_act(), attempt(), _dedup_act(), _heartbeat_timeout_act(), main(), _no_log_activity_act() (+20 more)

### Community 157 - "test_STM_03_warmup.py"
Cohesion: 0.33
Nodes (9): datetime, FR-STM-006: an agent's post-restart cold-start state is preserved through the…, warmingUp flags incomplete data for the caller to exclude; it does not mean the…, _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up(), test_data_from_a_restarted_bucket_is_still_merged_not_dropped(), test_restarted_bucket_count_reflects_only_buckets_a_restart_touched() (+1 more)

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 195 - "test_RE_callback_integration.py"
Cohesion: 0.24
Nodes (15): _aggregator(), _alert(), _dispatch(), _drain(), _fire(), UBS-74 integration: CallbackDispatcher -> CounterRegistry ->…, The registry is monotonic, so re-ingesting its absolute value on every tick…, `secondsSinceLastEvent` must stay untouched by the agent's own counters —… (+7 more)

### Community 201 - "AlertStore"
Cohesion: 0.08
Nodes (38): AlertStoreConfig, Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)., AlertStore, _InstanceAlerts, _is_active_status(), datetime, Lock, Merge one alert update (`FR-QRY-016`, `FR-QRY-017`). (+30 more)

### Community 207 - "test_RE_parse_error_integration.py"
Cohesion: 0.31
Nodes (12): _fire(), _ingest(), _rate(), UBS-18 integration: raw log bytes -> FixParser -> derive_parser_counters ->…, Needs a failure mode that errors once per line — see `_NO_MSG_TYPE`. The…, Documents the asymptote above as behaviour, not accident: three of every four…, `min_samples` is 20 for this rule. Under that, a single bad line in a handful…, test_a_clean_log_never_fires() (+4 more)

### Community 210 - "parse_fix_timestamp"
Cohesion: 0.27
Nodes (9): parse_fix_timestamp(), datetime, timedelta, Parse FIX SendingTime/TransactTime as UTC., TimestampResult, FR-PRS-025/026 timestamp tests., test_FR_PRS_025_bad_timestamp_falls_back_to_log(), test_FR_PRS_025_parses_fix_timestamp_utc() (+1 more)

### Community 212 - "time.py"
Cohesion: 0.27
Nodes (14): _local_midnight(), _parse_relative_duration(), _parse_short_datetime(), parse_time_expression(), datetime, timedelta, Time expression parsing for NL queries (FR-NLQ-011–014)., _relative_from_amount() (+6 more)

### Community 213 - "Rule Engine demo runbook"
Cohesion: 0.10
Nodes (23): NoLogActivity rule, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Dependent suppression (FR-RUL-021), Rule Engine, Safety and suppression (silences, grace, storm cap), SighupRuleReloader (+15 more)

### Community 214 - "RuleConfig"
Cohesion: 0.08
Nodes (39): How long to keep ticking after the last line, so a condition that was true at…, _tail_seconds(), _parse_duration_seconds(), BaseModel, field_validator, model_validator, RE-05: `config/rules.yaml` loading and live reload (`FR-RUL-008`/`009`).…, _RuleYaml (+31 more)

### Community 215 - "test_FR_CBK_013_action_config.py"
Cohesion: 0.37
Nodes (12): _agent_yaml(), Path, FR-CBK-013/014/015: the `actions:` block, `rules[].actions` and…, _rules_file(), test_a_command_must_be_on_the_operators_allowlist(), test_a_rule_names_its_actions(), test_agent_config_carries_the_allowlist_and_catalogue(), test_agent_config_refuses_to_start_on_an_unlisted_command() (+4 more)

### Community 216 - "test_log_monitor_lifecycle.py"
Cohesion: 0.27
Nodes (12): _line_texts(), Path, A long-running stream must checkpoint before it reaches EOF., A late write to the renamed file is read during the drain window., A restart backfills retained archives before reading the new active log., A restart recovers every retained archive, oldest archive first., test_checkpoints_offsets_while_file_is_still_busy(), test_does_not_emit_an_unterminated_line_until_it_is_complete() (+4 more)

### Community 217 - "test_UBS_110_alert_router_callbacks.py"
Cohesion: 0.32
Nodes (11): _dispatcher(), _NullCallbackSink, _pending(), UBS-110: AlertRouter fans each alert out to the Callback Dispatcher as well as…, The guard protects the batch; a callback has no batch to poison., _router(), test_a_failing_dispatcher_does_not_cost_the_backend_its_alert(), boom() (+3 more)

### Community 219 - "publishing/demo_quickstart.py"
Cohesion: 0.26
Nodes (9): _drain(), main(), _make_snapshot(), _print_state(), datetime, Minimal walkthrough of the Backend Publisher (UBS-103/104). uv run python -m…, Stands in for the backend: returns responses from a fixed script, one per call,…, _ScriptedSink (+1 more)

### Community 226 - "UBS-117: event publication and integration boundary"
Cohesion: 0.18
Nodes (10): Architecture comparison, Config, Current: implemented UBS-117 baseline, Implemented in this change, Intended to-be: same services, with planned additions, Other work remains separate, Sponsor review baseline (proposed; not yet approved), UBS-117: event publication and integration boundary (+2 more)

### Community 234 - "heartbeat_provider"
Cohesion: 0.09
Nodes (23): drop_hook(), on_drop(), heartbeat_provider(), provide(), AbstractContextManager, Any, The publisher's `heartbeat_provider`: a fresh, wire-shaped heartbeat on every…, The publisher's `on_drop`: one item evicted from a full outbox counts towards… (+15 more)

### Community 268 - "FixParser"
Cohesion: 0.11
Nodes (21): demo_log_lines(), Path, Return parsed corpus lines, optionally filtered to one source file label., FixParser, ParseError, Closed-set parse failure (FR-PRS-018 subset for framing stage)., The parsers a replay uses; built from agent config by the CLI., ReplayParsers (+13 more)

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

### Community 275 - "main"
Cohesion: 0.40
Nodes (5): _build_parser(), main(), ArgumentParser, _test_rule(), Namespace

### Community 276 - "Sponsor email — deployment and storage clarifications (Q-13)"
Cohesion: 0.40
Nodes (4): Our current design (for context), Our proposed alignment (pending your confirmation), Questions we'd like your help confirming, Sponsor email — deployment and storage clarifications (Q-13)

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **214 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `IntentDefinition`, `_IntentPattern`, `telemetry-simulator` (+209 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1584 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **123 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `MetricsAggregator ring buffer` to `config/rules.yaml live rule set`, `Rule Engine demo runbook`, `AgentHeartbeat wire contract`, `Implementation Status live document`, `decimal`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `AlertEvent` connect `AlertEvent` to `IngestionService`, `RuleEngine`, `telemetry_agent/main.py`, `make_snapshot`, `test_RE_publish_integration.py`, `test_UBS_122_signature_rules.py`, `demo_reload.py`, `dataclasses`, `make_alert`, `.fire`, `test_RE_session_integration.py`, `test_UBS_104_outage_isolation.py`, `build_agent`, `test_UBS_113_evaluator.py`, `create_app`, `EventEmitter`, `MetricsIngestor`, `CamelModel`, `parse_callbacks_config`, `test_UBS_35_36_reload_and_draft.py`, `test_UBS_117_event_publication.py`, `RuleEvaluator`, `test_RE_callback_integration.py`, `_Demo`, `AlertStore`, `test_RE_06_reload.py`, `test_RE_parse_error_integration.py`, `HeartbeatMonitor`, `test_UBS_110_alert_router_callbacks.py`, `buffer.py`, `test_UBS_109_alert_router.py`, `backtest.py`, `test_UBS_109_rule_engine_to_backend.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `MetricsAggregator` connect `MetricsAggregator` to `ingest.py`, `telemetry_agent/main.py`, `LatencyCorrelator`, `derive_counters`, `test_RE_publish_integration.py`, `test_RE_session_integration.py`, `test_MA_05_agent_counters.py`, `AggregatorConfig`, `test_UBS_113_evaluator.py`, `test_MA_03_correlation.py`, `MetricsIngestor`, `test_UBS_35_36_reload_and_draft.py`, `Histogram`, `RuleEvaluator`, `test_UBS_116_app_log_counters.py`, `test_RE_callback_integration.py`, `_Demo`, `test_RE_parse_error_integration.py`, `services/demo_quickstart.py`, `ParsedMessageEvent`, `telemetry_agent_metrics_aggregator`, `_Harness`, `test_UBS_115_snapshot_to_metricstore.py`, `test_UBS_109_rule_engine_to_backend.py`, `test_UBS_115_snapshot_bridge.py`, `decimal`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 81 INFERRED edges - model-reasoned connections that need verification._