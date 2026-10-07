# Graph Report - avengers-fyp-is484  (2026-10-07)

## Corpus Check
- 307 files · ~168,703 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 12, .example 1, .typed 1)

## Summary
- 3957 nodes · 10308 edges · 267 communities (142 shown, 125 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 1839 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ffdf0498`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- telemetry_backend/main.py
- frame.py
- test_metrics_event.py
- RuleEngine
- make_snapshot
- config_loader.py
- reporter.py
- test_RE_02_evaluators.py
- RetryPolicy
- LatencyCorrelator
- derive_counters
- test_RE_integration.py
- test_heartbeat.py
- LogMonitor
- PublishBuffer
- Confidence
- collections_abc
- PublishResult
- MetricsAggregator
- HealthSignals
- PipelineBridge
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- to_ingestion_heartbeat
- alerts.py
- parse_publish_config
- display.py
- DeliveryTracker
- telemetry_agent/config.py
- test_RE_publish_integration.py
- AggregatorConfig
- fix/parser.py
- test_UBS_113_evaluator.py
- test_MA_03_correlation.py
- pathlib
- config/rules.yaml live rule set
- test_health_monitor_e2e.py
- SourceMeta
- MetricsAggregator ring buffer
- services/self_metrics.py
- FixParser
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- heartbeat_json
- callbacks/config.py
- CallbackResult
- telemetry_agent_parser_applog_parser
- cli.py
- SeverityTier
- test_health_endpoints.py
- test_UBS_112_metrics_ingestor.py
- test_STM_02_merge_semantics.py
- metrics_event.py
- test_FR_CBK_001_002_003_payload.py
- CallbackDispatcher
- CounterRegistry
- SignatureMatcher
- test_queue_depth.py
- AgentRegistry
- dispatcher.py
- SeqTracker
- enrich.py
- BackendPublisher
- rules/demo_quickstart.py
- Telemetry Agent (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- parse_fix_timestamp
- datetime
- http
- 009 — Non-Functional Requirements and Security
- Histogram
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- test_RE_parse_error_integration.py
- pipeline_demo.py
- AlertEvent
- telemetry_agent/demo_suite.py
- services/demo_quickstart.py
- telemetry_agent_common_self_metrics
- Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing)
- _FlakyBackendSink
- test_ING_004_008_routes.py
- End-to-End Acceptance Scenario (FR-TST-010)
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- build_batch
- Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)
- telemetry_agent_callbacks_backoff
- StreamProcessorConfig
- test_STM_04_efficiency.py
- ParsedMessageEvent
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- decimal
- test_agent_registry.py
- AgentHeartbeat
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- health-reporter-overview.md
- telemetry_backend/config.py
- test_log_monitor_status.py
- 008 — Natural Language Query Layer (Copilot/Teams)
- test_QRY_03_memory.py
- telemetry_shared shared schema package
- ._make_key
- Requirement ID Scheme (FR-<AREA>-<NNN>)
- NFR-REL-003: Backend Outage Must Not Affect Alerting
- test_reporter.py
- test_UBS_109_rule_engine_to_backend.py
- test_snapshot.py
- publishing/demo_quickstart.py
- Stream Processor (component)
- Query Engine Requirements (FR-QRY-006–014)
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- test_UBS_104_outage_isolation.py
- telemetry_agent_parser_applog_signatures
- Rule Engine demo runbook
- DryRunCallbackSink
- effective_reject_reason
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- test_UBS_113_evaluation_loop.py
- publishing/__init__.py
- telemetry-shared
- telemetry_agent_parser_applog_telemetry
- telemetry_agent_parser_config
- telemetry_agent_callbacks_payload
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
- create_app
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
- align_to_canonical
- telemetry_shared_metrics
- telemetry_shared_metrics_histogram
- normalize.py
- telemetry_agent_common_backoff
- demo_reload.py
- test_UBS_103_publisher_backend.py
- test_readyz_shared_processor.py
- ._serialize_counters
- HttpsPublishSink
- .identities_match_batch
- http_server
- telemetry_agent_callbacks_config
- telemetry_agent_logs_log_monitor
- telemetry_agent_logs_offset_tracker
- telemetry_agent_parser_fix_fields
- .__init__
- telemetry_agent_parser_fix_seq_tracker
- telemetry_agent_parser_fix_timestamps
- HealthReporter
- telemetry_agent_callbacks_dispatcher
- telemetry_agent_callbacks_sink
- HeartbeatEmitter
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
- telemetry_agent_publishing_config
- telemetry_agent_publishing_publisher
- telemetry_agent_publishing_sink
- telemetry_shared_models_alerts
- telemetry_shared_models_metrics
- urllib_error
- urllib_request

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 101 edges
2. `HealthReporter` - 94 edges
3. `BackendPublisher` - 74 edges
4. `AlertEvent` - 74 edges
5. `SourceMeta` - 73 edges
6. `FixParser` - 72 edges
7. `ParseResult` - 62 edges
8. `StreamProcessorConfig` - 62 edges
9. `create_app()` - 62 edges
10. `LogMonitor` - 61 edges

## Surprising Connections (you probably didn't know these)
- `Missing downstream / upstream (what this branch cannot prove)` --references--> `BufferingHeartbeatSink`  [INFERRED]
  docs/plan/ubs58-60-notes.md → apps/agent/src/telemetry_agent/health/heartbeat.py
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py
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

## Communities (267 total, 125 thin omitted)

### Community 0 - "telemetry_backend/main.py"
Cohesion: 0.08
Nodes (31): HTTP routers, one file per concern (spec 007). `health.py` (UBS-69) serves the…, AlertsQueryParams, _build_parser(), get_alert(), invalid_payload(), list_alerts(), create_internal_app(), _error_response() (+23 more)

### Community 1 - "frame.py"
Cohesion: 0.08
Nodes (41): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+33 more)

### Community 2 - "test_metrics_event.py"
Cohesion: 0.06
Nodes (69): build_parsed_message_event(), Construct the Metrics Aggregator's event from one framed FIX line. Returns None…, _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), Decimal (+61 more)

### Community 3 - "RuleEngine"
Cohesion: 0.09
Nodes (34): _AlertState, AlwaysActive, _decimal_or_none(), _matched_condition(), _metric_context(), datetime, Decimal, Protocol (+26 more)

### Community 4 - "make_snapshot"
Cohesion: 0.18
Nodes (32): make_gauges(), make_indicator(), make_indicators(), make_latency(), make_snapshot(), datetime, Decimal, Shared test support for the rules package: builds `MetricsSnapshot` fixtures… (+24 more)

### Community 5 - "config_loader.py"
Cohesion: 0.10
Nodes (32): load_rules(), load_rules_from_yaml(), _parse_duration_seconds(), Any, BaseModel, Exception, field_validator, Path (+24 more)

### Community 6 - "reporter.py"
Cohesion: 0.09
Nodes (19): datetime, Health Reporter: per-file read lag (UBS-30), status rollup and heartbeat…, Per-file read health, keyed by the same name `monitors` was built with., Worst-case lag across files (heartbeat gauge). None if none have read yet., Files whose lag exceeds the threshold. Unread files are never flagged., Count a parse error from a producer that does not hand over a `ParseResult`…, Count successfully parsed lines in bulk (denominator only)., Count `n` buffer-eviction drops (`droppedEventsLast5Min`, `FR-PUB-004`) at… (+11 more)

### Community 7 - "test_RE_02_evaluators.py"
Cohesion: 0.16
Nodes (31): _read_observed(), StrEnum, FR-RUL-001: Day-1 supports exactly these five., Where a rule's observed value is read from in a MetricsSnapshot., RuleKind, ValueSource, _absence_rule(), _gauge_rule() (+23 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.13
Nodes (17): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, random, FR-CBK-004 exponential backoff with jitter tests., test_FR_CBK_004_delay_doubles_per_attempt_with_factor_2() (+9 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.10
Nodes (18): CorrelatorStats, LatencyCorrelator, OrderContext, Clock, datetime, Decimal, timedelta, MA-03: order correlation and latency. Standalone producer into the shared… (+10 more)

### Community 10 - "derive_counters"
Cohesion: 0.09
Nodes (42): derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MA-02: order / execution / reject counters and reject-reason normalisation.…, All four counter families in one event walk., fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not OrdStatus —…, Config-driven raw-reason -> canonical-label mapping. Backs MetricsAggregator's… (+34 more)

### Community 11 - "test_RE_integration.py"
Cohesion: 0.21
Nodes (10): _ack(), _Clock, _ingest(), _new_order(), RE-05: Metrics Aggregator -> snapshot() -> Rule Engine, using real…, Mutable clock shared by the aggregator and correlator, same pattern as…, _rejected(), _session_reject() (+2 more)

### Community 12 - "test_heartbeat.py"
Cohesion: 0.12
Nodes (22): HeartbeatEmitter, Event, Tick every `interval_seconds` until `stop` is set. First tick is immediate so a…, Collect, FakeClock, datetime, LogCaptureFixture, UBS-58 / FR-HLT-001: heartbeat emitter and wire format. (+14 more)

### Community 13 - "LogMonitor"
Cohesion: 0.06
Nodes (27): Harvester, LogMonitor, datetime, Path, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, Find retained rotations that were created while the agent was down. This…, Keep a rotated descriptor alive to collect its final writes. (+19 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.09
Nodes (27): PendingItem, PublishBuffer, datetime, FR-PUB-004: a pending-item buffer bounded by both total bytes and maximum age,…, Put previously-`take`n items back at the front, in original order -- they are…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both…, Drop items older than `max_age_seconds`. The deque is strictly insertion-…, Remove and return up to `max_items` from the front. (+19 more)

### Community 15 - "Confidence"
Cohesion: 0.06
Nodes (28): Confidence, Parser, Enum, Protocol, str, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'. (+20 more)

### Community 16 - "collections_abc"
Cohesion: 0.06
Nodes (39): UBS-74: bridges the agent's own since-startup counters into the windowed…, main(), ingest(), Minimal walkthrough of the Metrics Aggregator (MA-01–04). uv run python -m…, _step(), _build_gauges(), datetime, MA-04: calculated indicators and snapshot output. Wraps the already-tested… (+31 more)

### Community 17 - "PublishResult"
Cohesion: 0.15
Nodes (29): PublishAction, StrEnum, PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, make_snapshot(), _FakeSink, _publisher(), LogCaptureFixture (+21 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.12
Nodes (18): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator, Clock, datetime, Decimal (+10 more)

### Community 19 - "HealthSignals"
Cohesion: 0.11
Nodes (23): AgentStatus, HealthSignals, FR-HLT-002 rollup for the signals that exist; FR-HLT-003 reasons. Each rule…, spec 011 s1.1: publish queue depth >= critical watermark unhealthy, >= high…, spec 011 s2: parse error rate > 25% unhealthy, > 1% degraded., Everything `derive_status` looks at, sampled at one instant. `None` means the…, Also touched, and why, Design points (+15 more)

### Community 20 - "PipelineBridge"
Cohesion: 0.10
Nodes (20): Selects the first parser in a configured chain with Confidence.HIGH., Return unknown parser names in chain., Registry, PipelineConfig, Pipeline bridge sizing (spec 010 §pipeline, FR-PIP-002–004)., PipelineStats, Queue depths and drop counters for heartbeat/metrics (FR-PIP-005)., PipelineBridge (+12 more)

### Community 21 - "MetricStore"
Cohesion: 0.13
Nodes (16): _CanonicalBucket, MetricStore, datetime, Lock, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a…, Evict buckets that have aged out of retention within *one* instance's ring —…, Evict stale buckets across every instance's ring and check memory pressure. For… (+8 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.07
Nodes (36): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+28 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.14
Nodes (33): _key(), _keys(), _observe(), UBS-106: SessionHeartbeatTracker — the `heartbeat_timeouts` producer. A…, A logged-out session is silent forever. Counting that as a timeout would…, SeqTracker accepts both normalized names and raw tag values ("Logon"/"A");…, FIX only requires a Heartbeat when the session is otherwise idle, so a session…, Session keys from a timed_out() result, for terse assertions. (+25 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.11
Nodes (27): health: threshold config block, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry, HealthSignals sampled instant (+19 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "to_ingestion_heartbeat"
Cohesion: 0.18
Nodes (17): provide(), Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat(), telemetry_agent_health_wire, make(), UBS-58/66 wire compatibility: our heartbeat flattened to the Ingestion…, The whole point: the Ingestion Service must accept what we send., The ingestion contract has no null for these; the cost is recorded in the notes… (+9 more)

### Community 27 - "alerts.py"
Cohesion: 0.09
Nodes (23): AlertingConfig, Backend-owned alerting rules (spec 005 `FR-RUL-030`)., datetime, Shared service instances the routers reach through `request.app.state`. One…, _utc_now(), backend_alert_id(), HeartbeatMonitor, datetime (+15 more)

### Community 28 - "parse_publish_config"
Cohesion: 0.12
Nodes (31): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, _PublishYaml, Any, BaseModel (+23 more)

### Community 29 - "display.py"
Cohesion: 0.21
Nodes (20): _box_title(), _delimiter_label(), _explain_classification(), _format_field_row(), _hr(), print_demo_header(), print_demo_summary(), Pattern (+12 more)

### Community 30 - "DeliveryTracker"
Cohesion: 0.11
Nodes (25): DeliveryRecord, DeliveryStatus, DeliveryTracker, datetime, StrEnum, UBS-34: per-alert-occurrence callback delivery status, timestamped at each…, UBS-34 AC: every dispatched callback has exactly one of these five states at…, One alert's current delivery state. `attempt_count` and `last_error` are… (+17 more)

### Community 31 - "telemetry_agent/config.py"
Cohesion: 0.06
Nodes (62): AgentConfigError, load_agent_config(), LogsConfig, _LogsYaml, _PipelineYaml, Any, BaseModel, Exception (+54 more)

### Community 32 - "test_RE_publish_integration.py"
Cohesion: 0.06
Nodes (62): AgentCounterSampler, datetime, Turns monotonic since-startup counters into per-bucket deltas. Stateful across…, Ingest the increase in each tracked counter since the last call. The first call…, telemetry_agent_metrics_agent_counters, _aggregator(), _alert(), _dispatch() (+54 more)

### Community 33 - "AggregatorConfig"
Cohesion: 0.13
Nodes (35): AggregatorConfig, Bucket granularity, retained windows, and the per-metric dimension table (FR-…, FakeClock, hand_labelled_events(), Shared test support for the metrics package: a hand-labelled synthetic FIX-…, A `Clock` (`() -> float`) that only advances when told to — lets a test assert…, make_event(), minimal_aggregator() (+27 more)

### Community 34 - "fix/parser.py"
Cohesion: 0.14
Nodes (24): classify_line(), compile_app_log_patterns(), _looks_like_fix(), Pattern, Line classification (FR-PRS-010, FR-PRS-011)., Classify a log line before parsing (FR-PRS-010). Order: fix → app_log →…, True when 8=FIX/8=FIXT is followed by a delimiter and 35= within the window.…, Compile configured app-log regexes for use after FIX detection fails. (+16 more)

### Community 35 - "test_UBS_113_evaluator.py"
Cohesion: 0.10
Nodes (27): _Clock, _names(), datetime, Lock, Path, UBS-113: RuleEvaluator — the periodic loop between the metrics store and…, Write counters straight into the store, labelled with placeholder dimension…, RejectSpike reads 1m, HighRejectRate reads 5m: one tick, both. (+19 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "pathlib"
Cohesion: 0.06
Nodes (53): print_header(), run_demo(), setup_environment(), main(), Log monitoring, rotation and truncation handling., One complete log line with stable byte identity for idempotent ingest., ReadLine, MultiLogMonitor (+45 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.10
Nodes (31): Agent processing pipeline (monitor to health reporter), publish: Backend Publisher config block, BackendUnreachable rule, CallbackFailing rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule (+23 more)

### Community 39 - "test_health_monitor_e2e.py"
Cohesion: 0.11
Nodes (20): fastapi_testclient, committed_offsets(), FakeClock, fix_lines(), datetime, FastAPI, fixture, MonkeyPatch (+12 more)

### Community 40 - "SourceMeta"
Cohesion: 0.05
Nodes (41): Demo metrics sink for parser CLI (mirrors spec 004 counter names)., Metadata attached to each log line by the monitor., SourceMeta, QueueSnapshot, PipelineCommitter, Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)., Consumes ParsedEvent objects and commits file offsets after ingest., LinePosition (+33 more)

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.12
Nodes (23): AckLatencyBreach rule, ParseErrorRate rule, is_parse_error() definition, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent) (+15 more)

### Community 42 - "services/self_metrics.py"
Cohesion: 0.07
Nodes (34): _BoundSourcesCollector, _counter(), _gauge(), Clock, datetime, Backend self-metrics (UBS-96; FR-HLT-010, spec 006 s7). `SelfMetrics` owns a…, Prometheus exposition for the backend's own internals (FR-HLT-010)., Recompute per-agent gauges from the registry. Called per scrape so the exporter… (+26 more)

### Community 43 - "FixParser"
Cohesion: 0.11
Nodes (23): _poll_forever(), Drain each tailed file every 250ms so read lag / offsets stay honest, and feed…, is_parse_error(), Count one parsed line, and a parse error if `is_parse_error(result)`., What the heartbeat counts as a parse error (UBS-59). Same definition as the…, FixParser, Remove raw tag 58 text from egress (FR-PRS-022)., _strip_sensitive_fields() (+15 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.17
Nodes (17): FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides(), test_errors_counted_and_reported_in_heartbeat() (+9 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.13
Nodes (20): Clock, datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, at() (+12 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.19
Nodes (13): Backend Publisher (component), Callback Dispatcher (component), Consistent-Hash Routing on instanceId, 001 — Architecture, Failure Degradation Order (queries → freshness → callbacks → alerting), Log Monitor (component), Metrics Aggregator (component), Pipeline Bridge (component) (+5 more)

### Community 47 - "CamelModel"
Cohesion: 0.07
Nodes (50): Heartbeat emitter (UBS-58, FR-HLT-001). Ticks on a fixed interval regardless of…, Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, build_latency_summary(), Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004). Shared by the…, compute_indicators(), compute_ratio(), Decimal, RatioDef (+42 more)

### Community 48 - "heartbeat_json"
Cohesion: 0.14
Nodes (16): heartbeat_json(), Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, telemetry_agent_health_heartbeat, FakeClock, datetime, UBS-104: publish buffer bytes and dropped-event rate in the heartbeat. Mirrors…, A supervisor wiring the Publisher in calls this once at startup so a healthy…, test_buffer_bytes_is_none_without_a_provider() (+8 more)

### Community 49 - "callbacks/config.py"
Cohesion: 0.11
Nodes (26): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+18 more)

### Community 50 - "CallbackResult"
Cohesion: 0.17
Nodes (7): Stands in for Magic: keys its canned response off the alert ID inside the…, _ScriptedSink, CallbackResult, Outcome of one delivery attempt (`FR-CBK-009`). `status_code` is `None` on a…, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink

### Community 52 - "cli.py"
Cohesion: 0.12
Nodes (26): DemoMetricsSink, extract_log_level(), Extract [N/E/W/F/I] level from Magic-style log lines., _corpus_files(), _fields_dict(), _format_line_result(), _load_config(), main() (+18 more)

### Community 53 - "SeverityTier"
Cohesion: 0.17
Nodes (15): RE-03: the 14 default rules (spec 005 §1.2). Concrete `RuleConfig` values, used…, _tier(), _matched_tier(), Highest tier whose condition holds — not the first configured. Correct for the…, One (severity, threshold) rung. `FR-RUL-022`: the matched tier is whichever,…, SeverityTier, telemetry_agent_rules_types, test_matched_tier_picks_the_highest_crossed_tier() (+7 more)

### Community 54 - "test_health_endpoints.py"
Cohesion: 0.21
Nodes (11): datetime, FR-HLT-010, FR-QRY-005: `/healthz` is a liveness probe with no dependency…, FR-QRY-005: elapsed time alone must not flip `/readyz` to `ready` — if…, `has_data` is sticky: a legitimately quiet period after real data was already…, `main.py`'s module-level `StreamProcessor` singleton starts its warmup clock at…, _snapshot(), test_is_ready_returns_false_before_warmup_window_elapses_even_with_data(), test_is_ready_returns_true_once_warmup_window_has_elapsed_and_data_exists() (+3 more)

### Community 55 - "test_UBS_112_metrics_ingestor.py"
Cohesion: 0.24
Nodes (18): _counters(), _feed(), _ingestor(), _meta(), Decimal, parametrize, UBS-112: MetricsIngestor feeds one parse result into the aggregator, latency…, Known, documented difference (UBS-59 vs MA): the heartbeat counts an unreadable… (+10 more)

### Community 56 - "test_STM_02_merge_semantics.py"
Cohesion: 0.28
Nodes (14): HistogramPayload, Wire shape of one histogram (`FR-MET-025`/`FR-MET-026`): fixed boundaries…, _histogram_payload(), FR-STM-002/003/004: counters merge by summation; ratios are recomputed from…, Two agents of unequal volume (FR-STM-003's required test shape): agent A:…, A retried publish that misses batchId-level dedupe (a different ticket's…, _read_one_group(), _snapshot() (+6 more)

### Community 57 - "metrics_event.py"
Cohesion: 0.11
Nodes (18): UBS-106: per-session heartbeat-timeout detection. A heartbeat timeout is the…, Sessions that have *just* crossed the threshold, each latched so one silence is…, Stop tracking a session. Called on `Logout`, and the reason this exists: a…, One session that has just gone quiet for too long. Carries both identifiers on…, Internal tracking key, identical in format to `SeqTracker.session_key`.…, Record that a session was heard from at `at`. Any message counts, not just…, _SessionState, SessionTimeout (+10 more)

### Community 58 - "test_FR_CBK_001_002_003_payload.py"
Cohesion: 0.20
Nodes (15): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, make_alert_event(), Shared test support for the callbacks package: builds `AlertEvent` fixtures…, FR-CBK-001/002/003 callback payload shape tests. (+7 more)

### Community 59 - "CallbackDispatcher"
Cohesion: 0.11
Nodes (25): main(), _make_alert(), _print_counters(), Minimal walkthrough of the Callback Dispatcher (UBS-32/33). uv run python -m…, _run_one(), _step(), CallbackDispatcher, Spawns `maxInflight` workers pulling from the queue. Runs until cancelled by… (+17 more)

### Community 60 - "CounterRegistry"
Cohesion: 0.11
Nodes (11): Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, CounterRegistry, UBS-104: lightweight in-process counters, shared between the Callback…, Plain dict of named counters behind a lock -- increments happen from both async…, Logger, Self-observability, same shape as `BackendPublisher.counters` and…, UBS-104: `CounterRegistry` at its canonical `common/` location (moved from…, test_callbacks_shim_is_the_same_class() (+3 more)

### Community 61 - "SignatureMatcher"
Cohesion: 0.11
Nodes (20): AppLogParser, Parser plugin for configured application log patterns (Magic format)., compile_signature_rules(), First-match-wins signature rules with dynamic label templates., resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule (+12 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.12
Nodes (21): BufferingHeartbeatSink, Bounded retry buffer in front of another sink (UBS-60 demo stand-in). Not the…, HeartbeatSink, FakeQueue, Flaky, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend., test_at_critical_watermark_is_unhealthy() (+13 more)

### Community 63 - "AgentRegistry"
Cohesion: 0.08
Nodes (26): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary(), AgentRecord, AgentRegistry (+18 more)

### Community 64 - "dispatcher.py"
Cohesion: 0.10
Nodes (23): UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, DropOldestQueue, T, FR-CBK-007: bounded pending queue, drop-oldest on overflow., Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow policy (`FR-…, Enqueue `item`, non-blocking. Returns True if an existing item was dropped to…, classify_http_status(), StrEnum (+15 more)

### Community 65 - "SeqTracker"
Cohesion: 0.22
Nodes (9): Per-session MsgSeqNum tracking., SeqTracker, SeqGapEvent, FR-PRS-027 sequence gap tests., test_FR_PRS_027_detects_gap(), test_FR_PRS_027_detects_regression(), test_FR_PRS_027_logon_resets_without_gap(), `logouts`, `seq_gaps` and `clock_skew_events` all label their `session_id` with… (+1 more)

### Community 66 - "enrich.py"
Cohesion: 0.23
Nodes (17): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+9 more)

### Community 67 - "BackendPublisher"
Cohesion: 0.11
Nodes (16): make_pending_item(), Measured once at insert and cached on the `PendingItem` -- re-measuring on…, _size_of(), BackendPublisher, datetime, Event, UBS-75 / `FR-MET-031`: failed attempts in a row since the last successful…, Sync, non-blocking (`FR-PUB-007`) — never awaits, never blocks on a full buffer… (+8 more)

### Community 68 - "rules/demo_quickstart.py"
Cohesion: 0.06
Nodes (32): _alert_storm_act(), _alerts_to_backend_act(), _backend_unreachable_act(), attempt(), _dedup_act(), _Demo, _heartbeat_timeout_act(), main() (+24 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.13
Nodes (20): Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Magic simulator for development, Do not overengineer (development principle), Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores, Microsoft Teams as the only user interface (+12 more)

### Community 70 - "AppDeps"
Cohesion: 0.12
Nodes (34): healthz(), metrics(), get, Response, Operator probes (UBS-96; FR-HLT-010, FR-HLT-012; spec 007 s5.3). Mounted on the…, Liveness only: the process is up and serving. No dependency checks, so a broken…, Readiness incl. warm-up (FR-QRY-005), from the same…, readyz() (+26 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.10
Nodes (12): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+4 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (21): env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), datetime, fixture, TestClient (+13 more)

### Community 73 - "parse_fix_timestamp"
Cohesion: 0.27
Nodes (9): parse_fix_timestamp(), datetime, timedelta, Parse FIX SendingTime/TransactTime as UTC., TimestampResult, FR-PRS-025/026 timestamp tests., test_FR_PRS_025_bad_timestamp_falls_back_to_log(), test_FR_PRS_025_parses_fix_timestamp_utc() (+1 more)

### Community 74 - "datetime"
Cohesion: 0.09
Nodes (33): FR-CBK-001/011: the swappable Callback transport boundary (spec 005 §3).…, _build_parser(), _detect_session_timeouts(), main(), _main_async(), ArgumentParser, Event, Namespace (+25 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.14
Nodes (15): Resource Discipline (§9), Backend Configuration and Secrets (§9), Compliance and Operability Constraints (§7), 009 — Non-Functional Requirements and Security, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-SCA-001: Agent Independence/Statelessness, NFR-SEC-004: Secrets from Environment Only, Observability of the Telemetry System (§6) (+7 more)

### Community 77 - "Histogram"
Cohesion: 0.15
Nodes (13): Histogram, Decimal, Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012). Shared…, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, Reconstruct a mergeable `Histogram`, keyed on the canonical boundary set rather…, test_merge_is_bucket_wise_addition() (+5 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.15
Nodes (22): datetime, Logger, Wires `config/rules.yaml` reloading to SIGHUP for a live `RuleEngine`.…, Returns the `resolved` events `apply_rules()` emits for alerts whose rule was…, Standalone use only: this reloads inside the signal handler and drops the…, SighupRuleReloader, _engine(), _fire() (+14 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (18): C++ candidate (rejected: worst-case failure modes), ADR 0001: Telemetry Agent written in Go (Superseded), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), ADR 0002: Telemetry stack is Python 3.12 + FastAPI, .NET alternative (rejected) (+10 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.12
Nodes (18): ADR 0004: No-Raw-Persistence Design, Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Parser Engine Agent-Level Contract (FR-PRS-001–003), Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing), Scaffold Document (plan/scaffold.md) (+10 more)

### Community 82 - "test_RE_parse_error_integration.py"
Cohesion: 0.31
Nodes (12): _fire(), _ingest(), _rate(), UBS-18 integration: raw log bytes -> FixParser -> derive_parser_counters ->…, Needs a failure mode that errors once per line — see `_NO_MSG_TYPE`. The…, Documents the asymptote above as behaviour, not accident: three of every four…, `min_samples` is 20 for this rule. Under that, a single bad line in a handful…, test_a_clean_log_never_fires() (+4 more)

### Community 83 - "pipeline_demo.py"
Cohesion: 0.13
Nodes (24): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), OverflowPolicy, Path, End-to-end demo: LogMonitor → queue → parse → output → commit. (+16 more)

### Community 84 - "AlertEvent"
Cohesion: 0.09
Nodes (20): Sync, non-blocking — the entry point a future wiring step calls from the same…, AlertRouter, datetime, Run one path's enqueue so its failure stays on that path., Enqueues alerts for publication, rejecting any that would poison the batch they…, Hand every alert to the Callback Dispatcher (if configured), and every alert…, AbstractContextManager, Any (+12 more)

### Community 85 - "telemetry_agent/demo_suite.py"
Cohesion: 0.13
Nodes (20): main(), poll_available(), print_lines(), print_section(), Path, Deterministic local demo for Log Monitor lifecycle behaviour. Run with ``uv run…, Read every available line without entering the infinite stream loop., run_demo() (+12 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (15): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact…, The exact 3-order story from the Metrics Aggregator quickstart: two accepted… (+7 more)

### Community 88 - "Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing)"
Cohesion: 0.22
Nodes (9): Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Text Field Normalisation (FR-PRS-022), Error Response Shape (§7), Prompt-Injection and Abuse Considerations (FR-NLQ-023/024), NFR-SEC-015: Canonicalised Allowed Roots, Symlinks Refused, Security: Input Handling (§3.4), Agent Configuration Schema (§1) (+1 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (9): batch(), deps(), FakeClock, metrics(), datetime, UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)., test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() (+1 more)

### Community 91 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.25
Nodes (8): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Agent Restart Sequence (§8.2), NL Evaluation Requirements (FR-NLQ-025), End-to-End Acceptance Scenario (FR-TST-010), NL Evaluation Harness (FR-TST-007–009), Synthetic Load Generator (tools/fixgen, FR-TST-006), Cardinality Control (per-bucket max_label_sets/max_series_per_bucket)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (16): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Configurability NFRs (§5), NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test), NFR-SEC-012: Order Identifier Hashing, Rotatable Key, NFR-SEC-013: No Raw-Log Debug Mode in Release Build (+8 more)

### Community 94 - "build_batch"
Cohesion: 0.13
Nodes (22): BatchSequencer, build_batch(), datetime, FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, `FR-PUB-003`: a monotonically increasing `batchSeq` per agent, and a stable…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, inspect, NoReturn (+14 more)

### Community 95 - "Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)"
Cohesion: 0.17
Nodes (11): Register (or remove) the Publisher's queue-depth callback., 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 5.1 The window — `health/window.py`, 5. UBS-59 — parse error rate, 6. UBS-60 — publish queue depth, 8. What is still missing (so nobody is surprised) (+3 more)

### Community 97 - "StreamProcessorConfig"
Cohesion: 0.13
Nodes (22): StreamProcessorConfig, Read-only configuration shared with the ingestion boundary., datetime, FR-STM-001, FR-ING-005, FR-STM-005: canonical window alignment, rejection of…, FR-ING-005: out-of-order snapshots for the same bucket must still merge to the…, A snapshot the StreamProcessor accepts as within maxBucketAge must still be…, A cap below 1 would drop every series as over-cap while `merge()` still marks…, FR-QRY-003: the shed threshold must be strictly above the warn threshold, or… (+14 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (10): _CountingRing, datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in…, The old `tick()` swept every instance's ring on every merge — O(instances x…, A query over one 10s bucket on a 6h-capacity (2160-bucket) ring must not touch…, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to() (+2 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.10
Nodes (33): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent, BaseModel (+25 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.13
Nodes (22): extract_allowlisted_fields(), FixFields, _hash_or_none(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, Fixed-shape allowlisted field set. No attribute here may hold a raw, non-…, FR-PRS-020: extract only the tags in the compile-time allowlist above.…, hash_identifier(), HMAC-SHA256 of `raw` keyed with `key`, truncated to 16 hex chars. (+14 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (13): _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any…, _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved() (+5 more)

### Community 103 - "decimal"
Cohesion: 0.09
Nodes (26): _dim_key(), Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, _SeriesContribution, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, decimal, DimKey, Shared contract: one agent metric snapshot on the wire (spec 004 §3, `FR-…, FR-QRY-004: the store MUST be safe under concurrent read/write via a per-… (+18 more)

### Community 104 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 105 - "AgentHeartbeat"
Cohesion: 0.11
Nodes (15): LoggingHeartbeatSink, PrintHeartbeatSink, datetime, Logger, Write one JSON line per heartbeat to stdout (demo)., Build and send one heartbeat. Sink failures are counted, not raised: a dead…, Emit the wire JSON through `logging` (demo / local runs)., 4.1 Wire contract — `packages/telemetry_shared/models/health.py` (+7 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.12
Nodes (33): _alert(), _publisher(), LogCaptureFixture, Logger, parametrize, UBS-109: AlertRouter — the seam from Rule Engine output to the Backend…, Buffering is not publishing — this follows the alert all the way out through…, The containment that matters: the bad alert is dropped, the good ones are… (+25 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "health-reporter-overview.md"
Cohesion: 0.20
Nodes (9): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration, Not in this change (+1 more)

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.05
Nodes (59): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestGuardConfig, IngestionConfig (+51 more)

### Community 110 - "test_log_monitor_status.py"
Cohesion: 0.62
Nodes (6): make_monitor(), Path, test_status_after_read_reports_elapsed_lag(), test_status_before_any_read_has_no_lag(), test_status_missing_file_has_no_size_but_does_not_raise(), test_status_reports_offset_progress_between_polls()

### Community 111 - "008 — Natural Language Query Layer (Copilot/Teams)"
Cohesion: 0.40
Nodes (5): Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents), NL Intent Catalogue (FR-NLQ-003/004), 008 — Natural Language Query Layer (Copilot/Teams)

### Community 112 - "test_QRY_03_memory.py"
Cohesion: 0.17
Nodes (15): datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep…, _snapshot(), test_estimated_memory_bytes_counts_an_idle_instances_allocated_ring_shell() (+7 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "._make_key"
Cohesion: 0.17
Nodes (6): Path, Generates internal state ID format (e.g., 'native::16777232-1048201')., Loads state registry into memory Supports Filebeat's native JSON list array…, Retrieves the last known offset for a given (device, inode) pair., Persist committed offset after parse+ingest (FR-PIP-006)., Deprecated alias for commit_offset.

### Community 115 - "Requirement ID Scheme (FR-<AREA>-<NNN>)"
Cohesion: 0.16
Nodes (15): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Health Reporter (component), Ingestion Service (component) (+7 more)

### Community 116 - "NFR-REL-003: Backend Outage Must Not Affect Alerting"
Cohesion: 0.50
Nodes (5): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), NFR-REL-003: Backend Outage Must Not Affect Alerting, Reliability NFRs (§2), Runbook: Backend Unreachable

### Community 117 - "test_reporter.py"
Cohesion: 0.42
Nodes (9): make_monitor(), Path, UBS-33/34: HealthReporter.failed_deliveries() surfaces callback delivery…, test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_failed_deliveries_returns_only_failed_alert_ids(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet() (+1 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.07
Nodes (51): load_callback_secret(), FR-CBK-005: request signing so Magic can verify a callback originated from this…, `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), Identifier hashing (FR-PRS-021)., hashlib, hmac (+43 more)

### Community 119 - "test_snapshot.py"
Cohesion: 0.25
Nodes (7): Wire-format Snapshot contract (spec 004 §3, FR-MET-024..028)., FR-STM-004: there is no wire shape for 'summary percentiles only, no histogram'…, test_histogram_payload_requires_the_full_shape_not_a_percentile_summary(), test_parses_the_spec_004_example_verbatim(), test_to_histogram_ignores_unrecognised_bucket_keys_defensively(), test_unknown_dimension_shaped_extra_key_on_a_series_is_rejected(), test_unknown_top_level_field_is_rejected()

### Community 120 - "publishing/demo_quickstart.py"
Cohesion: 0.26
Nodes (9): _drain(), main(), _make_snapshot(), _print_state(), datetime, Minimal walkthrough of the Backend Publisher (UBS-103/104). uv run python -m…, Stands in for the backend: returns responses from a fixed script, one per call,…, _ScriptedSink (+1 more)

### Community 121 - "Stream Processor (component)"
Cohesion: 0.50
Nodes (4): Stream Processor (component), architecture-overview.png (client architecture diagram showing Stream Processor box), Ingestion Requirements (FR-ING-001–010), Stream Processing Requirements (FR-STM-001–006)

### Community 122 - "Query Engine Requirements (FR-QRY-006–014)"
Cohesion: 0.50
Nodes (4): Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009)

### Community 123 - "Implementation Status live document"
Cohesion: 0.31
Nodes (9): Implementation Status live document, M1 Log monitor and configuration (not started), M2 FIX parser (UBS-40-47), M3 Metrics aggregation (MA-01-04), Backend Metric Store and cross-agent merge, Ratios are recomputed, never averaged, Backend Stream Processor (UBS-88), Known rough edges (+1 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "test_UBS_104_outage_isolation.py"
Cohesion: 0.29
Nodes (7): _HangingSink, _make_alert(), _make_snapshot(), UBS-104 integration test: `NFR-REL-003` -- a backend outage must never affect…, Stands in for a backend that never responds -- e.g. a dropped connection to a…, _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher()

### Community 127 - "Rule Engine demo runbook"
Cohesion: 0.10
Nodes (23): NoLogActivity rule, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, Dependent suppression (FR-RUL-021), Rule Engine, Safety and suppression (silences, grace, storm cap), SighupRuleReloader (+15 more)

### Community 128 - "DryRunCallbackSink"
Cohesion: 0.24
Nodes (8): DryRunCallbackSink, Logger, `FR-CBK-011`: log the intended delivery, never open a socket. Use this while…, FR-CBK-011 dry-run mode tests., DryRunCallbackSink never imports/constructs an httpx client at all — completing…, test_FR_CBK_011_dry_run_logs_delivery_id_and_body(), test_FR_CBK_011_dry_run_never_opens_a_socket(), test_FR_CBK_011_dry_run_returns_synthetic_success()

### Community 129 - "effective_reject_reason"
Cohesion: 0.33
Nodes (7): effective_reject_reason(), Single precedence: ordRejReason → rejectReasonText label → unspecified. For…, FR-PRS-024 rejection precedence tests., test_FR_PRS_024_ord_rej_reason_wins(), test_FR_PRS_024_session_reject_for_msg_type_reject(), test_FR_PRS_024_text_label_when_no_ord_rej(), test_FR_PRS_024_unspecified_when_missing()

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "test_UBS_113_evaluation_loop.py"
Cohesion: 0.24
Nodes (11): _NullCallbackSink, datetime, UBS-113 integration: raw FIX bytes -> FixParser -> MetricsAggregator /…, Each tick is one second later, so pending -> firing happens on tick 2 without…, An order with no ack, its age read off the correlator each tick., _rule(), _run_ticks(), _stepping_clock() (+3 more)

### Community 133 - "publishing/__init__.py"
Cohesion: 0.31
Nodes (7): classify_publish_response(), PublishOutcome, UBS-103: HTTP response -> publish action classification (spec 007 §2.1's…, parametrize, test_429_carries_retry_after_seconds(), test_status_code_classification(), test_transport_error_is_backoff()

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 157 - "test_STM_03_warmup.py"
Cohesion: 0.33
Nodes (9): datetime, FR-STM-006: an agent's post-restart cold-start state is preserved through the…, warmingUp flags incomplete data for the caller to exclude; it does not mean the…, _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up(), test_data_from_a_restarted_bucket_is_still_merged_not_dropped(), test_restarted_bucket_count_reflects_only_buckets_a_restart_touched() (+1 more)

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 195 - "create_app"
Cohesion: 0.07
Nodes (58): BatchAccepted, _counts(), create_app(), enqueue_or_full(), ingest_batch(), ingest_events(), ingest_heartbeat(), validate_or_reject() (+50 more)

### Community 201 - "AlertStore"
Cohesion: 0.10
Nodes (32): AlertStoreConfig, Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)., AlertStore, _InstanceAlerts, _is_active_status(), datetime, Lock, In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`). (+24 more)

### Community 207 - "align_to_canonical"
Cohesion: 0.31
Nodes (6): align_to_canonical(), datetime, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., SnapshotOutcome, test_alignment_floors_a_phase_shifted_bucket_onto_the_canonical_grid(), test_alignment_is_a_no_op_when_already_on_the_grid()

### Community 210 - "normalize.py"
Cohesion: 0.28
Nodes (11): compile_reject_patterns(), match_reject_label(), normalize_reject_text(), Steps 1–2 of FR-PRS-022 (matching input only, not emitted)., Return (label, is_unclassified). On no match returns (None, True) — caller…, RejectPattern, FR-PRS-022 tag 58 normalisation tests., test_FR_PRS_022_cardinality_overflow() (+3 more)

### Community 212 - "demo_reload.py"
Cohesion: 0.26
Nodes (11): _banner(), _instructions(), main(), Path, Live walkthrough of SIGHUP rule reloading (`FR-RUL-008`/`009`). uv run python…, The watched file may be mid-edit or deliberately broken; a failed read here…, _run(), _safe_rule_count() (+3 more)

### Community 213 - "test_UBS_103_publisher_backend.py"
Cohesion: 0.48
Nodes (6): ASGITransport, _publisher(), UBS-103 integration test: the Backend Publisher against the *real* Telemetry…, _snapshot(), test_503_when_the_backend_queue_is_full(), test_happy_path_against_the_real_backend_app()

### Community 214 - "test_readyz_shared_processor.py"
Cohesion: 0.43
Nodes (6): _batch_with_snapshot(), datetime, TestClient, FR-QRY-005: `/readyz` probes the same StreamProcessor that ingestion feeds.…, test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store(), _wait_for_status()

### Community 216 - "HttpsPublishSink"
Cohesion: 0.13
Nodes (15): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), AsyncBaseTransport, `FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the compressed…, `FR-PUB-001`/`002`: HTTPS POST with a bearer token, gzip above…, gzip, Headers (+7 more)

### Community 223 - ".__init__"
Cohesion: 0.18
Nodes (9): on_drop(), _on_buffer_drop(), Logger, PublishSink, Protocol, The transport boundary. `HttpsPublishSink` is the Day-1 default (ADR 0003);…, BackendUnreachableCallback, DropCallback (+1 more)

### Community 226 - "HealthReporter"
Cohesion: 0.07
Nodes (41): HeartbeatConfig, _make_publisher(), The production route: reporter -> Backend Publisher -> backend., connect_reporter_to_publisher(), drop_hook(), heartbeat_provider(), AbstractContextManager, Any (+33 more)

### Community 229 - "HeartbeatEmitter"
Cohesion: 0.25
Nodes (8): heartbeat: interval config, HeartbeatEmitter, Parse error rate signal (UBS-59), record_parse_result() intake, SlidingWindowCounter, M1.5 Pipeline bridge (UBS-48/49), Heartbeat thread/async model, telemetry-agent-heartbeat demo entrypoint

### Community 234 - "telemetry_agent/main.py"
Cohesion: 0.07
Nodes (34): AbstractEventLoop, AgentConfig, Agent, build_agent(), _build_parser(), _install_signals(), _is_local(), main() (+26 more)

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **180 isolated node(s):** `telemetry-agent`, `telemetry-backend`, `telemetry-simulator`, `telemetry-teams`, `avengers-fyp-is484` (+175 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1330 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **125 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `MetricsAggregator ring buffer` to `AggregatorConfig`, `Implementation Status live document`, `config/rules.yaml live rule set`, `Rule Engine demo runbook`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `HealthReporter` connect `HealthReporter` to `reporter.py`, `test_heartbeat.py`, `LogMonitor`, `collections_abc`, `HealthSignals`, `DeliveryTracker`, `telemetry_agent/config.py`, `pathlib`, `test_health_monitor_e2e.py`, `FixParser`, `test_parse_errors.py`, `SlidingWindowCounter`, `CamelModel`, `heartbeat_json`, `test_UBS_112_metrics_ingestor.py`, `test_queue_depth.py`, `datetime`, `Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)`, `AgentHeartbeat`, `telemetry_agent/main.py`, `test_reporter.py`, `publishing/demo_quickstart.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `Implementation Status live document` connect `Implementation Status live document` to `Telemetry Agent (architecture constraint)`, `HeartbeatEmitter`, `config/rules.yaml live rule set`, `Scaffold and Build Plan`, `AgentHeartbeat wire contract`, `Rule Engine demo runbook`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 66 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 66 INFERRED edges - model-reasoned connections that need verification._