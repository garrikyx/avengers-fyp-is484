# Graph Report - avengers-fyp-is484  (2026-09-27)

## Corpus Check
- 263 files · ~138,192 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 12, .example 1, .typed 1)

## Summary
- 3161 nodes · 7262 edges · 201 communities (134 shown, 67 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1065 edges (avg confidence: 0.94)
- Token cost: 647,061 input · 0 output

## Community Hubs (Navigation)
- Backend Ingestion API
- FIX Framing and Delimiters
- Trading Counter Derivation
- Reject Text Normalisation
- Publisher Demo
- FIX Fields and Identifier Hashing
- Heartbeat Emission and Sinks
- Sequence Gap Tracking
- Publish Response Classification
- Backend Outage Isolation
- FIX Timestamp Parsing
- Publish Pending Items
- Parser Demo Config
- Processed Line Dedup
- Heartbeat Emitter Tests
- Publish Sink Interface
- Log Line Identity
- Dry Run Publish Sink
- Log Monitor and Harvester
- UBS-75 Flaky Backend Sink
- Publish Buffer
- Parser Registry and AppLog
- Backend Metric Store Merge
- Publish Response Contract
- Metrics Aggregator
- Pipeline Event Queue and Commit
- Shared Ingestion Schemas
- Metric Store Buckets
- Parser Worker Pool and Registry
- Heartbeat Wire Compatibility
- Pipeline Bridge and Line Queue
- Publish Config
- Health Thresholds and Status
- Rule Engine Evaluation
- Callback Delivery Tracking
- Health Config Loading
- Agent Counter Sampler
- Aggregator Config Tests
- Log Line Classification
- HTTPS Publish Sink
- Offset Tracking and Rotation
- Backend Unreachable Integration
- Default Rule Set Tests
- Bounded Queue
- Rule Engine Integration
- Parse Error Window Tests
- Sliding Window Counter
- Snapshot Schema Models
- Callback Config
- Rule Config Loading and Reload
- Callback Sink
- Parser Demo Display
- Rule Engine Safety Valves
- Multi Log Monitor and Demo Suite
- Backend Stream Processor
- Health Demo
- Callback Payload Building
- Callback Dispatcher HTTP Tests
- Agent Health Reporter
- Shared Metrics Ratios
- Publish Queue Depth Tests
- Callback Dispatcher Demo
- Callback Dispatcher Queue
- Log Monitor File Paths
- FIX Enrichment and Enums
- Backend Publisher
- Rule Engine Demo Harness
- FIX Parser Core
- AppLog Signature Matching
- Stream Processor Warmup
- Heartbeat Receiver Stub
- Latency Histogram
- Rule Hot Reload Tests
- Retry Backoff and Self Metrics
- Latency Correlation
- Buffer Bytes and Drop Tests
- HTTP Retry Classification
- Metric Store Efficiency Tests
- Pipeline Demo
- Identifier Hashing Tests
- Alert Lifecycle FSM Tests
- Metric Store Concurrency Tests
- Rule Reload Demo
- Demo Snapshot Helpers
- Metrics Demo
- Field Allowlist Extraction
- Reject Reason Precedence
- Demo Corpus Preparation
- Log Monitor Status Tests
- .counters()
- ._serialize_counters()
- .advance_correlator()
- .skip_sequence()
- Pipeline Supervisor and Workers
- Latency Correlation Tests
- Parser to Metrics Bridge
- Metrics Event Derivation Tests
- Parser CLI
- Stream Window Alignment
- Metrics Snapshot Quickstart
- Callback Failure Integration
- Session Counter Integration
- Rule Evaluator Tests
- Snapshot Output Tests
- Pipeline Backpressure Demo
- Callback Signing
- Magic Log Simulator
- Stream Processor Demo
- Health Integration Tests
- Metric Store Memory Tests
- Rule Engine Quickstart Acts
- Parse Error Integration
- Parsed Message Event Building
- Implementation Status
- Workspace Packages
- telemetry_agent/__init__.py
- telemetry_backend/__init__.py
- simulator/__init__.py
- teams_agent/__init__.py
- CLAUDE.md
- telemetry_shared/__init__.py
- OverflowPolicy
- T
- field_validator
- model_validator
- avengers-fyp-is484
- Heartbeat Wire Contract
- Aggregator Ring Buffer and KPIs
- Rule Engine Demo Runbook
- Transport and Storage ADRs
- Health Reporter Notes and Runbooks
- Workspace Package Layout
- Magic Demo Parsing Config
- Raw Log Non-Persistence ADR
- Monitor to Parser Bridge Sizing
- Natural Language Query Layer
- Backend Outage Reliability
- Auditability & Compliance rationale (deterministic order aud
- ADR 0002: Backend in Python/FastAPI
- ADR 0003: HTTPS/JSON Transport Day-1
- ADR 0005: In-Memory Metric Store
- ADR 0006: Agent in Python
- Parser Test Obligations (§10)
- Message Validation and Parse Error Reason Codes (FR-PRS-017–
- Data Completeness Block (FR-QRY-015)
- Backend Health and Self-Metrics (FR-HLT-010)
- reject_rate anomaly baseline config (baseline_window_minutes
- 000 — Overview, Scope and Conventions
- Problem P-3: Reactive troubleshooting via manual log inspect
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
- Ingestion Endpoints (POST /telemetry/batch, /events, /heartb
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
- Latency Histograms (ack/exec/cancel_latency_ms, scope correc
- Internal Contract Schema Evolution (no version negotiation, 
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- Scaffold Plan and Open Questions
- High-Level Architecture and Flows
- Architecture and Requirement Scheme
- Architecture Constraints
- Non-Functional and Security NFRs
- Language and Framework ADRs
- Documentation Index
- Pipeline Bridge Requirements
- Log Monitor Security Requirements
- FIX Test Corpus
- FIX Field Allowlist Security
- Alert Suppression and Safety
- Live Rule Set and Provenance

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 83 edges
2. `HealthReporter` - 72 edges
3. `SourceMeta` - 65 edges
4. `MetricStore` - 58 edges
5. `make_snapshot()` - 58 edges
6. `ParseResult` - 55 edges
7. `StreamProcessorConfig` - 54 edges
8. `LineClassification` - 49 edges
9. `LogMonitor` - 45 edges
10. `BackendPublisher` - 42 edges

## Surprising Connections (you probably didn't know these)
- `AgentHeartbeat` --references--> `4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py``  [INFERRED]
  packages/telemetry_shared/src/telemetry_shared/models/health.py → docs/plan/health-reporter-overview.md
- `BackendPublisher` --references--> `UBS-5 coverage`  [INFERRED]
  apps/agent/src/telemetry_agent/publishing/publisher.py → docs/plan/rule-engine-demo.md
- `FixParser` --references--> `Going deeper, if asked`  [INFERRED]
  apps/agent/src/telemetry_agent/parser/fix/parser.py → docs/plan/rule-engine-demo.md
- `LineJoiner` --references--> `If someone asks`  [INFERRED]
  apps/agent/src/telemetry_agent/parser/fix/frame.py → docs/plan/rule-engine-demo.md
- `BufferingHeartbeatSink` --references--> `Module map (`apps/agent/src/telemetry_agent/health/`)`  [INFERRED]
  apps/agent/src/telemetry_agent/health/heartbeat.py → docs/plan/ubs58-60-notes.md

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

## Communities (201 total, 67 thin omitted)

### Community 0 - "Backend Ingestion API"
Cohesion: 0.07
Nodes (45): BatchAccepted, ErrorBody, ErrorDetail, ErrorEnvelope, ItemCounts, RejectedItem, AcceptedIngestion, IngestionService (+37 more)

### Community 1 - "FIX Framing and Delimiters"
Cohesion: 0.08
Nodes (44): DelimiterMode, FramedMessage, FrameOptions, Framer, FrameResult, LineJoiner, _check_body_length(), _check_checksum() (+36 more)

### Community 10 - "Trading Counter Derivation"
Cohesion: 0.11
Nodes (34): ReasonNormalizer, derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), top_reject_reasons(), ingest(), build_aggregator(), _exec_report_event() (+26 more)

### Community 104 - "Reject Text Normalisation"
Cohesion: 0.28
Nodes (11): RejectPattern, compile_reject_patterns(), match_reject_label(), normalize_reject_text(), test_FR_PRS_022_cardinality_overflow(), test_FR_PRS_022_normalizes_digits_and_tokens(), test_FR_PRS_022_pattern_match(), test_FR_PRS_022_unclassified_increments_flag() (+3 more)

### Community 105 - "Publisher Demo"
Cohesion: 0.23
Nodes (10): _ScriptedSink, _drain(), main(), _make_snapshot(), _print_state(), _step(), datetime, Snapshot (+2 more)

### Community 109 - "FIX Fields and Identifier Hashing"
Cohesion: 0.20
Nodes (10): FixFields, _hash_or_none(), hash_identifier(), load_hash_key(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, Fixed-shape allowlisted field set. No attribute here may hold a raw, non-…, Identifier hashing (FR-PRS-021)., HMAC-SHA256 of `raw` keyed with `key`, truncated to 16 hex chars. (+2 more)

### Community 11 - "Heartbeat Emission and Sinks"
Cohesion: 0.07
Nodes (28): BufferingHeartbeatSink, HttpHeartbeatSink, LoggingHeartbeatSink, AgentHeartbeat, HeartbeatSink, Logger, 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence (+20 more)

### Community 110 - "Sequence Gap Tracking"
Cohesion: 0.27
Nodes (7): SeqTracker, SeqGapEvent, test_FR_PRS_027_detects_gap(), test_FR_PRS_027_detects_regression(), test_FR_PRS_027_logon_resets_without_gap(), Per-session MsgSeqNum tracking., FR-PRS-027 sequence gap tests.

### Community 111 - "Publish Response Classification"
Cohesion: 0.24
Nodes (9): PublishOutcome, classify_publish_response(), test_429_carries_retry_after_seconds(), test_status_code_classification(), test_transport_error_is_backoff(), parametrize, UBS-103: HTTP response -> publish action classification (spec 007 §2.1's…, UBS-103/104: batches buffered telemetry, gzip-compresses it, and POSTs it to… (+1 more)

### Community 114 - "Backend Outage Isolation"
Cohesion: 0.23
Nodes (9): _HangingSink, _make_alert(), _make_snapshot(), _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher(), AlertEvent, Snapshot, UBS-104 integration test: `NFR-REL-003` -- a backend outage must never affect… (+1 more)

### Community 116 - "FIX Timestamp Parsing"
Cohesion: 0.27
Nodes (9): TimestampResult, parse_fix_timestamp(), test_FR_PRS_025_bad_timestamp_falls_back_to_log(), test_FR_PRS_025_parses_fix_timestamp_utc(), test_FR_PRS_026_clock_skew_uses_agent_clock(), datetime, timedelta, Parse FIX SendingTime/TransactTime as UTC. (+1 more)

### Community 117 - "Publish Pending Items"
Cohesion: 0.25
Nodes (9): PendingItem, make_pending_item(), _size_of(), datetime, PendingKind, PendingPayload, FR-PUB-004: a pending-item buffer bounded by both total bytes and maximum age,…, Measured once at insert and cached on the `PendingItem` -- re-measuring on… (+1 more)

### Community 118 - "Parser Demo Config"
Cohesion: 0.31
Nodes (9): DemoConfig, _label_match_pairs(), load_demo_config(), _parse_duration(), _string_list(), Any, Path, timedelta (+1 more)

### Community 119 - "Processed Line Dedup"
Cohesion: 0.29
Nodes (3): LinePosition, ProcessedLineDeduper, Bounded LRU cache suppressing double-count on re-read.

### Community 12 - "Heartbeat Emitter Tests"
Cohesion: 0.10
Nodes (25): HeartbeatEmitter, Collect, FakeClock, _reporter(), test_heartbeat_carries_file_state_and_lag(), test_heartbeat_payload_matches_spec_004_section_6(), test_http_sink_posts_json_and_raises_on_4xx(), test_interval_defaults_from_reporter_config() (+17 more)

### Community 120 - "Publish Sink Interface"
Cohesion: 0.20
Nodes (7): PublishSink, Logger, Protocol, BackendUnreachableCallback, DropCallback, HeartbeatProvider, The transport boundary. `HttpsPublishSink` is the Day-1 default (ADR 0003);…

### Community 125 - "Log Line Identity"
Cohesion: 0.29
Nodes (4): ReadLine, One complete log line with stable byte identity for idempotent ingest., Reads available complete lines from the file handle until EOF., Yield ``(source_name, ReadLine)`` from every configured file. Tail mode polls…

### Community 129 - "Dry Run Publish Sink"
Cohesion: 0.40
Nodes (3): DryRunPublishSink, Logger, Log the intended publish, never open a socket. Use this while there's no real…

### Community 13 - "Log Monitor and Harvester"
Cohesion: 0.08
Nodes (20): Harvester, LogMonitor, Path, stat_result, TextIO, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, Find retained rotations that were created while the agent was down. This… (+12 more)

### Community 14 - "Publish Buffer"
Cohesion: 0.10
Nodes (24): PublishBuffer, _item(), _tags(), test_an_item_larger_than_the_whole_cap_is_not_self_evicted(), test_append_and_take_preserve_fifo_order(), test_byte_overflow_drops_oldest_and_counts(), on_drop(), test_expire_drops_only_items_older_than_max_age() (+16 more)

### Community 15 - "Parser Registry and AppLog"
Cohesion: 0.08
Nodes (19): AppLogParser, AppLogTelemetry, Confidence, SlowParser, StubParser, _meta(), test_applog_parser_classifies_and_parses_magic_line(), test_applog_parser_returns_none_confidence_for_fix_line() (+11 more)

### Community 16 - "Backend Metric Store Merge"
Cohesion: 0.10
Nodes (28): IngestionConfig, _SeriesContribution, _dim_key(), _histogram_payload(), _read_one_group(), _snapshot(), test_a_metric_no_contributing_agent_reported_is_absent_not_fabricated(), test_a_metric_only_some_agents_reported_still_merges_the_ones_that_did() (+20 more)

### Community 17 - "Publish Response Contract"
Cohesion: 0.15
Nodes (30): PublishAction, PublishResult, _FakeSink, _FakeSink, make_snapshot(), _publisher(), test_202_commits_and_empties_buffer(), test_400_drops_the_whole_batch_as_one_rejection() (+22 more)

### Community 18 - "Metrics Aggregator"
Cohesion: 0.12
Nodes (19): _Bucket, MetricRow, MetricsAggregator, default_resolve_reject_reason(), _dimension_value(), datetime, Decimal, ParsedMessageEvent (+11 more)

### Community 19 - "Pipeline Event Queue and Commit"
Cohesion: 0.09
Nodes (15): DemoMetricsSink, PipelineCommitter, EventQueue, MonitorPipelineAdapter, ParsedEvent, source_meta_from_read_line(), test_committed_offset_advances_only_after_committer_ingest(), _meta() (+7 more)

### Community 2 - "Shared Ingestion Schemas"
Cohesion: 0.07
Nodes (42): BatchSequencer, EventsRequest, Heartbeat, HeartbeatFile, ResourceUsage, TelemetryBatch, TelemetryEvent, _NeverCalledSink (+34 more)

### Community 21 - "Metric Store Buckets"
Cohesion: 0.13
Nodes (17): _CanonicalBucket, MetricStore, datetime, Snapshot, Lock, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a…, Evict buckets that have aged out of retention within *one* instance's ring —… (+9 more)

### Community 23 - "Parser Worker Pool and Registry"
Cohesion: 0.08
Nodes (21): Parser, Registry, PipelineConfig, ParserWorkerPool, get_parser(), _meta(), test_block_mode_never_drops_under_backpressure(), flood() (+13 more)

### Community 26 - "Heartbeat Wire Compatibility"
Cohesion: 0.09
Nodes (28): ResourceUsage, to_ingestion_heartbeat(), make(), test_files_get_an_instance_id_which_the_contract_requires(), test_health_wire_still_available_for_the_reversal(), test_http_sink_defaults_to_the_ingestion_contract(), test_ingestion_payload_validates_against_the_real_contract(), test_measured_signals_are_carried_through_unchanged() (+20 more)

### Community 27 - "Pipeline Bridge and Line Queue"
Cohesion: 0.08
Nodes (12): QueueSnapshot, LineQueue, PipelineStats, PipelineBridge, QueuedLine, monitors_by_resolved_path(), test_pipeline_stats_expose_prometheus_metric_names(), Handoff from the log monitor to parser workers. (+4 more)

### Community 28 - "Publish Config"
Cohesion: 0.12
Nodes (30): PublishConfig, PublishConfigError, _PublishYaml, _RetryYaml, load_publish_config(), load_publish_token(), parse_publish_config(), test_allows_plain_http_when_explicitly_opted_in() (+22 more)

### Community 29 - "Health Thresholds and Status"
Cohesion: 0.10
Nodes (27): HealthThresholds, HealthSignals, _utc_now(), _file(), test_every_lagging_file_gets_its_own_reason(), test_legacy_degraded_threshold_kwarg_still_wins(), test_no_signals_is_healthy_with_no_reasons(), test_read_lag_at_threshold_is_still_healthy() (+19 more)

### Community 3 - "Rule Engine Evaluation"
Cohesion: 0.11
Nodes (35): _AlertState, AlwaysActive, RuleEngine, ScheduleChecker, MetricsGroup, MetricsSnapshot, _decimal_or_none(), _matched_condition() (+27 more)

### Community 30 - "Callback Delivery Tracking"
Cohesion: 0.11
Nodes (26): DeliveryRecord, DeliveryStatus, DeliveryTracker, test_UBS_34_each_transition_is_timestamped(), test_UBS_34_enqueue_records_pending(), test_UBS_34_immediate_success_sequence(), test_UBS_34_last_error_persists_across_terminal_transition(), test_UBS_34_retried_then_delivered_sequence() (+18 more)

### Community 31 - "Health Config Loading"
Cohesion: 0.11
Nodes (28): _AgentConfigYaml, _AgentYaml, HealthConfigError, _HealthYaml, _HeartbeatYaml, _Strict, _drop_none(), load_health_config() (+20 more)

### Community 32 - "Agent Counter Sampler"
Cohesion: 0.13
Nodes (26): AgentCounterSampler, _aggregator(), test_agent_counters_group_by_instance_only(), test_deltas_land_in_the_bucket_for_their_own_timestamp(), test_first_sample_ingests_the_whole_count_from_zero(), test_ingest_agent_counters_does_not_mark_the_agent_as_having_seen_an_event(), test_ingest_agent_counters_lands_in_the_window(), test_missing_declared_dimension_raises_naming_the_dimension() (+18 more)

### Community 33 - "Aggregator Config Tests"
Cohesion: 0.16
Nodes (24): AggregatorConfig, FakeClock, make_event(), minimal_aggregator(), test_10k_events_in_60s_window_returns_correct_count(), test_cardinality_cap_folds_overflow_into_other_and_preserves_total(), test_cardinality_cap_resets_per_bucket_not_for_process_lifetime(), test_cardinality_folded_counts_every_fold_from_either_cap() (+16 more)

### Community 34 - "Log Line Classification"
Cohesion: 0.12
Nodes (25): LineClassification, classify_line(), compile_app_log_patterns(), _looks_like_fix(), test_FR_PRS_010_fix_detected_pipe_delimited(), test_FR_PRS_010_fix_detected_soh_delimited(), test_FR_PRS_010_fix_detected_with_log_prefix(), test_FR_PRS_010_rejects_begin_string_without_delimiter_before_msg_type() (+17 more)

### Community 35 - "HTTPS Publish Sink"
Cohesion: 0.11
Nodes (23): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), _publisher(), _snapshot(), test_503_when_the_backend_queue_is_full(), test_happy_path_against_the_real_backend_app(), test_allows_plain_http_when_explicitly_opted_in() (+15 more)

### Community 37 - "Offset Tracking and Rotation"
Cohesion: 0.11
Nodes (21): OffsetTracker, _line_texts(), test_checkpoints_offsets_while_file_is_still_busy(), test_does_not_emit_an_unterminated_line_until_it_is_complete(), test_multi_monitor_validates_read_mode(), test_restart_backfills_multiple_rotations_created_while_offline(), test_restart_recovers_retained_rotation_created_while_offline(), test_rotation_drains_late_writes_from_old_descriptor() (+13 more)

### Community 39 - "Backend Unreachable Integration"
Cohesion: 0.16
Nodes (26): _ScriptedSink, _aggregator(), _engine(), _fail_n_times(), _publisher(), _rule(), _snapshot_payload(), test_a_full_minute_of_outage_yields_exactly_five_failures() (+18 more)

### Community 4 - "Default Rule Set Tests"
Cohesion: 0.12
Nodes (44): Gauges, make_gauges(), make_indicator(), make_indicators(), make_snapshot(), _gauge_rule(), test_gauge_evaluator_none_when_gauge_is_none(), test_gauge_evaluator_reads_consecutive_publish_failures() (+36 more)

### Community 40 - "Bounded Queue"
Cohesion: 0.10
Nodes (13): BoundedQueue, test_block_policy_waits_for_capacity(), test_drop_oldest_policy_discards_oldest_on_overflow(), test_zero_capacity_rejects_without_storing(), test_full_queue_blocks_producer_without_drops(), OverflowPolicy, T, OverflowPolicy (+5 more)

### Community 42 - "Rule Engine Integration"
Cohesion: 0.10
Nodes (19): CorrelatorStats, _Clock, _timedelta_to_ms(), _ack(), _ingest(), _new_order(), _rejected(), _session_reject() (+11 more)

### Community 44 - "Parse Error Window Tests"
Cohesion: 0.14
Nodes (21): FakeClock, heartbeat_json(), bad(), make(), ok(), test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides(), test_errors_counted_and_reported_in_heartbeat() (+13 more)

### Community 45 - "Sliding Window Counter"
Cohesion: 0.15
Nodes (19): SlidingWindowCounter, at(), test_capacity_is_rounded_not_floored(), test_counts_events_inside_window(), test_decays_as_window_slides(), test_event_older_than_window_is_dropped(), test_idle_window_reads_zero_not_none(), test_late_event_still_inside_window_is_counted() (+11 more)

### Community 47 - "Snapshot Schema Models"
Cohesion: 0.11
Nodes (22): AlertEvent, CamelModel, HistogramPayload, SeriesEntry, Snapshot, test_histogram_payload_requires_the_full_shape_not_a_percentile_summary(), test_parses_the_spec_004_example_verbatim(), test_to_histogram_ignores_unrecognised_bucket_keys_defensively() (+14 more)

### Community 49 - "Callback Config"
Cohesion: 0.15
Nodes (22): CallbackConfigError, CallbacksConfig, _CallbacksYaml, _RetryYaml, load_callbacks_config(), parse_callbacks_config(), test_FR_CBK_001_allows_plain_http_with_explicit_opt_in(), test_FR_CBK_001_rejects_plain_http_by_default() (+14 more)

### Community 5 - "Rule Config Loading and Reload"
Cohesion: 0.08
Nodes (38): RuleConfigError, _RuleYaml, SighupRuleReloader, _TierYaml, RuleConfig, ValueSource, load_rules(), load_rules_from_yaml() (+30 more)

### Community 50 - "Callback Sink"
Cohesion: 0.10
Nodes (17): _ScriptedSink, CallbackResult, CallbackSink, DryRunCallbackSink, test_FR_CBK_011_dry_run_logs_delivery_id_and_body(), test_FR_CBK_011_dry_run_never_opens_a_socket(), test_FR_CBK_011_dry_run_returns_synthetic_success(), Logger (+9 more)

### Community 52 - "Parser Demo Display"
Cohesion: 0.18
Nodes (23): _Style, extract_log_level(), _box_title(), _delimiter_label(), _explain_classification(), _format_field_row(), _hr(), print_demo_header() (+15 more)

### Community 53 - "Rule Engine Safety Valves"
Cohesion: 0.12
Nodes (21): RuleKind, SeverityTier, Silence, _tier(), _counter_rule(), test_dependent_suppression_when_no_log_activity_is_firing(), test_max_active_alerts_emits_one_alertstorm_and_suppresses_further(), test_schedule_inactive_skips_rule_entirely() (+13 more)

### Community 55 - "Multi Log Monitor and Demo Suite"
Cohesion: 0.12
Nodes (18): MultiLogMonitor, print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines() (+10 more)

### Community 56 - "Backend Stream Processor"
Cohesion: 0.13
Nodes (18): SnapshotOutcome, StreamProcessor, _snapshot(), test_is_ready_returns_false_before_warmup_window_elapses_even_with_data(), test_is_ready_returns_true_once_warmup_window_has_elapsed_and_data_exists(), test_is_ready_stays_false_past_warmup_window_if_no_data_ever_arrived(), test_is_ready_stays_true_once_data_has_arrived_even_if_it_later_ages_out(), test_readyz_route_reports_warming_with_503_immediately_after_startup() (+10 more)

### Community 57 - "Health Demo"
Cohesion: 0.11
Nodes (20): HeartbeatConfig, PrintHeartbeatSink, _build_parser(), main(), _main_async(), _make_sink(), _poll_forever(), Event (+12 more)

### Community 58 - "Callback Payload Building"
Cohesion: 0.15
Nodes (19): CallbackAlertPayload, from_alert_event(), make_alert_event(), test_FR_CBK_001_payload_carries_ac_required_fields(), test_FR_CBK_002_payload_under_max_bytes_for_typical_alert(), test_FR_CBK_002_serialized_payload_matches_spec_shape(), test_FR_CBK_003_runbook_url_defaults_to_none(), test_FR_CBK_003_summary_stopgap_references_rule_and_condition() (+11 more)

### Community 59 - "Callback Dispatcher HTTP Tests"
Cohesion: 0.19
Nodes (14): HttpsCallbackSink, _make_alert(), _run_one(), test_FR_CBK_001_success_marks_delivered(), handler(), test_FR_CBK_004_006_persistent_5xx_retries_then_fails_after_max_attempts(), test_FR_CBK_004_006_retries_then_succeeds(), test_FR_CBK_006_429_is_retried_not_treated_as_permanent() (+6 more)

### Community 6 - "Agent Health Reporter"
Cohesion: 0.10
Nodes (27): HealthReporter, FileReadHealth, make_monitor(), test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read() (+19 more)

### Community 61 - "Shared Metrics Ratios"
Cohesion: 0.17
Nodes (18): RatioDef, Indicator, Indicators, LatencySummary, WindowBounds, build_latency_summary(), compute_indicators(), compute_ratio() (+10 more)

### Community 62 - "Publish Queue Depth Tests"
Cohesion: 0.17
Nodes (18): FakeQueue, Flaky, make(), test_at_critical_watermark_is_unhealthy(), test_at_high_watermark_is_degraded_with_reason_and_trend(), test_below_high_watermark_is_healthy(), test_buffer_drops_oldest_when_full(), test_buffer_fills_while_downstream_is_down_and_drains_in_order() (+10 more)

### Community 63 - "Callback Dispatcher Demo"
Cohesion: 0.15
Nodes (15): CallbackDispatcher, main(), _make_alert(), _print_counters(), _run_one(), _step(), _run_dispatcher_against_a_broken_magic(), drive() (+7 more)

### Community 64 - "Callback Dispatcher Queue"
Cohesion: 0.13
Nodes (12): DropOldestQueue, test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped(), test_FR_CBK_007_overflow_drops_oldest_and_increments_counter(), Logger, T, UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, FR-CBK-007: bounded pending queue, drop-oldest on overflow. (+4 more)

### Community 65 - "Log Monitor File Paths"
Cohesion: 0.16
Nodes (13): FileReadStatus, datetime, datetime, 7. Status rollup — the one table, Log monitoring, rotation and truncation handling., Offset + read lag for this file (UBS-30). See docs/plan/ubs30-notes.md., Multi-file polling and lifecycle management for the Log Monitor., Return offset and read-lag state for every configured file. (+5 more)

### Community 66 - "FIX Enrichment and Enums"
Cohesion: 0.23
Nodes (17): FixTelemetry, build_fix_telemetry(), normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+9 more)

### Community 67 - "Backend Publisher"
Cohesion: 0.14
Nodes (10): BackendPublisher, AlertEvent, datetime, Event, Snapshot, UBS-75 / `FR-MET-031`: failed attempts in a row since the last successful…, Sync, non-blocking (`FR-PUB-007`) — never awaits, never blocks on a full buffer…, Ticks `publish_once` every `interval_seconds` until `stop` is set. First tick… (+2 more)

### Community 68 - "Rule Engine Demo Harness"
Cohesion: 0.17
Nodes (7): _Demo, Holds the one parser/aggregator/engine trio the whole story runs on, so each…, ExecType/OrdStatus 8 = Rejected, OrdRejReason 3 = ExchangeClosed., 35=3, a session-level Reject — a FIX plumbing problem rather than a trading…, 35=9, a rejected cancel/replace — counted as `cancel_rejects`, kept apart from…, An ack whose SendingTime is `delay_ms` after its order. Latency is measured…, `count` orders that each get acked — the healthy baseline volume a reject…

### Community 7 - "FIX Parser Core"
Cohesion: 0.09
Nodes (29): FixParser, ParseError, ParseResult, SourceMeta, is_parse_error(), _strip_sensitive_fields(), register_parser(), test_is_parse_error_matches_aggregator_convention() (+21 more)

### Community 73 - "AppLog Signature Matching"
Cohesion: 0.19
Nodes (12): SignatureMatcher, SignatureRule, compile_signature_rules(), resolve_label_template(), _sanitize_capture(), test_cardinality_overflow_to_other(), test_dynamic_label_gr_disconnect(), test_dynamic_label_md_disconnect() (+4 more)

### Community 74 - "Stream Processor Warmup"
Cohesion: 0.16
Nodes (16): StreamProcessorConfig, test_existing_instance_does_not_raise_on_a_half_created_instance(), test_shed_oldest_tier_does_not_raise_on_a_half_created_instance(), test_series_over_the_cardinality_cap_are_dropped_and_counted(), _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up(), test_data_from_a_restarted_bucket_is_still_merged_not_dropped() (+8 more)

### Community 75 - "Heartbeat Receiver Stub"
Cohesion: 0.15
Nodes (13): _AgentRecord, _Registry, main(), _make_handler(), do_GET(), do_POST(), _send(), _stale_watch() (+5 more)

### Community 77 - "Latency Histogram"
Cohesion: 0.15
Nodes (13): Histogram, test_merge_is_bucket_wise_addition(), test_percentile_below_min_sample_size_returns_none(), test_percentile_interpolates_within_the_identified_bucket(), test_percentile_interpolates_within_the_overflow_bucket(), test_record_above_the_largest_boundary_falls_into_overflow(), test_record_places_values_into_the_correct_exclusive_bucket(), Decimal (+5 more)

### Community 78 - "Rule Hot Reload Tests"
Cohesion: 0.27
Nodes (17): AlertStatus, _engine(), _fire(), _snapshot(), test_apply_rules_force_resolves_a_firing_alert_whose_rule_was_removed(), test_apply_rules_leaves_unrelated_rules_untouched(), test_apply_rules_preserves_state_for_a_rule_whose_name_persists(), test_apply_rules_removes_a_pending_state_without_an_event() (+9 more)

### Community 8 - "Retry Backoff and Self Metrics"
Cohesion: 0.07
Nodes (26): RetryPolicy, CounterRegistry, test_FR_CBK_004_delay_doubles_per_attempt_with_factor_2(), test_FR_CBK_004_delay_is_capped(), test_FR_CBK_004_first_attempt_is_roughly_base(), test_FR_CBK_004_jitter_stays_within_bounds(), test_FR_CBK_004_retry_after_ignored_when_smaller(), test_FR_CBK_004_retry_after_overrides_when_larger() (+18 more)

### Community 9 - "Latency Correlation"
Cohesion: 0.09
Nodes (25): LatencyCorrelator, OrderContext, CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent (+17 more)

### Community 95 - "Buffer Bytes and Drop Tests"
Cohesion: 0.16
Nodes (12): FakeClock, test_buffer_bytes_is_none_without_a_provider(), test_buffer_bytes_is_read_fresh_on_every_snapshot(), test_buffer_bytes_provider_can_be_registered_and_removed(), test_dropped_events_accumulate_within_the_window(), test_dropped_events_is_none_until_the_first_record(), test_dropped_events_reach_the_wire(), test_dropped_events_roll_off_after_the_window() (+4 more)

### Community 96 - "HTTP Retry Classification"
Cohesion: 0.25
Nodes (13): RetryDecision, classify_http_status(), test_FR_CBK_006_2xx_is_success(), test_FR_CBK_006_408_429_5xx_is_retry(), test_FR_CBK_006_non_2xx_non_4xx_5xx_falls_back_to_permanent_failure(), test_FR_CBK_006_other_4xx_is_permanent_failure(), StrEnum, parametrize (+5 more)

### Community 98 - "Metric Store Efficiency Tests"
Cohesion: 0.19
Nodes (10): _CountingRing, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to(), test_read_indexes_only_the_requested_span_not_the_whole_ring(), test_restarted_bucket_count_also_indexes_only_the_requested_span(), datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in… (+2 more)

### Community 100 - "Pipeline Demo"
Cohesion: 0.23
Nodes (12): test_demo_scenarios_run_to_completion(), test_monitor_to_parse_pipeline(), parametrize, Path, End-to-end demo: LogMonitor → queue → parse → output → commit., shutil, telemetry_agent_logs_multi_log_monitor, telemetry_agent_parser_fix_parser (+4 more)

### Community 101 - "Identifier Hashing Tests"
Cohesion: 0.14
Nodes (3): FR-PRS-021 identifier hashing tests., telemetry_agent_parser_fix_fields, telemetry_agent_parser_fix_identifiers

### Community 102 - "Alert Lifecycle FSM Tests"
Cohesion: 0.35
Nodes (13): _engine(), _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved(), test_pending_fires_after_for_elapsed(), test_pending_reverts_to_inactive_if_condition_clears_before_for_elapsed() (+5 more)

### Community 103 - "Metric Store Concurrency Tests"
Cohesion: 0.15
Nodes (13): _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another(), write_a(), test_concurrent_drops_across_many_instances_are_all_counted(), drop_one(), test_concurrent_merges_into_the_same_instance_do_not_lose_updates(), write(), test_concurrent_stale_rejections_across_many_instances_are_all_counted() (+5 more)

### Community 106 - "Rule Reload Demo"
Cohesion: 0.23
Nodes (12): _banner(), _instructions(), main(), _run(), _safe_rule_count(), Path, Live walkthrough of SIGHUP rule reloading (`FR-RUL-008`/`009`). uv run python…, The watched file may be mid-edit or deliberately broken; a failed read here… (+4 more)

### Community 112 - "Demo Snapshot Helpers"
Cohesion: 0.18
Nodes (5): AlertEvent, Metric reference — what each rule reads, and where its number came from, Always with the correlator attached — that's what populates the `latency`…, Evaluate twice: once to move a matched rule to `pending`, then again past its…, One evaluation a moment later — enough for a tier escalation, which takes…

### Community 115 - "Metrics Demo"
Cohesion: 0.36
Nodes (10): _banner(), _implementation(), _line(), main(), _result(), _story(), _watch(), _wrap() (+2 more)

### Community 121 - "Field Allowlist Extraction"
Cohesion: 0.31
Nodes (8): extract_allowlisted_fields(), test_FR_PRS_020_excluded_tags_never_appear_in_output(), test_FR_PRS_020_fixed_struct_has_no_dict_no_map_allocation(), test_FR_PRS_020_missing_tags_default_to_none(), test_FR_PRS_020_only_allowlisted_tags_extracted(), FR-PRS-020: extract only the tags in the compile-time allowlist above.…, FR-PRS-020 / NFR-SEC-002 / NFR-PERF-004 allowlisted field extraction tests., NFR-PERF-004: fixed slotted struct, not a dict, per parsed message.

### Community 122 - "Reject Reason Precedence"
Cohesion: 0.33
Nodes (7): effective_reject_reason(), test_FR_PRS_024_ord_rej_reason_wins(), test_FR_PRS_024_session_reject_for_msg_type_reject(), test_FR_PRS_024_text_label_when_no_ord_rej(), test_FR_PRS_024_unspecified_when_missing(), Single precedence: ordRejReason → rejectReasonText label → unspecified. For…, FR-PRS-024 rejection precedence tests.

### Community 126 - "Demo Corpus Preparation"
Cohesion: 0.33
Nodes (6): demo_log_lines(), prepare_corpus_line(), Path, Synthetic FIX corpus loading helpers., Strip trailing `` # source.txt`` annotation from merged corpus lines., Return parsed corpus lines, optionally filtered to one source file label.

### Community 128 - "Log Monitor Status Tests"
Cohesion: 0.62
Nodes (6): make_monitor(), test_status_after_read_reports_elapsed_lag(), test_status_before_any_read_has_no_lag(), test_status_missing_file_has_no_size_but_does_not_raise(), test_status_reports_offset_progress_between_polls(), Path

### Community 20 - "Pipeline Supervisor and Workers"
Cohesion: 0.14
Nodes (18): _meta(), test_event_queue_defaults_to_256_capacity(), test_event_queue_drop_oldest_when_configured(), test_line_queue_defaults_to_2048_capacity(), test_line_queue_drop_oldest_when_configured(), Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)., Idempotent ingest dedupe by file byte position (FR-PIP-007)., Parser → aggregator bounded event queue (FR-PIP-004). (+10 more)

### Community 36 - "Latency Correlation Tests"
Cohesion: 0.18
Nodes (29): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), replaced() (+21 more)

### Community 43 - "Parser to Metrics Bridge"
Cohesion: 0.13
Nodes (24): _fixed_now(), main(), _step(), derive_parser_counters(), derive_session_counters(), _parse_error_reason(), _parse_transact_time(), parser_counter_dims() (+16 more)

### Community 48 - "Metrics Event Derivation Tests"
Cohesion: 0.13
Nodes (25): _meta(), _parser_counters(), _session_counters(), test_a_clean_fix_line_is_not_a_parse_error(), test_clean_line_reports_no_reason(), test_every_derived_session_counter_is_declared_in_counter_dimensions(), test_every_line_counts_toward_log_lines_read(), test_logon_derives_the_logons_counter() (+17 more)

### Community 51 - "Parser CLI"
Cohesion: 0.16
Nodes (23): main(), _corpus_files(), _fields_dict(), _format_line_result(), _load_config(), main(), _parse_line(), _record_metrics() (+15 more)

### Community 54 - "Stream Window Alignment"
Cohesion: 0.11
Nodes (24): align_to_canonical(), _snapshot(), test_a_stale_direct_merge_is_counted_not_silently_dropped(), test_alignment_floors_a_phase_shifted_bucket_onto_the_canonical_grid(), test_alignment_is_a_no_op_when_already_on_the_grid(), test_bucket_older_than_max_bucket_age_is_rejected_and_counted_as_dropped(), test_config_rejects_a_non_positive_max_series_per_bucket(), test_config_rejects_a_non_positive_memory_limit() (+16 more)

### Community 60 - "Metrics Snapshot Quickstart"
Cohesion: 0.13
Nodes (19): main(), ingest(), _step(), _build_gauges(), snapshot(), _fixed_now(), _ingest(), test_counters_and_latency_coexist_on_one_shared_aggregator() (+11 more)

### Community 70 - "Callback Failure Integration"
Cohesion: 0.20
Nodes (18): _aggregator(), _alert(), _dispatch(), _drain(), _fire(), _rule(), test_callback_failures_do_not_make_a_log_starved_agent_look_alive(), test_four_permanent_failures_fire_callback_failing() (+10 more)

### Community 71 - "Session Counter Integration"
Cohesion: 0.21
Nodes (19): _counters(), _fire(), _ingest(), _rule(), test_fix_session_down_fires_without_any_heartbeat_timeouts_producer(), test_healthy_session_produces_no_session_counters_and_fires_nothing(), test_logout_in_the_log_fires_fix_session_down_as_critical(), test_sequence_jump_in_the_log_fires_seq_gap_detected() (+11 more)

### Community 72 - "Rule Evaluator Tests"
Cohesion: 0.20
Nodes (19): make_latency(), _absence_rule(), _latency_rule(), _rate_rule(), test_absence_evaluator_fires_when_guard_satisfied_and_metric_is_zero(), test_absence_evaluator_guard_unmet_returns_none_not_zero(), test_absence_evaluator_without_guard_reads_metric_directly(), test_latency_evaluator_insufficient_when_count_below_rules_own_min_samples() (+11 more)

### Community 82 - "Snapshot Output Tests"
Cohesion: 0.23
Nodes (16): hand_labelled_events(), _ingest_all(), _shared_config(), test_gauges_are_empty_without_a_correlator(), test_gauges_reflect_pending_orders_and_event_staleness(), test_grouped_breakdown_by_symbol(), test_indicators_computed_from_hand_labelled_fixture(), test_latency_summary_present_for_recorded_histograms() (+8 more)

### Community 83 - "Pipeline Backpressure Demo"
Cohesion: 0.18
Nodes (14): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), run_happy_path(), run_slow_parser_backpressure(), DemoConfig (+6 more)

### Community 84 - "Callback Signing"
Cohesion: 0.18
Nodes (15): load_callback_secret(), sign(), test_FR_CBK_005_different_body_produces_different_signature(), test_FR_CBK_005_different_secret_produces_different_signature(), test_FR_CBK_005_different_timestamp_produces_different_signature(), test_FR_CBK_005_load_callback_secret_fails_fast_when_empty(), test_FR_CBK_005_load_callback_secret_fails_fast_when_unset(), test_FR_CBK_005_load_callback_secret_reads_env_var() (+7 more)

### Community 85 - "Magic Log Simulator"
Cohesion: 0.18
Nodes (12): main(), get_timestamps(), rotate_if_needed(), run_harness(), test_rotation_requires_at_least_one_archive(), test_rotation_retains_configured_number_of_archives(), Path, Path (+4 more)

### Community 86 - "Stream Processor Demo"
Cohesion: 0.24
Nodes (16): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), _reject(), _run_hong_kong_session(), _run_singapore_session() (+8 more)

### Community 89 - "Health Integration Tests"
Cohesion: 0.15
Nodes (16): test_degraded_status_flows_into_heartbeat_payload(), test_health_reporter_handles_truncation(), test_health_reporter_survives_log_rotation(), test_multi_file_group_tolerates_one_file_disappearing(), test_multi_file_health_reflects_real_tailing(), test_offset_persists_across_simulated_restart(), Path, Integration tests for UBS-30 (FR-LOG-010, FR-HLT-001). Unlike… (+8 more)

### Community 90 - "Metric Store Memory Tests"
Cohesion: 0.17
Nodes (15): _snapshot(), test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell(), test_estimated_memory_bytes_grows_with_merged_series_and_shrinks_on_eviction(), test_estimated_memory_bytes_is_zero_for_an_empty_store(), test_merge_alone_can_trigger_shedding_without_an_external_tick(), test_merges_within_the_throttle_interval_do_not_re_check_memory(), test_shedding_never_evicts_a_bucket_written_in_the_same_cycle_at_small_capacity(), test_tick_logs_a_warning_above_memory_warn_percent_but_does_not_shed() (+7 more)

### Community 91 - "Rule Engine Quickstart Acts"
Cohesion: 0.22
Nodes (13): _alert_storm_act(), _backend_unreachable_act(), _dedup_act(), main(), _no_log_activity_act(), _part(), _show_alerts(), _step() (+5 more)

### Community 94 - "Parse Error Integration"
Cohesion: 0.23
Nodes (15): _fire(), _ingest(), _rate(), test_a_clean_log_never_fires(), test_a_mostly_unparseable_log_escalates_to_critical(), test_below_min_samples_reads_insufficient_data_not_a_fire(), test_buffered_failures_alone_cannot_reach_the_critical_tier(), test_errors_are_attributable_to_a_reason() (+7 more)

### Community 97 - "Parsed Message Event Building"
Cohesion: 0.21
Nodes (15): build_parsed_message_event(), _parse(), test_execution_report_reject_maps_reason_code(), test_malformed_message_falls_back_to_base_event_instead_of_raising(), test_missing_comp_ids_fall_back_to_unknown_session_id(), test_missing_hash_key_still_builds_event_without_correlation_ids(), test_new_order_single_maps_to_new_order_event_with_normalized_enums(), test_non_fix_line_produces_no_event() (+7 more)

### Community 123 - "Implementation Status"
Cohesion: 0.31
Nodes (9): Known rough edges, M4 — Backend Ingestion, Store, Query, M1 Log monitor and configuration (not started), M2 FIX parser (UBS-40-47), M3 Metrics aggregation (MA-01-04), Backend Metric Store and cross-agent merge, Backend Stream Processor (UBS-88), Implementation Status live document (+1 more)

### Community 134 - "Workspace Packages"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 24 - "Heartbeat Wire Contract"
Cohesion: 0.09
Nodes (32): AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry, HeartbeatConfig / HealthThresholds / load_health_config, HealthSignals sampled instant (+24 more)

### Community 41 - "Aggregator Ring Buffer and KPIs"
Cohesion: 0.10
Nodes (28): MA-04: calculated indicators and snapshot output., AckLatencyBreach rule, ParseErrorRate rule, is_parse_error() definition, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, M1.5 Pipeline bridge (UBS-48/49) (+20 more)

### Community 87 - "Rule Engine Demo Runbook"
Cohesion: 0.14
Nodes (16): 1. `make rules-test`, 3. `make rules-reload-demo`, Going deeper, if asked, Pre-flight, Rule Engine demo runbook, Spoken script — sponsor demo (~3 min), The 5-minute version, The four edits (+8 more)

### Community 107 - "Transport and Storage ADRs"
Cohesion: 0.15
Nodes (13): gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups), agent metrics/ module (rolling metrics and aggregation), PostgreSQL (Day-2 historical metrics) (+5 more)

### Community 108 - "Health Reporter Notes and Runbooks"
Cohesion: 0.17
Nodes (13): M1 — Log Monitor and Configuration, Health Reporter, MultiLogMonitor (Stopgap), UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration, Health Reporter (component), Health Reporter Heartbeat Requirement (FR-HLT-001) (+5 more)

### Community 113 - "Workspace Package Layout"
Cohesion: 0.21
Nodes (12): AgentHeartbeat shared schema, AlertEvent shared schema, MetricSnapshot shared schema, Redis (Day-1 shared telemetry state), TelemetryEvent shared schema, docker compose redis service (redis:7-alpine, port 6379), Magic Simulator (apps/simulator), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 124 - "Magic Demo Parsing Config"
Cohesion: 0.32
Nodes (8): appLogPatterns regex, errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set, reject_text.txt scenario (ExecutionReport reject reasons), demo_config.yaml (Magic parsing demo config)

### Community 130 - "Raw Log Non-Persistence ADR"
Cohesion: 0.40
Nodes (5): Blocking CI sentinel test (FR-TST-005), Compile-time field allowlist mechanism, Identifier hashing with HMAC key, Note: raw log payloads must not be persisted permanently, ADR 0004: Raw log content is never persisted or transmitted

### Community 131 - "Monitor to Parser Bridge Sizing"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "Natural Language Query Layer"
Cohesion: 0.40
Nodes (5): Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents), NL Intent Catalogue (FR-NLQ-003/004), 008 — Natural Language Query Layer (Copilot/Teams)

### Community 133 - "Backend Outage Reliability"
Cohesion: 0.50
Nodes (5): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), NFR-REL-003: Backend Outage Must Not Affect Alerting, Reliability NFRs (§2), Runbook: Backend Unreachable

### Community 22 - "Scaffold Plan and Open Questions"
Cohesion: 0.08
Nodes (35): Callback Dispatcher, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent, Q-2 — Callback Protocol Magic Will Support, Q-3 — Auth Model for Backend APIs and Teams/Copilot (+27 more)

### Community 25 - "High-Level Architecture and Flows"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 46 - "Architecture and Requirement Scheme"
Cohesion: 0.11
Nodes (26): Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), Ingestion Service (component), Log Monitor (component), Metric Store (component) (+18 more)

### Community 69 - "Architecture Constraints"
Cohesion: 0.13
Nodes (20): Spec 004: Telemetry data model, Magic simulator for development, Unified Telemetry Intelligence (Magic), Identity fields (§1), Callback dispatch requirements (§3.1), Callback flow (§3.2), Callback payload and CallbackSink seam (§3.3), callbacks: Callback Dispatcher config block (+12 more)

### Community 76 - "Non-Functional and Security NFRs"
Cohesion: 0.11
Nodes (19): Resource Discipline (§9), Backend Configuration and Secrets (§9), Compliance and Operability Constraints (§7), Configurability NFRs (§5), NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-SCA-001: Agent Independence/Statelessness, NFR-SEC-004: Secrets from Environment Only (+11 more)

### Community 79 - "Language and Framework ADRs"
Cohesion: 0.16
Nodes (18): C++ candidate (rejected: worst-case failure modes), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), .NET alternative (rejected), FastAPI framework, Go for both components alternative (rejected) (+10 more)

### Community 80 - "Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements"
Cohesion: 0.12
Nodes (18): Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Parser Engine Agent-Level Contract (FR-PRS-001–003), Parser Invocation via Pipeline Bridge (§0), Parser Plugin Interface (Python Protocol, FR-PRS-030–032), FIX Parser Corpus (FR-TST-002/003) (+10 more)

### Community 88 - "Log Monitor Security Requirements"
Cohesion: 0.12
Nodes (17): Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025), NFR-SEC-015: Canonicalised Allowed Roots, Symlinks Refused, Security: Input Handling (§3.4), Agent Configuration Schema (§1), End-to-End Acceptance Scenario (FR-TST-010) (+9 more)

### Community 92 - "FIX Test Corpus"
Cohesion: 0.13
Nodes (16): Financial Information eXchange Stream (Fix.log), FIX Protocol Version 4.2, agent parser/ module (FIX parsing - M2), app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input) (+8 more)

### Community 93 - "FIX Field Allowlist Security"
Cohesion: 0.16
Nodes (16): Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test), NFR-SEC-012: Order Identifier Hashing, Rotatable Key, NFR-SEC-013: No Raw-Log Debug Mode in Release Build, Security: Data Minimisation (§3.1) (+8 more)

### Community 127 - "Alert Suppression and Safety"
Cohesion: 0.33
Nodes (7): NoLogActivity rule, Safety and suppression (silences, grace, storm cap), Event type catalogue (§2.1), Event envelope (§2), Alert lifecycle requirements (§2), Suppression and safety (§4), Dependent suppression (FR-RUL-021)

### Community 38 - "Live Rule Set and Provenance"
Cohesion: 0.11
Nodes (29): Agent processing pipeline (monitor to health reporter), BackendUnreachable rule, CallbackFailing rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule (+21 more)

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **179 isolated node(s):** `1. What the Health Reporter is for`, `2.1 One heartbeat tick, as a sequence`, `5.1 The window — `health/window.py``, `9. How to verify / demo`, `Also touched, and why` (+174 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1073 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **67 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `Aggregator Ring Buffer and KPIs` to `Snapshot Output Tests`, `Implementation Status`, `Live Rule Set and Provenance`, `Rule Engine Demo Runbook`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `Telemetry System Documentation Index` connect `Documentation Index` to `Raw Log Non-Persistence ADR`, `Transport and Storage ADRs`, `Architecture Constraints`, `Language and Framework ADRs`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `Spec 004: Telemetry data model` connect `Architecture Constraints` to `Documentation Index`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Are the 52 inferred relationships involving `MetricsAggregator` (e.g. with `_new_aggregator()` and `build_aggregator()`) actually correct?**
  _`MetricsAggregator` has 52 INFERRED edges - model-reasoned connections that need verification._