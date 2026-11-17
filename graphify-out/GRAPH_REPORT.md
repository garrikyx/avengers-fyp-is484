# Graph Report - avengers-fyp-is484  (2026-11-17)

## Corpus Check
- 448 files · ~236,774 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 11, .toml 1, .example 1)

## Summary
- 5697 nodes · 16902 edges · 247 communities (179 shown, 68 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 3504 edges (avg confidence: 0.92)
- Token cost: 647,061 input · 0 output

## Graph Freshness
- Built from commit: `66118ee2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- asyncio
- FixParser
- test_metrics_event.py
- RuleConfig
- make_snapshot
- test_FR_CBK_013_action_config.py
- HealthReporter
- CamelModel
- RetryPolicy
- LatencyCorrelator
- derive_counters
- telemetry_backend/config.py
- AgentHeartbeat
- LogMonitor
- PublishBuffer
- parser/protocol.py
- LlmConfig
- .derive_status
- MetricsAggregator
- EventStore
- make_alert
- MetricStore
- Scaffold and Build Plan
- test_RE_session_integration.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- test_bot_replies.py
- pipeline_demo.py
- agent.yaml
- create_app
- DeliveryTracker
- HeartbeatConfig
- test_MA_05_agent_counters.py
- make_snapshot
- test_ING_004_008_ingest_guard.py
- test_UBS_113_evaluator.py
- test_MA_03_correlation.py
- test_no_lines_are_lost_across_a_simulator_rotation
- config/rules.yaml live rule set
- CamelModel
- service.py
- Implementation Status live document
- rules
- test_UBS_112_metrics_ingestor.py
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- HeartbeatMonitor
- IngestionService
- telemetry_backend_nl_catalogue
- test_UBS_35_36_reload_and_draft.py
- test_UBS_36_backtest.py
- cli.py
- Confidence
- parse_publish_config
- QueryEngine
- Histogram
- StreamProcessorConfig
- test_nl_eval_fixtures.py
- test_FR_PRS_021_identifiers.py
- AlertEvent
- test_RE_publish_integration.py
- test_queue_depth.py
- RuleEvaluator
- test_reply_guard.py
- test_UBS_116_app_log_counters.py
- HttpsCallbackSink
- pytest
- _Demo
- Telemetry Backend (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- CallbackDispatcher
- test_agent_registry.py
- OffsetTracker
- 009 — Non-Functional Requirements and Security
- callbacks
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- test_UBS_36_backtest_cli.py
- test_QRY_03_memory.py
- RuleEvaluator
- publish
- services/demo_quickstart.py
- AlertStore
- End-to-End Acceptance Scenario (FR-TST-010)
- httpx
- test_RE_callback_integration.py
- _Stack
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- llm
- datetime
- hooks
- StreamProcessor
- test_STM_04_efficiency.py
- parsed_message.py
- parsing
- enrich.py
- test_RE_01_fsm.py
- threading
- sign
- Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- cards.py
- MetricsAggregator ring buffer
- backtest.py
- api/health.py
- manifest.json
- telemetry_shared shared schema package
- parse_callbacks_config
- test_tools.py
- query_engine.py
- test_UBS_115_snapshot_to_metricstore.py
- test_UBS_109_rule_engine_to_backend.py
- test_UBS_27_reject_reason_trends.py
- test_readyz_shared_processor.py
- AgentRegistry
- snapshot_bridge.py
- bot.py
- demo_config.yaml (Magic parsing demo config)
- services/self_metrics.py
- telemetry_backend_nl_compiler
- test_backend_self_metrics.py
- ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server
- Spec 005 — Rule Engine, Alerting and Callbacks
- teams/fixtures.py
- Monitor to parser bridge (bounded line queue + parser worker pool)
- test_UBS_123_snapshot_emitter.py
- healthcheck
- telemetry-shared
- AgentRegistry
- .markdownlint-cli2.yaml
- test_UBS_113_evaluation_loop.py
- _Stack
- Auditability & Compliance rationale (deterministic order audit trails)
- _load
- PublishResult
- ADR 0002: Backend in Python/FastAPI
- ADR 0003: HTTPS/JSON Transport Day-1
- ADR 0005: In-Memory Metric Store
- ADR 0006: Agent in Python
- Parser Test Obligations (§10)
- Message Validation and Parse Error Reason Codes (FR-PRS-017–019)
- Data Completeness Block (FR-QRY-015)
- Backend Health and Self-Metrics (FR-HLT-010)
- metrics/__init__.py
- .__init__
- _run_scenario
- test_data_completeness.py
- test_the_agent_process_alerts_magic_and_the_backend
- teams_agent/main.py
- ack_latency_ms
- 000 — Overview, Scope and Conventions
- Problem P-3: Reactive troubleshooting via manual log inspection
- Telemetry System (streaming-first, no raw log storage)
- Latency Measurement via ClOrdID Correlation (FR-MET-010–013)
- Metrics Aggregator Agent-Level Contract (FR-MET-001–004)
- Agent Process Model (asyncio per file + bounded queues)
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
- Runbook: Agent Heartbeat Missing
- Runbook: Callback Failures
- Runbook: High Reject Rate
- Runbook: No Log Activity
- Test Levels (§1)
- Internal Contract Schema Evolution (no version negotiation, Pydantic extra=forbid)
- test_heartbeat_provider_output_is_accepted_in_a_batch
- test_latency_phrase.py
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- render_answer
- RecordingTransport
- FakeClock
- telemetry_backend_nl_intents
- time.py
- baseline.py
- config_loader.py
- classify_http_status
- UBS-117: event publication and integration boundary
- telemetry_agent/main.py
- test_UBS_25_29_anomaly.py
- Project instructions
- Metrics Query API (UBS-68, UBS-91, UBS-92)
- _Clock
- Rule Engine
- BackendPublisher
- Teams bot
- Agent
- test_llm_fallback.py
- OllamaSlotFiller
- load_agent_config
- UBS-100 — Teams bot with Adaptive Card answers (spec)
- telemetry_backend/config.py
- health-reporter-overview.md
- NlQueryContext
- QueryTimeRange
- ActionRunner
- text_blocks
- PipelineStats
- build.sh
- RuleConfigError
- sign
- HttpsCallbackSink
- telemetry_agent/config.py
- MetricsQueryResponse
- NL query manual test plan: Ollama, Teams and Copilot (MCP)

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 121 edges
2. `AlertEvent` - 117 edges
3. `create_app()` - 106 edges
4. `HealthReporter` - 90 edges
5. `MetricStore` - 88 edges
6. `BackendPublisher` - 86 edges
7. `StreamProcessorConfig` - 86 edges
8. `SourceMeta` - 84 edges
9. `CamelModel` - 79 edges
10. `FixParser` - 75 edges

## Surprising Connections (you probably didn't know these)
- `BufferingHeartbeatSink` --semantically_similar_to--> `publish`  [INFERRED] [semantically similar]
  docs/plan/health-reporter-overview.md → config/agent.yaml
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

## Communities (247 total, 68 thin omitted)

### Community 0 - "asyncio"
Cohesion: 0.19
Nodes (20): EventsRequest, TelemetryBatch, SeriesEntry, Snapshot, _batch(), _endpoint(), _event(), _request() (+12 more)

### Community 1 - "FixParser"
Cohesion: 0.06
Nodes (40): demo_log_lines(), _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message() (+32 more)

### Community 2 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (28): build_parsed_message_event(), _meta(), _parse(), _parser_counters(), _session_counters(), test_a_clean_fix_line_is_not_a_parse_error(), test_clean_line_reports_no_reason(), test_every_derived_session_counter_is_declared_in_counter_dimensions() (+20 more)

### Community 3 - "RuleConfig"
Cohesion: 0.09
Nodes (27): validate_anomaly_rule(), _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _metric_context(), _read_absence() (+19 more)

### Community 4 - "make_snapshot"
Cohesion: 0.10
Nodes (49): ValueSource, make_gauges(), make_indicator(), make_indicators(), make_latency(), make_snapshot(), _absence_rule(), _gauge_rule() (+41 more)

### Community 5 - "test_FR_CBK_013_action_config.py"
Cohesion: 0.30
Nodes (11): _agent_yaml(), _rules_file(), test_a_command_must_be_on_the_operators_allowlist(), test_a_rule_names_its_actions(), test_agent_config_carries_the_allowlist_and_catalogue(), test_agent_config_refuses_to_start_on_an_unlisted_command(), test_an_unknown_action_name_fails_the_load(), test_command_and_callback_actions_parse_with_safe_defaults() (+3 more)

### Community 6 - "HealthReporter"
Cohesion: 0.07
Nodes (24): HealthReporter, _utc_now(), 3. UBS-30 — read lag (the foundation), Module map (`apps/agent/src/telemetry_agent/health/`), FileReadHealth, test_degraded_status_flows_into_heartbeat_payload(), test_multi_file_group_tolerates_one_file_disappearing(), test_multi_file_health_reflects_real_tailing() (+16 more)

### Community 7 - "CamelModel"
Cohesion: 0.13
Nodes (11): AppLogParser, AppLogTelemetry, ReplayParsers, _meta(), test_applog_parser_classifies_and_parses_magic_line(), test_applog_parser_returns_none_confidence_for_fix_line(), _ingested(), _meta() (+3 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.07
Nodes (24): RetryPolicy, main(), format_fix_line(), generate_application_log(), generate_fix_order_messages(), get_timestamps(), rotate_if_needed(), run_harness() (+16 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.05
Nodes (35): CorrelatorStats, LatencyCorrelator, OrderContext, _timedelta_to_ms(), main(), _step(), _build_gauges(), snapshot() (+27 more)

### Community 10 - "derive_counters"
Cohesion: 0.09
Nodes (35): derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), ReasonNormalizer, top_reject_reasons(), _banner(), _implementation(), _line() (+27 more)

### Community 11 - "telemetry_backend/config.py"
Cohesion: 0.21
Nodes (15): _aggregator(), _engine(), _fail_n_times(), _publisher(), _rule(), _ScriptedSink, _snapshot_payload(), test_a_full_minute_of_outage_yields_exactly_five_failures() (+7 more)

### Community 12 - "AgentHeartbeat"
Cohesion: 0.07
Nodes (22): HeartbeatEmitter, LoggingHeartbeatSink, PrintHeartbeatSink, 4.1 Wire contract — `packages/telemetry_shared/models/health.py`, 4.4 Emitter and sinks — `health/heartbeat.py`, 4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`, 4. UBS-58 — the heartbeat, AgentHeartbeat (+14 more)

### Community 13 - "LogMonitor"
Cohesion: 0.06
Nodes (16): Harvester, LogMonitor, _open_shared(), test_health_reporter_handles_truncation(), test_health_reporter_survives_log_rotation(), test_offset_persists_across_simulated_restart(), test_agent_heartbeat_reaches_the_health_endpoint(), test_heartbeat_carries_file_state_and_lag() (+8 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.14
Nodes (17): PendingItem, PublishBuffer, _item(), _tags(), test_an_item_larger_than_the_whole_cap_is_not_self_evicted(), test_append_and_take_preserve_fifo_order(), test_byte_overflow_drops_oldest_and_counts(), on_drop() (+9 more)

### Community 15 - "parser/protocol.py"
Cohesion: 0.05
Nodes (24): FixTelemetry, ParseResult, SourceMeta, QueueSnapshot, PipelineCommitter, LinePosition, ProcessedLineDeduper, EventQueue (+16 more)

### Community 16 - "LlmConfig"
Cohesion: 0.10
Nodes (19): LlmConfig, resolve_llm_config(), _JsonModeRejected, OpenAiCompatibleSlotFiller, config(), test_factory_vllm_uses_compat_client(), test_resolve_azure_default_timeout(), test_resolve_ollama_default_base_url() (+11 more)

### Community 17 - ".derive_status"
Cohesion: 0.10
Nodes (17): HealthSignals, is_parse_error(), 4.3 Rollup and payload — `health/reporter.py`, Also touched, and why, Design points, How to see it, Placeholder receiver — `scripts/heartbeat_receiver_stub.py`, Ticket vs. spec decisions (read first — these need team sign-off) (+9 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.05
Nodes (36): AggregatorConfig, _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator, _fire(), _ingest() (+28 more)

### Community 19 - "EventStore"
Cohesion: 0.12
Nodes (14): EventStoreConfig, EventStore, _InstanceEvents, TelemetryEvent, make_telemetry_event(), _drain_one(), test_process_events_appends_to_event_store(), test_run_drains_events_from_queue() (+6 more)

### Community 20 - "make_alert"
Cohesion: 0.14
Nodes (23): callback_action(), command_action(), make_alert(), write_script(), _runner(), test_a_command_that_overruns_its_timeout_is_killed(), test_a_missing_executable_is_an_error_not_a_crash(), test_a_non_zero_exit_is_counted_as_failed() (+15 more)

### Community 21 - "MetricStore"
Cohesion: 0.11
Nodes (4): _CanonicalBucket, MetricStore, test_existing_instance_does_not_raise_on_a_half_created_instance(), test_shed_oldest_tier_does_not_raise_on_a_half_created_instance()

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.06
Nodes (37): Open Questions and Decisions Required, Callback Dispatcher, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent, Q-2 — Callback Protocol Magic Will Support (+29 more)

### Community 23 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (22): _key(), _keys(), _observe(), test_a_clean_logout_never_times_out(), test_a_session_relogging_on_after_logout_is_tracked_again(), test_a_session_still_speaking_never_times_out(), test_a_session_that_recovers_can_time_out_again(), test_both_directions_share_one_dimension_id() (+14 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (24): health: threshold config block, heartbeat, interval, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup (+16 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (28): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+20 more)

### Community 26 - "test_bot_replies.py"
Cohesion: 0.21
Nodes (36): answer(), clarification(), converse(), group(), json_ok(), message(), texts(), test_a_half_hour_offset_is_labelled_with_its_minutes() (+28 more)

### Community 27 - "pipeline_demo.py"
Cohesion: 0.05
Nodes (41): print_header(), run_demo(), setup_environment(), _build_bridge(), _build_registry(), _load_config(), main(), _print_stage() (+33 more)

### Community 28 - "agent.yaml"
Cohesion: 0.06
Nodes (30): actions, allowedCommands, agent, id, instanceIds, version, label, match (+22 more)

### Community 29 - "create_app"
Cohesion: 0.06
Nodes (33): BatchAccepted, _build_parser(), _counts(), create_app(), enqueue_or_full(), get_alert(), get_event(), ingest_batch() (+25 more)

### Community 30 - "DeliveryTracker"
Cohesion: 0.09
Nodes (27): alert_delivery_from_record(), enrich_alert_delivery(), DeliveryRecord, DeliveryStatus, DeliveryTracker, notification_key(), test_enrich_alert_delivery_leaves_an_untracked_alert_alone(), test_enrich_alert_delivery_maps_tracker_state() (+19 more)

### Community 31 - "HeartbeatConfig"
Cohesion: 0.10
Nodes (23): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, HealthThresholds, _HealthYaml, HeartbeatConfig, _HeartbeatYaml (+15 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.10
Nodes (26): AgentCounterSampler, _aggregator(), _alert(), _dispatch(), _fire(), _rule(), test_callback_failures_do_not_make_a_log_starved_agent_look_alive(), test_four_permanent_failures_fire_callback_failing() (+18 more)

### Community 33 - "make_snapshot"
Cohesion: 0.11
Nodes (25): _client_with_data(), test_UBS_68_http_query_returns_totals(), test_UBS_68_unknown_field_returns_400(), _nl_service(), _aligned_now(), make_snapshot(), _analyse(), _service() (+17 more)

### Community 34 - "test_ING_004_008_ingest_guard.py"
Cohesion: 0.09
Nodes (20): IngestGuardConfig, Accept, Duplicate, IngestGuard, RateLimited, _utc_now(), FakeClock, guard() (+12 more)

### Community 35 - "test_UBS_113_evaluator.py"
Cohesion: 0.09
Nodes (31): _names(), _rule(), _Stack, test_a_cleared_condition_resolves_on_both_paths(), test_a_counter_rule_fires_and_reaches_both_paths(), test_a_rejected_reload_routes_nothing_and_keeps_the_rules(), test_a_reload_request_waits_for_the_next_tick(), test_a_reload_that_drops_a_firing_rule_routes_its_resolution() (+23 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (22): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), replaced() (+14 more)

### Community 37 - "test_no_lines_are_lost_across_a_simulator_rotation"
Cohesion: 0.38
Nodes (5): committed_offsets(), fix_lines(), test_no_lines_are_lost_across_a_simulator_rotation(), test_simulator_logs_reach_the_backend_health_api(), write_lines()

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.15
Nodes (16): BackendUnreachable rule, CallbackFailing rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule, PendingOrderTimeout rule (+8 more)

### Community 39 - "CamelModel"
Cohesion: 0.06
Nodes (34): AlertsQueryParams, EventsQueryParams, build_intents_response(), AlertCounts, AlertDelivery, AlertDetailResponse, AlertsListResponse, AlertTransition (+26 more)

### Community 40 - "service.py"
Cohesion: 0.09
Nodes (22): build_default_filters(), default_time_range(), IntentDefinition, _merge_group_by(), merge_interpreted_query(), _merge_metrics(), _merge_step(), _extract_filters() (+14 more)

### Community 41 - "Implementation Status live document"
Cohesion: 0.15
Nodes (16): ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, Implementation Status live document, M1.5 Pipeline bridge (UBS-48/49), M1 Log monitor and configuration (not started) (+8 more)

### Community 42 - "rules"
Cohesion: 0.08
Nodes (25): actions, args, command, dryRun, name, timeout, type, rules (+17 more)

### Community 43 - "test_UBS_112_metrics_ingestor.py"
Cohesion: 0.24
Nodes (13): _counters(), _feed(), _ingestor(), _meta(), _reporter(), test_a_failing_component_never_escapes_and_is_counted(), test_a_hard_parse_error_counts_for_aggregator_and_reporter(), test_bad_timestamp_is_a_heartbeat_error_but_not_an_aggregator_one() (+5 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.08
Nodes (26): heartbeat_json(), provide(), to_ingestion_heartbeat(), FakeClock, make(), ok(), test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides() (+18 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.17
Nodes (11): SlidingWindowCounter, at(), test_capacity_is_rounded_not_floored(), test_counts_events_inside_window(), test_decays_as_window_slides(), test_event_older_than_window_is_dropped(), test_idle_window_reads_zero_not_none(), test_late_event_still_inside_window_is_counted() (+3 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.11
Nodes (21): Problem P-1: Limited visibility into live trading activity and health, Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), 001 — Architecture, Ingestion Service (component), Log Monitor (component), Metric Store (component) (+13 more)

### Community 47 - "HeartbeatMonitor"
Cohesion: 0.11
Nodes (9): AlertingConfig, backend_alert_id(), HeartbeatMonitor, Not in this change, Open points for the team, UBS-69 / UBS-85 / UBS-96 — decisions and open points, _heartbeat(), test_FR_QRY_018_fresh_heartbeat_resolves_backend_alert() (+1 more)

### Community 48 - "IngestionService"
Cohesion: 0.10
Nodes (10): IngestionService, IngestionValidationIssue, _safe_key(), allowed_event_fields(), _app_with_store(), _event_payload(), test_UBS_118_batch_ingestion_makes_events_queryable(), test_UBS_118_events_endpoint_round_trip() (+2 more)

### Community 49 - "telemetry_backend_nl_catalogue"
Cohesion: 0.08
Nodes (11): _ScriptedSink, CallbackResult, CallbackSink, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink, _SlowFiringSink, _NullCallbackSink (+3 more)

### Community 50 - "test_UBS_35_36_reload_and_draft.py"
Cohesion: 0.21
Nodes (16): _broken(), _Clock, _engine(), _evaluator(), _NullPublisher, _rules_yaml(), test_a_draft_rule_never_fires_in_the_running_engine(), test_a_good_reload_commits_the_staged_catalogue_after_the_rules() (+8 more)

### Community 51 - "test_UBS_36_backtest.py"
Cohesion: 0.21
Nodes (14): _fix_log(), _nothing_may_be_dispatched(), _rule(), _run(), test_a_date_time_line_prefix_anchors_the_replay(), test_a_draft_rule_is_evaluated_and_reported_as_draft(), test_a_gauge_rule_carries_a_caveat(), test_a_quiet_log_never_fires() (+6 more)

### Community 52 - "cli.py"
Cohesion: 0.08
Nodes (44): DemoMetricsSink, compile_signature_rules(), extract_log_level(), resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule, _corpus_files() (+36 more)

### Community 53 - "Confidence"
Cohesion: 0.10
Nodes (6): Parser, get_parser(), register_parser(), test_FR_PRS_031_validate_chain_reports_unknown_parsers(), test_FR_PRS_032_duplicate_registration_raises(), test_FR_PRS_032_register_parser_at_import_time()

### Community 54 - "parse_publish_config"
Cohesion: 0.12
Nodes (19): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, test_allows_plain_http_when_explicitly_opted_in(), test_buffer_bytes_must_be_positive(), test_defaults_match_spec_010() (+11 more)

### Community 55 - "QueryEngine"
Cohesion: 0.11
Nodes (8): _AccumulatedGroup, QueryEngine, QueryValidationError, MetricsQueryRequest, is_known_metric(), resolve_dimension_name(), resolve_metric_name(), to_api_dimension()

### Community 56 - "Histogram"
Cohesion: 0.18
Nodes (8): Histogram, build_latency_summary(), test_merge_is_bucket_wise_addition(), test_percentile_below_min_sample_size_returns_none(), test_percentile_interpolates_within_the_identified_bucket(), test_percentile_interpolates_within_the_overflow_bucket(), test_record_above_the_largest_boundary_falls_into_overflow(), test_record_places_values_into_the_correct_exclusive_bucket()

### Community 57 - "StreamProcessorConfig"
Cohesion: 0.14
Nodes (12): StreamProcessorConfig, _snapshot(), test_a_stale_direct_merge_is_counted_not_silently_dropped(), test_bucket_older_than_max_bucket_age_is_rejected_and_counted_as_dropped(), test_config_rejects_a_non_positive_max_series_per_bucket(), test_config_rejects_a_non_positive_memory_limit(), test_config_rejects_a_shed_percent_not_above_warn_percent(), test_config_rejects_max_bucket_age_greater_than_retention_window() (+4 more)

### Community 58 - "test_nl_eval_fixtures.py"
Cohesion: 0.12
Nodes (11): _utc_now(), CallbackAlertPayload, from_alert_event(), test_operational_hooks_publish_and_are_queryable(), deliver(), make_alert_event(), test_FR_CBK_001_payload_carries_ac_required_fields(), test_FR_CBK_002_payload_under_max_bytes_for_typical_alert() (+3 more)

### Community 59 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.14
Nodes (17): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), _rule(), test_a_clean_logout_does_not_also_produce_a_timeout(), test_fix_session_down_fires_on_a_heartbeat_timeout_alone() (+9 more)

### Community 60 - "AlertEvent"
Cohesion: 0.07
Nodes (13): main(), _make_alert(), _print_counters(), _run_one(), _step(), CallbackDispatcher, _DiscardRouter, _run_dispatcher_against_a_broken_magic() (+5 more)

### Community 61 - "test_RE_publish_integration.py"
Cohesion: 0.06
Nodes (31): looks_like_magic_binary(), MagicBinaryParser, classify_line(), _looks_like_fix(), Confidence, LineClassification, test_FR_PRS_010_fix_detected_pipe_delimited(), test_FR_PRS_010_fix_detected_soh_delimited() (+23 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.10
Nodes (19): BufferingHeartbeatSink, Missing downstream / upstream (what this branch cannot prove), FakeQueue, Flaky, make(), test_at_critical_watermark_is_unhealthy(), test_at_high_watermark_is_degraded_with_reason_and_trend(), test_below_high_watermark_is_healthy() (+11 more)

### Community 63 - "RuleEvaluator"
Cohesion: 0.06
Nodes (11): CounterRegistry, EventEmitter, SnapshotEmitter, test_callbacks_shim_is_the_same_class(), test_increment_starts_at_zero_and_accumulates(), test_independent_counters_do_not_interfere(), test_snapshot_is_a_copy_not_a_live_view(), _Harness (+3 more)

### Community 64 - "test_reply_guard.py"
Cohesion: 0.07
Nodes (26): catalogue_summary_for_prompt(), normalize_question(), greeting_message(), help_message(), llm_unavailable_message(), out_of_scope_message(), suggested_questions(), thanks_message() (+18 more)

### Community 65 - "test_UBS_116_app_log_counters.py"
Cohesion: 0.18
Nodes (14): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), _ingest_app_log_lines(), _aggregator(), _ingest(), _tel(), test_component_flood_cannot_crowd_out_other_series() (+6 more)

### Community 66 - "HttpsCallbackSink"
Cohesion: 0.06
Nodes (37): build_fix_telemetry(), normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type(), normalize_session_reject_reason() (+29 more)

### Community 67 - "pytest"
Cohesion: 0.19
Nodes (19): _burst(), test_the_agent_process_alerts_magic_and_the_backend(), scenario(), parse(), app(), meta(), sent(), stack() (+11 more)

### Community 68 - "_Demo"
Cohesion: 0.06
Nodes (13): _alert_storm_act(), _dedup_act(), _Demo, main(), _no_log_activity_act(), _part(), _show_alerts(), _step() (+5 more)

### Community 69 - "Telemetry Backend (architecture constraint)"
Cohesion: 0.13
Nodes (9): Magic simulator for development, Unified Telemetry Intelligence (Magic), agent: identity config (id, instanceIds, version), Spec 004: Telemetry data model, Agent self counters (§4.3), Identity fields (§1), Callback dispatch requirements (§3.1), Callback flow (§3.2) (+1 more)

### Community 70 - "AppDeps"
Cohesion: 0.21
Nodes (15): AppDeps, env(), FakeClock, heartbeat(), post(), test_counts_cover_all_four_states(), test_detail_matches_spec_007_5_2(), test_detail_unknown_agent_is_404() (+7 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.09
Nodes (5): BoundedQueue, test_block_policy_waits_for_capacity(), test_drop_oldest_policy_discards_oldest_on_overflow(), test_zero_capacity_rejects_without_storing(), test_full_queue_blocks_producer_without_drops()

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (16): env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), test_decommissioned_agent_leaves_the_exposition(), test_healthz_is_liveness_only(), test_heartbeats_do_not_count_as_data_for_warmup() (+8 more)

### Community 73 - "CallbackDispatcher"
Cohesion: 0.16
Nodes (4): DropOldestQueue, test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped(), test_FR_CBK_007_overflow_drops_oldest_and_increments_counter()

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (12): FakeClock, hb(), make(), test_agent_clock_stepped_backwards_does_not_go_missing(), test_explicit_received_at_overrides_clock(), test_first_contact_is_reported_once(), test_late_older_heartbeat_keeps_newer_doc_but_refreshes_liveness(), test_missing_after_threshold_measured_on_backend_clock() (+4 more)

### Community 75 - "OffsetTracker"
Cohesion: 0.14
Nodes (3): OffsetTracker, test_corrupt_registry_is_reported_without_crashing(), test_valid_registry_does_not_report_reset()

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.14
Nodes (16): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), Resource Discipline (§9), Compliance and Operability Constraints (§7), 009 — Non-Functional Requirements and Security, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-REL-003: Backend Outage Must Not Affect Alerting, NFR-SCA-001: Agent Independence/Statelessness (+8 more)

### Community 77 - "callbacks"
Cohesion: 0.14
Nodes (17): callbacks, allowInsecureCallback, connectTimeout, dryRun, enabled, endpoint, maxAttempts, maxBytes (+9 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.21
Nodes (11): AlertStatus, _engine(), _fire(), _snapshot(), test_apply_rules_force_resolves_a_firing_alert_whose_rule_was_removed(), test_apply_rules_leaves_unrelated_rules_untouched(), test_apply_rules_preserves_state_for_a_rule_whose_name_persists(), test_apply_rules_removes_a_pending_state_without_an_event() (+3 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (15): C++ candidate (rejected: worst-case failure modes), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), .NET alternative (rejected), FastAPI framework, Go for both components alternative (rejected) (+7 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.12
Nodes (17): ADR 0004: No-Raw-Persistence Design, Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Parser Engine Agent-Level Contract (FR-PRS-001–003), Scaffold Document (plan/scaffold.md), 003 — Parser Engine and FIX Parsing (+9 more)

### Community 82 - "test_UBS_36_backtest_cli.py"
Cohesion: 0.57
Nodes (3): _simulate(), test_a_draft_rule_replayed_over_simulator_logs(), _test_rule()

### Community 83 - "test_QRY_03_memory.py"
Cohesion: 0.15
Nodes (9): _snapshot(), test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell(), test_estimated_memory_bytes_grows_with_merged_series_and_shrinks_on_eviction(), test_estimated_memory_bytes_is_zero_for_an_empty_store(), test_merge_alone_can_trigger_shedding_without_an_external_tick(), test_merges_within_the_throttle_interval_do_not_re_check_memory(), test_shedding_never_evicts_a_bucket_written_in_the_same_cycle_at_small_capacity(), test_tick_logs_a_warning_above_memory_warn_percent_but_does_not_shed() (+1 more)

### Community 84 - "RuleEvaluator"
Cohesion: 0.06
Nodes (10): AlertRouter, RuleEvaluator, _utc_now(), anomaly_path_for(), load_rules(), _mtime_or_none(), SighupRuleReloader, _Agent (+2 more)

### Community 85 - "publish"
Cohesion: 0.10
Nodes (19): Agent processing pipeline (monitor to health reporter), publish, allowInsecureEndpoint, bufferBytes, bufferMaxAge, compressThreshold, connectTimeout, dryRun (+11 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (9): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), _reject(), _run_hong_kong_session(), _run_singapore_session() (+1 more)

### Community 87 - "AlertStore"
Cohesion: 0.08
Nodes (31): AlertStoreConfig, AlertStore, _InstanceAlerts, _is_active_status(), _StoredAlert, AlertRecord, test_alert_status_answer_includes_callback_delivery(), test_a_retrying_firing_callback_does_not_share_state_with_resolved() (+23 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.12
Nodes (12): Open Questions Document (plan/open-questions.md), Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025), NFR-SEC-015: Canonicalised Allowed Roots, Symlinks Refused, Security: Input Handling (§3.4), Agent Configuration Schema (§1) (+4 more)

### Community 89 - "httpx"
Cohesion: 0.09
Nodes (15): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), CaptureTransport, test_monitor_parser_events_alerts_and_query_round_trip(), test_runtime_emits_start_and_stop_without_requiring_log_activity(), run(), _publisher() (+7 more)

### Community 90 - "test_RE_callback_integration.py"
Cohesion: 0.16
Nodes (11): _publisher(), _snapshot(), test_503_when_the_backend_queue_is_full(), test_happy_path_against_the_real_backend_app(), batch(), deps(), FakeClock, metrics() (+3 more)

### Community 91 - "_Stack"
Cohesion: 0.11
Nodes (19): _dim_key(), _SeriesContribution, HistogramPayload, _histogram_payload(), _read_one_group(), _snapshot(), test_a_metric_no_contributing_agent_reported_is_absent_not_fabricated(), test_a_metric_only_some_agents_reported_still_merges_the_ones_that_did() (+11 more)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (14): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+6 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.12
Nodes (14): Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), Configurability NFRs (§5), NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test), NFR-SEC-012: Order Identifier Hashing, Rotatable Key (+6 more)

### Community 94 - "llm"
Cohesion: 0.15
Nodes (12): baseUrl, keepAlive, model, numPredict, provider, requireApiKey, structuredOutput, timeout (+4 more)

### Community 95 - "datetime"
Cohesion: 0.07
Nodes (5): ReadLine, FileReadStatus, source_meta_from_read_line(), _PublishYaml, _RetryYaml

### Community 96 - "hooks"
Cohesion: 0.15
Nodes (12): exclude, additional_dependencies, args, entry, id, language, name, types_or (+4 more)

### Community 97 - "StreamProcessor"
Cohesion: 0.12
Nodes (14): align_to_canonical(), SnapshotOutcome, StreamProcessor, Decisions, test_merging_the_same_snapshot_twice_does_not_double_the_counters(), test_alignment_floors_a_phase_shifted_bucket_onto_the_canonical_grid(), test_alignment_is_a_no_op_when_already_on_the_grid(), _snapshot() (+6 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (5): _CountingRing, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to(), test_read_indexes_only_the_requested_span_not_the_whole_ring(), test_restarted_bucket_count_also_indexes_only_the_requested_span()

### Community 99 - "parsed_message.py"
Cohesion: 0.11
Nodes (22): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), test_histogram_payload_requires_the_full_shape_not_a_percentile_summary(), test_parses_the_spec_004_example_verbatim(), test_to_histogram_ignores_unrecognised_bucket_keys_defensively(), test_unknown_dimension_shaped_extra_key_on_a_series_is_rejected() (+14 more)

### Community 100 - "parsing"
Cohesion: 0.17
Nodes (11): appLogPatterns, label, match, parsing, errorSignatures, maxClockSkew, maxDynamicSignatureLabels, maxRejectReasonLabels (+3 more)

### Community 101 - "enrich.py"
Cohesion: 0.10
Nodes (20): extract_allowlisted_fields(), FixFields, _hash_or_none(), hash_identifier(), load_hash_key(), _strip_sensitive_fields(), test_FR_PRS_020_excluded_tags_never_appear_in_output(), test_FR_PRS_020_fixed_struct_has_no_dict_no_map_allocation() (+12 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (11): _engine(), _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved(), test_pending_fires_after_for_elapsed(), test_pending_reverts_to_inactive_if_condition_clears_before_for_elapsed() (+3 more)

### Community 103 - "threading"
Cohesion: 0.19
Nodes (10): _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another(), write_a(), test_concurrent_drops_across_many_instances_are_all_counted(), drop_one(), test_concurrent_merges_into_the_same_instance_do_not_lose_updates(), write(), test_concurrent_stale_rejections_across_many_instances_are_all_counted() (+2 more)

### Community 104 - "sign"
Cohesion: 0.10
Nodes (17): _drain(), main(), _make_snapshot(), _print_state(), _step(), BackendPublisher, _backend_unreachable_act(), attempt() (+9 more)

### Community 105 - "Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)"
Cohesion: 0.09
Nodes (16): 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 5.1 The window — `health/window.py`, 5. UBS-59 — parse error rate, 6. UBS-60 — publish queue depth, 7. Status rollup — the one table, 8. What is still missing (so nobody is surprised) (+8 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.12
Nodes (22): _alert(), _publisher(), _RecordingSink, _router(), test_a_mismatched_alert_is_dropped_before_it_reaches_the_buffer(), test_a_routed_alert_reaches_the_wire_in_the_batch(), test_an_empty_list_is_a_no_op(), test_an_unguarded_mismatch_poisons_the_whole_batch() (+14 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (11): gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups), agent metrics/ module (rolling metrics and aggregation), PostgreSQL (Day-2 historical metrics) (+3 more)

### Community 108 - "cards.py"
Cohesion: 0.16
Nodes (17): _alert_badge(), _ask_again(), _breakdown(), _breakdown_rows(), build_answer_card(), build_clarification_card(), build_error_card(), _card() (+9 more)

### Community 109 - "MetricsAggregator ring buffer"
Cohesion: 0.14
Nodes (16): AckLatencyBreach rule, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent), Histogram (fixed buckets, merge, percentile), LatencyCorrelator (+8 more)

### Community 110 - "backtest.py"
Cohesion: 0.11
Nodes (19): _app_log_time(), backtest(), tick(), BacktestReport, _first_dated_time(), _first_time(), _fix_time(), _iso() (+11 more)

### Community 111 - "api/health.py"
Cohesion: 0.14
Nodes (6): get_agent(), list_agents(), healthz(), metrics(), readyz(), get_deps()

### Community 112 - "manifest.json"
Cohesion: 0.09
Nodes (22): accentColor, bots, description, full, short, developer, name, privacyUrl (+14 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (11): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams), Telemetry Agent (apps/agent) (+3 more)

### Community 114 - "parse_callbacks_config"
Cohesion: 0.08
Nodes (23): ActionConfigError, _ActionYaml, _command_key(), _is_rooted(), load_action_catalogue(), _parse_action(), parse_actions(), parse_allowed_commands() (+15 more)

### Community 115 - "test_tools.py"
Cohesion: 0.06
Nodes (26): _answer_result(), _clarification_result(), _error_kind(), error_result(), _path(), TelemetryBackend, McpServerConfig, _number() (+18 more)

### Community 116 - "query_engine.py"
Cohesion: 0.19
Nodes (9): QueryConfig, QueryTimeoutError, _engine(), _request(), test_UBS_91_max_range_seconds_returns_400(), test_UBS_91_max_series_points_returns_400(), test_UBS_91_query_timeout_returns_error(), _execute_sync() (+1 more)

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.22
Nodes (11): _aggregator(), _drain_backend(), _evaluator(), _ingest_three_orders(), _publish_and_drain(), _publisher(), _read_counters(), test_app_log_metrics_reach_the_metric_store_as_distinct_series() (+3 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.12
Nodes (22): _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _order(), _publish_and_drain(), _publisher(), _reject() (+14 more)

### Community 119 - "test_UBS_27_reject_reason_trends.py"
Cohesion: 0.14
Nodes (9): _bad_window(), _by_reason(), classify(), RejectReasonTrendService, FanoutClient, ReasonTrend, RejectReasonTrendsRequest, RejectReasonTrendsResponse (+1 more)

### Community 120 - "test_readyz_shared_processor.py"
Cohesion: 0.17
Nodes (10): _batch_with_snapshot(), test_create_app_probes_the_supplied_services_own_processor(), test_create_app_rejects_a_processor_the_service_does_not_feed(), test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store(), _wait_for_status(), client(), test_body_limit_is_loaded_from_existing_ingest_config(), test_compressed_events_are_accepted_with_existing_contract() (+2 more)

### Community 121 - "AgentRegistry"
Cohesion: 0.12
Nodes (6): _summary(), AgentRecord, AgentRegistry, _utc_now(), build(), DataCompleteness

### Community 122 - "snapshot_bridge.py"
Cohesion: 0.13
Nodes (9): build_snapshot(), _to_payload(), _to_wire_dimensions(), _aggregator(), test_app_log_dimensions_survive_the_wire_allowlist(), test_build_snapshot_is_pure_and_repeatable(), _build(), test_each_metric_appears_exactly_once_at_its_own_native_dimensions() (+1 more)

### Community 123 - "bot.py"
Cohesion: 0.18
Nodes (12): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Requirement ID Scheme (FR-<AREA>-<NNN>), Health Reporter (component), Health Reporter Heartbeat Requirement (FR-HLT-001), Backend Configuration and Secrets (§9), NFR-SEC-004: Secrets from Environment Only (+4 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.18
Nodes (11): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Blocking CI sentinel test (FR-TST-005) (+3 more)

### Community 125 - "services/self_metrics.py"
Cohesion: 0.13
Nodes (4): _BoundSourcesCollector, _counter(), _gauge(), _utc_now()

### Community 126 - "telemetry_backend_nl_compiler"
Cohesion: 0.16
Nodes (4): DryRunCallbackSink, test_FR_CBK_011_dry_run_logs_delivery_id_and_body(), test_FR_CBK_011_dry_run_never_opens_a_socket(), test_FR_CBK_011_dry_run_returns_synthetic_success()

### Community 127 - "test_backend_self_metrics.py"
Cohesion: 0.17
Nodes (9): SelfMetrics, body(), test_concurrent_scrapes_never_produce_a_torn_exposition(), scrape(), test_every_series_is_present_before_ingestion_is_bound(), test_ingestion_and_store_numbers_are_read_at_scrape_time(), test_query_latency_histogram_is_labelled_by_route(), test_two_instances_do_not_share_a_registry() (+1 more)

### Community 128 - "ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server"
Cohesion: 0.18
Nodes (10): ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server, Consequences, Context, Decision, Rationale, Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents) (+2 more)

### Community 129 - "Spec 005 — Rule Engine, Alerting and Callbacks"
Cohesion: 0.15
Nodes (11): ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell, Consequences, Context, Decision, Rationale, Conflict with spec 000 §3.2, Design decisions, Not done / follow-ups (+3 more)

### Community 130 - "teams/fixtures.py"
Cohesion: 0.40
Nodes (6): _ask(), _backend(), _card(), test_alert_question_shows_the_alert_badge_from_real_citations(), test_disabled_backend_renders_the_disabled_card(), test_rejection_question_renders_a_real_answer_card()

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "test_UBS_123_snapshot_emitter.py"
Cohesion: 0.60
Nodes (3): _build(), test_build_agent_logs_emitter_skips_with_the_evaluator_counters(), test_build_agent_rejects_a_bucket_longer_than_retention_allows()

### Community 133 - "healthcheck"
Cohesion: 0.20
Nodes (9): interval, retries, test, timeout, healthcheck, image, ports, services (+1 more)

### Community 134 - "telemetry-shared"
Cohesion: 0.33
Nodes (6): telemetry-agent, telemetry-backend, telemetry-mcp, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 135 - "AgentRegistry"
Cohesion: 0.22
Nodes (9): _error_card_text(), test_bad_request_gets_a_rephrase_card(), test_connection_failure_hides_the_exception_text(), test_disabled_nl_gets_a_clear_card(), test_gateway_timeout_gets_the_try_again_card(), test_server_error_says_the_service_is_unreachable_without_internals(), test_timeout_gets_a_try_again_card(), boom() (+1 more)

### Community 136 - ".markdownlint-cli2.yaml"
Cohesion: 0.50
Nodes (3): config, MD013, ignores

### Community 137 - "test_UBS_113_evaluation_loop.py"
Cohesion: 0.27
Nodes (4): _rule(), _run_ticks(), _stepping_clock(), test_the_loop_delivers_a_real_reject_spike_to_both_paths()

### Community 138 - "_Stack"
Cohesion: 0.15
Nodes (6): _burst(), _Stack, test_a_bad_edit_is_rejected_and_the_agent_keeps_its_actions(), test_a_firing_rule_runs_each_of_its_actions_once(), done(), test_an_edited_rules_file_binds_an_action_without_a_restart()

### Community 143 - "_load"
Cohesion: 0.60
Nodes (4): _load(), test_a_label_on_a_non_signature_rule_is_rejected(), test_a_signature_rule_loads_with_its_label(), test_a_signature_rule_without_a_label_is_rejected()

### Community 145 - "PublishResult"
Cohesion: 0.08
Nodes (27): _ScriptedSink, classify_publish_response(), PublishAction, PublishOutcome, PublishResult, _alerts_to_backend_act(), send(), _FlakyBackendSink (+19 more)

### Community 155 - "metrics/__init__.py"
Cohesion: 0.27
Nodes (5): compute_indicators(), compute_ratio(), RatioDef, Indicator, Indicators

### Community 156 - ".__init__"
Cohesion: 0.18
Nodes (3): on_drop(), _on_buffer_drop(), PublishSink

### Community 157 - "_run_scenario"
Cohesion: 0.18
Nodes (5): _HangingSink, _make_alert(), _make_snapshot(), _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher()

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (9): hb(), registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded(), test_one_stale_agent_is_partial() (+1 more)

### Community 160 - "test_the_agent_process_alerts_magic_and_the_backend"
Cohesion: 0.11
Nodes (8): _number(), TeamsBotConfig, _authorize(), create_app(), main(), test_defaults_when_the_environment_is_empty(), test_invalid_values_fail_with_a_clear_message(), test_values_are_read_from_the_environment()

### Community 161 - "teams_agent/main.py"
Cohesion: 0.09
Nodes (11): BackendError, NlBackendClient, _parse(), build_reply(), question_text(), register_handlers(), on_message(), resolve_timezone() (+3 more)

### Community 162 - "ack_latency_ms"
Cohesion: 0.10
Nodes (20): ack_latency_ms, baseline_window_minutes, enabled, minimum_samples, window_minutes, execution_issue_rate, baseline_window_minutes, enabled (+12 more)

### Community 194 - "test_heartbeat_provider_output_is_accepted_in_a_batch"
Cohesion: 0.25
Nodes (3): FakeClock, test_heartbeat_provider_output_is_accepted_in_a_batch(), test_unknown_agent_is_404()

### Community 195 - "test_latency_phrase.py"
Cohesion: 0.36
Nodes (4): _summary(), test_latency_phrase_reports_the_percentiles_and_sample_count(), test_latency_phrase_says_so_when_percentiles_are_withheld(), test_latency_phrase_says_so_when_there_are_no_samples()

### Community 201 - "render_answer"
Cohesion: 0.11
Nodes (26): escape_adaptive_card_text(), alert_duration_minutes(), alert_prose(), breakdown_phrase(), chart_rows_from_groups(), compare_delta_phrase(), completeness_sentence(), delivery_phrase() (+18 more)

### Community 207 - "telemetry_backend_nl_intents"
Cohesion: 0.07
Nodes (16): _fixed_now(), main(), _step(), SessionHeartbeatTracker, _SessionState, SessionTimeout, session_id_for(), derive_heartbeat_timeout_counters() (+8 more)

### Community 212 - "time.py"
Cohesion: 0.23
Nodes (10): baseline_time_range_before(), _local_midnight(), _parse_relative_duration(), _parse_short_datetime(), parse_time_expression(), _relative_from_amount(), _this_morning_start(), TimeParseResult (+2 more)

### Community 213 - "baseline.py"
Cohesion: 0.10
Nodes (13): AnomalyMetric, AnomalyReading, _baseline_value(), BaselineTracker, _current_sample(), _current_value(), _minutes(), _percent() (+5 more)

### Community 214 - "config_loader.py"
Cohesion: 0.11
Nodes (10): _AnomalyYaml, _RuleYaml, _TierYaml, _to_rule_config(), _tier(), _matched_tier(), RuleKind, RuleState (+2 more)

### Community 215 - "classify_http_status"
Cohesion: 0.27
Nodes (6): classify_http_status(), RetryDecision, test_FR_CBK_006_2xx_is_success(), test_FR_CBK_006_408_429_5xx_is_retry(), test_FR_CBK_006_non_2xx_non_4xx_5xx_falls_back_to_permanent_failure(), test_FR_CBK_006_other_4xx_is_permanent_failure()

### Community 226 - "UBS-117: event publication and integration boundary"
Cohesion: 0.18
Nodes (10): Architecture comparison, Config, Current: implemented UBS-117 baseline, Implemented in this change, Intended to-be: same services, with planned additions, Other work remains separate, Sponsor review baseline (proposed; not yet approved), UBS-117: event publication and integration boundary (+2 more)

### Community 234 - "telemetry_agent/main.py"
Cohesion: 0.06
Nodes (24): ActionType, AgentConfig, connect_reporter_to_publisher(), drop_hook(), heartbeat_provider(), build_agent(), check_action_secret(), stage_actions() (+16 more)

### Community 268 - "test_UBS_25_29_anomaly.py"
Cohesion: 0.21
Nodes (28): load_anomaly_rules(), _engine(), _fire(), _ratio_snapshot(), _rule(), test_a_long_incident_keeps_alerting_instead_of_auto_resolving(), test_a_resolved_anomaly_carries_no_fabricated_metric_context(), test_a_thin_current_window_is_not_judged() (+20 more)

### Community 270 - "Project instructions"
Cohesion: 0.08
Nodes (23): Agent guidance, Architecture constraints, Development workflow, Git attribution, Graphify, graphify, Project instructions, Requirements and decisions (+15 more)

### Community 272 - "Metrics Query API (UBS-68, UBS-91, UBS-92)"
Cohesion: 0.22
Nodes (9): Code locations, Endpoint, Example request, Example response, Metric and dimension aliases, Metrics Query API (UBS-68, UBS-91, UBS-92), Multi-replica mode (UBS-92), Operational limits (UBS-91) (+1 more)

### Community 275 - "Rule Engine"
Cohesion: 0.09
Nodes (25): NoLogActivity rule, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Rule Engine, Safety and suppression (silences, grace, storm cap), SighupRuleReloader, 1. `make rules-test` (+17 more)

### Community 279 - "BackendPublisher"
Cohesion: 0.08
Nodes (17): BatchSequencer, build_batch(), make_pending_item(), _size_of(), make_alert(), make_event(), test_batch_sequencer_seq_is_monotonic_and_ids_differ(), test_build_batch_envelope_fields() (+9 more)

### Community 280 - "Teams bot"
Cohesion: 0.12
Nodes (13): Configuration, Connect Copilot, Run it locally, Telemetry MCP server, Configuration, Questions to try, Real Teams (later, not tested against a real tenant), Run it locally (5 terminals, all from the repo root) (+5 more)

### Community 281 - "Agent"
Cohesion: 0.15
Nodes (11): Agent, agent(), _simulate(), _SimulationFinished, test_every_simulator_application_variant_reaches_the_shipped_counters(), test_simulator_failure_lines_fire_app_log_failure(), test_simulator_rotation_preserves_application_counters_and_fix_parsing(), test_simulator_signature_alert_reaches_backend_and_signed_callback() (+3 more)

### Community 283 - "test_llm_fallback.py"
Cohesion: 0.09
Nodes (24): build_llm_filler(), build_nl_service(), AzureOpenAiSlotFiller, default_mock_responses(), OllamaSlotFiller, _normalize_time_range(), parse_llm_slot_payload(), _sanitize_filters() (+16 more)

### Community 284 - "OllamaSlotFiller"
Cohesion: 0.12
Nodes (13): native_base_url(), _chat(), _run(), go(), record(), test_FR_NLQ_007_payload_uses_schema_keep_alive_and_token_cap(), test_FR_NLQ_021_connection_error_is_unavailable(), test_FR_NLQ_030_none_intent_carries_reply() (+5 more)

### Community 285 - "load_agent_config"
Cohesion: 0.22
Nodes (18): AgentConfigError, load_agent_config(), test_a_bad_section_is_named_in_the_error(), test_binary_magic_is_read_as_hex(), test_binary_parsing_defaults_to_disabled(), test_disabled_callbacks_mean_no_dispatcher(), test_error_signatures_are_read_from_parsing(), test_insecure_publish_endpoint_needs_the_explicit_flag() (+10 more)

### Community 286 - "UBS-100 — Teams bot with Adaptive Card answers (spec)"
Cohesion: 0.20
Nodes (9): As Built, Further Notes, Implementation Decisions, Out of Scope, Problem Statement, Solution, Testing Decisions, UBS-100 — Teams bot with Adaptive Card answers (spec) (+1 more)

### Community 287 - "telemetry_backend/config.py"
Cohesion: 0.08
Nodes (30): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), ensure_nl_llm_credentials(), IngestionConfig (+22 more)

### Community 288 - "health-reporter-overview.md"
Cohesion: 0.29
Nodes (5): UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration

### Community 290 - "NlQueryContext"
Cohesion: 0.22
Nodes (17): MockLlmSlotFiller, NlQueryContext, _ask(), _ForbiddenLlm, _service(), test_FR_NLQ_021_timeout_falls_back_to_weak_rule_match(), test_FR_NLQ_021_unreachable_llm_without_rule_match_is_friendly(), test_FR_NLQ_030_guarded_llm_reply_is_returned() (+9 more)

### Community 291 - "QueryTimeRange"
Cohesion: 0.20
Nodes (12): to_metrics_query(), _clamp_time_range(), InterpretedValidationError, _schema_issues(), validate_interpreted_query(), ValidationIssue, ValidationResult, QueryTimeRange (+4 more)

### Community 299 - "RuleConfigError"
Cohesion: 0.12
Nodes (20): _defined_action_names(), load_rules_from_yaml(), read_rules_file(), _rule_label(), RuleConfigError, test_a_level_rule_loads_with_its_level(), test_level_must_be_one_of_the_closed_level_set(), test_level_on_a_metric_without_a_level_dimension_fails_load() (+12 more)

### Community 303 - "sign"
Cohesion: 0.21
Nodes (10): load_callback_secret(), sign(), test_FR_CBK_005_different_body_produces_different_signature(), test_FR_CBK_005_different_secret_produces_different_signature(), test_FR_CBK_005_different_timestamp_produces_different_signature(), test_FR_CBK_005_load_callback_secret_fails_fast_when_empty(), test_FR_CBK_005_load_callback_secret_fails_fast_when_unset(), test_FR_CBK_005_load_callback_secret_reads_env_var() (+2 more)

### Community 305 - "HttpsCallbackSink"
Cohesion: 0.21
Nodes (10): HttpsCallbackSink, _make_alert(), _run_one(), test_FR_CBK_001_success_marks_delivered(), handler(), test_FR_CBK_004_006_persistent_5xx_retries_then_fails_after_max_attempts(), test_FR_CBK_004_006_retries_then_succeeds(), test_FR_CBK_006_429_is_retried_not_treated_as_permanent() (+2 more)

### Community 307 - "telemetry_agent/config.py"
Cohesion: 0.13
Nodes (13): _ActionsYaml, LogsConfig, _LogsYaml, ParsingConfig, _ParsingYaml, _PipelineYaml, _RulesYaml, _Section (+5 more)

### Community 310 - "MetricsQueryResponse"
Cohesion: 0.14
Nodes (8): HttpxFanoutClient, ReplicaFanout, DataCompleteness, MetricsQueryResponse, _request(), _StubPeerClient, test_UBS_92_fanout_merges_peer_totals(), test_UBS_92_peer_failure_marks_partial()

### Community 312 - "NL query manual test plan: Ollama, Teams and Copilot (MCP)"
Cohesion: 0.17
Nodes (12): 0. Setup, A. Backend startup, B. Direct API, C. Ollama slow or down, D. Teams (Agents Playground), E. MCP server (MCP Inspector), F. Copilot Studio (optional), G. Safety (+4 more)

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements

## Knowledge Gaps
- **165 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `telemetry-mcp`, `telemetry-simulator`, `telemetry-teams` (+160 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1831 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **68 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MA-04: calculated indicators and snapshot output.` connect `Implementation Status live document` to `AgentHeartbeat wire contract`, `LatencyCorrelator`, `Rule Engine`, `MetricsAggregator ring buffer`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Are the 78 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 78 INFERRED edges - model-reasoned connections that need verification._
- **What connects `telemetry-agent`, `telemetry-backend`, `telemetry-mcp` to the rest of the system?**
  _165 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `FixParser` be split into smaller, more focused modules?**
  _Cohesion score 0.059298245614035086 - nodes in this community are weakly interconnected._
- **Why does `Telemetry System Documentation Index` connect `Telemetry System Documentation Index` to `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1`, `demo_config.yaml (Magic parsing demo config)`, `Telemetry Backend (architecture constraint)`, `ADR 0001: Telemetry Agent written in Go (Superseded)`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._