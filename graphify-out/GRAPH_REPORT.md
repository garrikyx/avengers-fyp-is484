# Graph Report - avengers-fyp-is484  (2026-10-16)

## Corpus Check
- 337 files · ~185,608 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 9, .example 1, .typed 1)

## Summary
- 4149 nodes · 10800 edges · 271 communities (146 shown, 125 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 1937 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4aa36773`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- create_app
- FixParser
- test_metrics_event.py
- RuleEngine
- make_snapshot
- config_loader.py
- HealthReporter
- decimal
- RetryPolicy
- LatencyCorrelator
- derive_counters
- test_RE_publish_integration.py
- test_heartbeat.py
- ReadLine
- PublishBuffer
- SourceMeta
- demo_metrics_bridge.py
- PublishResult
- MetricsAggregator
- .__init__
- test_RE_session_integration.py
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- heartbeat.py
- load_agent_config
- RuleEvaluator
- Agent
- DeliveryTracker
- HeartbeatConfig
- test_MA_05_agent_counters.py
- AggregatorConfig
- test_heartbeat_roundtrip.py
- test_UBS_113_evaluator.py
- test_MA_03_correlation.py
- Stack
- config/rules.yaml live rule set
- telemetry_backend/main.py
- metrics_event.py
- MetricsAggregator ring buffer
- AgentRegistry
- test_RE_callback_integration.py
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- heartbeat_json
- callbacks/config.py
- CallbackResult
- telemetry_agent_callbacks_config
- ParseResult
- Histogram
- parse_publish_config
- MetricsIngestor
- test_STM_02_merge_semantics.py
- CallbackDispatcher
- from_alert_event
- HttpsCallbackSink
- AlertEvent
- Confidence
- test_queue_depth.py
- HeartbeatMonitor
- classify_http_status
- telemetry_agent_metrics_aggregator
- enrich.py
- BackendPublisher
- rules/demo_quickstart.py
- Telemetry Agent (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- asyncio
- test_agent_registry.py
- http
- 009 — Non-Functional Requirements and Security
- SessionHeartbeatTracker
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- test_UBS_123_snapshot_emitter.py
- pipeline_demo.py
- telemetry_agent/config.py
- datetime
- telemetry_agent_metrics_counters
- signing.py
- End-to-End Acceptance Scenario (FR-TST-010)
- publishing/sink.py
- test_ING_004_008_routes.py
- Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- publisher.py
- MultiLogMonitor
- telemetry_agent_callbacks_backoff
- StreamProcessor
- test_STM_04_efficiency.py
- ParsedMessageEvent
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- test_QRY_04_concurrency.py
- test_STM_01_window_alignment.py
- AgentHeartbeat
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- health-reporter-overview.md
- telemetry_backend/config.py
- test_UBS_104_outage_isolation.py
- test_publishing_helpers.py
- StreamProcessorConfig
- telemetry_shared shared schema package
- LogMonitor
- UBS-49 — Pipeline Bridge Integration (live agent path)
- NFR-REL-003: Backend Outage Must Not Affect Alerting
- test_UBS_115_snapshot_to_metricstore.py
- test_UBS_109_rule_engine_to_backend.py
- test_UBS_116_app_log_ingest.py
- is_parse_error
- test_snapshot.py
- snapshot_bridge.py
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- HealthThresholds
- telemetry_agent_parser_applog_signatures
- Rule Engine
- ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server
- ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- test_UBS_113_evaluation_loop.py
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
- test_the_agent_process_alerts_magic_and_the_backend
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
- DryRunPublishSink
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
- SeqTracker
- telemetry_shared_metrics
- telemetry_shared_metrics_histogram
- metric_store.py
- telemetry_agent_common_backoff
- ._serialize_counters
- Rule Engine demo runbook
- test_RE_03_safety.py
- metrics/__init__.py
- test_a_logged_reject_burst_reaches_the_backend_alert_store
- http_server
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
- _alerts_to_backend_act
- Issue tracker: Jira
- Domain Docs
- triage-labels.md
- .seed

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 117 edges
2. `HealthReporter` - 89 edges
3. `AlertEvent` - 80 edges
4. `BackendPublisher` - 80 edges
5. `SourceMeta` - 74 edges
6. `FixParser` - 69 edges
7. `create_app()` - 66 edges
8. `StreamProcessorConfig` - 62 edges
9. `ParseResult` - 62 edges
10. `LatencyCorrelator` - 60 edges

## Surprising Connections (you probably didn't know these)
- `4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`` --references--> `AgentHeartbeat`  [INFERRED]
  docs/plan/health-reporter-overview.md → packages/telemetry_shared/src/telemetry_shared/models/health.py
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py
- `Decisions` --references--> `IngestionService`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/backend/src/telemetry_backend/services/ingestion.py

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

## Communities (271 total, 125 thin omitted)

### Community 0 - "create_app"
Cohesion: 0.08
Nodes (42): attempt(), create_app(), Build an application, allowing tests and deployment to supply a service., IngestionService, Apply the backend-side allowlists and bucket cardinality cap. Pydantic has…, Undo an admission reservation when the bounded queue is full., Keep store work off FastAPI's request path. A single consumer preserves the…, Owns a bounded queue and one background consumer. (+34 more)

### Community 1 - "FixParser"
Cohesion: 0.05
Nodes (63): demo_log_lines(), Path, Return parsed corpus lines, optionally filtered to one source file label., FixFields, Fixed-shape allowlisted field set. No attribute here may hold a raw, non-…, _check_body_length(), _check_checksum(), _contains_tag() (+55 more)

### Community 2 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (40): build_parsed_message_event(), Construct the Metrics Aggregator's event from one framed FIX line. Returns None…, _meta(), _parse(), _parser_counters(), datetime, Decimal, parametrize (+32 more)

### Community 3 - "RuleEngine"
Cohesion: 0.08
Nodes (41): _AlertState, AlwaysActive, _decimal_or_none(), _evaluates_on(), _matched_condition(), _matched_tier(), _metric_context(), datetime (+33 more)

### Community 4 - "make_snapshot"
Cohesion: 0.19
Nodes (31): make_gauges(), make_indicator(), make_indicators(), make_snapshot(), datetime, Decimal, Shared test support for the rules package: builds `MetricsSnapshot` fixtures…, `empty=True` builds a snapshot with zero groups (nothing ingested this window… (+23 more)

### Community 5 - "config_loader.py"
Cohesion: 0.08
Nodes (39): load_rules(), load_rules_from_yaml(), _parse_duration_seconds(), Any, BaseModel, Exception, field_validator, Logger (+31 more)

### Community 6 - "HealthReporter"
Cohesion: 0.09
Nodes (30): HealthReporter, datetime, Per-file read health, keyed by the same name `monitors` was built with., Worst-case lag across files (heartbeat gauge). None if none have read yet., Files whose lag exceeds the threshold. Unread files are never flagged., Count a parse error from a producer that does not hand over a `ParseResult`…, Count successfully parsed lines in bulk (denominator only)., Count `n` buffer-eviction drops (`droppedEventsLast5Min`, `FR-PUB-004`) at… (+22 more)

### Community 7 - "decimal"
Cohesion: 0.13
Nodes (38): RE-03: the 16 default rules (spec 005 §1.2). Concrete `RuleConfig` values, used…, _tier(), _read_observed(), StrEnum, RE-01: rule and alert lifecycle types (spec 005 §1-2). Agent-internal…, FR-RUL-001: Day-1 supports exactly these five., Where a rule's observed value is read from in a MetricsSnapshot., One (severity, threshold) rung. `FR-RUL-022`: the matched tier is whichever,… (+30 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.08
Nodes (30): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, main(), generate_application_log(), get_timestamps() (+22 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.05
Nodes (38): Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, CounterRegistry, UBS-104: lightweight in-process counters, shared between the Callback…, Plain dict of named counters behind a lock -- increments happen from both async…, CorrelatorStats, LatencyCorrelator, OrderContext, Clock (+30 more)

### Community 10 - "derive_counters"
Cohesion: 0.10
Nodes (37): derive_counters(), All four counter families in one event walk., Config-driven raw-reason -> canonical-label mapping. Backs MetricsAggregator's…, Top-N normalised reject reasons by `metric` in `window`, N configurable., ReasonNormalizer, top_reject_reasons(), _banner(), _implementation() (+29 more)

### Community 11 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (22): _aggregator(), _engine(), _fail_n_times(), _publisher(), UBS-75 integration: BackendPublisher -> consecutive_publish_failures gauge ->…, The whole reason this is a gauge: recovery is observable. A windowed failure…, FR-MET-031. An agent with no publisher must not look like an agent that is…, Regression guard on spec 005 §1.2's withdrawn approximation.… (+14 more)

### Community 12 - "test_heartbeat.py"
Cohesion: 0.12
Nodes (22): HeartbeatEmitter, Event, Tick every `interval_seconds` until `stop` is set. First tick is immediate so a…, Collect, FakeClock, datetime, LogCaptureFixture, UBS-58 / FR-HLT-001: heartbeat emitter and wire format. (+14 more)

### Community 13 - "ReadLine"
Cohesion: 0.07
Nodes (20): Harvester, Path, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, One complete log line with stable byte identity for idempotent ingest., Find retained rotations that were created while the agent was down. This…, Keep a rotated descriptor alive to collect its final writes., Persist progress even when a continuously busy file never reaches EOF. (+12 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (24): PublishBuffer, Put previously-`take`n items back at the front, in original order -- they are…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both…, Drop items older than `max_age_seconds`. The deque is strictly insertion-…, Remove and return up to `max_items` from the front., _item(), FR-PUB-004: the byte-and-age-bounded `PublishBuffer` (UBS-104's replacement for…, Drop-oldest still holds after a requeue: the items just put back are the oldest… (+16 more)

### Community 15 - "SourceMeta"
Cohesion: 0.04
Nodes (54): Metadata attached to each log line by the monitor., SourceMeta, Selects the first parser in a configured chain with Confidence.HIGH., Return unknown parser names in chain., Registry, QueueSnapshot, PipelineCommitter, Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007). (+46 more)

### Community 16 - "demo_metrics_bridge.py"
Cohesion: 0.11
Nodes (28): _fixed_now(), main(), Minimal walkthrough of parser/metrics_event.py: the same three-order story as…, _step(), derive_parser_counters(), derive_session_counters(), _parse_error_reason(), parser_counter_dims() (+20 more)

### Community 17 - "PublishResult"
Cohesion: 0.11
Nodes (37): classify_publish_response(), PublishAction, PublishOutcome, StrEnum, UBS-103: HTTP response -> publish action classification (spec 007 §2.1's…, PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, _StatusSink (+29 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.10
Nodes (21): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator, Clock, datetime, Decimal (+13 more)

### Community 19 - ".__init__"
Cohesion: 0.33
Nodes (4): Clock, Register (or remove) the Publisher's buffer-bytes callback…, BufferBytesProvider, QueueDepthProvider

### Community 20 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (29): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), Decimal, UBS-73 integration: raw FIX log bytes -> FixParser -> metrics_event bridge ->…, A tracker that has watched `lines` go past, so it knows which sessions exist… (+21 more)

### Community 21 - "MetricStore"
Cohesion: 0.13
Nodes (16): _CanonicalBucket, MetricStore, datetime, Lock, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a…, Evict buckets that have aged out of retention within *one* instance's ring —…, Evict stale buckets across every instance's ring and check memory pressure. For… (+8 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.07
Nodes (36): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+28 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.16
Nodes (31): _key(), _keys(), _observe(), UBS-106: SessionHeartbeatTracker — the `heartbeat_timeouts` producer. A…, A logged-out session is silent forever. Counting that as a timeout would…, SeqTracker accepts both normalized names and raw tag values ("Logon"/"A");…, FIX only requires a Heartbeat when the session is otherwise idle, so a session…, Session keys from a timed_out() result, for terse assertions. (+23 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (31): health: threshold config block, heartbeat: interval config, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry (+23 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "heartbeat.py"
Cohesion: 0.14
Nodes (19): datetime, Heartbeat emitter (UBS-58, FR-HLT-001). Ticks on a fixed interval regardless of…, Build and send one heartbeat. Sink failures are counted, not raised: a dead…, Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat(), telemetry_agent_health_wire, make(), UBS-58/66 wire compatibility: our heartbeat flattened to the Ingestion… (+11 more)

### Community 27 - "load_agent_config"
Cohesion: 0.24
Nodes (20): AgentConfigError, load_agent_config(), Exception, Path, `agent.yaml` is missing or a section is invalid; the message names it., parametrize, Path, UBS-114: `config/agent.yaml` is read once and each section reaches the loader… (+12 more)

### Community 28 - "RuleEvaluator"
Cohesion: 0.15
Nodes (11): AbstractContextManager, Any, datetime, Event, Logger, Signal-safe: only sets a flag. Register it with…, One tick. Returns every alert routed, in routing order., Tick every `interval_seconds` until `stop` is set; the first tick is immediate.… (+3 more)

### Community 29 - "Agent"
Cohesion: 0.22
Nodes (14): Agent, agent(), fixture, MonkeyPatch, parametrize, Path, skipif, Run the real infinite harness for a finite, controlled set of writes. (+6 more)

### Community 30 - "DeliveryTracker"
Cohesion: 0.12
Nodes (24): DeliveryRecord, DeliveryStatus, DeliveryTracker, datetime, StrEnum, UBS-34: per-alert-occurrence callback delivery status, timestamped at each…, UBS-34 AC: every dispatched callback has exactly one of these five states at…, One alert's current delivery state. `attempt_count` and `last_error` are… (+16 more)

### Community 31 - "HeartbeatConfig"
Cohesion: 0.10
Nodes (34): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, HeartbeatConfig, _HeartbeatYaml, load_health_config() (+26 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.13
Nodes (25): AgentCounterSampler, datetime, UBS-74: bridges the agent's own since-startup counters into the windowed…, Turns monotonic since-startup counters into per-bucket deltas. Stateful across…, Ingest the increase in each tracked counter since the last call. The first call…, _aggregator(), Decimal, UBS-74: `MetricsAggregator.ingest_agent_counters` and the `AgentCounterSampler`… (+17 more)

### Community 33 - "AggregatorConfig"
Cohesion: 0.13
Nodes (36): AggregatorConfig, Bucket granularity, retained windows, and the per-metric dimension table (FR-…, FakeClock, hand_labelled_events(), Shared test support for the metrics package: a hand-labelled synthetic FIX-…, A `Clock` (`() -> float`) that only advances when told to — lets a test assert…, make_event(), minimal_aggregator() (+28 more)

### Community 34 - "test_heartbeat_roundtrip.py"
Cohesion: 0.22
Nodes (9): FakeClock, _publisher(), datetime, Path, Agent Health Reporter (UBS-58/59/60) -> Backend Publisher -> Ingestion (UBS-66)…, The backend contract for the batch's heartbeat slot, without the publisher:…, test_agent_heartbeat_reaches_the_health_endpoint(), test_heartbeat_provider_output_is_accepted_in_a_batch() (+1 more)

### Community 35 - "test_UBS_113_evaluator.py"
Cohesion: 0.11
Nodes (38): pytest, _Stack, telemetry_agent_rules_config_loader, _names(), Path, UBS-113: RuleEvaluator — the periodic loop between the metrics store and…, RejectSpike reads 1m, HighRejectRate reads 5m: one tick, both., The tracker latches each silence: many ticks after the timeout still put… (+30 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "Stack"
Cohesion: 0.09
Nodes (18): committed_offsets(), FakeClock, fix_lines(), datetime, FastAPI, fixture, MonkeyPatch, Path (+10 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.11
Nodes (28): Agent processing pipeline (monitor to health reporter), publish: Backend Publisher config block, BackendUnreachable rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule (+20 more)

### Community 39 - "telemetry_backend/main.py"
Cohesion: 0.07
Nodes (43): HTTP routers, one file per concern (spec 007). `health.py` (UBS-69) serves the…, AlertsQueryParams, BatchAccepted, _build_parser(), _counts(), enqueue_or_full(), get_alert(), ingest_batch() (+35 more)

### Community 40 - "metrics_event.py"
Cohesion: 0.18
Nodes (15): UBS-106: per-session heartbeat-timeout detection. A heartbeat timeout is the…, One session that has just gone quiet for too long. Carries both identifiers on…, SessionTimeout, FixTelemetry, Sanitized telemetry derived from a framed FIX message., The canonical `session_id` *dimension* value (`FR-MET-030`). Deliberately…, session_id_for(), derive_heartbeat_timeout_counters() (+7 more)

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.12
Nodes (21): AckLatencyBreach rule, Parse error rate signal (UBS-59), SlidingWindowCounter, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent) (+13 more)

### Community 42 - "AgentRegistry"
Cohesion: 0.04
Nodes (53): AgentRecord, AgentRegistry, Clock, datetime, Agent Registry (spec 006 FR-ING-010; UBS-69 read side, UBS-87 write side). One…, `missing` if stale, otherwise whatever the agent last reported., Agent IDs past the threshold - the `dataCompleteness.staleAgents` input (FR-…, Thread-safe map of known agents. Memory-only by design (FR-QRY-005). (+45 more)

### Community 43 - "test_RE_callback_integration.py"
Cohesion: 0.24
Nodes (15): _aggregator(), _alert(), _dispatch(), _drain(), _fire(), UBS-74 integration: CallbackDispatcher -> CounterRegistry ->…, The registry is monotonic, so re-ingesting its absolute value on every tick…, `secondsSinceLastEvent` must stay untouched by the agent's own counters —… (+7 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (18): bad(), FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides() (+10 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.12
Nodes (22): Clock, datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, drive() (+14 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.09
Nodes (30): Problem P-1: Limited visibility into live trading activity and health, Problem P-4: No way to ask questions of live telemetry, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), Consistent-Hash Routing on instanceId, 001 — Architecture (+22 more)

### Community 47 - "CamelModel"
Cohesion: 0.08
Nodes (43): Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, AlertCounts, AlertDelivery, AlertDetailResponse, AlertRecord, AlertsListResponse, AlertTransition, Alert query response models (spec 007 §4, `FR-QRY-016`). (+35 more)

### Community 48 - "heartbeat_json"
Cohesion: 0.14
Nodes (16): heartbeat_json(), Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, telemetry_agent_health_heartbeat, FakeClock, datetime, UBS-104: publish buffer bytes and dropped-event rate in the heartbeat. Mirrors…, A supervisor wiring the Publisher in calls this once at startup so a healthy…, test_buffer_bytes_is_none_without_a_provider() (+8 more)

### Community 49 - "callbacks/config.py"
Cohesion: 0.15
Nodes (22): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+14 more)

### Community 50 - "CallbackResult"
Cohesion: 0.15
Nodes (7): Stands in for Magic: keys its canned response off the alert ID inside the…, _ScriptedSink, CallbackResult, Outcome of one delivery attempt (`FR-CBK-009`). `status_code` is `None` on a…, _NullCallbackSink, _NullCallbackSink, _NullCallbackSink

### Community 52 - "ParseResult"
Cohesion: 0.05
Nodes (80): DemoMetricsSink, AppLogParser, Parser plugin for configured application log patterns (Magic format)., compile_signature_rules(), extract_log_level(), First-match-wins signature rules with dynamic label templates., Extract [N/E/W/F/I] level from Magic-style log lines., resolve_label_template() (+72 more)

### Community 53 - "Histogram"
Cohesion: 0.12
Nodes (17): Histogram, Decimal, Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012). Shared…, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, build_latency_summary(), Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004). Shared by the… (+9 more)

### Community 54 - "parse_publish_config"
Cohesion: 0.12
Nodes (31): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, _PublishYaml, Any, BaseModel (+23 more)

### Community 55 - "MetricsIngestor"
Cohesion: 0.20
Nodes (20): MetricsIngestor, The production set: an aggregator that accepts every counter and latency…, _counters(), _feed(), _ingestor(), _meta(), Decimal, parametrize (+12 more)

### Community 56 - "test_STM_02_merge_semantics.py"
Cohesion: 0.23
Nodes (16): HistogramPayload, Wire shape of one histogram (`FR-MET-025`/`FR-MET-026`): fixed boundaries…, _histogram_payload(), FR-STM-002/003/004: counters merge by summation; ratios are recomputed from…, Two agents of unequal volume (FR-STM-003's required test shape): agent A:…, FR-MET-030-equivalent guard: cross-agent merge is exactly the case where per-…, A retried publish that misses batchId-level dedupe (a different ticket's…, _read_one_group() (+8 more)

### Community 57 - "CallbackDispatcher"
Cohesion: 0.12
Nodes (18): main(), _make_alert(), _print_counters(), Minimal walkthrough of the Callback Dispatcher (UBS-32/33). uv run python -m…, _run_one(), _step(), CallbackDispatcher, Logger (+10 more)

### Community 58 - "from_alert_event"
Cohesion: 0.20
Nodes (15): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, make_alert_event(), Shared test support for the callbacks package: builds `AlertEvent` fixtures…, FR-CBK-001/002/003 callback payload shape tests. (+7 more)

### Community 59 - "HttpsCallbackSink"
Cohesion: 0.20
Nodes (13): HttpsCallbackSink, AsyncBaseTransport, `FR-CBK-001`: HTTPS POST to the configured Magic endpoint. Rejects plain HTTP…, _make_alert(), UBS-32/33 integration test: dispatch and retry against a mock Magic endpoint.…, _run_one(), test_FR_CBK_001_success_marks_delivered(), handler() (+5 more)

### Community 60 - "AlertEvent"
Cohesion: 0.09
Nodes (18): Sync, non-blocking — the entry point a future wiring step calls from the same…, AlertRouter, Logger, Run one path's enqueue so its failure stays on that path., Enqueues alerts for publication, rejecting any that would poison the batch they…, Self-observability, same shape as `BackendPublisher.counters` and…, Hand every alert to the Callback Dispatcher (if configured), and every alert…, datetime (+10 more)

### Community 61 - "Confidence"
Cohesion: 0.05
Nodes (31): Confidence, Parser, Enum, Protocol, str, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'. (+23 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.17
Nodes (18): FakeQueue, Flaky, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend., test_at_critical_watermark_is_unhealthy(), test_at_high_watermark_is_degraded_with_reason_and_trend(), test_below_high_watermark_is_healthy(), test_buffer_drops_oldest_when_full() (+10 more)

### Community 63 - "HeartbeatMonitor"
Cohesion: 0.16
Nodes (11): AlertingConfig, Backend-owned alerting rules (spec 005 `FR-RUL-030`)., backend_alert_id(), HeartbeatMonitor, Resolve a backend alert immediately when a fresh heartbeat arrives., Periodically evaluates agent heartbeat staleness., _heartbeat(), datetime (+3 more)

### Community 64 - "classify_http_status"
Cohesion: 0.25
Nodes (13): classify_http_status(), StrEnum, FR-CBK-006: HTTP outcome -> retry decision classification., `FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent failure., RetryDecision, enum, parametrize, FR-CBK-006 HTTP status -> retry decision classification tests. (+5 more)

### Community 65 - "telemetry_agent_metrics_aggregator"
Cohesion: 0.13
Nodes (24): app_log_counter_dims(), ComponentLimiter, derive_app_log_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MA-02: order / execution / reject counters and reject-reason normalisation.…, fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not OrdStatus —… (+16 more)

### Community 66 - "enrich.py"
Cohesion: 0.08
Nodes (42): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+34 more)

### Community 67 - "BackendPublisher"
Cohesion: 0.09
Nodes (20): _drain(), main(), _make_snapshot(), _print_state(), datetime, Minimal walkthrough of the Backend Publisher (UBS-103/104). uv run python -m…, Stands in for the backend: returns responses from a fixed script, one per call,…, _ScriptedSink (+12 more)

### Community 68 - "rules/demo_quickstart.py"
Cohesion: 0.05
Nodes (39): _alert_storm_act(), _backend_unreachable_act(), _dedup_act(), _Demo, _FlakyBackendSink, _heartbeat_timeout_act(), main(), _no_log_activity_act() (+31 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.13
Nodes (20): Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Magic simulator for development, Do not overengineer (development principle), Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores, Microsoft Teams as the only user interface (+12 more)

### Community 70 - "AppDeps"
Cohesion: 0.09
Nodes (43): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary(), healthz(), metrics() (+35 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.10
Nodes (13): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+5 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (21): env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), datetime, fixture, TestClient (+13 more)

### Community 73 - "asyncio"
Cohesion: 0.11
Nodes (15): DropOldestQueue, T, FR-CBK-007: bounded pending queue, drop-oldest on overflow., Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow policy (`FR-…, Enqueue `item`, non-blocking. Returns True if an existing item was dropped to…, asyncio, FR-CBK-007 bounded queue, drop-oldest overflow tests., test_FR_CBK_007_enqueue_under_capacity_never_drops() (+7 more)

### Community 74 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.14
Nodes (15): Resource Discipline (§9), Compliance and Operability Constraints (§7), Configurability NFRs (§5), 009 — Non-Functional Requirements and Security, NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-SCA-001: Agent Independence/Statelessness, Observability of the Telemetry System (§6) (+7 more)

### Community 77 - "SessionHeartbeatTracker"
Cohesion: 0.14
Nodes (10): Sessions that have *just* crossed the threshold, each latched so one silence is…, Stop tracking a session. Called on `Logout`, and the reason this exists: a…, Introspection for demos/debug; not used by the detection path., Flags FIX sessions quiet for longer than `timeout_seconds`. Stateful across…, Internal tracking key, identical in format to `SeqTracker.session_key`.…, Record that a session was heard from at `at`. Any message counts, not just…, SessionHeartbeatTracker, _SessionState (+2 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.17
Nodes (21): datetime, Wires `config/rules.yaml` reloading to SIGHUP for a live `RuleEngine`.…, Returns the `resolved` events `apply_rules()` emits for alerts whose rule was…, Standalone use only: this reloads inside the signal handler and drops the…, SighupRuleReloader, _engine(), _fire(), datetime (+13 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (18): C++ candidate (rejected: worst-case failure modes), ADR 0001: Telemetry Agent written in Go (Superseded), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), ADR 0002: Telemetry stack is Python 3.12 + FastAPI, .NET alternative (rejected) (+10 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.12
Nodes (18): ADR 0004: No-Raw-Persistence Design, Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Parser Engine Agent-Level Contract (FR-PRS-001–003), Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing), Scaffold Document (plan/scaffold.md) (+10 more)

### Community 82 - "test_UBS_123_snapshot_emitter.py"
Cohesion: 0.14
Nodes (13): _build(), _Harness, _orders(), Decimal, parametrize, Path, UBS-123: `snapshot_bridge.SnapshotEmitter` unit tests., At t=1200 only [1150,1200) is fully retained; 1000-1140 are skipped. (+5 more)

### Community 83 - "pipeline_demo.py"
Cohesion: 0.17
Nodes (19): _build_bridge(), _build_registry(), _load_config(), main(), _print_stage(), OverflowPolicy, Path, End-to-end demo: LogMonitor → queue → parse → output → commit. (+11 more)

### Community 84 - "telemetry_agent/config.py"
Cohesion: 0.24
Nodes (11): LogsConfig, _LogsYaml, ParsingConfig, _ParsingYaml, _PipelineYaml, Any, BaseModel, Agent configuration: `config/agent.yaml` loaded once (UBS-114). Each section is… (+3 more)

### Community 85 - "datetime"
Cohesion: 0.08
Nodes (39): Health Reporter: per-file read lag (UBS-30), status rollup and heartbeat…, Log monitoring, rotation and truncation handling., datetime, Multi-file polling and lifecycle management for the Log Monitor., Return offset and read-lag state for every configured file., FileReadStatus, Value objects published by the Log Monitor., Offset, size and read lag for one monitored file. (+31 more)

### Community 86 - "telemetry_agent_metrics_counters"
Cohesion: 0.15
Nodes (22): Minimal walkthrough of the Metrics Aggregator (MA-01–04). uv run python -m…, _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact… (+14 more)

### Community 87 - "signing.py"
Cohesion: 0.16
Nodes (16): load_callback_secret(), FR-CBK-005: request signing so Magic can verify a callback originated from this…, `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), hashlib, hmac, FR-CBK-005 request-signing tests. (+8 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.12
Nodes (17): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Text Field Normalisation (FR-PRS-022), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025) (+9 more)

### Community 89 - "publishing/sink.py"
Cohesion: 0.11
Nodes (23): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), AsyncBaseTransport, UBS-103: the swappable Publisher transport boundary (spec 002 §6). Mirrors…, `FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the compressed…, `FR-PUB-001`/`002`: HTTPS POST with a bearer token, gzip above…, ASGITransport (+15 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (9): batch(), deps(), FakeClock, metrics(), datetime, UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)., test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() (+1 more)

### Community 91 - "Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)"
Cohesion: 0.17
Nodes (11): datetime, Offset + read lag for this file (UBS-30). See docs/plan/ubs30-notes.md., 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 5.1 The window — `health/window.py`, 5. UBS-59 — parse error rate, 7. Status rollup — the one table (+3 more)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (16): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009), NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test) (+8 more)

### Community 94 - "publisher.py"
Cohesion: 0.10
Nodes (31): BatchSequencer, build_batch(), datetime, FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, `FR-PUB-003`: a monotonically increasing `batchSeq` per agent, and a stable…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, make_pending_item(), PendingItem (+23 more)

### Community 95 - "MultiLogMonitor"
Cohesion: 0.07
Nodes (32): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+24 more)

### Community 97 - "StreamProcessor"
Cohesion: 0.09
Nodes (29): align_to_canonical(), datetime, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., Aligns, age-checks, and merges snapshots into a `MetricStore`. Non-blocking and…, FR-QRY-005: `False` ("warming") until `warmupWindow` has elapsed since this…, SnapshotOutcome, StreamProcessor (+21 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (10): _CountingRing, datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in…, The old `tick()` swept every instance's ring on every merge — O(instances x…, A query over one 10s bucket on a 6h-capacity (2160-bucket) ring must not touch…, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to() (+2 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.08
Nodes (42): main(), ingest(), _step(), CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent (+34 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.11
Nodes (27): extract_allowlisted_fields(), _hash_or_none(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, FR-PRS-020: extract only the tags in the compile-time allowlist above.…, hash_identifier(), load_hash_key(), Identifier hashing (FR-PRS-021)., HMAC-SHA256 of `raw` keyed with `key`, truncated to 16 hex chars. (+19 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (13): _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any…, _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved() (+5 more)

### Community 103 - "test_QRY_04_concurrency.py"
Cohesion: 0.13
Nodes (18): FR-QRY-004: the store MUST be safe under concurrent read/write via a per-…, A per-instance lock must still serialise writes *within* one instance — safety…, `dropped_after_retention_total` is a single store-wide counter incremented from…, `StreamProcessor.dropped_buckets_total` is incremented outside any per-instance…, `_get_or_create_instance` sets `_rings[instance_id]` before…, `_shed_oldest_tier` iterates `_rings.items()` and indexed `_instance_locks`…, _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another() (+10 more)

### Community 104 - "test_STM_01_window_alignment.py"
Cohesion: 0.13
Nodes (20): datetime, FR-STM-001, FR-ING-005, FR-STM-005: canonical window alignment, rejection of…, FR-ING-005: out-of-order snapshots for the same bucket must still merge to the…, A snapshot the StreamProcessor accepts as within maxBucketAge must still be…, A cap below 1 would drop every series as over-cap while `merge()` still marks…, FR-QRY-003: the shed threshold must be strictly above the warn threshold, or…, FR-MET-028 + FR-ING-005 together: gauges are last-write-wins, but this stage…, FR-STM-005: even if something calls MetricStore.merge() directly with a… (+12 more)

### Community 105 - "AgentHeartbeat"
Cohesion: 0.08
Nodes (22): BufferingHeartbeatSink, LoggingHeartbeatSink, PrintHeartbeatSink, Logger, Write one JSON line per heartbeat to stdout (demo)., Bounded retry buffer in front of another sink (UBS-60 demo stand-in). Not the…, Emit the wire JSON through `logging` (demo / local runs)., Register (or remove) the Publisher's queue-depth callback. (+14 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.12
Nodes (34): _alert(), _publisher(), LogCaptureFixture, Logger, parametrize, UBS-109: AlertRouter — the seam from Rule Engine output to the Backend…, Buffering is not publishing — this follows the alert all the way out through…, The containment that matters: the bad alert is dropped, the good ones are… (+26 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "health-reporter-overview.md"
Cohesion: 0.20
Nodes (9): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration, Not in this change (+1 more)

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.05
Nodes (59): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestGuardConfig, IngestionConfig (+51 more)

### Community 110 - "test_UBS_104_outage_isolation.py"
Cohesion: 0.29
Nodes (7): _HangingSink, _make_alert(), _make_snapshot(), UBS-104 integration test: `NFR-REL-003` -- a backend outage must never affect…, Stands in for a backend that never responds -- e.g. a dropped connection to a…, _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher()

### Community 111 - "test_publishing_helpers.py"
Cohesion: 0.29
Nodes (6): FakePublisher, UBS-58/60: the Health Reporter reaches the backend only through the Backend…, _reporter(), test_connect_points_outbox_signals_at_the_publisher(), test_drop_hook_counts_each_evicted_item(), test_provider_returns_a_fresh_wire_heartbeat_each_call()

### Community 112 - "StreamProcessorConfig"
Cohesion: 0.16
Nodes (17): StreamProcessorConfig, Read-only configuration shared with the ingestion boundary., datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep… (+9 more)

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "LogMonitor"
Cohesion: 0.06
Nodes (46): LogMonitor, Advance committed offset after successful parse+ingest (FR-PIP-006)., Persist committed offsets to disk (checkpoint / shutdown)., Monitors file paths, handles rotations/truncations, spawns Harvesters, and…, OffsetTracker, Path, Registrar subsystem for tracking offsets of log files. Stores file offsets…, Generates internal state ID format (e.g., 'native::16777232-1048201'). (+38 more)

### Community 115 - "UBS-49 — Pipeline Bridge Integration (live agent path)"
Cohesion: 0.18
Nodes (11): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Health Reporter (component), Health Reporter Heartbeat Requirement (FR-HLT-001), Backend Configuration and Secrets (§9), NFR-SEC-004: Secrets from Environment Only, Security: Secrets (§3.2) (+3 more)

### Community 116 - "NFR-REL-003: Backend Outage Must Not Affect Alerting"
Cohesion: 0.50
Nodes (5): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), NFR-REL-003: Backend Outage Must Not Affect Alerting, Reliability NFRs (§2), Runbook: Backend Unreachable

### Community 117 - "test_UBS_115_snapshot_to_metricstore.py"
Cohesion: 0.23
Nodes (17): _aggregator(), _drain_backend(), _evaluator(), _ingest_three_orders(), _publish_and_drain(), _publisher(), Decimal, FastAPI (+9 more)

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.12
Nodes (33): _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _publish_and_drain(), _publisher(), UBS-109 integration: raw FIX bytes -> FixParser -> MetricsAggregator ->…, Run the ingestion consumer until the queued batch is fully processed.… (+25 more)

### Community 119 - "test_UBS_116_app_log_ingest.py"
Cohesion: 0.39
Nodes (6): _ingested(), _meta(), UBS-116: MetricsIngestor turns parsed Application.log lines into app-log…, test_app_log_counts_appear_in_the_snapshot(), test_app_log_counts_group_by_signature_level_and_component(), test_fix_metrics_do_not_appear_for_app_log_lines()

### Community 120 - "is_parse_error"
Cohesion: 0.29
Nodes (5): is_parse_error(), Count one parsed line, and a parse error if `is_parse_error(result)`., What the heartbeat counts as a parse error (UBS-59). Same definition as the…, UBS-59: parse-error window, test_is_parse_error_matches_aggregator_convention()

### Community 121 - "test_snapshot.py"
Cohesion: 0.25
Nodes (7): Wire-format Snapshot contract (spec 004 §3, FR-MET-024..028)., FR-STM-004: there is no wire shape for 'summary percentiles only, no histogram'…, test_histogram_payload_requires_the_full_shape_not_a_percentile_summary(), test_parses_the_spec_004_example_verbatim(), test_to_histogram_ignores_unrecognised_bucket_keys_defensively(), test_unknown_dimension_shaped_extra_key_on_a_series_is_rejected(), test_unknown_top_level_field_is_rejected()

### Community 122 - "snapshot_bridge.py"
Cohesion: 0.16
Nodes (15): build_snapshot(), datetime, UBS-115: converts `MetricsAggregator` buckets into the wire `Snapshot`.…, Enqueue missed and latest buckets; returns how many were enqueued., Rename each internal dim to its wire name and drop anything not allowlisted…, One `Snapshot` for the closed interval `[bucket_start, bucket_start +…, _to_payload(), _to_wire_dimensions() (+7 more)

### Community 123 - "Implementation Status live document"
Cohesion: 0.24
Nodes (10): is_parse_error() definition, record_parse_result() intake, Implementation Status live document, M1.5 Pipeline bridge (UBS-48/49), M1 Log monitor and configuration (not started), M2 FIX parser (UBS-40-47), M3 Metrics aggregation (MA-01-04), derive_parser_counters (UBS-18) (+2 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "HealthThresholds"
Cohesion: 0.13
Nodes (22): AgentStatus, HealthThresholds, FR-HLT-002 thresholds. Only the read-lag one has a producer on UBS-58; the rest…, HealthSignals, FR-HLT-002 rollup for the signals that exist; FR-HLT-003 reasons. Each rule…, spec 011 s1.1: publish queue depth >= critical watermark unhealthy, >= high…, spec 011 s2: parse error rate > 25% unhealthy, > 1% degraded., Everything `derive_status` looks at, sampled at one instant. `None` means the… (+14 more)

### Community 127 - "Rule Engine"
Cohesion: 0.13
Nodes (21): CallbackFailing rule, NoLogActivity rule, Multi-tier severity rule shape, M5 Rules, alerts, callbacks, AgentCounterSampler (UBS-74), Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, rules.config_loader (FR-RUL-008/009) (+13 more)

### Community 128 - "ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server"
Cohesion: 0.33
Nodes (5): ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server, Consequences, Context, Decision, Rationale

### Community 129 - "ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell"
Cohesion: 0.33
Nodes (5): ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell, Consequences, Context, Decision, Rationale

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "test_UBS_113_evaluation_loop.py"
Cohesion: 0.23
Nodes (12): _order(), _NullCallbackSink, datetime, UBS-113 integration: raw FIX bytes -> FixParser -> MetricsAggregator /…, Each tick is one second later, so pending -> firing happens on tick 2 without…, An order with no ack, its age read off the correlator each tick., _rule(), _run_ticks() (+4 more)

### Community 133 - "_Clock"
Cohesion: 0.29
Nodes (3): _Clock, datetime, One wall clock for the aggregator (epoch floats) and the evaluator (datetimes),…

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 143 - "test_the_agent_process_alerts_magic_and_the_backend"
Cohesion: 0.33
Nodes (4): _burst(), Path, test_the_agent_process_alerts_magic_and_the_backend(), scenario()

### Community 157 - "test_STM_03_warmup.py"
Cohesion: 0.33
Nodes (9): datetime, FR-STM-006: an agent's post-restart cold-start state is preserved through the…, warmingUp flags incomplete data for the caller to exclude; it does not mean the…, _snapshot(), test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window(), test_an_unrelated_instance_is_not_marked_warming_up(), test_data_from_a_restarted_bucket_is_still_merged_not_dropped(), test_restarted_bucket_count_reflects_only_buckets_a_restart_touched() (+1 more)

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 195 - "DryRunPublishSink"
Cohesion: 0.40
Nodes (3): DryRunPublishSink, Logger, Log the intended publish, never open a socket. Use this while there's no real…

### Community 201 - "AlertStore"
Cohesion: 0.08
Nodes (39): AlertStoreConfig, Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)., AlertStore, _InstanceAlerts, _is_active_status(), datetime, Lock, In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`). (+31 more)

### Community 207 - "SeqTracker"
Cohesion: 0.23
Nodes (9): Per-session MsgSeqNum tracking., SeqTracker, SeqGapEvent, FR-PRS-027 sequence gap tests., test_FR_PRS_027_detects_gap(), test_FR_PRS_027_detects_regression(), test_FR_PRS_027_logon_resets_without_gap(), `logouts`, `seq_gaps` and `clock_skew_events` all label their `session_id` with… (+1 more)

### Community 210 - "metric_store.py"
Cohesion: 0.40
Nodes (4): _dim_key(), Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, _SeriesContribution, DimKey

### Community 213 - "Rule Engine demo runbook"
Cohesion: 0.15
Nodes (12): 1. `make rules-test`, 2. `make rules-quickstart`, 3. `make rules-reload-demo`, Going deeper, if asked, If someone asks, Pre-flight, Rule Engine demo runbook, make rules-quickstart (17-act demo) (+4 more)

### Community 214 - "test_RE_03_safety.py"
Cohesion: 0.36
Nodes (7): _counter_rule(), RE-02: suppression and safety (spec 005 §4) — maxActiveAlerts/AlertStorm,…, test_dependent_suppression_when_no_log_activity_is_firing(), test_max_active_alerts_emits_one_alertstorm_and_suppresses_further(), test_schedule_inactive_skips_rule_entirely(), test_silence_suppresses_notification_but_still_tracks_state(), test_storm_clears_once_under_cap_and_the_suppressed_rule_fires()

### Community 215 - "metrics/__init__.py"
Cohesion: 0.31
Nodes (8): spec 004 §5 / FR-ING-007: the dimension-key allowlist shared by both trust-…, compute_indicators(), compute_ratio(), Decimal, RatioDef, Derived-ratio computation (spec 004 §4.5, FR-QRY-010, FR-STM-003). Shared by…, `value` is None when `denominator` is 0 (never fabricate a rate from no data).…, All four spec 004 §4.5 indicators from one counters map — the caller supplies…

### Community 217 - "test_a_logged_reject_burst_reaches_the_backend_alert_store"
Cohesion: 0.15
Nodes (15): drop_hook(), on_drop(), heartbeat_provider(), provide(), AbstractContextManager, Any, Connect the Health Reporter to the Backend Publisher (UBS-58, UBS-60). The…, The publisher's `heartbeat_provider`: a fresh, wire-shaped heartbeat on every… (+7 more)

### Community 226 - ".__init__"
Cohesion: 0.22
Nodes (7): Logger, PublishSink, Protocol, The transport boundary. `HttpsPublishSink` is the Day-1 default (ADR 0003);…, BackendUnreachableCallback, DropCallback, HeartbeatProvider

### Community 234 - "telemetry_agent/main.py"
Cohesion: 0.10
Nodes (27): AbstractEventLoop, DryRunCallbackSink, Logger, `FR-CBK-011`: log the intended delivery, never open a socket. Use this while…, AgentConfig, connect_reporter_to_publisher(), Point the reporter's outbox signals at the publisher (UBS-60). Also records…, build_agent() (+19 more)

### Community 269 - "_alerts_to_backend_act"
Cohesion: 0.29
Nodes (4): _alerts_to_backend_act(), UBS-109. Every act above raised its alert locally and stopped there —…, _CapturingSink, Accepts (202) and keeps every batch.

### Community 270 - "Issue tracker: Jira"
Cohesion: 0.29
Nodes (6): Conventions, Issue tracker: Jira, Pull requests as a triage surface, Wayfinding operations, When a skill says "fetch the relevant ticket", When a skill says "publish to the issue tracker"

### Community 271 - "Domain Docs"
Cohesion: 0.33
Nodes (5): Before exploring, read these, Domain Docs, File structure, Flag ADR and spec conflicts, Use the glossary's vocabulary

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **198 isolated node(s):** `Context`, `Decision`, `Rationale`, `Consequences`, `Context` (+193 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1403 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **125 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `_Demo` connect `rules/demo_quickstart.py` to `AggregatorConfig`, `FixParser`, `RuleEngine`, `LatencyCorrelator`, `_alerts_to_backend_act`, `SourceMeta`, `demo_metrics_bridge.py`, `MetricsAggregator`, `datetime`, `AlertEvent`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `FixParser` connect `FixParser` to `test_metrics_event.py`, `test_UBS_113_evaluation_loop.py`, `HealthReporter`, `SourceMeta`, `demo_metrics_bridge.py`, `MetricsAggregator`, `test_RE_session_integration.py`, `Stack`, `ParseResult`, `MetricsIngestor`, `Confidence`, `enrich.py`, `rules/demo_quickstart.py`, `SeqTracker`, `pipeline_demo.py`, `Rule Engine demo runbook`, `test_a_logged_reject_burst_reaches_the_backend_alert_store`, `MultiLogMonitor`, `test_FR_PRS_021_identifiers.py`, `telemetry_agent/main.py`, `test_UBS_109_rule_engine_to_backend.py`, `is_parse_error`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `MetricsAggregator` connect `MetricsAggregator` to `RuleEngine`, `test_UBS_113_evaluation_loop.py`, `LatencyCorrelator`, `derive_counters`, `test_RE_publish_integration.py`, `demo_metrics_bridge.py`, `test_RE_session_integration.py`, `RuleEvaluator`, `test_MA_05_agent_counters.py`, `AggregatorConfig`, `test_UBS_113_evaluator.py`, `test_MA_03_correlation.py`, `test_RE_callback_integration.py`, `Histogram`, `MetricsIngestor`, `telemetry_agent_metrics_aggregator`, `rules/demo_quickstart.py`, `test_UBS_123_snapshot_emitter.py`, `datetime`, `telemetry_agent_metrics_counters`, `ParsedMessageEvent`, `test_UBS_115_snapshot_to_metricstore.py`, `test_UBS_109_rule_engine_to_backend.py`, `snapshot_bridge.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 78 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 78 INFERRED edges - model-reasoned connections that need verification._