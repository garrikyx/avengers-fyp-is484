# Graph Report - avengers-fyp-is484  (2026-10-08)

## Corpus Check
- 314 files · ~173,495 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 9, .example 1, .typed 1)

## Summary
- 4085 nodes · 10703 edges · 268 communities (135 shown, 133 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 1918 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `540ae7a0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- telemetry_backend/main.py
- frame.py
- test_metrics_event.py
- RuleEngine
- make_snapshot
- test_RE_05_config_loader.py
- HealthReporter
- test_RE_02_evaluators.py
- RetryPolicy
- LatencyCorrelator
- derive_counters
- test_RE_integration.py
- test_heartbeat.py
- LogMonitor
- PublishBuffer
- PipelineBridge
- demo_metrics_bridge.py
- PublishResult
- MetricsAggregator
- UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth
- test_RE_session_integration.py
- MetricStore
- Scaffold and Build Plan
- SessionHeartbeatTracker
- AgentHeartbeat wire contract
- Telemetry Backend Service
- to_ingestion_heartbeat
- IngestionService
- RuleEvaluator
- deps.py
- DeliveryTracker
- health/config.py
- test_RE_publish_integration.py
- AggregatorConfig
- health/demo.py
- test_UBS_113_evaluator.py
- test_MA_03_correlation.py
- dataclasses
- config/rules.yaml live rule set
- test_the_agent_process_alerts_magic_and_the_backend
- SourceMeta
- MetricsAggregator ring buffer
- services/ingestion.py
- HeartbeatMonitor
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- heartbeat_json
- parse_callbacks_config
- CallbackResult
- ParseResult
- test_RE_03_safety.py
- parse_publish_config
- test_UBS_112_metrics_ingestor.py
- Snapshot
- datetime
- from_alert_event
- CallbackDispatcher
- CounterRegistry
- protocol.py
- test_queue_depth.py
- AgentRegistry
- classify_http_status
- telemetry_agent_metrics_aggregator
- enrich.py
- BackendPublisher
- _Demo
- Telemetry Agent (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- DropOldestQueue
- test_agent_registry.py
- 009 — Non-Functional Requirements and Security
- telemetry_agent/config.py
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- load_agent_config
- pipeline_demo.py
- AlertEvent
- pathlib
- services/demo_quickstart.py
- test_FR_CBK_005_signing.py
- Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing)
- pytest
- test_ING_004_008_routes.py
- End-to-End Acceptance Scenario (FR-TST-010)
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- publisher.py
- Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)
- StreamProcessorConfig
- test_STM_04_efficiency.py
- ParsedMessageEvent
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- test_QRY_04_concurrency.py
- test_UBS_94_alerts_query.py
- AgentHeartbeat
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- UBS-58/59/60 implementation notes
- telemetry_backend/config.py
- test_log_monitor_status.py
- 008 — Natural Language Query Layer (Copilot/Teams)
- test_QRY_03_memory.py
- telemetry_shared shared schema package
- OffsetTracker
- Requirement ID Scheme (FR-<AREA>-<NNN>)
- NFR-REL-003: Backend Outage Must Not Affect Alerting
- test_UBS_115_snapshot_to_metricstore.py
- test_UBS_109_rule_engine_to_backend.py
- test_publishing_helpers.py
- FixParser
- Stream Processor (component)
- snapshot_bridge.py
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- callbacks/config.py
- Rule Engine demo runbook
- SnapshotCursor
- mock_logger.py
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- test_UBS_113_evaluation_loop.py
- .__init__
- telemetry-shared
- Auditability & Compliance rationale (deterministic order audit trails)
- CLAUDE.md
- ADR 0002: Backend in Python/FastAPI
- ADR 0003: HTTPS/JSON Transport Day-1
- ADR 0005: In-Memory Metric Store
- ADR 0006: Agent in Python
- Parser Test Obligations (§10)
- Message Validation and Parse Error Reason Codes (FR-PRS-017–019)
- Data Completeness Block (FR-QRY-015)
- Backend Health and Self-Metrics (FR-HLT-010)
- test_STM_03_warmup.py
- test_data_completeness.py
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
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- AlertStore
- test_reporter.py
- test_readyz_shared_processor.py
- decimal
- Histogram
- .__init__
- test_degraded_status_flows_into_heartbeat_payload
- telemetry_agent/main.py

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 110 edges
2. `HealthReporter` - 94 edges
3. `BackendPublisher` - 79 edges
4. `AlertEvent` - 78 edges
5. `SourceMeta` - 76 edges
6. `FixParser` - 72 edges
7. `create_app()` - 64 edges
8. `ParseResult` - 62 edges
9. `StreamProcessorConfig` - 62 edges
10. `LogMonitor` - 61 edges

## Surprising Connections (you probably didn't know these)
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py
- `4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`` --references--> `AgentHeartbeat`  [INFERRED]
  docs/plan/health-reporter-overview.md → packages/telemetry_shared/src/telemetry_shared/models/health.py
- `Placeholder receiver — `scripts/heartbeat_receiver_stub.py`` --references--> `AgentHeartbeat`  [INFERRED]
  docs/plan/ubs58-60-notes.md → packages/telemetry_shared/src/telemetry_shared/models/health.py

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

## Communities (268 total, 133 thin omitted)

### Community 0 - "telemetry_backend/main.py"
Cohesion: 0.07
Nodes (38): AlertsQueryParams, BatchAccepted, _build_parser(), _counts(), create_app(), enqueue_or_full(), get_alert(), ingest_batch() (+30 more)

### Community 1 - "frame.py"
Cohesion: 0.08
Nodes (26): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+18 more)

### Community 2 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (29): build_parsed_message_event(), _to_decimal(), _meta(), _parse(), _parser_counters(), _session_counters(), test_a_clean_fix_line_is_not_a_parse_error(), test_clean_line_reports_no_reason() (+21 more)

### Community 3 - "RuleEngine"
Cohesion: 0.09
Nodes (21): _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _matched_tier(), _metric_context(), _read_absence() (+13 more)

### Community 4 - "make_snapshot"
Cohesion: 0.19
Nodes (24): make_gauges(), make_indicator(), make_indicators(), make_snapshot(), _engine(), _fire(), _rule(), test_ack_latency_breach_insufficient_samples_never_fires() (+16 more)

### Community 5 - "test_RE_05_config_loader.py"
Cohesion: 0.12
Nodes (13): load_rules(), load_rules_from_yaml(), _parse_duration_seconds(), _rule_label(), RuleConfigError, test_duplicate_rule_name_raises(), test_existing_but_malformed_file_never_falls_back_to_defaults(), test_malformed_rule_raises_naming_the_rule() (+5 more)

### Community 6 - "HealthReporter"
Cohesion: 0.08
Nodes (16): HealthThresholds, HealthReporter, HealthSignals, _utc_now(), 3. UBS-30 — read lag (the foundation), 4.3 Rollup and payload — `health/reporter.py`, Design points, Module map (`apps/agent/src/telemetry_agent/health/`) (+8 more)

### Community 7 - "test_RE_02_evaluators.py"
Cohesion: 0.21
Nodes (22): _read_observed(), make_latency(), _absence_rule(), _gauge_rule(), _latency_rule(), _rate_rule(), test_absence_evaluator_fires_when_guard_satisfied_and_metric_is_zero(), test_absence_evaluator_guard_unmet_returns_none_not_zero() (+14 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.13
Nodes (10): RetryPolicy, test_FR_CBK_004_delay_doubles_per_attempt_with_factor_2(), test_FR_CBK_004_delay_is_capped(), test_FR_CBK_004_first_attempt_is_roughly_base(), test_FR_CBK_004_jitter_stays_within_bounds(), test_FR_CBK_004_retry_after_ignored_when_smaller(), test_FR_CBK_004_retry_after_overrides_when_larger(), test_callbacks_shim_is_the_same_class() (+2 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.08
Nodes (9): CorrelatorStats, LatencyCorrelator, OrderContext, _timedelta_to_ms(), main(), _step(), _build_gauges(), snapshot() (+1 more)

### Community 10 - "derive_counters"
Cohesion: 0.09
Nodes (35): derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), ReasonNormalizer, top_reject_reasons(), _banner(), _implementation(), _line() (+27 more)

### Community 11 - "test_RE_integration.py"
Cohesion: 0.19
Nodes (8): _ack(), _Clock, _ingest(), _new_order(), _rejected(), _session_reject(), test_real_snapshot_output_drives_the_rule_engine_correctly(), _snapshot_now()

### Community 12 - "test_heartbeat.py"
Cohesion: 0.14
Nodes (14): HeartbeatEmitter, Collect, FakeClock, _reporter(), test_heartbeat_payload_matches_spec_004_section_6(), test_interval_defaults_from_reporter_config(), test_logging_sink_writes_wire_json(), test_run_emits_on_interval_with_no_log_activity() (+6 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (16): PublishBuffer, _item(), _tags(), test_an_item_larger_than_the_whole_cap_is_not_self_evicted(), test_append_and_take_preserve_fifo_order(), test_byte_overflow_drops_oldest_and_counts(), on_drop(), test_expire_drops_only_items_older_than_max_age() (+8 more)

### Community 15 - "PipelineBridge"
Cohesion: 0.05
Nodes (13): Parser, Registry, PipelineConfig, PipelineStats, PipelineBridge, ParserWorkerPool, test_block_mode_never_drops_under_backpressure(), test_demo_scenarios_run_to_completion() (+5 more)

### Community 16 - "demo_metrics_bridge.py"
Cohesion: 0.11
Nodes (16): _fixed_now(), main(), _step(), derive_parser_counters(), derive_session_counters(), _parse_error_reason(), parser_counter_dims(), _fire() (+8 more)

### Community 17 - "PublishResult"
Cohesion: 0.10
Nodes (29): classify_publish_response(), PublishAction, PublishOutcome, PublishResult, _FlakyBackendSink, make_snapshot(), test_429_carries_retry_after_seconds(), test_status_code_classification() (+21 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.12
Nodes (5): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator

### Community 19 - "UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth"
Cohesion: 0.12
Nodes (8): 6. UBS-60 — publish queue depth, Also touched, and why, How to see it, Placeholder receiver — `scripts/heartbeat_receiver_stub.py`, Ticket vs. spec decisions (read first — these need team sign-off), UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth, UBS-60: publish queue depth, Wire compatibility with UBS-66 (decided 2026-09-22 — revisit)

### Community 20 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (17): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), _rule(), test_a_clean_logout_does_not_also_produce_a_timeout(), test_fix_session_down_fires_on_a_heartbeat_timeout_alone() (+9 more)

### Community 21 - "MetricStore"
Cohesion: 0.11
Nodes (4): _CanonicalBucket, _dim_key(), MetricStore, _SeriesContribution

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.07
Nodes (33): Open Questions and Decisions Required, Callback Dispatcher, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent, Q-2 — Callback Protocol Magic Will Support (+25 more)

### Community 23 - "SessionHeartbeatTracker"
Cohesion: 0.08
Nodes (25): SessionHeartbeatTracker, _SessionState, _key(), _keys(), _observe(), test_a_clean_logout_never_times_out(), test_a_session_relogging_on_after_logout_is_tracked_again(), test_a_session_still_speaking_never_times_out() (+17 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (26): health: threshold config block, heartbeat: interval config, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry (+18 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (28): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+20 more)

### Community 26 - "to_ingestion_heartbeat"
Cohesion: 0.20
Nodes (9): to_ingestion_heartbeat(), make(), test_files_get_an_instance_id_which_the_contract_requires(), test_health_wire_still_available_for_the_reversal(), test_ingestion_payload_validates_against_the_real_contract(), test_measured_signals_are_carried_through_unchanged(), test_status_survives_but_reasons_are_dropped(), test_unmeasured_signals_become_zero_not_null() (+1 more)

### Community 27 - "IngestionService"
Cohesion: 0.10
Nodes (9): AcceptedIngestion, IngestionService, IngestionValidationIssue, _safe_key(), _publisher(), _snapshot(), test_503_when_the_backend_queue_is_full(), test_happy_path_against_the_real_backend_app() (+1 more)

### Community 29 - "deps.py"
Cohesion: 0.17
Nodes (5): healthz(), metrics(), readyz(), get_deps(), _utc_now()

### Community 30 - "DeliveryTracker"
Cohesion: 0.10
Nodes (13): DeliveryRecord, DeliveryStatus, DeliveryTracker, test_UBS_34_each_transition_is_timestamped(), test_UBS_34_enqueue_records_pending(), test_UBS_34_immediate_success_sequence(), test_UBS_34_last_error_persists_across_terminal_transition(), test_UBS_34_retried_then_delivered_sequence() (+5 more)

### Community 31 - "health/config.py"
Cohesion: 0.10
Nodes (20): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, _HeartbeatYaml, load_health_config(), parse_duration_seconds() (+12 more)

### Community 32 - "test_RE_publish_integration.py"
Cohesion: 0.06
Nodes (42): AgentCounterSampler, _aggregator(), _alert(), _dispatch(), _drain(), _fire(), _rule(), test_callback_failures_do_not_make_a_log_starved_agent_look_alive() (+34 more)

### Community 33 - "AggregatorConfig"
Cohesion: 0.13
Nodes (31): AggregatorConfig, FakeClock, hand_labelled_events(), make_event(), minimal_aggregator(), test_10k_events_in_60s_window_returns_correct_count(), test_cardinality_cap_folds_overflow_into_other_and_preserves_total(), test_cardinality_cap_resets_per_bucket_not_for_process_lifetime() (+23 more)

### Community 34 - "health/demo.py"
Cohesion: 0.10
Nodes (12): HeartbeatConfig, _build_parser(), _detect_session_timeouts(), main(), _main_async(), _make_publisher(), _poll_forever(), PrintHeartbeatSink (+4 more)

### Community 35 - "test_UBS_113_evaluator.py"
Cohesion: 0.10
Nodes (29): _names(), _rule(), _Stack, test_a_cleared_condition_resolves_on_both_paths(), test_a_counter_rule_fires_and_reaches_both_paths(), test_a_rejected_reload_routes_nothing_and_keeps_the_rules(), test_a_reload_request_waits_for_the_next_tick(), test_a_reload_that_drops_a_firing_rule_routes_its_resolution() (+21 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (22): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), replaced() (+14 more)

### Community 37 - "dataclasses"
Cohesion: 0.08
Nodes (10): _PublishYaml, _RetryYaml, committed_offsets(), FakeClock, fix_lines(), RecordingTransport, test_no_lines_are_lost_across_a_simulator_rotation(), test_simulator_logs_reach_the_backend_health_api() (+2 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.13
Nodes (19): Agent processing pipeline (monitor to health reporter), publish: Backend Publisher config block, BackendUnreachable rule, CallbackFailing rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule (+11 more)

### Community 39 - "test_the_agent_process_alerts_magic_and_the_backend"
Cohesion: 0.33
Nodes (3): _burst(), test_the_agent_process_alerts_magic_and_the_backend(), scenario()

### Community 40 - "SourceMeta"
Cohesion: 0.05
Nodes (20): DemoMetricsSink, SourceMeta, QueueSnapshot, PipelineCommitter, LinePosition, ProcessedLineDeduper, EventQueue, LineQueue (+12 more)

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.14
Nodes (16): AckLatencyBreach rule, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent), Histogram (fixed buckets, merge, percentile), LatencyCorrelator (+8 more)

### Community 42 - "services/ingestion.py"
Cohesion: 0.10
Nodes (4): _BoundSourcesCollector, _counter(), _gauge(), _utc_now()

### Community 43 - "HeartbeatMonitor"
Cohesion: 0.12
Nodes (9): AlertingConfig, backend_alert_id(), HeartbeatMonitor, Not in this change, Open points for the team, UBS-69 / UBS-85 / UBS-96 — decisions and open points, _heartbeat(), test_FR_QRY_018_fresh_heartbeat_resolves_backend_alert() (+1 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (16): bad(), FakeClock, make(), ok(), test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides(), test_errors_counted_and_reported_in_heartbeat(), test_parse_fields_are_none_until_a_producer_reports() (+8 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.18
Nodes (11): SlidingWindowCounter, at(), test_capacity_is_rounded_not_floored(), test_counts_events_inside_window(), test_decays_as_window_slides(), test_event_older_than_window_is_dropped(), test_idle_window_reads_zero_not_none(), test_late_event_still_inside_window_is_counted() (+3 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.19
Nodes (11): Backend Publisher (component), Callback Dispatcher (component), 001 — Architecture, Log Monitor (component), Metrics Aggregator (component), Pipeline Bridge (component), Rule Engine (component), Scatter-Gather Cross-Replica Query (+3 more)

### Community 47 - "CamelModel"
Cohesion: 0.11
Nodes (14): get_agent(), list_agents(), _summary(), RejectedItem, CamelModel, AgentHealthDetail, AgentHealthFile, AgentHealthList (+6 more)

### Community 48 - "heartbeat_json"
Cohesion: 0.13
Nodes (10): heartbeat_json(), FakeClock, test_buffer_bytes_is_none_without_a_provider(), test_buffer_bytes_is_read_fresh_on_every_snapshot(), test_buffer_bytes_provider_can_be_registered_and_removed(), test_dropped_events_accumulate_within_the_window(), test_dropped_events_is_none_until_the_first_record(), test_dropped_events_reach_the_wire() (+2 more)

### Community 49 - "parse_callbacks_config"
Cohesion: 0.17
Nodes (10): CallbackConfigError, CallbacksConfig, load_callbacks_config(), parse_callbacks_config(), test_FR_CBK_001_allows_plain_http_with_explicit_opt_in(), test_FR_CBK_001_rejects_plain_http_by_default(), test_FR_CBK_config_custom_timeouts_and_limits(), test_FR_CBK_config_defaults_match_spec_010() (+2 more)

### Community 50 - "CallbackResult"
Cohesion: 0.15
Nodes (6): _ScriptedSink, CallbackResult, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink

### Community 52 - "ParseResult"
Cohesion: 0.09
Nodes (42): compile_signature_rules(), extract_log_level(), resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule, _corpus_files(), _fields_dict() (+34 more)

### Community 53 - "test_RE_03_safety.py"
Cohesion: 0.31
Nodes (6): _counter_rule(), test_dependent_suppression_when_no_log_activity_is_firing(), test_max_active_alerts_emits_one_alertstorm_and_suppresses_further(), test_schedule_inactive_skips_rule_entirely(), test_silence_suppresses_notification_but_still_tracks_state(), test_storm_clears_once_under_cap_and_the_suppressed_rule_fires()

### Community 54 - "parse_publish_config"
Cohesion: 0.14
Nodes (17): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfigError, test_allows_plain_http_when_explicitly_opted_in(), test_buffer_bytes_must_be_positive(), test_defaults_match_spec_010(), test_load_publish_config_invalid_yaml_raises() (+9 more)

### Community 55 - "test_UBS_112_metrics_ingestor.py"
Cohesion: 0.24
Nodes (13): _counters(), _feed(), _ingestor(), _meta(), _reporter(), test_a_failing_component_never_escapes_and_is_counted(), test_a_hard_parse_error_counts_for_aggregator_and_reporter(), test_bad_timestamp_is_a_heartbeat_error_but_not_an_aggregator_one() (+5 more)

### Community 56 - "Snapshot"
Cohesion: 0.11
Nodes (20): HistogramPayload, SeriesEntry, Snapshot, test_merging_the_same_snapshot_twice_does_not_double_the_counters(), batch_at(), _histogram_payload(), _read_one_group(), _snapshot() (+12 more)

### Community 57 - "datetime"
Cohesion: 0.05
Nodes (15): main(), _make_alert(), _print_counters(), _run_one(), _step(), DryRunCallbackSink, SessionTimeout, session_id_for() (+7 more)

### Community 58 - "from_alert_event"
Cohesion: 0.20
Nodes (8): CallbackAlertPayload, from_alert_event(), make_alert_event(), test_FR_CBK_001_payload_carries_ac_required_fields(), test_FR_CBK_002_payload_under_max_bytes_for_typical_alert(), test_FR_CBK_002_serialized_payload_matches_spec_shape(), test_FR_CBK_003_runbook_url_defaults_to_none(), test_FR_CBK_003_summary_stopgap_references_rule_and_condition()

### Community 59 - "CallbackDispatcher"
Cohesion: 0.14
Nodes (13): CallbackDispatcher, HttpsCallbackSink, _run_dispatcher_against_a_broken_magic(), drive(), _make_alert(), _run_one(), test_FR_CBK_001_success_marks_delivered(), handler() (+5 more)

### Community 60 - "CounterRegistry"
Cohesion: 0.13
Nodes (5): CounterRegistry, test_callbacks_shim_is_the_same_class(), test_increment_starts_at_zero_and_accumulates(), test_independent_counters_do_not_interfere(), test_snapshot_is_a_copy_not_a_live_view()

### Community 61 - "protocol.py"
Cohesion: 0.06
Nodes (31): AppLogParser, AppLogTelemetry, classify_line(), compile_app_log_patterns(), _looks_like_fix(), Confidence, LineClassification, get_parser() (+23 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.17
Nodes (17): FakeQueue, Flaky, make(), test_at_critical_watermark_is_unhealthy(), test_at_high_watermark_is_degraded_with_reason_and_trend(), test_below_high_watermark_is_healthy(), test_buffer_drops_oldest_when_full(), test_buffer_fills_while_downstream_is_down_and_drains_in_order() (+9 more)

### Community 63 - "AgentRegistry"
Cohesion: 0.06
Nodes (15): AgentRecord, AgentRegistry, _utc_now(), build(), DataCompleteness, SelfMetrics, Heartbeat, body() (+7 more)

### Community 64 - "classify_http_status"
Cohesion: 0.25
Nodes (6): classify_http_status(), RetryDecision, test_FR_CBK_006_2xx_is_success(), test_FR_CBK_006_408_429_5xx_is_retry(), test_FR_CBK_006_non_2xx_non_4xx_5xx_falls_back_to_permanent_failure(), test_FR_CBK_006_other_4xx_is_permanent_failure()

### Community 65 - "telemetry_agent_metrics_aggregator"
Cohesion: 0.16
Nodes (13): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), _aggregator(), _ingest(), _tel(), test_component_flood_cannot_crowd_out_other_series(), test_component_limiter_folds_past_its_cap() (+5 more)

### Community 66 - "enrich.py"
Cohesion: 0.06
Nodes (36): build_fix_telemetry(), normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type(), normalize_session_reject_reason() (+28 more)

### Community 67 - "BackendPublisher"
Cohesion: 0.10
Nodes (8): _drain(), main(), _make_snapshot(), _print_state(), _ScriptedSink, _step(), BackendPublisher, _publish_and_query()

### Community 68 - "_Demo"
Cohesion: 0.05
Nodes (16): _alert_storm_act(), _alerts_to_backend_act(), _backend_unreachable_act(), attempt(), _dedup_act(), _Demo, main(), _no_log_activity_act() (+8 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.13
Nodes (9): Magic simulator for development, Unified Telemetry Intelligence (Magic), callbacks: Callback Dispatcher config block, agent: identity config (id, instanceIds, version), Spec 004: Telemetry data model, Identity fields (§1), Callback dispatch requirements (§3.1), Callback flow (§3.2) (+1 more)

### Community 70 - "AppDeps"
Cohesion: 0.21
Nodes (15): AppDeps, env(), FakeClock, heartbeat(), post(), test_counts_cover_all_four_states(), test_detail_matches_spec_007_5_2(), test_detail_unknown_agent_is_404() (+7 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.09
Nodes (5): BoundedQueue, test_block_policy_waits_for_capacity(), test_drop_oldest_policy_discards_oldest_on_overflow(), test_zero_capacity_rejects_without_storing(), test_full_queue_blocks_producer_without_drops()

### Community 72 - "test_internal_api.py"
Cohesion: 0.13
Nodes (18): create_internal_app(), env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), test_decommissioned_agent_leaves_the_exposition(), test_healthz_is_liveness_only() (+10 more)

### Community 73 - "DropOldestQueue"
Cohesion: 0.18
Nodes (4): DropOldestQueue, test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped(), test_FR_CBK_007_overflow_drops_oldest_and_increments_counter()

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (12): FakeClock, hb(), make(), test_agent_clock_stepped_backwards_does_not_go_missing(), test_explicit_received_at_overrides_clock(), test_first_contact_is_reported_once(), test_late_older_heartbeat_keeps_newer_doc_but_refreshes_liveness(), test_missing_after_threshold_measured_on_backend_clock() (+4 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.11
Nodes (19): Resource Discipline (§9), Backend Configuration and Secrets (§9), Compliance and Operability Constraints (§7), Configurability NFRs (§5), 009 — Non-Functional Requirements and Security, NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-SCA-001: Agent Independence/Statelessness (+11 more)

### Community 77 - "telemetry_agent/config.py"
Cohesion: 0.15
Nodes (11): AgentConfigError, LogsConfig, _LogsYaml, ParsingConfig, _ParsingYaml, _PipelineYaml, _RulesYaml, _Section (+3 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.16
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

### Community 82 - "load_agent_config"
Cohesion: 0.28
Nodes (12): load_agent_config(), test_a_bad_section_is_named_in_the_error(), test_disabled_callbacks_mean_no_dispatcher(), test_error_signatures_are_read_from_parsing(), test_insecure_publish_endpoint_needs_the_explicit_flag(), test_invalid_error_signature_regex_is_rejected(), test_minimal_config_gets_the_defaults(), test_missing_file_is_an_error() (+4 more)

### Community 83 - "pipeline_demo.py"
Cohesion: 0.09
Nodes (16): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), run_happy_path(), run_slow_parser_backpressure(), MultiLogMonitor (+8 more)

### Community 84 - "AlertEvent"
Cohesion: 0.11
Nodes (6): AlertRouter, AlertEvent, _Agent, _signature_alerts(), test_app_log_lines_keep_no_log_activity_quiet_end_to_end(), test_shipped_signature_rules_fire_on_their_own_patterns_only()

### Community 85 - "pathlib"
Cohesion: 0.09
Nodes (11): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+3 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.22
Nodes (9): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), _reject(), _run_hong_kong_session(), _run_singapore_session() (+1 more)

### Community 87 - "test_FR_CBK_005_signing.py"
Cohesion: 0.21
Nodes (10): load_callback_secret(), sign(), test_FR_CBK_005_different_body_produces_different_signature(), test_FR_CBK_005_different_secret_produces_different_signature(), test_FR_CBK_005_different_timestamp_produces_different_signature(), test_FR_CBK_005_load_callback_secret_fails_fast_when_empty(), test_FR_CBK_005_load_callback_secret_fails_fast_when_unset(), test_FR_CBK_005_load_callback_secret_reads_env_var() (+2 more)

### Community 88 - "Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing)"
Cohesion: 0.22
Nodes (6): Offset Checkpointing (state.json), Error Response Shape (§7), NFR-SEC-015: Canonicalised Allowed Roots, Symlinks Refused, Security: Input Handling (§3.4), Agent Configuration Schema (§1), Log Monitor Harness (FR-TST-004)

### Community 89 - "pytest"
Cohesion: 0.14
Nodes (9): _maybe_gzip(), _parse_retry_after(), test_allows_plain_http_when_explicitly_opted_in(), test_body_over_threshold_is_gzipped_and_round_trips(), test_body_under_threshold_is_not_compressed(), test_rejects_plain_http_by_default(), test_sink_does_not_gzip_small_bodies(), test_sink_sets_content_encoding_header_when_gzipped() (+1 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (7): batch(), deps(), FakeClock, metrics(), test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once(), test_batches_past_the_per_agent_limit_get_429_with_retry_after()

### Community 91 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.25
Nodes (6): Open Questions Document (plan/open-questions.md), Agent Restart Sequence (§8.2), NL Evaluation Requirements (FR-NLQ-025), End-to-End Acceptance Scenario (FR-TST-010), NL Evaluation Harness (FR-TST-007–009), Synthetic Load Generator (tools/fixgen, FR-TST-006)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (14): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+6 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (10): Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test), NFR-SEC-012: Order Identifier Hashing, Rotatable Key, NFR-SEC-013: No Raw-Log Debug Mode in Release Build, Security: Data Minimisation (§3.1) (+2 more)

### Community 94 - "publisher.py"
Cohesion: 0.07
Nodes (19): on_drop(), BatchSequencer, build_batch(), make_pending_item(), PendingItem, _size_of(), PublishConfig, _on_buffer_drop() (+11 more)

### Community 95 - "Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)"
Cohesion: 0.12
Nodes (13): 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 4.1 Wire contract — `packages/telemetry_shared/models/health.py`, 4.2 Configuration — `health/config.py`, 4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`, 4. UBS-58 — the heartbeat, 5.1 The window — `health/window.py` (+5 more)

### Community 97 - "StreamProcessorConfig"
Cohesion: 0.07
Nodes (24): StreamProcessorConfig, align_to_canonical(), SnapshotOutcome, StreamProcessor, Decisions, _snapshot(), test_a_stale_direct_merge_is_counted_not_silently_dropped(), test_alignment_floors_a_phase_shifted_bucket_onto_the_canonical_grid() (+16 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (5): _CountingRing, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to(), test_read_indexes_only_the_requested_span_not_the_whole_ring(), test_restarted_bucket_count_also_indexes_only_the_requested_span()

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.10
Nodes (24): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent, _fixed_now() (+16 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.09
Nodes (21): extract_allowlisted_fields(), FixFields, _hash_or_none(), hash_identifier(), load_hash_key(), _strip_sensitive_fields(), test_FR_PRS_020_end_to_end_excluded_tag_never_in_parse_result(), test_FR_PRS_020_excluded_tags_never_appear_in_output() (+13 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (11): _engine(), _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved(), test_pending_fires_after_for_elapsed(), test_pending_reverts_to_inactive_if_condition_clears_before_for_elapsed() (+3 more)

### Community 103 - "test_QRY_04_concurrency.py"
Cohesion: 0.13
Nodes (12): _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another(), write_a(), test_concurrent_drops_across_many_instances_are_all_counted(), drop_one(), test_concurrent_merges_into_the_same_instance_do_not_lose_updates(), write(), test_concurrent_stale_rejections_across_many_instances_are_all_counted() (+4 more)

### Community 104 - "test_UBS_94_alerts_query.py"
Cohesion: 0.16
Nodes (15): AlertStoreConfig, _app_with_store(), test_UBS_94_detail_returns_transition_history_and_unknown_is_404(), test_UBS_94_list_filters_by_status_instance_and_since(), test_UBS_94_list_reports_truncation_when_limit_is_exceeded(), test_UBS_94_unknown_query_parameter_returns_invalid_field(), make_alert_event(), make_resolved_event() (+7 more)

### Community 105 - "AgentHeartbeat"
Cohesion: 0.09
Nodes (6): BufferingHeartbeatSink, LoggingHeartbeatSink, 4.4 Emitter and sinks — `health/heartbeat.py`, Missing downstream / upstream (what this branch cannot prove), AgentHeartbeat, test_naive_sent_at_is_rejected_and_aware_is_normalised_to_utc()

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.12
Nodes (22): _alert(), _publisher(), _RecordingSink, _router(), test_a_mismatched_alert_is_dropped_before_it_reaches_the_buffer(), test_a_routed_alert_reaches_the_wire_in_the_batch(), test_an_empty_list_is_a_no_op(), test_an_unguarded_mismatch_poisons_the_whole_batch() (+14 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (11): gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups), agent metrics/ module (rolling metrics and aggregation), PostgreSQL (Day-2 historical metrics) (+3 more)

### Community 108 - "UBS-58/59/60 implementation notes"
Cohesion: 0.22
Nodes (7): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration, UBS-58/59/60 implementation notes

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.05
Nodes (37): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestGuardConfig, IngestionConfig (+29 more)

### Community 110 - "test_log_monitor_status.py"
Cohesion: 0.62
Nodes (5): make_monitor(), test_status_after_read_reports_elapsed_lag(), test_status_before_any_read_has_no_lag(), test_status_missing_file_has_no_size_but_does_not_raise(), test_status_reports_offset_progress_between_polls()

### Community 111 - "008 — Natural Language Query Layer (Copilot/Teams)"
Cohesion: 0.40
Nodes (5): Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents), NL Intent Catalogue (FR-NLQ-003/004), 008 — Natural Language Query Layer (Copilot/Teams)

### Community 112 - "test_QRY_03_memory.py"
Cohesion: 0.17
Nodes (9): _snapshot(), test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell(), test_estimated_memory_bytes_grows_with_merged_series_and_shrinks_on_eviction(), test_estimated_memory_bytes_is_zero_for_an_empty_store(), test_merge_alone_can_trigger_shedding_without_an_external_tick(), test_merges_within_the_throttle_interval_do_not_re_check_memory(), test_shedding_never_evicts_a_bucket_written_in_the_same_cycle_at_small_capacity(), test_tick_logs_a_warning_above_memory_warn_percent_but_does_not_shed() (+1 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (11): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams), Telemetry Agent (apps/agent) (+3 more)

### Community 114 - "OffsetTracker"
Cohesion: 0.09
Nodes (9): OffsetTracker, test_heartbeat_carries_file_state_and_lag(), _line_texts(), test_checkpoints_offsets_while_file_is_still_busy(), test_does_not_emit_an_unterminated_line_until_it_is_complete(), test_multi_monitor_validates_read_mode(), test_restart_backfills_multiple_rotations_created_while_offline(), test_restart_recovers_retained_rotation_created_while_offline() (+1 more)

### Community 115 - "Requirement ID Scheme (FR-<AREA>-<NNN>)"
Cohesion: 0.16
Nodes (15): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Health Reporter (component), Ingestion Service (component) (+7 more)

### Community 116 - "NFR-REL-003: Backend Outage Must Not Affect Alerting"
Cohesion: 0.50
Nodes (5): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), NFR-REL-003: Backend Outage Must Not Affect Alerting, Reliability NFRs (§2), Runbook: Backend Unreachable

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.27
Nodes (9): _aggregator(), _drain_backend(), _evaluator(), _ingest_three_orders(), _publish_and_drain(), _publisher(), _read_counters(), test_real_aggregator_counters_reach_the_metric_store() (+1 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.12
Nodes (21): _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _publish_and_drain(), _publisher(), _reject(), _router() (+13 more)

### Community 119 - "test_publishing_helpers.py"
Cohesion: 0.29
Nodes (5): FakePublisher, _reporter(), test_connect_points_outbox_signals_at_the_publisher(), test_drop_hook_counts_each_evicted_item(), test_provider_returns_a_fresh_wire_heartbeat_each_call()

### Community 120 - "FixParser"
Cohesion: 0.09
Nodes (15): is_parse_error(), demo_log_lines(), FixParser, ParseError, 5.2 Intake and rules — `health/reporter.py`, UBS-59: parse-error window, test_is_parse_error_matches_aggregator_convention(), test_FR_PRS_012_corpus_files_frame_without_errors() (+7 more)

### Community 121 - "Stream Processor (component)"
Cohesion: 0.50
Nodes (3): Stream Processor (component), architecture-overview.png (client architecture diagram showing Stream Processor box), Ingestion Requirements (FR-ING-001–010)

### Community 122 - "snapshot_bridge.py"
Cohesion: 0.21
Nodes (8): build_snapshot(), _to_payload(), _to_wire_dimensions(), _aggregator(), test_build_snapshot_is_pure_and_repeatable(), _build(), test_each_metric_appears_exactly_once_at_its_own_native_dimensions(), test_wire_identity_fields_and_bucket_window()

### Community 123 - "Implementation Status live document"
Cohesion: 0.14
Nodes (16): ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, Implementation Status live document, M1.5 Pipeline bridge (UBS-48/49), M1 Log monitor and configuration (not started) (+8 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "callbacks/config.py"
Cohesion: 0.15
Nodes (7): _CallbacksYaml, _RetryYaml, _HangingSink, _make_alert(), _make_snapshot(), _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher()

### Community 127 - "Rule Engine demo runbook"
Cohesion: 0.08
Nodes (27): NoLogActivity rule, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Rule Engine, Safety and suppression (silences, grace, storm cap), SighupRuleReloader, 1. `make rules-test` (+19 more)

### Community 129 - "mock_logger.py"
Cohesion: 0.24
Nodes (6): main(), get_timestamps(), rotate_if_needed(), run_harness(), test_rotation_requires_at_least_one_archive(), test_rotation_retains_configured_number_of_archives()

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (3): Blocking CI sentinel test (FR-TST-005), Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "test_UBS_113_evaluation_loop.py"
Cohesion: 0.20
Nodes (7): _order(), _rule(), _run_ticks(), _stepping_clock(), test_the_loop_delivers_a_real_reject_spike_to_both_paths(), test_the_loop_feeds_the_correlator_gauge_to_pending_order_timeout(), _wire()

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 157 - "test_STM_03_warmup.py"
Cohesion: 0.33
Nodes (6): _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up(), test_data_from_a_restarted_bucket_is_still_merged_not_dropped(), test_restarted_bucket_count_reflects_only_buckets_a_restart_touched(), test_restarted_bucket_marks_the_instance_warming_up_for_the_warmup_window()

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (9): hb(), registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded(), test_one_stale_agent_is_partial() (+1 more)

### Community 201 - "AlertStore"
Cohesion: 0.14
Nodes (10): AlertStore, _InstanceAlerts, _is_active_status(), _StoredAlert, AlertCounts, AlertDelivery, AlertDetailResponse, AlertRecord (+2 more)

### Community 210 - "test_reporter.py"
Cohesion: 0.42
Nodes (7): make_monitor(), test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_failed_deliveries_returns_only_failed_alert_ids(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 213 - "test_readyz_shared_processor.py"
Cohesion: 0.31
Nodes (5): _batch_with_snapshot(), test_create_app_probes_the_supplied_services_own_processor(), test_create_app_rejects_a_processor_the_service_does_not_feed(), test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store(), _wait_for_status()

### Community 214 - "decimal"
Cohesion: 0.13
Nodes (9): _RuleYaml, _TierYaml, _to_rule_config(), _tier(), RuleKind, SeverityTier, ValueSource, test_gauge_evaluator_reads_consecutive_publish_failures() (+1 more)

### Community 215 - "Histogram"
Cohesion: 0.08
Nodes (16): Histogram, build_latency_summary(), compute_indicators(), compute_ratio(), RatioDef, Gauges, Indicator, Indicators (+8 more)

### Community 226 - "test_degraded_status_flows_into_heartbeat_payload"
Cohesion: 0.15
Nodes (6): test_degraded_status_flows_into_heartbeat_payload(), test_health_reporter_handles_truncation(), test_health_reporter_survives_log_rotation(), test_multi_file_group_tolerates_one_file_disappearing(), test_multi_file_health_reflects_real_tailing(), test_offset_persists_across_simulated_restart()

### Community 234 - "telemetry_agent/main.py"
Cohesion: 0.05
Nodes (30): AgentConfig, connect_reporter_to_publisher(), drop_hook(), heartbeat_provider(), provide(), Agent, build_agent(), _install_signals() (+22 more)

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **180 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `telemetry-simulator`, `telemetry-teams`, `avengers-fyp-is484` (+175 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1373 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **133 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MetricsAggregator` connect `MetricsAggregator` to `test_UBS_113_evaluation_loop.py`, `.__init__`, `LatencyCorrelator`, `derive_counters`, `test_RE_integration.py`, `demo_metrics_bridge.py`, `test_RE_session_integration.py`, `RuleEvaluator`, `test_RE_publish_integration.py`, `AggregatorConfig`, `test_UBS_113_evaluator.py`, `test_MA_03_correlation.py`, `test_UBS_112_metrics_ingestor.py`, `datetime`, `telemetry_agent_metrics_aggregator`, `_Demo`, `services/demo_quickstart.py`, `Histogram`, `ParsedMessageEvent`, `telemetry_agent/main.py`, `test_UBS_115_snapshot_to_metricstore.py`, `test_UBS_109_rule_engine_to_backend.py`, `FixParser`, `snapshot_bridge.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `Implementation Status live document` to `MetricsAggregator ring buffer`, `AggregatorConfig`, `Rule Engine demo runbook`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `HealthReporter` connect `HealthReporter` to `test_heartbeat.py`, `LogMonitor`, `UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth`, `DeliveryTracker`, `health/demo.py`, `test_parse_errors.py`, `SlidingWindowCounter`, `heartbeat_json`, `ParseResult`, `test_UBS_112_metrics_ingestor.py`, `datetime`, `test_queue_depth.py`, `telemetry_agent_metrics_aggregator`, `BackendPublisher`, `test_reporter.py`, `test_degraded_status_flows_into_heartbeat_payload`, `AgentHeartbeat`, `telemetry_agent/main.py`, `OffsetTracker`, `test_publishing_helpers.py`, `FixParser`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 73 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 73 INFERRED edges - model-reasoned connections that need verification._