# Graph Report - avengers-fyp-is484  (2026-11-03)

## Corpus Check
- 449 files · ~236,503 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 11, .toml 1, .example 1)

## Summary
- 5714 nodes · 16753 edges · 248 communities (180 shown, 68 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 3472 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `049098cc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- asyncio
- frame.py
- test_metrics_event.py
- RuleConfig
- make_snapshot
- test_FR_CBK_013_action_config.py
- HealthReporter
- AppLogParser
- RetryPolicy
- LatencyCorrelator
- test_MA_02_counters.py
- test_RE_publish_integration.py
- AgentHeartbeat
- LogMonitor
- PublishBuffer
- supervisor.py
- test_openai_compatible.py
- SourceMeta
- MetricsAggregator
- EventStore
- make_alert
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- test_bot_replies.py
- PipelineBridge
- agent.yaml
- telemetry_agent/main.py
- DeliveryTracker
- health/config.py
- test_MA_05_agent_counters.py
- FakeClock
- load_backend_health_config
- test_UBS_113_evaluator.py
- test_MA_03_correlation.py
- test_health_monitor_e2e.py
- config/rules.yaml live rule set
- telemetry_backend/main.py
- rule_matcher.py
- Implementation Status live document
- rules
- MetricsIngestor
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- TelemetryBackend
- heartbeat_json
- CallbackResult
- test_UBS_35_36_reload_and_draft.py
- display.py
- cli.py
- Parser
- parse_publish_config
- QueryEngine
- Histogram
- LineClassification
- from_alert_event
- test_RE_session_integration.py
- AlertEvent
- Confidence
- test_queue_depth.py
- RuleEvaluator
- service.py
- demo.py
- enrich.py
- test_UBS_117_events.py
- rules/demo_quickstart.py
- Telemetry Agent (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- DropOldestQueue
- test_agent_registry.py
- SignatureMatcher
- 009 — Non-Functional Requirements and Security
- callbacks
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- test_UBS_36_backtest_cli.py
- pipeline_demo.py
- .reload
- publish
- services/demo_quickstart.py
- AlertStore
- End-to-End Acceptance Scenario (FR-TST-010)
- test_FR_PUB_002_compression.py
- test_ING_004_008_routes.py
- .merge
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- llm
- pathlib
- hooks
- StreamProcessorConfig
- test_STM_04_efficiency.py
- pytest
- parsing
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- telemetry_backend/config.py
- BackendPublisher
- UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- cards.py
- Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)
- backtest.py
- test_real_snapshot_output_drives_the_rule_engine_correctly
- manifest.json
- telemetry_shared shared schema package
- parse_callbacks_config
- test_tools.py
- AggregatorConfig
- test_UBS_115_snapshot_to_metricstore.py
- _publish_and_drain
- test_UBS_27_reject_reason_trends.py
- time
- AgentRegistry
- snapshot_bridge.py
- Requirement ID Scheme (FR-<AREA>-<NNN>)
- ADR 0004: Raw log content is never persisted or transmitted
- services/self_metrics.py
- DryRunCallbackSink
- snapshot
- ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server
- Spec 005 — Rule Engine, Alerting and Callbacks
- test_UBS_100_teams_bot_to_backend.py
- Monitor to parser bridge (bounded line queue + parser worker pool)
- datetime
- healthcheck
- telemetry-shared
- _error_card_text
- .markdownlint-cli2.yaml
- _stepping_clock
- GLOSSARY.md
- Auditability & Compliance rationale (deterministic order audit trails)
- test_UBS_122_signature_rules.py
- PublishResult
- ADR 0002: Backend in Python/FastAPI
- ADR 0003: HTTPS/JSON Transport Day-1
- ADR 0005: In-Memory Metric Store
- ADR 0006: Agent in Python
- Parser Test Obligations (§10)
- Message Validation and Parse Error Reason Codes (FR-PRS-017–019)
- Data Completeness Block (FR-QRY-015)
- Backend Health and Self-Metrics (FR-HLT-010)
- test_data_completeness.py
- TeamsBotConfig
- nl_query.py
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
- _dispatch
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- render_answer
- ingest.py
- time.py
- baseline.py
- _RuleYaml
- classify_http_status
- NlQueryService
- build_agent
- test_UBS_25_29_anomaly.py
- Project instructions
- Metrics Query API (UBS-68, UBS-91, UBS-92)
- _Clock
- test_reporter.py
- Rule Engine demo runbook
- test_RE_02_evaluators.py
- publishing/__init__.py
- Teams bot
- Agent
- _aggregator_with_a_reject_burst
- factory.py
- test_ollama_native.py
- load_agent_config
- UBS-100 — Teams bot with Adaptive Card answers (spec)
- LlmConfig
- health-reporter-overview.md
- NlQueryContext
- metrics_query.py
- ActionRunner
- text_blocks
- PipelineStats
- build.sh
- RuleConfigError
- to_ingestion_heartbeat
- sign
- test_reply_guard.py
- CallbackDispatcher
- test_RE_parse_error_integration.py
- telemetry_agent/config.py
- MetricsQueryResponse
- NL query manual test plan: Ollama, Teams and Copilot (MCP)
- test_STM_03_warmup.py
- MultiLogMonitor

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

## Communities (248 total, 68 thin omitted)

### Community 0 - "asyncio"
Cohesion: 0.05
Nodes (49): BatchAccepted, _counts(), create_app(), enqueue_or_full(), ingest_batch(), ingest_events(), ingest_heartbeat(), validate_or_reject() (+41 more)

### Community 1 - "frame.py"
Cohesion: 0.08
Nodes (26): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+18 more)

### Community 2 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (27): _meta(), _parse(), _parser_counters(), _session_counters(), test_a_clean_fix_line_is_not_a_parse_error(), test_clean_line_reports_no_reason(), test_every_derived_session_counter_is_declared_in_counter_dimensions(), test_every_line_counts_toward_log_lines_read() (+19 more)

### Community 3 - "RuleConfig"
Cohesion: 0.08
Nodes (24): validate_anomaly_rule(), _tier(), _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _matched_tier() (+16 more)

### Community 4 - "make_snapshot"
Cohesion: 0.13
Nodes (31): Gauges, make_gauges(), make_indicator(), make_indicators(), make_snapshot(), _counter_rule(), test_dependent_suppression_when_no_log_activity_is_firing(), test_max_active_alerts_emits_one_alertstorm_and_suppresses_further() (+23 more)

### Community 5 - "test_FR_CBK_013_action_config.py"
Cohesion: 0.11
Nodes (21): ActionConfigError, _ActionYaml, _command_key(), _is_rooted(), load_action_catalogue(), _parse_action(), parse_actions(), parse_allowed_commands() (+13 more)

### Community 6 - "HealthReporter"
Cohesion: 0.08
Nodes (16): HealthThresholds, HealthReporter, HealthSignals, _utc_now(), 3. UBS-30 — read lag (the foundation), 4.3 Rollup and payload — `health/reporter.py`, Design points, Module map (`apps/agent/src/telemetry_agent/health/`) (+8 more)

### Community 7 - "AppLogParser"
Cohesion: 0.16
Nodes (10): AppLogParser, AppLogTelemetry, _meta(), test_applog_parser_classifies_and_parses_magic_line(), test_applog_parser_returns_none_confidence_for_fix_line(), _ingested(), _meta(), test_app_log_counts_appear_in_the_snapshot() (+2 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.07
Nodes (23): RetryPolicy, format_fix_line(), generate_application_log(), generate_fix_order_messages(), get_timestamps(), rotate_if_needed(), run_harness(), test_FR_CBK_004_delay_doubles_per_attempt_with_factor_2() (+15 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.07
Nodes (12): CorrelatorStats, LatencyCorrelator, OrderContext, _timedelta_to_ms(), main(), ingest(), _step(), _build_gauges() (+4 more)

### Community 10 - "test_MA_02_counters.py"
Cohesion: 0.15
Nodes (21): ReasonNormalizer, build_aggregator(), _exec_report_event(), ingest_fixture(), _reject_event(), test_business_cancel_and_session_rejects_stay_separate_but_sum_to_total(), test_counts_match_the_hand_labelled_fixture(), test_every_counter_is_broken_down_by_symbol() (+13 more)

### Community 11 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (15): _aggregator(), _engine(), _fail_n_times(), _publisher(), _rule(), _ScriptedSink, _snapshot_payload(), test_a_full_minute_of_outage_yields_exactly_five_failures() (+7 more)

### Community 12 - "AgentHeartbeat"
Cohesion: 0.07
Nodes (19): HeartbeatEmitter, LoggingHeartbeatSink, PrintHeartbeatSink, 4.4 Emitter and sinks — `health/heartbeat.py`, AgentHeartbeat, Collect, FakeClock, _reporter() (+11 more)

### Community 13 - "LogMonitor"
Cohesion: 0.05
Nodes (21): Harvester, LogMonitor, _open_shared(), ReadLine, OffsetTracker, test_degraded_status_flows_into_heartbeat_payload(), test_health_reporter_handles_truncation(), test_health_reporter_survives_log_rotation() (+13 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (22): make_pending_item(), PendingItem, PublishBuffer, _size_of(), _item(), _tags(), test_an_item_larger_than_the_whole_cap_is_not_self_evicted(), test_append_and_take_preserve_fifo_order() (+14 more)

### Community 15 - "supervisor.py"
Cohesion: 0.06
Nodes (16): QueueSnapshot, PipelineCommitter, LinePosition, ProcessedLineDeduper, EventQueue, LineQueue, ParsedEvent, QueuedLine (+8 more)

### Community 16 - "test_openai_compatible.py"
Cohesion: 0.19
Nodes (9): config(), test_fill_slots_coerces_ollama_time_range_shape(), run(), test_fill_slots_sends_bearer_when_api_key_set(), handler(), run(), test_json_mode_rejected_retries_without_response_format(), run() (+1 more)

### Community 17 - "SourceMeta"
Cohesion: 0.07
Nodes (28): is_parse_error(), extract_allowlisted_fields(), FixFields, _hash_or_none(), FrameResult, FixParser, _strip_sensitive_fields(), ParseError (+20 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.13
Nodes (4): _Bucket, _dimension_value(), MetricRow, MetricsAggregator

### Community 19 - "EventStore"
Cohesion: 0.11
Nodes (15): EventStoreConfig, EventStore, _InstanceEvents, TelemetryEvent, _app_with_store(), test_UBS_118_missing_event_returns_404(), test_UBS_118_unknown_query_param_returns_400(), make_telemetry_event() (+7 more)

### Community 20 - "make_alert"
Cohesion: 0.14
Nodes (24): callback_action(), command_action(), make_alert(), write_script(), _runner(), test_a_command_that_overruns_its_timeout_is_killed(), test_a_missing_executable_is_an_error_not_a_crash(), test_a_non_zero_exit_is_counted_as_failed() (+16 more)

### Community 21 - "MetricStore"
Cohesion: 0.07
Nodes (14): _CanonicalBucket, MetricStore, _snapshot(), test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell(), test_estimated_memory_bytes_grows_with_merged_series_and_shrinks_on_eviction(), test_estimated_memory_bytes_is_zero_for_an_empty_store(), test_merge_alone_can_trigger_shedding_without_an_external_tick(), test_merges_within_the_throttle_interval_do_not_re_check_memory() (+6 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.06
Nodes (37): Open Questions and Decisions Required, Callback Dispatcher, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent, Q-2 — Callback Protocol Magic Will Support (+29 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.14
Nodes (22): _key(), _keys(), _observe(), test_a_clean_logout_never_times_out(), test_a_session_relogging_on_after_logout_is_tracked_again(), test_a_session_still_speaking_never_times_out(), test_a_session_that_recovers_can_time_out_again(), test_both_directions_share_one_dimension_id() (+14 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (26): health: threshold config block, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry, HeartbeatConfig / HealthThresholds / load_health_config (+18 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (28): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+20 more)

### Community 26 - "test_bot_replies.py"
Cohesion: 0.20
Nodes (37): QueryGroup, NlCitation, answer(), converse(), group(), json_ok(), message(), texts() (+29 more)

### Community 27 - "PipelineBridge"
Cohesion: 0.08
Nodes (21): _build_bridge(), _pump(), Registry, PipelineConfig, MonitorPipelineAdapter, monitors_by_resolved_path(), source_meta_from_read_line(), PipelineBridge (+13 more)

### Community 28 - "agent.yaml"
Cohesion: 0.06
Nodes (32): actions, allowedCommands, agent, id, instanceIds, version, label, match (+24 more)

### Community 29 - "telemetry_agent/main.py"
Cohesion: 0.09
Nodes (11): ActionType, AgentConfig, _build_parser(), _install_signals(), main(), _main_async(), run_agent(), _shutdown() (+3 more)

### Community 30 - "DeliveryTracker"
Cohesion: 0.08
Nodes (27): alert_delivery_from_record(), enrich_alert_delivery(), DeliveryRecord, DeliveryStatus, DeliveryTracker, notification_key(), test_enrich_alert_delivery_leaves_an_untracked_alert_alone(), test_enrich_alert_delivery_maps_tracker_state() (+19 more)

### Community 31 - "health/config.py"
Cohesion: 0.10
Nodes (21): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, HeartbeatConfig, _HeartbeatYaml, load_health_config() (+13 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.17
Nodes (16): AgentCounterSampler, _aggregator(), test_agent_counters_group_by_instance_only(), test_deltas_land_in_the_bucket_for_their_own_timestamp(), test_first_sample_ingests_the_whole_count_from_zero(), test_ingest_agent_counters_does_not_mark_the_agent_as_having_seen_an_event(), test_ingest_agent_counters_lands_in_the_window(), test_missing_declared_dimension_raises_naming_the_dimension() (+8 more)

### Community 33 - "FakeClock"
Cohesion: 0.24
Nodes (16): FakeClock, make_event(), minimal_aggregator(), test_10k_events_in_60s_window_returns_correct_count(), test_cardinality_cap_folds_overflow_into_other_and_preserves_total(), test_cardinality_cap_resets_per_bucket_not_for_process_lifetime(), test_cardinality_folded_counts_every_fold_from_either_cap(), test_group_by_multiple_dimensions_respects_the_requested_order() (+8 more)

### Community 34 - "load_backend_health_config"
Cohesion: 0.05
Nodes (39): _AlertingYaml, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestGuardConfig, _IngestYaml, _Lenient (+31 more)

### Community 35 - "test_UBS_113_evaluator.py"
Cohesion: 0.08
Nodes (27): _names(), _NullCallbackSink, _rule(), _Stack, _StatusSink, test_a_cleared_condition_resolves_on_both_paths(), test_a_counter_rule_fires_and_reaches_both_paths(), test_a_rejected_reload_routes_nothing_and_keeps_the_rules() (+19 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (22): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), replaced() (+14 more)

### Community 37 - "test_health_monitor_e2e.py"
Cohesion: 0.12
Nodes (8): committed_offsets(), FakeClock, fix_lines(), RecordingTransport, Stack, test_no_lines_are_lost_across_a_simulator_rotation(), test_simulator_logs_reach_the_backend_health_api(), write_lines()

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.12
Nodes (19): Agent processing pipeline (monitor to health reporter), BackendUnreachable rule, CallbackFailing rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule (+11 more)

### Community 39 - "telemetry_backend/main.py"
Cohesion: 0.04
Nodes (47): AlertsQueryParams, get_alert(), get_event(), ingestion_body(), invalid_payload(), list_alerts(), list_events(), nl_intents() (+39 more)

### Community 40 - "rule_matcher.py"
Cohesion: 0.12
Nodes (17): build_default_filters(), default_time_range(), IntentDefinition, _merge_group_by(), merge_interpreted_query(), _merge_metrics(), _merge_step(), _extract_filters() (+9 more)

### Community 41 - "Implementation Status live document"
Cohesion: 0.08
Nodes (31): AckLatencyBreach rule, ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, Implementation Status live document, M1.5 Pipeline bridge (UBS-48/49) (+23 more)

### Community 42 - "rules"
Cohesion: 0.08
Nodes (25): actions, args, command, dryRun, name, timeout, type, rules (+17 more)

### Community 43 - "MetricsIngestor"
Cohesion: 0.18
Nodes (14): MetricsIngestor, _counters(), _feed(), _ingestor(), _meta(), _reporter(), test_a_failing_component_never_escapes_and_is_counted(), test_a_hard_parse_error_counts_for_aggregator_and_reporter() (+6 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (16): bad(), FakeClock, make(), ok(), test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides(), test_errors_counted_and_reported_in_heartbeat(), test_parse_fields_are_none_until_a_producer_reports() (+8 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.13
Nodes (11): SlidingWindowCounter, at(), test_capacity_is_rounded_not_floored(), test_counts_events_inside_window(), test_decays_as_window_slides(), test_event_older_than_window_is_dropped(), test_idle_window_reads_zero_not_none(), test_late_event_still_inside_window_is_counted() (+3 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.11
Nodes (21): Problem P-1: Limited visibility into live trading activity and health, Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), 001 — Architecture, Ingestion Service (component), Log Monitor (component), Metric Store (component) (+13 more)

### Community 47 - "TelemetryBackend"
Cohesion: 0.19
Nodes (7): _answer_result(), _clarification_result(), _error_kind(), error_result(), _path(), TelemetryBackend, NlQueryRequest

### Community 48 - "heartbeat_json"
Cohesion: 0.13
Nodes (10): heartbeat_json(), FakeClock, test_buffer_bytes_is_none_without_a_provider(), test_buffer_bytes_is_read_fresh_on_every_snapshot(), test_buffer_bytes_provider_can_be_registered_and_removed(), test_dropped_events_accumulate_within_the_window(), test_dropped_events_is_none_until_the_first_record(), test_dropped_events_reach_the_wire() (+2 more)

### Community 49 - "CallbackResult"
Cohesion: 0.11
Nodes (7): _ScriptedSink, CallbackResult, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink, _SlowFiringSink, test_a_retrying_firing_callback_does_not_share_state_with_resolved()

### Community 50 - "test_UBS_35_36_reload_and_draft.py"
Cohesion: 0.19
Nodes (17): RuleState, _broken(), _Clock, _engine(), _evaluator(), _NullPublisher, _rules_yaml(), test_a_draft_rule_never_fires_in_the_running_engine() (+9 more)

### Community 51 - "display.py"
Cohesion: 0.23
Nodes (16): _box_title(), _delimiter_label(), _explain_classification(), _format_field_row(), _hr(), print_demo_header(), print_demo_summary(), _render_applog() (+8 more)

### Community 52 - "cli.py"
Cohesion: 0.13
Nodes (17): DemoMetricsSink, extract_log_level(), _corpus_files(), _fields_dict(), _format_line_result(), _load_config(), main(), _parse_line() (+9 more)

### Community 53 - "Parser"
Cohesion: 0.10
Nodes (6): Parser, get_parser(), register_parser(), test_FR_PRS_031_validate_chain_reports_unknown_parsers(), test_FR_PRS_032_duplicate_registration_raises(), test_FR_PRS_032_register_parser_at_import_time()

### Community 54 - "parse_publish_config"
Cohesion: 0.13
Nodes (18): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfigError, test_allows_plain_http_when_explicitly_opted_in(), test_buffer_bytes_must_be_positive(), test_defaults_match_spec_010(), test_load_publish_config_invalid_yaml_raises() (+10 more)

### Community 55 - "QueryEngine"
Cohesion: 0.09
Nodes (12): _AccumulatedGroup, QueryEngine, QueryValidationError, MetricsGroup, EffectiveTimeRange, MetricsQueryRequest, QueryInterpretation, SeriesPoint (+4 more)

### Community 56 - "Histogram"
Cohesion: 0.10
Nodes (14): Histogram, build_latency_summary(), compute_indicators(), compute_ratio(), RatioDef, Indicator, Indicators, LatencySummary (+6 more)

### Community 57 - "LineClassification"
Cohesion: 0.13
Nodes (14): classify_line(), compile_app_log_patterns(), _looks_like_fix(), LineClassification, test_FR_PRS_010_fix_detected_pipe_delimited(), test_FR_PRS_010_fix_detected_soh_delimited(), test_FR_PRS_010_fix_detected_with_log_prefix(), test_FR_PRS_010_rejects_begin_string_without_delimiter_before_msg_type() (+6 more)

### Community 58 - "from_alert_event"
Cohesion: 0.18
Nodes (9): CallbackAlertPayload, from_alert_event(), deliver(), make_alert_event(), test_FR_CBK_001_payload_carries_ac_required_fields(), test_FR_CBK_002_payload_under_max_bytes_for_typical_alert(), test_FR_CBK_002_serialized_payload_matches_spec_shape(), test_FR_CBK_003_runbook_url_defaults_to_none() (+1 more)

### Community 59 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (17): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), _rule(), test_a_clean_logout_does_not_also_produce_a_timeout(), test_fix_session_down_fires_on_a_heartbeat_timeout_alone() (+9 more)

### Community 60 - "AlertEvent"
Cohesion: 0.09
Nodes (11): AlertRouter, drive(), AlertEvent, _Agent, _signature_alerts(), test_app_log_lines_keep_no_log_activity_quiet_end_to_end(), test_shipped_signature_rules_fire_on_their_own_patterns_only(), _ExplodingRunner (+3 more)

### Community 61 - "Confidence"
Cohesion: 0.09
Nodes (20): looks_like_magic_binary(), MagicBinaryParser, Confidence, SlowParser, StubParser, test_FR_PRS_030_fix_parser_classify_high_for_fix_line(), test_FR_PRS_030_fix_parser_classify_none_for_garbage(), test_FR_PRS_031_chain_selects_first_high_confidence() (+12 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.11
Nodes (19): BufferingHeartbeatSink, Missing downstream / upstream (what this branch cannot prove), FakeQueue, Flaky, make(), test_at_critical_watermark_is_unhealthy(), test_at_high_watermark_is_degraded_with_reason_and_trend(), test_below_high_watermark_is_healthy() (+11 more)

### Community 63 - "RuleEvaluator"
Cohesion: 0.06
Nodes (10): CounterRegistry, RuleEvaluator, _utc_now(), EventEmitter, Implemented in this change, allowed_event_fields(), test_callbacks_shim_is_the_same_class(), test_increment_starts_at_zero_and_accumulates() (+2 more)

### Community 64 - "service.py"
Cohesion: 0.15
Nodes (16): catalogue_summary_for_prompt(), normalize_question(), greeting_message(), help_message(), llm_unavailable_message(), out_of_scope_message(), suggested_questions(), thanks_message() (+8 more)

### Community 65 - "demo.py"
Cohesion: 0.10
Nodes (25): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), _derive_execution_report_counters(), _derive_fill_split(), top_reject_reasons(), _banner(), _implementation() (+17 more)

### Community 66 - "enrich.py"
Cohesion: 0.08
Nodes (31): build_fix_telemetry(), normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type(), normalize_session_reject_reason() (+23 more)

### Community 67 - "test_UBS_117_events.py"
Cohesion: 0.09
Nodes (22): _burst(), scenario(), parse(), app(), meta(), sent(), Sink, stack() (+14 more)

### Community 68 - "rules/demo_quickstart.py"
Cohesion: 0.05
Nodes (11): SessionHeartbeatTracker, _SessionState, _alert_storm_act(), _dedup_act(), _Demo, _heartbeat_timeout_act(), main(), _no_log_activity_act() (+3 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.13
Nodes (8): Magic simulator for development, Unified Telemetry Intelligence (Magic), agent: identity config (id, instanceIds, version), Spec 004: Telemetry data model, Agent self counters (§4.3), Identity fields (§1), Callback dispatch requirements (§3.1), Callback payload and CallbackSink seam (§3.3)

### Community 70 - "AppDeps"
Cohesion: 0.12
Nodes (19): healthz(), metrics(), readyz(), AppDeps, get_deps(), env(), FakeClock, heartbeat() (+11 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.10
Nodes (4): BoundedQueue, test_block_policy_waits_for_capacity(), test_drop_oldest_policy_discards_oldest_on_overflow(), test_zero_capacity_rejects_without_storing()

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (15): env(), FakeClock, heartbeat(), post_heartbeat(), test_decommissioned_agent_leaves_the_exposition(), test_healthz_is_liveness_only(), test_heartbeats_do_not_count_as_data_for_warmup(), test_metrics_exposition_is_prometheus_text() (+7 more)

### Community 73 - "DropOldestQueue"
Cohesion: 0.18
Nodes (4): DropOldestQueue, test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped(), test_FR_CBK_007_overflow_drops_oldest_and_increments_counter()

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (12): FakeClock, hb(), make(), test_agent_clock_stepped_backwards_does_not_go_missing(), test_explicit_received_at_overrides_clock(), test_first_contact_is_reported_once(), test_late_older_heartbeat_keeps_newer_doc_but_refreshes_liveness(), test_missing_after_threshold_measured_on_backend_clock() (+4 more)

### Community 75 - "SignatureMatcher"
Cohesion: 0.22
Nodes (10): compile_signature_rules(), resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule, test_cardinality_overflow_to_other(), test_dynamic_label_gr_disconnect(), test_dynamic_label_md_disconnect() (+2 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.14
Nodes (16): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), Resource Discipline (§9), Compliance and Operability Constraints (§7), 009 — Non-Functional Requirements and Security, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-REL-003: Backend Outage Must Not Affect Alerting, NFR-SCA-001: Agent Independence/Statelessness (+8 more)

### Community 77 - "callbacks"
Cohesion: 0.14
Nodes (17): callbacks, allowInsecureCallback, connectTimeout, dryRun, enabled, endpoint, maxAttempts, maxBytes (+9 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.20
Nodes (11): SighupRuleReloader, _engine(), _fire(), _snapshot(), test_apply_rules_force_resolves_a_firing_alert_whose_rule_was_removed(), test_apply_rules_leaves_unrelated_rules_untouched(), test_apply_rules_preserves_state_for_a_rule_whose_name_persists(), test_apply_rules_removes_a_pending_state_without_an_event() (+3 more)

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

### Community 83 - "pipeline_demo.py"
Cohesion: 0.11
Nodes (18): _build_registry(), _load_config(), main(), _print_stage(), run_happy_path(), run_slow_parser_backpressure(), DemoConfig, _label_match_pairs() (+10 more)

### Community 85 - "publish"
Cohesion: 0.15
Nodes (13): publish, allowInsecureEndpoint, bufferBytes, bufferMaxAge, compressThreshold, connectTimeout, dryRun, enabled (+5 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (9): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), _reject(), _run_hong_kong_session(), _run_singapore_session() (+1 more)

### Community 87 - "AlertStore"
Cohesion: 0.10
Nodes (26): AlertStoreConfig, AlertStore, _InstanceAlerts, _is_active_status(), _StoredAlert, test_alert_status_answer_includes_callback_delivery(), _app_with_store(), test_UBS_94_batch_ingestion_makes_alerts_queryable() (+18 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.12
Nodes (12): Open Questions Document (plan/open-questions.md), Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025), NFR-SEC-015: Canonicalised Allowed Roots, Symlinks Refused, Security: Input Handling (§3.4), Agent Configuration Schema (§1) (+4 more)

### Community 89 - "test_FR_PUB_002_compression.py"
Cohesion: 0.19
Nodes (9): _maybe_gzip(), _parse_retry_after(), test_allows_plain_http_when_explicitly_opted_in(), test_body_over_threshold_is_gzipped_and_round_trips(), test_body_under_threshold_is_not_compressed(), test_rejects_plain_http_by_default(), test_sink_does_not_gzip_small_bodies(), test_sink_sets_content_encoding_header_when_gzipped() (+1 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (7): batch(), deps(), FakeClock, metrics(), test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once(), test_batches_past_the_per_agent_limit_get_429_with_retry_after()

### Community 91 - ".merge"
Cohesion: 0.14
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

### Community 95 - "pathlib"
Cohesion: 0.08
Nodes (11): FileReadStatus, 7. Status rollup — the one table, _now_sending_time(), FakeClock, test_heartbeat_provider_output_is_accepted_in_a_batch(), test_unknown_agent_is_404(), make_monitor(), test_status_after_read_reports_elapsed_lag() (+3 more)

### Community 96 - "hooks"
Cohesion: 0.15
Nodes (12): exclude, additional_dependencies, args, entry, id, language, name, types_or (+4 more)

### Community 97 - "StreamProcessorConfig"
Cohesion: 0.07
Nodes (29): StreamProcessorConfig, align_to_canonical(), SnapshotOutcome, StreamProcessor, on_message(), Decisions, test_merging_the_same_snapshot_twice_does_not_double_the_counters(), merge_snapshot() (+21 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (5): _CountingRing, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to(), test_read_indexes_only_the_requested_span_not_the_whole_ring(), test_restarted_bucket_count_also_indexes_only_the_requested_span()

### Community 99 - "pytest"
Cohesion: 0.09
Nodes (27): default_resolve_reject_reason(), CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent (+19 more)

### Community 100 - "parsing"
Cohesion: 0.17
Nodes (11): appLogPatterns, label, match, parsing, errorSignatures, maxClockSkew, maxDynamicSignatureLabels, maxRejectReasonLabels (+3 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.15
Nodes (12): hash_identifier(), load_hash_key(), test_FR_PRS_021_different_input_produces_different_hash(), test_FR_PRS_021_different_key_produces_different_hash(), test_FR_PRS_021_extracted_fields_carry_hashes_not_plaintext(), test_FR_PRS_021_load_hash_key_fails_fast_when_empty(), test_FR_PRS_021_load_hash_key_fails_fast_when_unset(), test_FR_PRS_021_load_hash_key_reads_env_var() (+4 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (11): _engine(), _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved(), test_pending_fires_after_for_elapsed(), test_pending_reverts_to_inactive_if_condition_clears_before_for_elapsed() (+3 more)

### Community 103 - "telemetry_backend/config.py"
Cohesion: 0.05
Nodes (28): IngestionConfig, _utc_now(), IngestionValidationIssue, _safe_key(), test_nl_query_disabled_returns_503(), test_nl_query_enabled_returns_answer(), _client_with_data(), test_UBS_68_http_query_returns_totals() (+20 more)

### Community 104 - "BackendPublisher"
Cohesion: 0.10
Nodes (18): _drain(), main(), _make_snapshot(), _print_state(), _step(), BackendPublisher, _backend_unreachable_act(), attempt() (+10 more)

### Community 105 - "UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth"
Cohesion: 0.12
Nodes (8): 6. UBS-60 — publish queue depth, Also touched, and why, How to see it, Placeholder receiver — `scripts/heartbeat_receiver_stub.py`, Ticket vs. spec decisions (read first — these need team sign-off), UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth, UBS-60: publish queue depth, Wire compatibility with UBS-66 (decided 2026-09-22 — revisit)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.12
Nodes (21): _alert(), _publisher(), _RecordingSink, _router(), test_a_mismatched_alert_is_dropped_before_it_reaches_the_buffer(), test_a_routed_alert_reaches_the_wire_in_the_batch(), test_an_empty_list_is_a_no_op(), test_an_unguarded_mismatch_poisons_the_whole_batch() (+13 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (11): gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups), agent metrics/ module (rolling metrics and aggregation), PostgreSQL (Day-2 historical metrics) (+3 more)

### Community 108 - "cards.py"
Cohesion: 0.16
Nodes (17): _alert_badge(), _ask_again(), _breakdown(), _breakdown_rows(), build_answer_card(), build_clarification_card(), build_error_card(), _card() (+9 more)

### Community 109 - "Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)"
Cohesion: 0.17
Nodes (12): 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 4.1 Wire contract — `packages/telemetry_shared/models/health.py`, 4.2 Configuration — `health/config.py`, 4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`, 4. UBS-58 — the heartbeat, 5.1 The window — `health/window.py` (+4 more)

### Community 110 - "backtest.py"
Cohesion: 0.05
Nodes (39): parse_fix_timestamp(), TimestampResult, _app_log_time(), backtest(), tick(), BacktestReport, _DiscardRouter, _first_dated_time() (+31 more)

### Community 111 - "test_real_snapshot_output_drives_the_rule_engine_correctly"
Cohesion: 0.18
Nodes (7): _ack(), _Clock, _new_order(), _rejected(), _session_reject(), test_real_snapshot_output_drives_the_rule_engine_correctly(), _snapshot_now()

### Community 112 - "manifest.json"
Cohesion: 0.09
Nodes (22): accentColor, bots, description, full, short, developer, name, privacyUrl (+14 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (11): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams), Telemetry Agent (apps/agent) (+3 more)

### Community 114 - "parse_callbacks_config"
Cohesion: 0.09
Nodes (14): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), _RetryYaml, CallbackSink, _dispatcher() (+6 more)

### Community 115 - "test_tools.py"
Cohesion: 0.09
Nodes (20): McpServerConfig, _number(), build_server(), list_alerts(), list_events(), main(), _params(), _ok() (+12 more)

### Community 116 - "AggregatorConfig"
Cohesion: 0.08
Nodes (9): AggregatorConfig, SnapshotEmitter, test_missing_dimension_value_becomes_unspecified_not_the_string_none(), test_cardinality_cap_folds_agent_labels_like_any_other_metric(), _app_log_aggregator(), _Harness, _orders(), _starts() (+1 more)

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.20
Nodes (12): _aggregator(), _drain_backend(), _evaluator(), _ingest_app_log_lines(), _ingest_three_orders(), _publish_and_drain(), _publisher(), _read_counters() (+4 more)

### Community 118 - "_publish_and_drain"
Cohesion: 0.15
Nodes (17): _drain_backend(), _engine(), _fire_reject_spike(), _publish_and_drain(), _publisher(), _router(), test_a_real_alert_reaches_the_backend_alert_store(), test_firing_then_resolved_is_one_stored_alert_with_both_transitions() (+9 more)

### Community 119 - "test_UBS_27_reject_reason_trends.py"
Cohesion: 0.10
Nodes (21): _bad_window(), _by_reason(), classify(), RejectReasonTrendService, ReasonTrend, RejectReasonTrendsRequest, RejectReasonTrendsResponse, _analyse() (+13 more)

### Community 120 - "time"
Cohesion: 0.10
Nodes (13): CaptureTransport, test_monitor_parser_events_alerts_and_query_round_trip(), test_operational_hooks_publish_and_are_queryable(), test_runtime_emits_start_and_stop_without_requiring_log_activity(), test_full_queue_blocks_producer_without_drops(), _batch_with_snapshot(), test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store(), _wait_for_status() (+5 more)

### Community 121 - "AgentRegistry"
Cohesion: 0.05
Nodes (24): get_agent(), list_agents(), _summary(), AlertingConfig, AgentRecord, AgentRegistry, _utc_now(), build() (+16 more)

### Community 122 - "snapshot_bridge.py"
Cohesion: 0.18
Nodes (9): build_snapshot(), _to_payload(), _to_wire_dimensions(), _aggregator(), test_app_log_dimensions_survive_the_wire_allowlist(), test_build_snapshot_is_pure_and_repeatable(), _build(), test_each_metric_appears_exactly_once_at_its_own_native_dimensions() (+1 more)

### Community 123 - "Requirement ID Scheme (FR-<AREA>-<NNN>)"
Cohesion: 0.18
Nodes (12): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Requirement ID Scheme (FR-<AREA>-<NNN>), Health Reporter (component), Health Reporter Heartbeat Requirement (FR-HLT-001), Backend Configuration and Secrets (§9), NFR-SEC-004: Secrets from Environment Only (+4 more)

### Community 124 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.18
Nodes (11): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Blocking CI sentinel test (FR-TST-005) (+3 more)

### Community 125 - "services/self_metrics.py"
Cohesion: 0.13
Nodes (4): _BoundSourcesCollector, _counter(), _gauge(), _utc_now()

### Community 126 - "DryRunCallbackSink"
Cohesion: 0.27
Nodes (4): DryRunCallbackSink, test_FR_CBK_011_dry_run_logs_delivery_id_and_body(), test_FR_CBK_011_dry_run_never_opens_a_socket(), test_FR_CBK_011_dry_run_returns_synthetic_success()

### Community 127 - "snapshot"
Cohesion: 0.33
Nodes (12): hand_labelled_events(), _ingest_all(), _shared_config(), test_gauges_are_empty_without_a_correlator(), test_gauges_reflect_pending_orders_and_event_staleness(), test_grouped_breakdown_by_symbol(), test_indicators_computed_from_hand_labelled_fixture(), test_latency_summary_present_for_recorded_histograms() (+4 more)

### Community 128 - "ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server"
Cohesion: 0.18
Nodes (10): ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server, Consequences, Context, Decision, Rationale, Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents) (+2 more)

### Community 129 - "Spec 005 — Rule Engine, Alerting and Callbacks"
Cohesion: 0.18
Nodes (9): ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell, Consequences, Context, Decision, Rationale, Rule definition and tiers (§1.1), The five Day-1 rule kinds (FR-RUL-001), Spec 005 — Rule Engine, Alerting and Callbacks (+1 more)

### Community 130 - "test_UBS_100_teams_bot_to_backend.py"
Cohesion: 0.40
Nodes (6): _ask(), _backend(), _card(), test_alert_question_shows_the_alert_badge_from_real_citations(), test_disabled_backend_renders_the_disabled_card(), test_rejection_question_renders_a_real_answer_card()

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "datetime"
Cohesion: 0.06
Nodes (5): _utc_now(), PublishConfig, _PublishYaml, _RetryYaml, _parse_duration_seconds()

### Community 133 - "healthcheck"
Cohesion: 0.20
Nodes (9): interval, retries, test, timeout, healthcheck, image, ports, services (+1 more)

### Community 134 - "telemetry-shared"
Cohesion: 0.33
Nodes (6): telemetry-agent, telemetry-backend, telemetry-mcp, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 135 - "_error_card_text"
Cohesion: 0.22
Nodes (9): _error_card_text(), test_bad_request_gets_a_rephrase_card(), test_connection_failure_hides_the_exception_text(), test_disabled_nl_gets_a_clear_card(), test_gateway_timeout_gets_the_try_again_card(), test_server_error_says_the_service_is_unreachable_without_internals(), test_timeout_gets_a_try_again_card(), boom() (+1 more)

### Community 136 - ".markdownlint-cli2.yaml"
Cohesion: 0.50
Nodes (3): config, MD013, ignores

### Community 143 - "test_UBS_122_signature_rules.py"
Cohesion: 0.21
Nodes (11): _load(), _seed_signature(), _summary(), test_a_label_on_a_non_signature_rule_is_rejected(), test_a_signature_fires_its_own_rule_with_the_label_as_group_by(), test_a_signature_rule_loads_with_its_label(), test_a_signature_rule_without_a_label_is_rejected(), test_instance_rules_still_evaluate_alongside_signature_rules() (+3 more)

### Community 145 - "PublishResult"
Cohesion: 0.08
Nodes (26): _ScriptedSink, classify_publish_response(), PublishAction, PublishOutcome, PublishResult, _alerts_to_backend_act(), send(), _FlakyBackendSink (+18 more)

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (9): hb(), registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded(), test_one_stale_agent_is_partial() (+1 more)

### Community 160 - "TeamsBotConfig"
Cohesion: 0.11
Nodes (8): _number(), TeamsBotConfig, _authorize(), create_app(), main(), test_defaults_when_the_environment_is_empty(), test_invalid_values_fail_with_a_clear_message(), test_values_are_read_from_the_environment()

### Community 161 - "nl_query.py"
Cohesion: 0.09
Nodes (11): BackendError, NlBackendClient, _parse(), build_reply(), question_text(), register_handlers(), resolve_timezone(), NlClarificationResponse (+3 more)

### Community 162 - "ack_latency_ms"
Cohesion: 0.10
Nodes (20): ack_latency_ms, baseline_window_minutes, enabled, minimum_samples, window_minutes, execution_issue_rate, baseline_window_minutes, enabled (+12 more)

### Community 195 - "_dispatch"
Cohesion: 0.22
Nodes (10): _aggregator(), _alert(), _dispatch(), _fire(), _rule(), test_callback_failures_do_not_make_a_log_starved_agent_look_alive(), test_four_permanent_failures_fire_callback_failing(), test_repeated_sampling_does_not_inflate_the_counter_toward_a_false_alert() (+2 more)

### Community 201 - "render_answer"
Cohesion: 0.09
Nodes (30): escape_adaptive_card_text(), alert_duration_minutes(), alert_prose(), breakdown_phrase(), chart_rows_from_groups(), compare_delta_phrase(), completeness_sentence(), delivery_phrase() (+22 more)

### Community 207 - "ingest.py"
Cohesion: 0.10
Nodes (17): derive_counters(), _fixed_now(), main(), _step(), SessionTimeout, FixTelemetry, session_id_for(), build_parsed_message_event() (+9 more)

### Community 212 - "time.py"
Cohesion: 0.23
Nodes (10): baseline_time_range_before(), _local_midnight(), _parse_relative_duration(), _parse_short_datetime(), parse_time_expression(), _relative_from_amount(), _this_morning_start(), TimeParseResult (+2 more)

### Community 213 - "baseline.py"
Cohesion: 0.10
Nodes (13): AnomalyMetric, AnomalyReading, _baseline_value(), BaselineTracker, _current_sample(), _current_value(), _minutes(), _percent() (+5 more)

### Community 214 - "_RuleYaml"
Cohesion: 0.21
Nodes (4): _AnomalyYaml, _RuleYaml, _TierYaml, _to_rule_config()

### Community 215 - "classify_http_status"
Cohesion: 0.27
Nodes (6): classify_http_status(), RetryDecision, test_FR_CBK_006_2xx_is_success(), test_FR_CBK_006_408_429_5xx_is_retry(), test_FR_CBK_006_non_2xx_non_4xx_5xx_falls_back_to_permanent_failure(), test_FR_CBK_006_other_4xx_is_permanent_failure()

### Community 226 - "NlQueryService"
Cohesion: 0.11
Nodes (11): build_nl_service(), NlQueryService, Architecture comparison, Config, Current: implemented UBS-117 baseline, Intended to-be: same services, with planned additions, Other work remains separate, Sponsor review baseline (proposed; not yet approved) (+3 more)

### Community 234 - "build_agent"
Cohesion: 0.08
Nodes (15): connect_reporter_to_publisher(), drop_hook(), heartbeat_provider(), build_agent(), check_action_secret(), stage_actions(), _is_local(), _secret() (+7 more)

### Community 268 - "test_UBS_25_29_anomaly.py"
Cohesion: 0.20
Nodes (30): load_anomaly_rules(), make_latency(), _engine(), _fire(), _ratio_snapshot(), _rule(), test_a_long_incident_keeps_alerting_instead_of_auto_resolving(), test_a_resolved_anomaly_carries_no_fabricated_metric_context() (+22 more)

### Community 270 - "Project instructions"
Cohesion: 0.08
Nodes (22): Agent guidance, Architecture constraints, Development workflow, Git attribution, Graphify, Project instructions, Requirements and decisions, Safety (+14 more)

### Community 272 - "Metrics Query API (UBS-68, UBS-91, UBS-92)"
Cohesion: 0.12
Nodes (14): Code locations, Endpoint, Example request, Example response, Metric and dimension aliases, Metrics Query API (UBS-68, UBS-91, UBS-92), Multi-replica mode (UBS-92), Operational limits (UBS-91) (+6 more)

### Community 274 - "test_reporter.py"
Cohesion: 0.61
Nodes (6): make_monitor(), test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 275 - "Rule Engine demo runbook"
Cohesion: 0.10
Nodes (22): NoLogActivity rule, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Rule Engine, Safety and suppression (silences, grace, storm cap), SighupRuleReloader, 1. `make rules-test` (+14 more)

### Community 276 - "test_RE_02_evaluators.py"
Cohesion: 0.16
Nodes (25): _read_observed(), RuleKind, ValueSource, _absence_rule(), _gauge_rule(), _latency_rule(), _rate_rule(), test_absence_evaluator_fires_when_guard_satisfied_and_metric_is_zero() (+17 more)

### Community 279 - "publishing/__init__.py"
Cohesion: 0.08
Nodes (15): on_drop(), BatchSequencer, build_batch(), _on_buffer_drop(), PublishSink, make_alert(), make_event(), test_batch_sequencer_seq_is_monotonic_and_ids_differ() (+7 more)

### Community 280 - "Teams bot"
Cohesion: 0.12
Nodes (13): Configuration, Connect Copilot, Run it locally, Telemetry MCP server, Configuration, Questions to try, Real Teams (later, not tested against a real tenant), Run it locally (5 terminals, all from the repo root) (+5 more)

### Community 281 - "Agent"
Cohesion: 0.13
Nodes (14): Agent, agent(), _simulate(), _SimulationFinished, test_every_simulator_application_variant_reaches_the_shipped_counters(), test_simulator_failure_lines_fire_app_log_failure(), test_simulator_rotation_preserves_application_counters_and_fix_parsing(), test_simulator_signature_alert_reaches_backend_and_signed_callback() (+6 more)

### Community 282 - "_aggregator_with_a_reject_burst"
Cohesion: 0.24
Nodes (8): _aggregator_with_a_reject_burst(), _order(), _reject(), _rule(), _run_ticks(), test_the_loop_delivers_a_real_reject_spike_to_both_paths(), test_the_loop_feeds_the_correlator_gauge_to_pending_order_timeout(), _wire()

### Community 283 - "factory.py"
Cohesion: 0.07
Nodes (23): AzureOpenAiSlotFiller, default_mock_responses(), OllamaSlotFiller, _JsonModeRejected, OpenAiCompatibleSlotFiller, _normalize_time_range(), parse_llm_slot_payload(), _sanitize_filters() (+15 more)

### Community 284 - "test_ollama_native.py"
Cohesion: 0.12
Nodes (13): native_base_url(), _chat(), _run(), go(), record(), test_FR_NLQ_007_payload_uses_schema_keep_alive_and_token_cap(), test_FR_NLQ_021_connection_error_is_unavailable(), test_FR_NLQ_030_none_intent_carries_reply() (+5 more)

### Community 285 - "load_agent_config"
Cohesion: 0.22
Nodes (18): AgentConfigError, load_agent_config(), test_a_bad_section_is_named_in_the_error(), test_binary_magic_is_read_as_hex(), test_binary_parsing_defaults_to_disabled(), test_disabled_callbacks_mean_no_dispatcher(), test_error_signatures_are_read_from_parsing(), test_insecure_publish_endpoint_needs_the_explicit_flag() (+10 more)

### Community 286 - "UBS-100 — Teams bot with Adaptive Card answers (spec)"
Cohesion: 0.20
Nodes (9): As Built, Further Notes, Implementation Decisions, Out of Scope, Problem Statement, Solution, Testing Decisions, UBS-100 — Teams bot with Adaptive Card answers (spec) (+1 more)

### Community 287 - "LlmConfig"
Cohesion: 0.15
Nodes (18): BackendConfigError, ensure_nl_llm_credentials(), LlmConfig, NlConfig, resolve_llm_config(), _build_parser(), main(), build_llm_filler() (+10 more)

### Community 288 - "health-reporter-overview.md"
Cohesion: 0.20
Nodes (8): UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration, Not in this change, Open points for the team, UBS-69 / UBS-85 / UBS-96 — decisions and open points

### Community 290 - "NlQueryContext"
Cohesion: 0.22
Nodes (17): MockLlmSlotFiller, NlQueryContext, _ask(), _ForbiddenLlm, _service(), test_FR_NLQ_021_timeout_falls_back_to_weak_rule_match(), test_FR_NLQ_021_unreachable_llm_without_rule_match_is_friendly(), test_FR_NLQ_030_guarded_llm_reply_is_returned() (+9 more)

### Community 291 - "metrics_query.py"
Cohesion: 0.14
Nodes (18): to_metrics_query(), _clamp_time_range(), InterpretedValidationError, _schema_issues(), validate_interpreted_query(), ValidationIssue, ValidationResult, QueryTimeRange (+10 more)

### Community 299 - "RuleConfigError"
Cohesion: 0.11
Nodes (22): anomaly_path_for(), _defined_action_names(), load_rules(), load_rules_from_yaml(), read_rules_file(), _rule_label(), RuleConfigError, test_a_level_rule_loads_with_its_level() (+14 more)

### Community 300 - "to_ingestion_heartbeat"
Cohesion: 0.18
Nodes (10): provide(), to_ingestion_heartbeat(), make(), test_files_get_an_instance_id_which_the_contract_requires(), test_health_wire_still_available_for_the_reversal(), test_ingestion_payload_validates_against_the_real_contract(), test_measured_signals_are_carried_through_unchanged(), test_status_survives_but_reasons_are_dropped() (+2 more)

### Community 303 - "sign"
Cohesion: 0.21
Nodes (10): load_callback_secret(), sign(), test_FR_CBK_005_different_body_produces_different_signature(), test_FR_CBK_005_different_secret_produces_different_signature(), test_FR_CBK_005_different_timestamp_produces_different_signature(), test_FR_CBK_005_load_callback_secret_fails_fast_when_empty(), test_FR_CBK_005_load_callback_secret_fails_fast_when_unset(), test_FR_CBK_005_load_callback_secret_reads_env_var() (+2 more)

### Community 304 - "test_reply_guard.py"
Cohesion: 0.18
Nodes (7): guard_reply(), match_small_talk(), test_FR_NLQ_030_guard_accepts_the_configured_application(), test_FR_NLQ_030_guard_cleans_whitespace(), test_FR_NLQ_030_guard_rejects_unsafe_replies(), test_FR_NLQ_030_small_talk_matches(), test_FR_NLQ_030_telemetry_questions_are_not_small_talk()

### Community 305 - "CallbackDispatcher"
Cohesion: 0.10
Nodes (24): main(), _make_alert(), _print_counters(), _run_one(), _step(), CallbackDispatcher, HttpsCallbackSink, _run_dispatcher_against_a_broken_magic() (+16 more)

### Community 306 - "test_RE_parse_error_integration.py"
Cohesion: 0.31
Nodes (8): _fire(), _ingest(), _rate(), test_a_clean_log_never_fires(), test_a_mostly_unparseable_log_escalates_to_critical(), test_below_min_samples_reads_insufficient_data_not_a_fire(), test_buffered_failures_alone_cannot_reach_the_critical_tier(), test_unparseable_lines_fire_parse_error_rate()

### Community 307 - "telemetry_agent/config.py"
Cohesion: 0.22
Nodes (10): _ActionsYaml, LogsConfig, _LogsYaml, ParsingConfig, _ParsingYaml, _PipelineYaml, _RulesYaml, _Section (+2 more)

### Community 310 - "MetricsQueryResponse"
Cohesion: 0.10
Nodes (13): QueryConfig, FanoutClient, HttpxFanoutClient, ReplicaFanout, DataCompleteness, MetricsQueryResponse, assert_answer_numbers_in_data(), _numbers_from_data() (+5 more)

### Community 312 - "NL query manual test plan: Ollama, Teams and Copilot (MCP)"
Cohesion: 0.17
Nodes (13): 0. Setup, A. Backend startup, B. Direct API, C. Ollama slow or down, D. Teams (Agents Playground), E. MCP server (MCP Inspector), F. Copilot Studio (optional), G. Safety (+5 more)

### Community 317 - "test_STM_03_warmup.py"
Cohesion: 0.33
Nodes (6): _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up(), test_data_from_a_restarted_bucket_is_still_merged_not_dropped(), test_restarted_bucket_count_reflects_only_buckets_a_restart_touched(), test_restarted_bucket_marks_the_instance_warming_up_for_the_warmup_window()

### Community 318 - "MultiLogMonitor"
Cohesion: 0.14
Nodes (12): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+4 more)

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements

## Knowledge Gaps
- **165 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `telemetry-mcp`, `telemetry-simulator`, `telemetry-teams` (+160 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1830 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **68 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MA-04: calculated indicators and snapshot output.` connect `Implementation Status live document` to `AgentHeartbeat wire contract`, `Rule Engine demo runbook`, `snapshot`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 81 INFERRED edges - model-reasoned connections that need verification._
- **What connects `telemetry-agent`, `telemetry-backend`, `telemetry-mcp` to the rest of the system?**
  _165 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `asyncio` be split into smaller, more focused modules?**
  _Cohesion score 0.053387691710347504 - nodes in this community are weakly interconnected._
- **Why does `Telemetry System Documentation Index` connect `Telemetry System Documentation Index` to `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1`, `ADR 0004: Raw log content is never persisted or transmitted`, `Telemetry Agent (architecture constraint)`, `ADR 0001: Telemetry Agent written in Go (Superseded)`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._