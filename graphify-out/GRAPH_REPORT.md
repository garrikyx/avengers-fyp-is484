# Graph Report - avengers-fyp-is484  (2026-10-22)

## Corpus Check
- 390 files · ~209,950 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: (none) 11, .example 1, .typed 1)

## Summary
- 4996 nodes · 13570 edges · 304 communities (174 shown, 130 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 2385 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d17cfff5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SourceMeta
- frame.py
- test_metrics_event.py
- RuleEngine
- make_snapshot
- config_loader.py
- HealthReporter
- FixParser
- RetryPolicy
- LatencyCorrelator
- derive_counters
- factory.py
- test_heartbeat.py
- OffsetTracker
- PublishBuffer
- test_UBS_112_metrics_ingestor.py
- test_bot_replies.py
- PublishResult
- MetricsAggregator
- EventStore
- test_RE_session_integration.py
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- LogMonitor
- AgentHeartbeat
- BackendPublisher
- pathlib
- DeliveryStatus
- health/config.py
- test_RE_publish_integration.py
- AggregatorConfig
- test_ING_004_008_ingest_guard.py
- pytest
- test_MA_03_correlation.py
- ParseResult
- config/rules.yaml live rule set
- create_app
- SessionHeartbeatTracker
- MetricsAggregator ring buffer
- manifest.json
- AppDeps
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- test_UBS_36_backtest.py
- telemetry_agent/config.py
- CallbackResult
- display.py
- decimal
- parse_publish_config
- QueryEngine
- Agent
- LineClassification
- CallbackDispatcher
- HttpsCallbackSink
- MetricsQueryRequest
- bot.py
- test_queue_depth.py
- AlertEvent
- PipelineBridge
- test_UBS_116_app_log_counters.py
- enrich.py
- telemetry_backend/main.py
- rules/demo_quickstart.py
- Telemetry Agent (architecture constraint)
- DropOldestQueue
- BoundedQueue
- HeartbeatMonitor
- from_alert_event
- test_agent_registry.py
- 009 — Non-Functional Requirements and Security
- StreamProcessorConfig
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- IngestionService
- datetime
- CounterRegistry
- test_heartbeat_roundtrip.py
- services/demo_quickstart.py
- test_internal_api.py
- End-to-End Acceptance Scenario (FR-TST-010)
- HttpsPublishSink
- test_ING_004_008_routes.py
- metrics/__init__.py
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- publish_fixtures.py
- api/health.py
- Snapshot
- SignatureMatcher
- ParsedMessageEvent
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- validator.py
- callbacks/config.py
- .__init__
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- _wire
- telemetry_backend/config.py
- service.py
- classify_http_status
- test_FR_CBK_017_isolation.py
- telemetry_shared shared schema package
- ActionRunner
- UBS-30 Implementation Notes
- AgentRegistry
- test_UBS_115_snapshot_to_metricstore.py
- test_UBS_109_rule_engine_to_backend.py
- Confidence
- OpenAiCompatibleSlotFiller
- make_snapshot
- pipeline_demo.py
- services/self_metrics.py
- demo_config.yaml (Magic parsing demo config)
- test_QRY_04_concurrency.py
- Rule Engine demo runbook
- 008 — Natural Language Query Layer (Copilot/Teams)
- LlmConfig
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- fields.py
- make_alert
- telemetry-shared
- test_UBS_35_36_reload_and_draft.py
- Auditability & Compliance rationale (deterministic order audit trails)
- PublishAction
- AppLogParser
- ADR 0002: Backend in Python/FastAPI
- ADR 0003: HTTPS/JSON Transport Day-1
- ADR 0005: In-Memory Metric Store
- ADR 0006: Agent in Python
- Parser Test Obligations (§10)
- Message Validation and Parse Error Reason Codes (FR-PRS-017–019)
- Data Completeness Block (FR-QRY-015)
- Backend Health and Self-Metrics (FR-HLT-010)
- Sponsor email — deployment and storage clarifications (Q-13)
- test_data_completeness.py
- telemetry_agent/main.py
- teams_agent/main.py
- reject_rate anomaly baseline config (baseline_window_minutes=60, minimum_samples=100)
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
- fix/normalize.py
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- AlertStore
- QueryTimeRange
- backtest.py
- parse_fix_timestamp
- Implementation Status live document
- _Harness
- test_UBS_100_teams_bot_to_backend.py
- cards.py
- UBS-49 — Pipeline Bridge Integration (live agent path)
- test_reporter.py
- publishing/__init__.py
- heartbeat_json
- snapshot_bridge.py
- agent_registry.py
- Issue tracker: Jira
- ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell
- Metrics Query API (UBS-68, UBS-91, UBS-92)
- test_STM_04_efficiency.py
- test_UBS_36_backtest_cli.py
- .__init__
- test_STM_03_warmup.py
- time.py
- teams/fixtures.py
- test_health_monitor_e2e.py
- test_ingestion.py
- test_log_monitor_status.py
- SeqTracker
- _run
- build.sh
- Teams bot
- _error_card_text
- UBS-100 — Teams bot with Adaptive Card answers (spec)
- HeartbeatEmitter
- telemetry_agent_rules_engine
- effective_reject_reason
- signing.py
- test_UBS_116_app_log_ingest.py
- classify_publish_response
- IngestionConfig
- test_UBS_123_snapshot_emitter.py
- Rule Engine
- data_completeness.py
- health-reporter-overview.md
- _run_scenario

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 120 edges
2. `AlertEvent` - 96 edges
3. `create_app()` - 92 edges
4. `HealthReporter` - 89 edges
5. `MetricStore` - 84 edges
6. `StreamProcessorConfig` - 82 edges
7. `BackendPublisher` - 81 edges
8. `SourceMeta` - 76 edges
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

## Communities (304 total, 130 thin omitted)

### Community 0 - "SourceMeta"
Cohesion: 0.08
Nodes (21): _fixed_now(), main(), _step(), derive_heartbeat_timeout_counters(), derive_parser_counters(), derive_session_counters(), _parse_error_reason(), _parse_transact_time() (+13 more)

### Community 1 - "frame.py"
Cohesion: 0.08
Nodes (26): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+18 more)

### Community 2 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (28): build_parsed_message_event(), _meta(), _parse(), _parser_counters(), _session_counters(), test_a_clean_fix_line_is_not_a_parse_error(), test_clean_line_reports_no_reason(), test_every_derived_session_counter_is_declared_in_counter_dimensions() (+20 more)

### Community 3 - "RuleEngine"
Cohesion: 0.08
Nodes (23): _tier(), _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _matched_tier(), _metric_context() (+15 more)

### Community 4 - "make_snapshot"
Cohesion: 0.11
Nodes (48): _read_observed(), make_gauges(), make_indicator(), make_indicators(), make_latency(), make_snapshot(), _absence_rule(), _gauge_rule() (+40 more)

### Community 5 - "config_loader.py"
Cohesion: 0.07
Nodes (21): _defined_action_names(), load_rules(), load_rules_from_yaml(), _parse_duration_seconds(), read_rules_file(), _rule_label(), RuleConfigError, _RuleYaml (+13 more)

### Community 6 - "HealthReporter"
Cohesion: 0.07
Nodes (16): HealthThresholds, HealthReporter, HealthSignals, _utc_now(), 3. UBS-30 — read lag (the foundation), 4.3 Rollup and payload — `health/reporter.py`, Design points, Module map (`apps/agent/src/telemetry_agent/health/`) (+8 more)

### Community 7 - "FixParser"
Cohesion: 0.11
Nodes (15): is_parse_error(), demo_log_lines(), FixParser, ParseError, 5.2 Intake and rules — `health/reporter.py`, UBS-59: parse-error window, test_is_parse_error_matches_aggregator_convention(), test_FR_PRS_012_corpus_files_frame_without_errors() (+7 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.06
Nodes (24): RetryPolicy, main(), format_fix_line(), generate_application_log(), generate_fix_order_messages(), get_timestamps(), rotate_if_needed(), run_harness() (+16 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.08
Nodes (9): CorrelatorStats, LatencyCorrelator, OrderContext, _timedelta_to_ms(), main(), ingest(), _step(), _build_gauges() (+1 more)

### Community 10 - "derive_counters"
Cohesion: 0.09
Nodes (34): derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), ReasonNormalizer, top_reject_reasons(), _banner(), _implementation(), _line() (+26 more)

### Community 11 - "factory.py"
Cohesion: 0.12
Nodes (14): build_nl_service(), AzureOpenAiSlotFiller, default_mock_responses(), MockLlmSlotFiller, parse_llm_slot_payload(), LlmSlotFiller, LlmSlotFillError, LlmSlotResult (+6 more)

### Community 12 - "test_heartbeat.py"
Cohesion: 0.11
Nodes (16): HeartbeatEmitter, Collect, FakeClock, _reporter(), test_heartbeat_carries_file_state_and_lag(), test_heartbeat_payload_matches_spec_004_section_6(), test_interval_defaults_from_reporter_config(), test_logging_sink_writes_wire_json() (+8 more)

### Community 13 - "OffsetTracker"
Cohesion: 0.07
Nodes (13): OffsetTracker, test_degraded_status_flows_into_heartbeat_payload(), test_health_reporter_handles_truncation(), test_health_reporter_survives_log_rotation(), test_offset_persists_across_simulated_restart(), test_agent_heartbeat_reaches_the_health_endpoint(), _line_texts(), test_checkpoints_offsets_while_file_is_still_busy() (+5 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (16): PublishBuffer, _item(), _tags(), test_an_item_larger_than_the_whole_cap_is_not_self_evicted(), test_append_and_take_preserve_fifo_order(), test_byte_overflow_drops_oldest_and_counts(), on_drop(), test_expire_drops_only_items_older_than_max_age() (+8 more)

### Community 15 - "test_UBS_112_metrics_ingestor.py"
Cohesion: 0.24
Nodes (13): _counters(), _feed(), _ingestor(), _meta(), _reporter(), test_a_failing_component_never_escapes_and_is_counted(), test_a_hard_parse_error_counts_for_aggregator_and_reporter(), test_bad_timestamp_is_a_heartbeat_error_but_not_an_aggregator_one() (+5 more)

### Community 16 - "test_bot_replies.py"
Cohesion: 0.21
Nodes (36): QueryGroup, answer(), clarification(), converse(), group(), json_ok(), message(), texts() (+28 more)

### Community 17 - "PublishResult"
Cohesion: 0.09
Nodes (14): _ScriptedSink, PublishResult, _FlakyBackendSink, _HangingSink, _StatusSink, _config(), _FakeSink, test_age_eviction_runs_on_each_publish_tick() (+6 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.10
Nodes (5): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator

### Community 19 - "EventStore"
Cohesion: 0.09
Nodes (16): EventStoreConfig, EventStore, _InstanceEvents, _app_with_store(), test_UBS_118_missing_event_returns_404(), test_UBS_118_unknown_query_param_returns_400(), make_telemetry_event(), _drain_one() (+8 more)

### Community 20 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (17): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), _rule(), test_a_clean_logout_does_not_also_produce_a_timeout(), test_fix_session_down_fires_on_a_heartbeat_timeout_alone() (+9 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.08
Nodes (32): Open Questions and Decisions Required, Callback Dispatcher, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent, Q-2 — Callback Protocol Magic Will Support (+24 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.16
Nodes (21): _key(), _keys(), _observe(), test_a_clean_logout_never_times_out(), test_a_session_relogging_on_after_logout_is_tracked_again(), test_a_session_still_speaking_never_times_out(), test_a_session_that_recovers_can_time_out_again(), test_both_directions_share_one_dimension_id() (+13 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.12
Nodes (19): health: threshold config block, AgentHeartbeat wire contract, AgentStatus literal vocabulary, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry, HealthSignals sampled instant, scripts/heartbeat_receiver_stub.py placeholder receiver (+11 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (28): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+20 more)

### Community 26 - "LogMonitor"
Cohesion: 0.06
Nodes (11): Harvester, LogMonitor, 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 5.1 The window — `health/window.py`, 5. UBS-59 — parse error rate, 7. Status rollup — the one table (+3 more)

### Community 27 - "AgentHeartbeat"
Cohesion: 0.08
Nodes (14): LoggingHeartbeatSink, PrintHeartbeatSink, 4.1 Wire contract — `packages/telemetry_shared/models/health.py`, 4.2 Configuration — `health/config.py`, 4.4 Emitter and sinks — `health/heartbeat.py`, 4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`, 4. UBS-58 — the heartbeat, Also touched, and why (+6 more)

### Community 28 - "BackendPublisher"
Cohesion: 0.09
Nodes (9): make_pending_item(), _size_of(), _drain(), main(), _make_snapshot(), _print_state(), _step(), BackendPublisher (+1 more)

### Community 29 - "pathlib"
Cohesion: 0.06
Nodes (15): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+7 more)

### Community 30 - "DeliveryStatus"
Cohesion: 0.10
Nodes (14): DeliveryRecord, DeliveryStatus, DeliveryTracker, test_UBS_34_each_transition_is_timestamped(), test_UBS_34_enqueue_records_pending(), test_UBS_34_immediate_success_sequence(), test_UBS_34_last_error_persists_across_terminal_transition(), test_UBS_34_retried_then_delivered_sequence() (+6 more)

### Community 31 - "health/config.py"
Cohesion: 0.10
Nodes (21): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, HeartbeatConfig, _HeartbeatYaml, load_health_config() (+13 more)

### Community 32 - "test_RE_publish_integration.py"
Cohesion: 0.06
Nodes (42): AgentCounterSampler, _aggregator(), _alert(), _dispatch(), _drain(), _fire(), _rule(), test_callback_failures_do_not_make_a_log_starved_agent_look_alive() (+34 more)

### Community 33 - "AggregatorConfig"
Cohesion: 0.13
Nodes (31): AggregatorConfig, FakeClock, hand_labelled_events(), make_event(), minimal_aggregator(), test_10k_events_in_60s_window_returns_correct_count(), test_cardinality_cap_folds_overflow_into_other_and_preserves_total(), test_cardinality_cap_resets_per_bucket_not_for_process_lifetime() (+23 more)

### Community 34 - "test_ING_004_008_ingest_guard.py"
Cohesion: 0.10
Nodes (16): Accept, Duplicate, IngestGuard, RateLimited, _utc_now(), FakeClock, guard(), test_batch_ids_are_scoped_per_agent() (+8 more)

### Community 35 - "pytest"
Cohesion: 0.07
Nodes (30): _Clock, _names(), _rule(), _Stack, test_a_cleared_condition_resolves_on_both_paths(), test_a_counter_rule_fires_and_reaches_both_paths(), test_a_rejected_reload_routes_nothing_and_keeps_the_rules(), test_a_reload_request_waits_for_the_next_tick() (+22 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (22): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), replaced() (+14 more)

### Community 37 - "ParseResult"
Cohesion: 0.16
Nodes (16): DemoMetricsSink, extract_log_level(), _corpus_files(), _fields_dict(), _format_line_result(), _load_config(), main(), _parse_line() (+8 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.14
Nodes (19): Agent processing pipeline (monitor to health reporter), publish: Backend Publisher config block, BackendUnreachable rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule (+11 more)

### Community 39 - "create_app"
Cohesion: 0.08
Nodes (33): _counts(), create_app(), enqueue_or_full(), get_alert(), get_event(), ingest_batch(), ingest_events(), ingest_heartbeat() (+25 more)

### Community 40 - "SessionHeartbeatTracker"
Cohesion: 0.10
Nodes (7): SessionHeartbeatTracker, _SessionState, SessionTimeout, session_id_for(), _session_id(), test_default_threshold_mirrors_the_backend_registry(), test_session_key_matches_seq_tracker_exactly()

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.14
Nodes (16): AckLatencyBreach rule, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent), Histogram (fixed buckets, merge, percentile), LatencyCorrelator (+8 more)

### Community 42 - "manifest.json"
Cohesion: 0.09
Nodes (22): accentColor, bots, description, full, short, developer, name, privacyUrl (+14 more)

### Community 43 - "AppDeps"
Cohesion: 0.21
Nodes (15): AppDeps, env(), FakeClock, heartbeat(), post(), test_counts_cover_all_four_states(), test_detail_matches_spec_007_5_2(), test_detail_unknown_agent_is_404() (+7 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (16): bad(), FakeClock, make(), ok(), test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides(), test_errors_counted_and_reported_in_heartbeat(), test_parse_fields_are_none_until_a_producer_reports() (+8 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.13
Nodes (12): SlidingWindowCounter, drive(), at(), test_capacity_is_rounded_not_floored(), test_counts_events_inside_window(), test_decays_as_window_slides(), test_event_older_than_window_is_dropped(), test_idle_window_reads_zero_not_none() (+4 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.11
Nodes (22): Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), 001 — Architecture, Ingestion Service (component), Log Monitor (component) (+14 more)

### Community 47 - "CamelModel"
Cohesion: 0.07
Nodes (28): AlertsQueryParams, EventsQueryParams, RejectedItem, build_intents_response(), AlertDetailResponse, CamelModel, EventsListResponse, AgentHealthDetail (+20 more)

### Community 48 - "test_UBS_36_backtest.py"
Cohesion: 0.20
Nodes (15): _fix_log(), _nothing_may_be_dispatched(), _rule(), _run(), test_a_date_time_line_prefix_anchors_the_replay(), test_a_draft_rule_is_evaluated_and_reported_as_draft(), test_a_gauge_rule_carries_a_caveat(), test_a_quiet_log_never_fires() (+7 more)

### Community 49 - "telemetry_agent/config.py"
Cohesion: 0.06
Nodes (48): ActionConfigError, ActionDef, _ActionYaml, _command_key(), _is_rooted(), load_action_catalogue(), _parse_action(), parse_actions() (+40 more)

### Community 50 - "CallbackResult"
Cohesion: 0.16
Nodes (7): _ScriptedSink, CallbackResult, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink

### Community 52 - "display.py"
Cohesion: 0.21
Nodes (17): _box_title(), _delimiter_label(), _explain_classification(), _format_field_row(), _hr(), print_demo_header(), print_demo_summary(), _render_applog() (+9 more)

### Community 53 - "decimal"
Cohesion: 0.08
Nodes (19): Histogram, HistogramPayload, _aligned_now(), _histogram_payload(), _read_one_group(), _snapshot(), test_a_metric_no_contributing_agent_reported_is_absent_not_fabricated(), test_a_metric_only_some_agents_reported_still_merges_the_ones_that_did() (+11 more)

### Community 54 - "parse_publish_config"
Cohesion: 0.13
Nodes (18): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, test_allows_plain_http_when_explicitly_opted_in(), test_buffer_bytes_must_be_positive(), test_defaults_match_spec_010() (+10 more)

### Community 55 - "QueryEngine"
Cohesion: 0.10
Nodes (10): _AccumulatedGroup, QueryEngine, QueryValidationError, EffectiveTimeRange, QueryInterpretation, SeriesPoint, is_known_metric(), resolve_dimension_name() (+2 more)

### Community 56 - "Agent"
Cohesion: 0.12
Nodes (10): Agent, DryRunPublishSink, agent(), _simulate(), _SimulationFinished, test_every_simulator_application_variant_reaches_the_shipped_counters(), test_simulator_rotation_preserves_application_counters_and_fix_parsing(), test_simulator_signature_alert_reaches_backend_and_signed_callback() (+2 more)

### Community 57 - "LineClassification"
Cohesion: 0.14
Nodes (14): classify_line(), compile_app_log_patterns(), _looks_like_fix(), LineClassification, test_FR_PRS_010_fix_detected_pipe_delimited(), test_FR_PRS_010_fix_detected_soh_delimited(), test_FR_PRS_010_fix_detected_with_log_prefix(), test_FR_PRS_010_rejects_begin_string_without_delimiter_before_msg_type() (+6 more)

### Community 58 - "CallbackDispatcher"
Cohesion: 0.12
Nodes (7): main(), _make_alert(), _print_counters(), _run_one(), _step(), CallbackDispatcher, CallbackSink

### Community 59 - "HttpsCallbackSink"
Cohesion: 0.17
Nodes (10): HttpsCallbackSink, _make_alert(), _run_one(), test_FR_CBK_001_success_marks_delivered(), handler(), test_FR_CBK_004_006_persistent_5xx_retries_then_fails_after_max_attempts(), test_FR_CBK_004_006_retries_then_succeeds(), test_FR_CBK_006_429_is_retried_not_treated_as_permanent() (+2 more)

### Community 60 - "MetricsQueryRequest"
Cohesion: 0.12
Nodes (12): QueryConfig, QueryTimeoutError, FanoutClient, HttpxFanoutClient, ReplicaFanout, DataCompleteness, MetricsQueryRequest, MetricsQueryResponse (+4 more)

### Community 61 - "bot.py"
Cohesion: 0.15
Nodes (9): BackendError, NlBackendClient, _parse(), build_reply(), question_text(), resolve_timezone(), run(), recording() (+1 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.11
Nodes (19): BufferingHeartbeatSink, Missing downstream / upstream (what this branch cannot prove), FakeQueue, Flaky, make(), test_at_critical_watermark_is_unhealthy(), test_at_high_watermark_is_degraded_with_reason_and_trend(), test_below_high_watermark_is_healthy() (+11 more)

### Community 63 - "AlertEvent"
Cohesion: 0.07
Nodes (6): AlertRouter, RuleEvaluator, _utc_now(), AlertEvent, _Agent, test_app_log_lines_keep_no_log_activity_quiet_end_to_end()

### Community 64 - "PipelineBridge"
Cohesion: 0.04
Nodes (26): Registry, QueueSnapshot, PipelineCommitter, PipelineConfig, LinePosition, ProcessedLineDeduper, EventQueue, LineQueue (+18 more)

### Community 65 - "test_UBS_116_app_log_counters.py"
Cohesion: 0.14
Nodes (15): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), AppLogTelemetry, _ingest_app_log_lines(), _aggregator(), _ingest(), _tel() (+7 more)

### Community 66 - "enrich.py"
Cohesion: 0.23
Nodes (13): build_fix_telemetry(), normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type(), normalize_session_reject_reason() (+5 more)

### Community 67 - "telemetry_backend/main.py"
Cohesion: 0.06
Nodes (6): _utc_now(), _PublishYaml, _RetryYaml, _utc_now(), _signature_alerts(), test_shipped_signature_rules_fire_on_their_own_patterns_only()

### Community 68 - "rules/demo_quickstart.py"
Cohesion: 0.06
Nodes (14): _alert_storm_act(), _alerts_to_backend_act(), _backend_unreachable_act(), attempt(), _dedup_act(), _Demo, _heartbeat_timeout_act(), main() (+6 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.19
Nodes (3): Magic simulator for development, Unified Telemetry Intelligence (Magic), Spec 004: Telemetry data model

### Community 70 - "DropOldestQueue"
Cohesion: 0.18
Nodes (4): DropOldestQueue, test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped(), test_FR_CBK_007_overflow_drops_oldest_and_increments_counter()

### Community 71 - "BoundedQueue"
Cohesion: 0.10
Nodes (5): BoundedQueue, test_block_policy_waits_for_capacity(), test_drop_oldest_policy_discards_oldest_on_overflow(), test_zero_capacity_rejects_without_storing(), test_full_queue_blocks_producer_without_drops()

### Community 72 - "HeartbeatMonitor"
Cohesion: 0.16
Nodes (6): AlertingConfig, backend_alert_id(), HeartbeatMonitor, _heartbeat(), test_FR_QRY_018_fresh_heartbeat_resolves_backend_alert(), test_FR_QRY_018_stale_heartbeat_fires_backend_alert()

### Community 73 - "from_alert_event"
Cohesion: 0.20
Nodes (8): CallbackAlertPayload, from_alert_event(), make_alert_event(), test_FR_CBK_001_payload_carries_ac_required_fields(), test_FR_CBK_002_payload_under_max_bytes_for_typical_alert(), test_FR_CBK_002_serialized_payload_matches_spec_shape(), test_FR_CBK_003_runbook_url_defaults_to_none(), test_FR_CBK_003_summary_stopgap_references_rule_and_condition()

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (12): FakeClock, hb(), make(), test_agent_clock_stepped_backwards_does_not_go_missing(), test_explicit_received_at_overrides_clock(), test_first_contact_is_reported_once(), test_late_older_heartbeat_keeps_newer_doc_but_refreshes_liveness(), test_missing_after_threshold_measured_on_backend_clock() (+4 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.11
Nodes (20): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), Resource Discipline (§9), Compliance and Operability Constraints (§7), Configurability NFRs (§5), 009 — Non-Functional Requirements and Security, NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed (+12 more)

### Community 77 - "StreamProcessorConfig"
Cohesion: 0.07
Nodes (23): StreamProcessorConfig, _dim_key(), _SeriesContribution, _snapshot(), test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell(), test_estimated_memory_bytes_grows_with_merged_series_and_shrinks_on_eviction(), test_estimated_memory_bytes_is_zero_for_an_empty_store(), test_merge_alone_can_trigger_shedding_without_an_external_tick() (+15 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.12
Nodes (11): SighupRuleReloader, _engine(), _fire(), _snapshot(), test_apply_rules_force_resolves_a_firing_alert_whose_rule_was_removed(), test_apply_rules_leaves_unrelated_rules_untouched(), test_apply_rules_preserves_state_for_a_rule_whose_name_persists(), test_apply_rules_removes_a_pending_state_without_an_event() (+3 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (15): C++ candidate (rejected: worst-case failure modes), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), .NET alternative (rejected), FastAPI framework, Go for both components alternative (rejected) (+7 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.08
Nodes (23): ADR 0004: No-Raw-Persistence Design, Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Offset Checkpointing (state.json), Parser Engine Agent-Level Contract (FR-PRS-001–003), Scaffold Document (plan/scaffold.md) (+15 more)

### Community 82 - "IngestionService"
Cohesion: 0.08
Nodes (11): IngestionService, IngestionValidationIssue, _safe_key(), _batch_with_snapshot(), test_create_app_probes_the_supplied_services_own_processor(), test_create_app_rejects_a_processor_the_service_does_not_feed(), test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store(), _wait_for_status() (+3 more)

### Community 83 - "datetime"
Cohesion: 0.15
Nodes (5): _meta(), flood(), test_demo_scenarios_run_to_completion(), _now_sending_time(), test_tailed_fix_lines_reach_the_real_aggregator()

### Community 84 - "CounterRegistry"
Cohesion: 0.12
Nodes (5): CounterRegistry, test_callbacks_shim_is_the_same_class(), test_increment_starts_at_zero_and_accumulates(), test_independent_counters_do_not_interfere(), test_snapshot_is_a_copy_not_a_live_view()

### Community 85 - "test_heartbeat_roundtrip.py"
Cohesion: 0.12
Nodes (8): FakeClock, test_heartbeat_provider_output_is_accepted_in_a_batch(), test_unknown_agent_is_404(), FakePublisher, _reporter(), test_connect_points_outbox_signals_at_the_publisher(), test_drop_hook_counts_each_evicted_item(), test_provider_returns_a_fresh_wire_heartbeat_each_call()

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (9): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), _reject(), _run_hong_kong_session(), _run_singapore_session() (+1 more)

### Community 87 - "test_internal_api.py"
Cohesion: 0.12
Nodes (19): create_internal_app(), _serve(), env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), test_decommissioned_agent_leaves_the_exposition() (+11 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.25
Nodes (6): Open Questions Document (plan/open-questions.md), Agent Restart Sequence (§8.2), NL Evaluation Requirements (FR-NLQ-025), End-to-End Acceptance Scenario (FR-TST-010), NL Evaluation Harness (FR-TST-007–009), Synthetic Load Generator (tools/fixgen, FR-TST-006)

### Community 89 - "HttpsPublishSink"
Cohesion: 0.13
Nodes (10): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), test_allows_plain_http_when_explicitly_opted_in(), test_body_over_threshold_is_gzipped_and_round_trips(), test_body_under_threshold_is_not_compressed(), test_rejects_plain_http_by_default(), test_sink_does_not_gzip_small_bodies() (+2 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (7): batch(), deps(), FakeClock, metrics(), test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once(), test_batches_past_the_per_agent_limit_get_429_with_retry_after()

### Community 91 - "metrics/__init__.py"
Cohesion: 0.15
Nodes (7): build_latency_summary(), compute_indicators(), compute_ratio(), RatioDef, Indicator, Indicators, LatencySummary

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (14): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+6 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (10): Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test), NFR-SEC-012: Order Identifier Hashing, Rotatable Key, NFR-SEC-013: No Raw-Log Debug Mode in Release Build, Security: Data Minimisation (§3.1) (+2 more)

### Community 94 - "publish_fixtures.py"
Cohesion: 0.20
Nodes (6): make_alert(), make_event(), _NeverCalledSink, _publisher(), test_enqueue_methods_are_plain_sync_functions(), test_enqueue_never_touches_the_sink_even_when_the_buffer_overflows()

### Community 95 - "api/health.py"
Cohesion: 0.15
Nodes (7): get_agent(), list_agents(), _summary(), healthz(), metrics(), readyz(), get_deps()

### Community 97 - "Snapshot"
Cohesion: 0.08
Nodes (19): align_to_canonical(), SnapshotOutcome, StreamProcessor, Decisions, Snapshot, test_merging_the_same_snapshot_twice_does_not_double_the_counters(), test_alignment_floors_a_phase_shifted_bucket_onto_the_canonical_grid(), test_alignment_is_a_no_op_when_already_on_the_grid() (+11 more)

### Community 98 - "SignatureMatcher"
Cohesion: 0.18
Nodes (10): compile_signature_rules(), resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule, test_cardinality_overflow_to_other(), test_dynamic_label_gr_disconnect(), test_dynamic_label_md_disconnect() (+2 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.07
Nodes (32): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent, _fixed_now() (+24 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.21
Nodes (10): hash_identifier(), load_hash_key(), test_FR_PRS_021_different_input_produces_different_hash(), test_FR_PRS_021_different_key_produces_different_hash(), test_FR_PRS_021_load_hash_key_fails_fast_when_empty(), test_FR_PRS_021_load_hash_key_fails_fast_when_unset(), test_FR_PRS_021_load_hash_key_reads_env_var(), test_FR_PRS_021_output_is_16_lowercase_hex_chars() (+2 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (11): _engine(), _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved(), test_pending_fires_after_for_elapsed(), test_pending_reverts_to_inactive_if_condition_clears_before_for_elapsed() (+3 more)

### Community 103 - "validator.py"
Cohesion: 0.25
Nodes (11): to_metrics_query(), _clamp_time_range(), InterpretedValidationError, _schema_issues(), validate_interpreted_query(), ValidationIssue, ValidationResult, InterpretedQuery (+3 more)

### Community 104 - "callbacks/config.py"
Cohesion: 0.15
Nodes (12): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), _RetryYaml, test_FR_CBK_001_allows_plain_http_with_explicit_opt_in(), test_FR_CBK_001_rejects_plain_http_by_default() (+4 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.12
Nodes (21): _alert(), _publisher(), _RecordingSink, _router(), test_a_mismatched_alert_is_dropped_before_it_reaches_the_buffer(), test_a_routed_alert_reaches_the_wire_in_the_batch(), test_an_empty_list_is_a_no_op(), test_an_unguarded_mismatch_poisons_the_whole_batch() (+13 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (11): gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups), agent metrics/ module (rolling metrics and aggregation), PostgreSQL (Day-2 historical metrics) (+3 more)

### Community 108 - "_wire"
Cohesion: 0.22
Nodes (6): _rule(), _run_ticks(), _stepping_clock(), test_the_loop_delivers_a_real_reject_spike_to_both_paths(), test_the_loop_feeds_the_correlator_gauge_to_pending_order_timeout(), _wire()

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.09
Nodes (26): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestGuardConfig, _IngestYaml (+18 more)

### Community 110 - "service.py"
Cohesion: 0.09
Nodes (21): build_default_filters(), default_time_range(), IntentDefinition, merge_interpreted_query(), catalogue_summary_for_prompt(), normalize_question(), render_stub_answer(), _extract_filters() (+13 more)

### Community 111 - "classify_http_status"
Cohesion: 0.27
Nodes (6): classify_http_status(), RetryDecision, test_FR_CBK_006_2xx_is_success(), test_FR_CBK_006_408_429_5xx_is_retry(), test_FR_CBK_006_non_2xx_non_4xx_5xx_falls_back_to_permanent_failure(), test_FR_CBK_006_other_4xx_is_permanent_failure()

### Community 112 - "test_FR_CBK_017_isolation.py"
Cohesion: 0.14
Nodes (10): callback_action(), _ExplodingRunner, _Recorder, _runner(), test_a_callback_action_is_signed_like_the_magic_callback(), handle(), test_a_dry_run_callback_action_sends_nothing(), test_a_failed_callback_action_counts_as_failed_on_its_own_counters() (+2 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (11): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams), Telemetry Agent (apps/agent) (+3 more)

### Community 115 - "UBS-30 Implementation Notes"
Cohesion: 0.33
Nodes (6): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration

### Community 116 - "AgentRegistry"
Cohesion: 0.11
Nodes (10): AgentRegistry, SelfMetrics, body(), test_concurrent_scrapes_never_produce_a_torn_exposition(), scrape(), test_every_series_is_present_before_ingestion_is_bound(), test_ingestion_and_store_numbers_are_read_at_scrape_time(), test_query_latency_histogram_is_labelled_by_route() (+2 more)

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.22
Nodes (11): _aggregator(), _drain_backend(), _evaluator(), _ingest_three_orders(), _publish_and_drain(), _publisher(), _read_counters(), test_app_log_metrics_reach_the_metric_store_as_distinct_series() (+3 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.05
Nodes (38): load_callback_secret(), sign(), _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _order(), _publish_and_drain() (+30 more)

### Community 119 - "Confidence"
Cohesion: 0.06
Nodes (14): Confidence, Parser, get_parser(), register_parser(), registered_names(), SlowParser, StubParser, test_FR_PRS_030_fix_parser_classify_high_for_fix_line() (+6 more)

### Community 120 - "OpenAiCompatibleSlotFiller"
Cohesion: 0.13
Nodes (11): _JsonModeRejected, OpenAiCompatibleSlotFiller, on_message(), test_fill_slots_parses_json_without_auth_header(), run(), test_fill_slots_sends_bearer_when_api_key_set(), handler(), run() (+3 more)

### Community 121 - "make_snapshot"
Cohesion: 0.24
Nodes (10): _client_with_data(), test_UBS_68_http_query_returns_totals(), test_UBS_68_unknown_field_returns_400(), make_snapshot(), _engine(), _request(), test_UBS_68_application_filter_selects_instances(), test_UBS_68_group_by_reject_reason() (+2 more)

### Community 122 - "pipeline_demo.py"
Cohesion: 0.11
Nodes (14): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), run_happy_path(), run_slow_parser_backpressure(), DemoConfig (+6 more)

### Community 123 - "services/self_metrics.py"
Cohesion: 0.13
Nodes (4): _BoundSourcesCollector, _counter(), _gauge(), _utc_now()

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "test_QRY_04_concurrency.py"
Cohesion: 0.13
Nodes (12): _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another(), write_a(), test_concurrent_drops_across_many_instances_are_all_counted(), drop_one(), test_concurrent_merges_into_the_same_instance_do_not_lose_updates(), write(), test_concurrent_stale_rejections_across_many_instances_are_all_counted() (+4 more)

### Community 127 - "Rule Engine demo runbook"
Cohesion: 0.15
Nodes (12): 1. `make rules-test`, 2. `make rules-quickstart`, 3. `make rules-reload-demo`, Going deeper, if asked, If someone asks, Pre-flight, Rule Engine demo runbook, make rules-quickstart (17-act demo) (+4 more)

### Community 128 - "008 — Natural Language Query Layer (Copilot/Teams)"
Cohesion: 0.33
Nodes (5): Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents), NL Intent Catalogue (FR-NLQ-003/004), 008 — Natural Language Query Layer (Copilot/Teams)

### Community 129 - "LlmConfig"
Cohesion: 0.22
Nodes (16): ensure_nl_llm_credentials(), LlmConfig, NlConfig, resolve_llm_config(), build_llm_filler(), test_nl_query_enabled_returns_answer(), test_ensure_credentials_azure_requires_key(), test_ensure_credentials_compat_require_api_key() (+8 more)

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (3): Blocking CI sentinel test (FR-TST-005), Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "fields.py"
Cohesion: 0.15
Nodes (11): extract_allowlisted_fields(), FixFields, _hash_or_none(), _strip_sensitive_fields(), test_FR_PRS_020_end_to_end_excluded_tag_never_in_parse_result(), test_FR_PRS_020_excluded_tags_never_appear_in_output(), test_FR_PRS_020_fixed_struct_has_no_dict_no_map_allocation(), test_FR_PRS_020_missing_tags_default_to_none() (+3 more)

### Community 133 - "make_alert"
Cohesion: 0.21
Nodes (17): command_action(), make_alert(), write_script(), _runner(), test_a_command_that_overruns_its_timeout_is_killed(), test_a_missing_executable_is_an_error_not_a_crash(), test_a_non_zero_exit_is_counted_as_failed(), test_alert_json_goes_on_stdin_and_argv_is_exactly_the_config() (+9 more)

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 138 - "test_UBS_35_36_reload_and_draft.py"
Cohesion: 0.21
Nodes (16): _broken(), _Clock, _engine(), _evaluator(), _NullPublisher, _rules_yaml(), test_a_draft_rule_never_fires_in_the_running_engine(), test_a_good_reload_commits_the_staged_catalogue_after_the_rules() (+8 more)

### Community 143 - "PublishAction"
Cohesion: 0.30
Nodes (14): PublishAction, make_snapshot(), _FakeSink, _publisher(), test_202_commits_and_empties_buffer(), test_400_drops_the_whole_batch_as_one_rejection(), test_400_logs_once_across_repeated_rejections(), test_401_halts_alerts_and_probes_slowly_then_recovers() (+6 more)

### Community 145 - "AppLogParser"
Cohesion: 0.21
Nodes (5): AppLogParser, ReplayParsers, _meta(), test_applog_parser_classifies_and_parses_magic_line(), test_applog_parser_returns_none_confidence_for_fix_line()

### Community 157 - "Sponsor email — deployment and storage clarifications (Q-13)"
Cohesion: 0.40
Nodes (4): Our current design (for context), Our proposed alignment (pending your confirmation), Questions we'd like your help confirming, Sponsor email — deployment and storage clarifications (Q-13)

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (9): hb(), registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded(), test_one_stale_agent_is_partial() (+1 more)

### Community 160 - "telemetry_agent/main.py"
Cohesion: 0.06
Nodes (22): ActionType, DryRunCallbackSink, connect_reporter_to_publisher(), drop_hook(), heartbeat_provider(), build_agent(), check_action_secret(), stage_actions() (+14 more)

### Community 161 - "teams_agent/main.py"
Cohesion: 0.08
Nodes (9): register_handlers(), _number(), TeamsBotConfig, _authorize(), create_app(), main(), test_defaults_when_the_environment_is_empty(), test_invalid_values_fail_with_a_clear_message() (+1 more)

### Community 195 - "fix/normalize.py"
Cohesion: 0.28
Nodes (8): compile_reject_patterns(), match_reject_label(), normalize_reject_text(), RejectPattern, test_FR_PRS_022_cardinality_overflow(), test_FR_PRS_022_normalizes_digits_and_tokens(), test_FR_PRS_022_pattern_match(), test_FR_PRS_022_unclassified_increments_flag()

### Community 201 - "AlertStore"
Cohesion: 0.08
Nodes (30): AlertStoreConfig, AlertStore, _InstanceAlerts, _is_active_status(), _StoredAlert, AlertCounts, AlertDelivery, AlertRecord (+22 more)

### Community 207 - "QueryTimeRange"
Cohesion: 0.27
Nodes (8): QueryTimeRange, _engine(), _request(), test_UBS_91_max_range_seconds_returns_400(), test_UBS_91_max_series_points_returns_400(), test_UBS_91_query_timeout_returns_error(), _execute_sync(), test_UBS_91_response_includes_data_completeness()

### Community 210 - "backtest.py"
Cohesion: 0.11
Nodes (16): _app_log_time(), backtest(), tick(), BacktestReport, _DiscardRouter, _first_dated_time(), _first_time(), _fix_time() (+8 more)

### Community 212 - "parse_fix_timestamp"
Cohesion: 0.27
Nodes (5): parse_fix_timestamp(), TimestampResult, test_FR_PRS_025_bad_timestamp_falls_back_to_log(), test_FR_PRS_025_parses_fix_timestamp_utc(), test_FR_PRS_026_clock_skew_uses_agent_clock()

### Community 213 - "Implementation Status live document"
Cohesion: 0.17
Nodes (13): ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, Implementation Status live document, M1.5 Pipeline bridge (UBS-48/49), M1 Log monitor and configuration (not started) (+5 more)

### Community 214 - "_Harness"
Cohesion: 0.17
Nodes (4): _Harness, _orders(), _starts(), TestSnapshotEmitter

### Community 215 - "test_UBS_100_teams_bot_to_backend.py"
Cohesion: 0.40
Nodes (6): _ask(), _backend(), _card(), test_alert_question_shows_the_alert_badge_from_real_citations(), test_disabled_backend_renders_the_disabled_card(), test_rejection_question_renders_a_real_answer_card()

### Community 216 - "cards.py"
Cohesion: 0.17
Nodes (15): _alert_badge(), _breakdown(), _breakdown_rows(), build_answer_card(), build_clarification_card(), build_error_card(), _card(), _format_value() (+7 more)

### Community 217 - "UBS-49 — Pipeline Bridge Integration (live agent path)"
Cohesion: 0.18
Nodes (11): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Health Reporter (component), Health Reporter Heartbeat Requirement (FR-HLT-001), Backend Configuration and Secrets (§9), NFR-SEC-004: Secrets from Environment Only, Security: Secrets (§3.2) (+3 more)

### Community 219 - "test_reporter.py"
Cohesion: 0.61
Nodes (6): make_monitor(), test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 226 - "publishing/__init__.py"
Cohesion: 0.18
Nodes (7): BatchSequencer, build_batch(), PendingItem, test_batch_sequencer_seq_is_monotonic_and_ids_differ(), test_build_batch_envelope_fields(), test_build_batch_sorts_items_into_the_right_arrays(), test_build_batch_with_only_a_heartbeat_and_no_items()

### Community 234 - "heartbeat_json"
Cohesion: 0.08
Nodes (20): heartbeat_json(), provide(), to_ingestion_heartbeat(), FakeClock, test_buffer_bytes_is_none_without_a_provider(), test_buffer_bytes_is_read_fresh_on_every_snapshot(), test_buffer_bytes_provider_can_be_registered_and_removed(), test_dropped_events_accumulate_within_the_window() (+12 more)

### Community 268 - "snapshot_bridge.py"
Cohesion: 0.11
Nodes (11): build_snapshot(), SnapshotEmitter, _to_payload(), _to_wire_dimensions(), _aggregator(), _app_log_aggregator(), test_app_log_dimensions_survive_the_wire_allowlist(), test_build_snapshot_is_pure_and_repeatable() (+3 more)

### Community 270 - "Issue tracker: Jira"
Cohesion: 0.12
Nodes (13): graphify, Before exploring, read these, Domain Docs, File structure, Flag ADR and spec conflicts, Use the glossary's vocabulary, Conventions, Issue tracker: Jira (+5 more)

### Community 271 - "ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell"
Cohesion: 0.12
Nodes (15): callbacks: Callback Dispatcher config block, agent: identity config (id, instanceIds, version), CallbackFailing rule, ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell, Consequences, Context, Decision, Rationale (+7 more)

### Community 272 - "Metrics Query API (UBS-68, UBS-91, UBS-92)"
Cohesion: 0.22
Nodes (9): Code locations, Endpoint, Example request, Example response, Metric and dimension aliases, Metrics Query API (UBS-68, UBS-91, UBS-92), Multi-replica mode (UBS-92), Operational limits (UBS-91) (+1 more)

### Community 273 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (5): _CountingRing, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to(), test_read_indexes_only_the_requested_span_not_the_whole_ring(), test_restarted_bucket_count_also_indexes_only_the_requested_span()

### Community 274 - "test_UBS_36_backtest_cli.py"
Cohesion: 0.48
Nodes (3): _simulate(), test_a_draft_rule_replayed_over_simulator_logs(), _test_rule()

### Community 275 - ".__init__"
Cohesion: 0.18
Nodes (3): on_drop(), _on_buffer_drop(), PublishSink

### Community 276 - "test_STM_03_warmup.py"
Cohesion: 0.33
Nodes (6): _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up(), test_data_from_a_restarted_bucket_is_still_merged_not_dropped(), test_restarted_bucket_count_reflects_only_buckets_a_restart_touched(), test_restarted_bucket_marks_the_instance_warming_up_for_the_warmup_window()

### Community 277 - "time.py"
Cohesion: 0.27
Nodes (9): _local_midnight(), _parse_relative_duration(), _parse_short_datetime(), parse_time_expression(), _relative_from_amount(), _this_morning_start(), TimeParseResult, test_last_30_minutes_is_explicit() (+1 more)

### Community 279 - "test_health_monitor_e2e.py"
Cohesion: 0.11
Nodes (8): committed_offsets(), FakeClock, fix_lines(), RecordingTransport, Stack, test_no_lines_are_lost_across_a_simulator_rotation(), test_simulator_logs_reach_the_backend_health_api(), write_lines()

### Community 280 - "test_ingestion.py"
Cohesion: 0.15
Nodes (19): BatchAccepted, EventsRequest, TelemetryBatch, SeriesEntry, _batch(), _endpoint(), _event(), _request() (+11 more)

### Community 281 - "test_log_monitor_status.py"
Cohesion: 0.62
Nodes (5): make_monitor(), test_status_after_read_reports_elapsed_lag(), test_status_before_any_read_has_no_lag(), test_status_missing_file_has_no_size_but_does_not_raise(), test_status_reports_offset_progress_between_polls()

### Community 282 - "SeqTracker"
Cohesion: 0.29
Nodes (5): SeqTracker, SeqGapEvent, test_FR_PRS_027_detects_gap(), test_FR_PRS_027_detects_regression(), test_FR_PRS_027_logon_resets_without_gap()

### Community 283 - "_run"
Cohesion: 0.38
Nodes (5): _banner(), _instructions(), main(), _run(), _safe_rule_count()

### Community 285 - "Teams bot"
Cohesion: 0.18
Nodes (9): Configuration, Questions to try, Real Teams (later, not tested against a real tenant), Run it locally (5 terminals, all from the repo root), Teams bot, ADR 0009 — Build the Teams bot on the Microsoft 365 Agents SDK, Consequences, Context (+1 more)

### Community 286 - "_error_card_text"
Cohesion: 0.22
Nodes (9): _error_card_text(), test_bad_request_gets_a_rephrase_card(), test_connection_failure_hides_the_exception_text(), test_disabled_nl_gets_a_clear_card(), test_gateway_timeout_gets_the_try_again_card(), test_server_error_says_the_service_is_unreachable_without_internals(), test_timeout_gets_a_try_again_card(), boom() (+1 more)

### Community 287 - "UBS-100 — Teams bot with Adaptive Card answers (spec)"
Cohesion: 0.20
Nodes (9): As Built, Further Notes, Implementation Decisions, Out of Scope, Problem Statement, Solution, Testing Decisions, UBS-100 — Teams bot with Adaptive Card answers (spec) (+1 more)

### Community 288 - "HeartbeatEmitter"
Cohesion: 0.29
Nodes (7): heartbeat: interval config, BufferingHeartbeatSink, HeartbeatEmitter, heartbeat_json() serialisation helper, HeartbeatSink callable seam, HttpHeartbeatSink, telemetry-agent-heartbeat demo entrypoint

### Community 289 - "telemetry_agent_rules_engine"
Cohesion: 0.31
Nodes (6): _counter_rule(), test_dependent_suppression_when_no_log_activity_is_firing(), test_max_active_alerts_emits_one_alertstorm_and_suppresses_further(), test_schedule_inactive_skips_rule_entirely(), test_silence_suppresses_notification_but_still_tracks_state(), test_storm_clears_once_under_cap_and_the_suppressed_rule_fires()

### Community 290 - "effective_reject_reason"
Cohesion: 0.33
Nodes (5): effective_reject_reason(), test_FR_PRS_024_ord_rej_reason_wins(), test_FR_PRS_024_session_reject_for_msg_type_reject(), test_FR_PRS_024_text_label_when_no_ord_rej(), test_FR_PRS_024_unspecified_when_missing()

### Community 291 - "signing.py"
Cohesion: 0.16
Nodes (3): _burst(), test_the_agent_process_alerts_magic_and_the_backend(), scenario()

### Community 292 - "test_UBS_116_app_log_ingest.py"
Cohesion: 0.39
Nodes (5): _ingested(), _meta(), test_app_log_counts_appear_in_the_snapshot(), test_app_log_counts_group_by_signature_level_and_component(), test_fix_metrics_do_not_appear_for_app_log_lines()

### Community 293 - "classify_publish_response"
Cohesion: 0.38
Nodes (5): classify_publish_response(), PublishOutcome, test_429_carries_retry_after_seconds(), test_status_code_classification(), test_transport_error_is_backoff()

### Community 296 - "test_UBS_123_snapshot_emitter.py"
Cohesion: 0.48
Nodes (3): _build(), test_build_agent_logs_emitter_skips_with_the_evaluator_counters(), test_build_agent_rejects_a_bucket_longer_than_retention_allows()

### Community 297 - "Rule Engine"
Cohesion: 0.16
Nodes (15): NoLogActivity rule, HeartbeatConfig / HealthThresholds / load_health_config, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, rules.config_loader (FR-RUL-008/009), Rule Engine, Safety and suppression (silences, grace, storm cap) (+7 more)

### Community 301 - "health-reporter-overview.md"
Cohesion: 0.40
Nodes (3): Not in this change, Open points for the team, UBS-69 / UBS-85 / UBS-96 — decisions and open points

### Community 302 - "_run_scenario"
Cohesion: 0.40
Nodes (4): _make_alert(), _make_snapshot(), _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher()

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **241 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `IntentDefinition`, `_IntentPattern`, `telemetry-simulator` (+236 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1640 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **130 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `Implementation Status live document` to `AggregatorConfig`, `config/rules.yaml live rule set`, `Rule Engine`, `MetricsAggregator ring buffer`, `AgentHeartbeat wire contract`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `Telemetry System Documentation Index` connect `Telemetry System Documentation Index` to `ADR 0004: Raw log content is never persisted or transmitted`, `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1`, `Telemetry Agent (architecture constraint)`, `ADR 0001: Telemetry Agent written in Go (Superseded)`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `Spec 004: Telemetry data model` connect `Telemetry Agent (architecture constraint)` to `Telemetry System Documentation Index`, `ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 81 INFERRED edges - model-reasoned connections that need verification._