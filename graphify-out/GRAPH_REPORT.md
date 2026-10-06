# Graph Report - avengers-fyp-is484  (2026-10-06)

## Corpus Check
- 297 files · ~160,999 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 12, .example 1, .typed 1)

## Summary
- 3791 nodes · 9328 edges · 231 communities (139 shown, 92 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 1658 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8c69396f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- telemetry_backend/main.py
- fix/parser.py
- test_RE_session_integration.py
- AlertEvent
- make_snapshot
- config_loader.py
- HealthReporter
- deps.py
- RetryPolicy
- LatencyCorrelator
- test_MA_02_counters.py
- LineQueue
- AgentHeartbeat
- LogMonitor
- PublishBuffer
- datetime
- derive_counters
- PublishResult
- MetricsAggregator
- SignatureMatcher
- PipelineBridge
- MetricStore
- Scaffold and Build Plan
- test_UBS_106_session_tracker.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- to_ingestion_heartbeat
- HeartbeatMonitor
- parse_publish_config
- test_ING_004_008_ingest_guard.py
- DeliveryTracker
- load_health_config
- test_MA_05_agent_counters.py
- AggregatorConfig
- classify_line
- publisher.py
- test_MA_03_correlation.py
- OffsetTracker
- config/rules.yaml live rule set
- Stack
- supervisor.py
- MetricsAggregator ring buffer
- _Clock
- SourceMeta
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- test_metrics_event.py
- callbacks/config.py
- CallbackResult
- telemetry_agent_parser_applog_parser
- ParseResult
- telemetry_agent_rules_engine
- StreamProcessor
- dataclasses
- test_health_endpoints.py
- health/demo.py
- test_FR_CBK_001_002_003_payload.py
- HttpsCallbackSink
- CallbackDispatcher
- metrics/__init__.py
- test_queue_depth.py
- AgentRegistry
- DropOldestQueue
- SeqTracker
- enrich.py
- BackendPublisher
- _Demo
- Telemetry Agent (architecture constraint)
- AppDeps
- BoundedQueue
- test_internal_api.py
- test_RE_publish_integration.py
- PipelineCommitter
- json
- 009 — Non-Functional Requirements and Security
- Histogram
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- test_RE_callback_integration.py
- pipeline_demo.py
- identifiers.py
- mock_logger.py
- services/demo_quickstart.py
- committer.py
- End-to-End Acceptance Scenario (FR-TST-010)
- rules/demo_quickstart.py
- test_ING_004_008_routes.py
- AgentRecord
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- Heartbeat
- heartbeat_json
- dispatcher.py
- StreamProcessorConfig
- Decimal
- ParsedMessageEvent
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- test_QRY_04_concurrency.py
- test_agent_registry.py
- HttpHeartbeatSink
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- health-reporter-overview.md
- telemetry_backend/config.py
- test_UBS_110_alert_router_callbacks.py
- snapshot
- test_readyz_shared_processor.py
- telemetry_shared shared schema package
- internal.py
- UBS-49 — Pipeline Bridge Integration (live agent path)
- .snapshot
- test_reporter.py
- test_UBS_109_rule_engine_to_backend.py
- _backend_unreachable_act
- test_RE_02_evaluators.py
- ParserWorkerPool
- BackendPublisher
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- test_UBS_104_outage_isolation.py
- telemetry_agent_parser_applog_signatures
- Rule Engine
- Event
- effective_reject_reason
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- CounterRegistry
- telemetry-shared
- telemetry_agent_parser_applog_telemetry
- telemetry_agent_parser_config
- PipelineStats
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
- IngestionService
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- AlertStore
- telemetry_agent_parser_fix_telemetry
- telemetry_agent_parser_registry
- metrics.py
- telemetry_backend/api/__init__.py
- Decimal
- telemetry_shared_metrics
- telemetry_shared_metrics_histogram
- Path
- ArgumentParser
- demo_reload.py
- FastAPI
- MultiLogMonitor
- Request
- pytest
- metrics_event.py
- LogCaptureFixture
- parametrize
- telemetry_agent_logs_log_monitor
- telemetry_agent_logs_offset_tracker
- telemetry_agent_parser_fix_fields
- telemetry_agent_parser_fix_seq_tracker
- telemetry_agent_parser_fix_timestamps
- AlertRouter
- telemetry_shared_models_parsed_message
- Rule Engine demo runbook
- .__init__

## God Nodes (most connected - your core abstractions)
1. `MetricsAggregator` - 84 edges
2. `HealthReporter` - 77 edges
3. `SourceMeta` - 65 edges
4. `FixParser` - 63 edges
5. `LogMonitor` - 61 edges
6. `StreamProcessorConfig` - 61 edges
7. `MetricStore` - 59 edges
8. `ParseResult` - 58 edges
9. `make_snapshot()` - 58 edges
10. `create_app()` - 52 edges

## Surprising Connections (you probably didn't know these)
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`` --references--> `AgentHeartbeat`  [INFERRED]
  docs/plan/health-reporter-overview.md → packages/telemetry_shared/src/telemetry_shared/models/health.py
- `Placeholder receiver — `scripts/heartbeat_receiver_stub.py`` --references--> `AgentHeartbeat`  [INFERRED]
  docs/plan/ubs58-60-notes.md → packages/telemetry_shared/src/telemetry_shared/models/health.py
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py

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

## Communities (231 total, 92 thin omitted)

### Community 0 - "telemetry_backend/main.py"
Cohesion: 0.06
Nodes (49): AppDeps, AlertsQueryParams, _build_parser(), _counts(), create_app(), enqueue_or_full(), get_alert(), ingest_batch() (+41 more)

### Community 1 - "fix/parser.py"
Cohesion: 0.08
Nodes (42): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), frame_message(), FramedMessage (+34 more)

### Community 2 - "test_RE_session_integration.py"
Cohesion: 0.14
Nodes (29): _counters(), _fire(), _ingest(), _ingest_tick(), _ingest_timeouts(), Decimal, UBS-73 integration: raw FIX log bytes -> FixParser -> metrics_event bridge ->…, A tracker that has watched `lines` go past, so it knows which sessions exist… (+21 more)

### Community 3 - "AlertEvent"
Cohesion: 0.10
Nodes (37): _AlertState, AlwaysActive, _decimal_or_none(), _matched_condition(), _matched_tier(), _metric_context(), datetime, Decimal (+29 more)

### Community 4 - "make_snapshot"
Cohesion: 0.19
Nodes (31): make_gauges(), make_indicator(), make_indicators(), make_snapshot(), datetime, Decimal, Shared test support for the rules package: builds `MetricsSnapshot` fixtures…, `empty=True` builds a snapshot with zero groups (nothing ingested this window… (+23 more)

### Community 5 - "config_loader.py"
Cohesion: 0.08
Nodes (36): load_rules(), load_rules_from_yaml(), _parse_duration_seconds(), Any, BaseModel, datetime, Exception, field_validator (+28 more)

### Community 6 - "HealthReporter"
Cohesion: 0.08
Nodes (35): AgentStatus, HealthReporter, HealthSignals, datetime, Per-file read health, keyed by the same name `monitors` was built with., Worst-case lag across files (heartbeat gauge). None if none have read yet., Files whose lag exceeds the threshold. Unread files are never flagged., Count a parse error from a producer that does not hand over a `ParseResult`… (+27 more)

### Community 7 - "deps.py"
Cohesion: 0.11
Nodes (20): datetime, Shared service instances the routers reach through `request.app.state`. One…, _utc_now(), Agent Registry (spec 006 FR-ING-010; UBS-69 read side, UBS-87 write side). One…, In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`)., Backend-owned `AgentHeartbeatMissing` rule (`FR-QRY-018`, `FR-RUL-030`)., IngestionValidationIssue, datetime (+12 more)

### Community 8 - "RetryPolicy"
Cohesion: 0.08
Nodes (26): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, CounterRegistry, UBS-104: lightweight in-process counters, shared between the Callback… (+18 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.11
Nodes (16): CorrelatorStats, LatencyCorrelator, OrderContext, datetime, Decimal, timedelta, MA-03: order correlation and latency. Standalone producer into the shared…, Recorded so consumers of a snapshot know what a latency number means (MA-03 AC)… (+8 more)

### Community 10 - "test_MA_02_counters.py"
Cohesion: 0.15
Nodes (22): Config-driven raw-reason -> canonical-label mapping. Backs MetricsAggregator's…, ReasonNormalizer, build_aggregator(), _exec_report_event(), ingest_fixture(), _reject_event(), test_business_cancel_and_session_rejects_stay_separate_but_sum_to_total(), test_counts_match_the_hand_labelled_fixture() (+14 more)

### Community 11 - "LineQueue"
Cohesion: 0.12
Nodes (11): LineQueue, OverflowPolicy, Handoff from the log monitor to parser workers., Monitor handoff (FR-PIP-001). Blocks by default when queue is full., QueuedLine, One complete log line waiting for a parser worker., _meta(), test_event_queue_defaults_to_256_capacity() (+3 more)

### Community 12 - "AgentHeartbeat"
Cohesion: 0.08
Nodes (29): HeartbeatEmitter, LoggingHeartbeatSink, datetime, Event, Logger, Emit the wire JSON through `logging` (demo / local runs)., Build and send one heartbeat. Sink failures are counted, not raised: a dead…, Tick every `interval_seconds` until `stop` is set. First tick is immediate so a… (+21 more)

### Community 13 - "LogMonitor"
Cohesion: 0.07
Nodes (26): Harvester, LogMonitor, datetime, Path, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, One complete log line with stable byte identity for idempotent ingest., Find retained rotations that were created while the agent was down. This… (+18 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (25): PendingItem, PublishBuffer, Put previously-`take`n items back at the front, in original order -- they are…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both…, Drop items older than `max_age_seconds`. The deque is strictly insertion-…, Remove and return up to `max_items` from the front., _item(), FR-PUB-004: the byte-and-age-bounded `PublishBuffer` (UBS-104's replacement for… (+17 more)

### Community 15 - "datetime"
Cohesion: 0.07
Nodes (29): Confidence, Parser, Enum, Protocol, str, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'. (+21 more)

### Community 16 - "derive_counters"
Cohesion: 0.10
Nodes (32): UBS-74: bridges the agent's own since-startup counters into the windowed…, derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MA-02: order / execution / reject counters and reject-reason normalisation.…, All four counter families in one event walk., fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not OrdStatus —… (+24 more)

### Community 17 - "PublishResult"
Cohesion: 0.14
Nodes (31): Stands in for the backend: returns responses from a fixed script, one per call,…, _ScriptedSink, PublishAction, StrEnum, PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, make_snapshot(), _FakeSink (+23 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.13
Nodes (17): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator, datetime, Decimal, Shared metrics store (spec 004 §3): a time-bucketed ring buffer holding both… (+9 more)

### Community 19 - "SignatureMatcher"
Cohesion: 0.11
Nodes (19): AppLogParser, Parser plugin for configured application log patterns (Magic format)., compile_signature_rules(), First-match-wins signature rules with dynamic label templates., resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule (+11 more)

### Community 20 - "PipelineBridge"
Cohesion: 0.09
Nodes (23): _build_bridge(), OverflowPolicy, Selects the first parser in a configured chain with Confidence.HIGH., Return unknown parser names in chain., Return a parser from this registry by configuration name., Registry, PipelineConfig, Pipeline bridge sizing (spec 010 §pipeline, FR-PIP-002–004). (+15 more)

### Community 21 - "MetricStore"
Cohesion: 0.13
Nodes (16): _CanonicalBucket, MetricStore, datetime, Lock, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a…, Evict buckets that have aged out of retention within *one* instance's ring —…, Evict stale buckets across every instance's ring and check memory pressure. For… (+8 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.07
Nodes (36): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+28 more)

### Community 23 - "test_UBS_106_session_tracker.py"
Cohesion: 0.08
Nodes (43): Sessions that have *just* crossed the threshold, each latched so one silence is…, Stop tracking a session. Called on `Logout`, and the reason this exists: a…, Introspection for demos/debug; not used by the detection path., Flags FIX sessions quiet for longer than `timeout_seconds`. Stateful across…, Internal tracking key, identical in format to `SeqTracker.session_key`.…, Record that a session was heard from at `at`. Any message counts, not just…, SessionHeartbeatTracker, _SessionState (+35 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (31): health: threshold config block, heartbeat: interval config, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry (+23 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "to_ingestion_heartbeat"
Cohesion: 0.17
Nodes (17): Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat(), make(), UBS-58/66 wire compatibility: our heartbeat flattened to the Ingestion…, The whole point: the Ingestion Service must accept what we send., The ingestion contract has no null for these; the cost is recorded in the notes…, Never claim a second of uptime the agent has not had. (+9 more)

### Community 27 - "HeartbeatMonitor"
Cohesion: 0.12
Nodes (15): AlertingConfig, Backend-owned alerting rules (spec 005 `FR-RUL-030`)., backend_alert_id(), HeartbeatMonitor, datetime, Resolve a backend alert immediately when a fresh heartbeat arrives., Periodically evaluates agent heartbeat staleness., Not in this change (+7 more)

### Community 28 - "parse_publish_config"
Cohesion: 0.13
Nodes (27): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, Any, Exception, Path (+19 more)

### Community 29 - "test_ING_004_008_ingest_guard.py"
Cohesion: 0.11
Nodes (27): Accept, Duplicate, IngestGuard, datetime, RateLimited, Batch dedupe and per-agent rate limiting (UBS-85; FR-ING-004, FR-ING-008).…, Record a batch that is now on the ingest queue., _utc_now() (+19 more)

### Community 30 - "DeliveryTracker"
Cohesion: 0.07
Nodes (40): classify_http_status(), StrEnum, FR-CBK-006: HTTP outcome -> retry decision classification., `FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent failure., RetryDecision, DeliveryRecord, DeliveryStatus, DeliveryTracker (+32 more)

### Community 31 - "load_health_config"
Cohesion: 0.08
Nodes (39): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, HealthThresholds, _HealthYaml, HeartbeatConfig, _HeartbeatYaml (+31 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.14
Nodes (24): AgentCounterSampler, datetime, Turns monotonic since-startup counters into per-bucket deltas. Stateful across…, Ingest the increase in each tracked counter since the last call. The first call…, _aggregator(), Decimal, UBS-74: `MetricsAggregator.ingest_agent_counters` and the `AgentCounterSampler`…, A restarted dispatcher's registry drops back to 0. That is a new baseline, not… (+16 more)

### Community 33 - "AggregatorConfig"
Cohesion: 0.19
Nodes (22): AggregatorConfig, Bucket granularity, retained windows, and the per-metric dimension table (FR-…, FakeClock, A `Clock` (`() -> float`) that only advances when told to — lets a test assert…, make_event(), minimal_aggregator(), Decimal, test_10k_events_in_60s_window_returns_correct_count() (+14 more)

### Community 34 - "classify_line"
Cohesion: 0.13
Nodes (22): classify_line(), compile_app_log_patterns(), _looks_like_fix(), Pattern, Line classification (FR-PRS-010, FR-PRS-011)., Classify a log line before parsing (FR-PRS-010). Order: fix → app_log →…, True when 8=FIX/8=FIXT is followed by a delimiter and 35= within the window.…, Compile configured app-log regexes for use after FIX detection fails. (+14 more)

### Community 35 - "publisher.py"
Cohesion: 0.19
Nodes (12): UBS-103/104: batches buffered telemetry, gzip-compresses it, and POSTs it to…, ASGITransport, telemetry_agent_common_backoff, telemetry_agent_publishing_batch, telemetry_agent_publishing_buffer, telemetry_shared_models_ingestion, telemetry_shared_models_snapshot, _publisher() (+4 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "OffsetTracker"
Cohesion: 0.08
Nodes (30): Path, OffsetTracker, Path, Registrar subsystem for tracking offsets of log files. Stores file offsets…, Generates internal state ID format (e.g., 'native::16777232-1048201')., Loads state registry into memory Supports Filebeat's native JSON list array…, Retrieves the last known offset for a given (device, inode) pair., Persist committed offset after parse+ingest (FR-PIP-006). (+22 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.11
Nodes (28): Agent processing pipeline (monitor to health reporter), publish: Backend Publisher config block, BackendUnreachable rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule (+20 more)

### Community 39 - "Stack"
Cohesion: 0.05
Nodes (33): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), AsyncBaseTransport, `FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the compressed…, `FR-PUB-001`/`002`: HTTPS POST with a bearer token, gzip above…, gzip, Headers (+25 more)

### Community 40 - "supervisor.py"
Cohesion: 0.15
Nodes (9): QueueSnapshot, EventQueue, Parser → aggregator bounded event queue (FR-PIP-004)., Handoff from parser workers to downstream stages., Monitor → parser bounded line queue (FR-PIP-001, FR-PIP-002)., Pipeline bridge wiring monitor enqueue to parser workers (M1.5)., ParsedEvent, ParseResult plus the monitor metadata that produced it. (+1 more)

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.13
Nodes (20): AckLatencyBreach rule, Parse error rate signal (UBS-59), SlidingWindowCounter, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent) (+12 more)

### Community 42 - "_Clock"
Cohesion: 0.11
Nodes (11): _BoundSourcesCollector, _counter(), _gauge(), Reads ingestion / stream processor / store state at scrape time., Collector, CounterMetricFamily, GaugeMetricFamily, IngestionSource (+3 more)

### Community 43 - "SourceMeta"
Cohesion: 0.09
Nodes (25): is_parse_error(), Count one parsed line, and a parse error if `is_parse_error(result)`., What the heartbeat counts as a parse error (UBS-59). Same definition as the…, demo_log_lines(), Path, Return parsed corpus lines, optionally filtered to one source file label., FixParser, ParseError (+17 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.17
Nodes (17): FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides(), test_errors_counted_and_reported_in_heartbeat() (+9 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.13
Nodes (21): datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, drive(), telemetry_agent_health_window (+13 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.09
Nodes (30): Problem P-1: Limited visibility into live trading activity and health, Problem P-4: No way to ask questions of live telemetry, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), Consistent-Hash Routing on instanceId, 001 — Architecture (+22 more)

### Community 47 - "CamelModel"
Cohesion: 0.08
Nodes (35): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary(), _is_active_status(), datetime (+27 more)

### Community 48 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (41): build_parsed_message_event(), Construct the Metrics Aggregator's event from one framed FIX line. Returns None…, _to_decimal(), _meta(), _parse(), _parser_counters(), datetime, Decimal (+33 more)

### Community 49 - "callbacks/config.py"
Cohesion: 0.15
Nodes (22): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+14 more)

### Community 50 - "CallbackResult"
Cohesion: 0.10
Nodes (15): Stands in for Magic: keys its canned response off the alert ID inside the…, _ScriptedSink, CallbackResult, CallbackSink, DryRunCallbackSink, Logger, Protocol, `FR-CBK-011`: log the intended delivery, never open a socket. Use this while… (+7 more)

### Community 52 - "ParseResult"
Cohesion: 0.10
Nodes (45): main(), Telemetry Agent entrypoint., DemoMetricsSink, Demo metrics sink for parser CLI (mirrors spec 004 counter names)., extract_log_level(), Extract [N/E/W/F/I] level from Magic-style log lines., _corpus_files(), _fields_dict() (+37 more)

### Community 53 - "telemetry_agent_rules_engine"
Cohesion: 0.33
Nodes (7): telemetry_agent_rules_engine, _counter_rule(), RE-02: suppression and safety (spec 005 §4) — maxActiveAlerts/AlertStorm,…, test_max_active_alerts_emits_one_alertstorm_and_suppresses_further(), test_schedule_inactive_skips_rule_entirely(), test_silence_suppresses_notification_but_still_tracks_state(), test_storm_clears_once_under_cap_and_the_suppressed_rule_fires()

### Community 54 - "StreamProcessor"
Cohesion: 0.08
Nodes (32): align_to_canonical(), datetime, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., Aligns, age-checks, and merges snapshots into a `MetricStore`. Non-blocking and…, Read-only configuration shared with the ingestion boundary., FR-QRY-005: `False` ("warming") until `warmupWindow` has elapsed since this…, SnapshotOutcome (+24 more)

### Community 55 - "dataclasses"
Cohesion: 0.07
Nodes (43): FR-CBK-007: bounded pending queue, drop-oldest on overflow., FR-CBK-001/011: the swappable Callback transport boundary (spec 005 §3).…, Heartbeat emitter (UBS-58, FR-HLT-001). Ticks on a fixed interval regardless of…, Health Reporter: per-file read lag (UBS-30), status rollup and heartbeat…, _utc_now(), Log monitoring, rotation and truncation handling., datetime, Multi-file polling and lifecycle management for the Log Monitor. (+35 more)

### Community 56 - "test_health_endpoints.py"
Cohesion: 0.21
Nodes (11): datetime, FR-HLT-010, FR-QRY-005: `/healthz` is a liveness probe with no dependency…, FR-QRY-005: elapsed time alone must not flip `/readyz` to `ready` — if…, `has_data` is sticky: a legitimately quiet period after real data was already…, `main.py`'s module-level `StreamProcessor` singleton starts its warmup clock at…, _snapshot(), test_is_ready_returns_false_before_warmup_window_elapses_even_with_data(), test_is_ready_returns_true_once_warmup_window_has_elapsed_and_data_exists() (+3 more)

### Community 57 - "health/demo.py"
Cohesion: 0.17
Nodes (15): _build_parser(), _detect_session_timeouts(), main(), _main_async(), _make_sink(), _poll_forever(), ArgumentParser, Event (+7 more)

### Community 58 - "test_FR_CBK_001_002_003_payload.py"
Cohesion: 0.20
Nodes (15): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, make_alert_event(), Shared test support for the callbacks package: builds `AlertEvent` fixtures…, FR-CBK-001/002/003 callback payload shape tests. (+7 more)

### Community 59 - "HttpsCallbackSink"
Cohesion: 0.20
Nodes (13): HttpsCallbackSink, AsyncBaseTransport, `FR-CBK-001`: HTTPS POST to the configured Magic endpoint. Rejects plain HTTP…, _make_alert(), UBS-32/33 integration test: dispatch and retry against a mock Magic endpoint.…, _run_one(), test_FR_CBK_001_success_marks_delivered(), handler() (+5 more)

### Community 60 - "CallbackDispatcher"
Cohesion: 0.11
Nodes (18): main(), _make_alert(), _print_counters(), Minimal walkthrough of the Callback Dispatcher (UBS-32/33). uv run python -m…, _run_one(), _step(), CallbackDispatcher, AlertEvent (+10 more)

### Community 61 - "metrics/__init__.py"
Cohesion: 0.18
Nodes (15): build_latency_summary(), Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004). Shared by the…, compute_indicators(), compute_ratio(), Decimal, RatioDef, Derived-ratio computation (spec 004 §4.5, FR-QRY-010, FR-STM-003). Shared by…, `value` is None when `denominator` is 0 (never fabricate a rate from no data).… (+7 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.11
Nodes (21): BufferingHeartbeatSink, HeartbeatSink, Bounded retry buffer in front of another sink (UBS-60 demo stand-in). Not the…, FakeQueue, Flaky, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend., test_at_critical_watermark_is_unhealthy() (+13 more)

### Community 63 - "AgentRegistry"
Cohesion: 0.10
Nodes (26): AgentRegistry, Thread-safe map of known agents. Memory-only by design (FR-QRY-005)., Decommission (spec 011 runbook) so `missing` does not fire forever., build(), DataCompleteness, datetime, `dataCompleteness` block for query responses (spec 006 s4.1, FR-QRY-015).…, Derive completeness from the registry at `at`. `expected_agent_ids` is the set… (+18 more)

### Community 64 - "DropOldestQueue"
Cohesion: 0.18
Nodes (8): DropOldestQueue, T, Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow policy (`FR-…, Enqueue `item`, non-blocking. Returns True if an existing item was dropped to…, FR-CBK-007 bounded queue, drop-oldest overflow tests., test_FR_CBK_007_enqueue_under_capacity_never_drops(), test_FR_CBK_007_oldest_item_is_the_one_dropped(), test_FR_CBK_007_overflow_drops_oldest_and_increments_counter()

### Community 65 - "SeqTracker"
Cohesion: 0.29
Nodes (7): Per-session MsgSeqNum tracking., SeqTracker, SeqGapEvent, FR-PRS-027 sequence gap tests., test_FR_PRS_027_detects_gap(), test_FR_PRS_027_detects_regression(), test_FR_PRS_027_logon_resets_without_gap()

### Community 66 - "enrich.py"
Cohesion: 0.13
Nodes (28): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+20 more)

### Community 67 - "BackendPublisher"
Cohesion: 0.09
Nodes (19): make_pending_item(), datetime, FR-PUB-004: a pending-item buffer bounded by both total bytes and maximum age,…, Measured once at insert and cached on the `PendingItem` -- re-measuring on…, _size_of(), BackendPublisher, AlertEvent, datetime (+11 more)

### Community 68 - "_Demo"
Cohesion: 0.11
Nodes (9): _Demo, Holds the one parser/aggregator/engine trio the whole story runs on, so each…, Pretend `by` messages were lost in transit., ExecType/OrdStatus 8 = Rejected, OrdRejReason 3 = ExchangeClosed., 35=3, a session-level Reject — a FIX plumbing problem rather than a trading…, 35=9, a rejected cancel/replace — counted as `cancel_rejects`, kept apart from…, An ack whose SendingTime is `delay_ms` after its order. Latency is measured…, `count` orders that each get acked — the healthy baseline volume a reject… (+1 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.10
Nodes (25): Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Magic simulator for development, Do not overengineer (development principle), Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores, Microsoft Teams as the only user interface (+17 more)

### Community 70 - "AppDeps"
Cohesion: 0.21
Nodes (23): AppDeps, env(), FakeClock, heartbeat(), post(), datetime, fixture, TestClient (+15 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.10
Nodes (12): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+4 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.13
Nodes (24): create_internal_app(), UBS-96, FR-HLT-012: `/healthz`, `/readyz` and `/metrics` for the internal…, env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), datetime (+16 more)

### Community 73 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (22): _aggregator(), _engine(), _fail_n_times(), _publisher(), UBS-75 integration: BackendPublisher -> consecutive_publish_failures gauge ->…, The whole reason this is a gauge: recovery is observable. A windowed failure…, FR-MET-031. An agent with no publisher must not look like an agent that is…, Regression guard on spec 005 §1.2's withdrawn approximation.… (+14 more)

### Community 74 - "PipelineCommitter"
Cohesion: 0.13
Nodes (6): PipelineCommitter, Consumes ParsedEvent objects and commits file offsets after ingest., ProcessedLineDeduper, Bounded LRU cache suppressing double-count on re-read., Path, test_committed_offset_advances_only_after_committer_ingest()

### Community 75 - "json"
Cohesion: 0.14
Nodes (14): BaseHTTPRequestHandler, http, http_server, json, _AgentRecord, main(), _make_handler(), do_GET() (+6 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.11
Nodes (20): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), Resource Discipline (§9), Compliance and Operability Constraints (§7), Configurability NFRs (§5), 009 — Non-Functional Requirements and Security, NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed (+12 more)

### Community 77 - "Histogram"
Cohesion: 0.10
Nodes (29): Histogram, Decimal, Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012). Shared…, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, HistogramPayload, Wire shape of one histogram (`FR-MET-025`/`FR-MET-026`): fixed boundaries… (+21 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.28
Nodes (16): _engine(), _fire(), datetime, LogCaptureFixture, Path, skipif, RE-05: `RuleEngine.apply_rules` and `SighupRuleReloader` (`FR-RUL-008`)., Two evaluate() calls: the first only enters `pending` (no event, per the FSM's… (+8 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (18): C++ candidate (rejected: worst-case failure modes), ADR 0001: Telemetry Agent written in Go (Superseded), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), ADR 0002: Telemetry stack is Python 3.12 + FastAPI, .NET alternative (rejected) (+10 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.12
Nodes (18): ADR 0004: No-Raw-Persistence Design, Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Parser Engine Agent-Level Contract (FR-PRS-001–003), Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing), Scaffold Document (plan/scaffold.md) (+10 more)

### Community 82 - "test_RE_callback_integration.py"
Cohesion: 0.12
Nodes (29): telemetry_agent_metrics_counters, telemetry_agent_metrics_snapshot, _aggregator(), _alert(), _dispatch(), _drain(), _fire(), UBS-74 integration: CallbackDispatcher -> CounterRegistry ->… (+21 more)

### Community 83 - "pipeline_demo.py"
Cohesion: 0.12
Nodes (23): _build_registry(), _load_config(), main(), _print_stage(), Path, End-to-end demo: LogMonitor → queue → parse → output → commit., Hands back the `FixParser` alongside the registry it went into. Callers need…, run_happy_path() (+15 more)

### Community 84 - "identifiers.py"
Cohesion: 0.15
Nodes (17): load_callback_secret(), FR-CBK-005: request signing so Magic can verify a callback originated from this…, `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), Identifier hashing (FR-PRS-021)., hashlib, hmac (+9 more)

### Community 85 - "mock_logger.py"
Cohesion: 0.21
Nodes (12): main(), get_timestamps(), Path, Rotate with numbered retained archives, like ``logrotate``.…, rotate_if_needed(), run_harness(), argparse, sys (+4 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (15): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact…, The exact 3-order story from the Metrics Aggregator quickstart: two accepted… (+7 more)

### Community 87 - "committer.py"
Cohesion: 0.15
Nodes (13): Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)., LinePosition, Idempotent ingest dedupe by file byte position (FR-PIP-007)., M1.5 pipeline bridge: bounded queues between log monitor and parser., telemetry_agent_metrics_demo_sink, telemetry_agent_pipeline_committer, telemetry_agent_pipeline_config, telemetry_agent_pipeline_deduper (+5 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.12
Nodes (17): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Text Field Normalisation (FR-PRS-022), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025) (+9 more)

### Community 89 - "rules/demo_quickstart.py"
Cohesion: 0.11
Nodes (21): _alert_storm_act(), _alerts_to_backend_act(), _dedup_act(), _heartbeat_timeout_act(), main(), _no_log_activity_act(), _part(), Minimal walkthrough of the Rule Engine firing on real data. uv run python -m… (+13 more)

### Community 90 - "test_ING_004_008_routes.py"
Cohesion: 0.29
Nodes (9): batch(), deps(), FakeClock, metrics(), datetime, UBS-85: POST /telemetry/batch dedupe (FR-ING-004) and 429 (FR-ING-008)., test_a_batch_refused_with_queue_full_is_accepted_on_retry(), test_a_retried_batch_is_acknowledged_as_duplicate_and_enqueued_once() (+1 more)

### Community 91 - "AgentRecord"
Cohesion: 0.17
Nodes (7): AgentRecord, datetime, `missing` if stale, otherwise whatever the agent last reported., Agent IDs past the threshold - the `dataCompleteness.staleAgents` input (FR-…, Store the latest heartbeat. Returns True on first contact so the caller can…, _utc_now(), RegistryStatus

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (16): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009), NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test) (+8 more)

### Community 94 - "Heartbeat"
Cohesion: 0.11
Nodes (24): BatchSequencer, build_batch(), datetime, FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, `FR-PUB-003`: a monotonically increasing `batchSeq` per agent, and a stable…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, inspect, NoReturn (+16 more)

### Community 95 - "heartbeat_json"
Cohesion: 0.09
Nodes (24): heartbeat_json(), Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, fastapi_testclient, telemetry_agent_health_heartbeat, FakeClock, datetime, Path, Agent Health Reporter (UBS-58/59/60) -> Ingestion (UBS-66) -> health read side… (+16 more)

### Community 96 - "dispatcher.py"
Cohesion: 0.11
Nodes (23): UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, Request, telemetry_agent_callbacks_backoff, telemetry_agent_callbacks_config, telemetry_agent_callbacks_payload, telemetry_agent_callbacks_queue, telemetry_agent_callbacks_retry, telemetry_agent_callbacks_self_metrics (+15 more)

### Community 97 - "StreamProcessorConfig"
Cohesion: 0.12
Nodes (25): StreamProcessorConfig, datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep…, _snapshot() (+17 more)

### Community 98 - "Decimal"
Cohesion: 0.07
Nodes (29): _dim_key(), Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, _SeriesContribution, Decimal, DimKey, Shared agent-to-backend ingestion contracts., One derived operational event., TelemetryEvent (+21 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.09
Nodes (41): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent, BaseModel (+33 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.11
Nodes (26): extract_allowlisted_fields(), _hash_or_none(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, FR-PRS-020: extract only the tags in the compile-time allowlist above.…, hash_identifier(), load_hash_key(), HMAC-SHA256 of `raw` keyed with `key`, truncated to 16 hex chars., Read the identifier hash key from the environment (NFR-SEC-004). Raises… (+18 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (13): _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any…, _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved() (+5 more)

### Community 103 - "test_QRY_04_concurrency.py"
Cohesion: 0.13
Nodes (18): FR-QRY-004: the store MUST be safe under concurrent read/write via a per-…, A per-instance lock must still serialise writes *within* one instance — safety…, `dropped_after_retention_total` is a single store-wide counter incremented from…, `StreamProcessor.dropped_buckets_total` is incremented outside any per-instance…, `_get_or_create_instance` sets `_rings[instance_id]` before…, `_shed_oldest_tier` iterates `_rings.items()` and indexed `_instance_locks`…, _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another() (+10 more)

### Community 104 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 105 - "HttpHeartbeatSink"
Cohesion: 0.07
Nodes (26): HttpHeartbeatSink, `POST /telemetry/heartbeat` (spec 007 §2.3) with the stdlib only. Placeholder…, Register (or remove) the Publisher's queue-depth callback., 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 4.1 Wire contract — `packages/telemetry_shared/models/health.py`, 4.4 Emitter and sinks — `health/heartbeat.py` (+18 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.12
Nodes (28): LogCaptureFixture, parametrize, telemetry_agent_publishing_config, telemetry_agent_publishing_publisher, telemetry_agent_publishing_sink, _alert(), _publisher(), AlertEvent (+20 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "health-reporter-overview.md"
Cohesion: 0.25
Nodes (7): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-49 — Pipeline Bridge Integration

### Community 109 - "telemetry_backend/config.py"
Cohesion: 0.10
Nodes (31): _AlertingYaml, BackendConfigError, _BackendConfigYaml, BackendHealthConfig, _BackendYaml, _drop_none(), IngestGuardConfig, IngestionConfig (+23 more)

### Community 110 - "test_UBS_110_alert_router_callbacks.py"
Cohesion: 0.23
Nodes (13): CallbackResult, _dispatcher(), _NullCallbackSink, _pending(), UBS-110: AlertRouter fans each alert out to the Callback Dispatcher as well as…, The guard protects the batch; a callback has no batch to poison., _router(), test_a_failing_dispatcher_does_not_cost_the_backend_its_alert() (+5 more)

### Community 111 - "snapshot"
Cohesion: 0.36
Nodes (13): hand_labelled_events(), Shared test support for the metrics package: a hand-labelled synthetic FIX-…, _ingest_all(), _shared_config(), test_gauges_are_empty_without_a_correlator(), test_gauges_reflect_pending_orders_and_event_staleness(), test_grouped_breakdown_by_symbol(), test_indicators_computed_from_hand_labelled_fixture() (+5 more)

### Community 112 - "test_readyz_shared_processor.py"
Cohesion: 0.31
Nodes (8): _batch_with_snapshot(), datetime, TestClient, FR-QRY-005: `/readyz` probes the same StreamProcessor that ingestion feeds.…, test_create_app_probes_the_supplied_services_own_processor(), test_create_app_rejects_a_processor_the_service_does_not_feed(), test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store(), _wait_for_status()

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "internal.py"
Cohesion: 0.21
Nodes (11): healthz(), metrics(), get, Response, Operator probes (UBS-96; FR-HLT-010, FR-HLT-012; spec 007 s5.3). Mounted on the…, Liveness only: the process is up and serving. No dependency checks, so a broken…, Readiness incl. warm-up (FR-QRY-005), from the same…, readyz() (+3 more)

### Community 115 - "UBS-49 — Pipeline Bridge Integration (live agent path)"
Cohesion: 0.18
Nodes (11): UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library, UBS-49 — Pipeline Bridge Integration (live agent path), Health Reporter (component), Health Reporter Heartbeat Requirement (FR-HLT-001), Backend Configuration and Secrets (§9), NFR-SEC-004: Secrets from Environment Only, Security: Secrets (§3.2) (+3 more)

### Community 116 - ".snapshot"
Cohesion: 0.22
Nodes (5): AlertEvent, Always with the correlator attached — that's what populates the `latency`…, Evaluate twice: once to move a matched rule to `pending`, then again past its…, One evaluation a moment later — enough for a tier escalation, which takes…, MetricsSnapshot

### Community 117 - "test_reporter.py"
Cohesion: 0.61
Nodes (7): make_monitor(), Path, test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.16
Nodes (26): MetricsAggregator, RuleEngine, _aggregator_with_a_reject_burst(), _drain_backend(), _engine(), _fire_reject_spike(), _order(), _publish_and_drain() (+18 more)

### Community 119 - "_backend_unreachable_act"
Cohesion: 0.25
Nodes (6): _backend_unreachable_act(), attempt(), _FlakyBackendSink, PublishResult, UBS-75. A real BackendPublisher against a backend that answers 503, driven one…, Backend stand-in for the UBS-75 act: answers whatever `status` currently says,…

### Community 120 - "test_RE_02_evaluators.py"
Cohesion: 0.12
Nodes (39): RE-03: the 14 default rules (spec 005 §1.2). Concrete `RuleConfig` values, used…, _tier(), _read_observed(), StrEnum, RE-01: rule and alert lifecycle types (spec 005 §1-2). Agent-internal…, FR-RUL-001: Day-1 supports exactly these five., Where a rule's observed value is read from in a MetricsSnapshot., One (severity, threshold) rung. `FR-RUL-022`: the matched tier is whichever,… (+31 more)

### Community 123 - "Implementation Status live document"
Cohesion: 0.24
Nodes (10): is_parse_error() definition, record_parse_result() intake, Implementation Status live document, M1.5 Pipeline bridge (UBS-48/49), M1 Log monitor and configuration (not started), M2 FIX parser (UBS-40-47), M3 Metrics aggregation (MA-01-04), derive_parser_counters (UBS-18) (+2 more)

### Community 124 - "demo_config.yaml (Magic parsing demo config)"
Cohesion: 0.32
Nodes (8): reject_text.txt scenario (ExecutionReport reject reasons), appLogPatterns regex, demo_config.yaml (Magic parsing demo config), errorSignatures (connection_disconnected, connect_timeout, venue_connect_failed), parsing thresholds (maxClockSkew, maxRejectReasonLabels, maxDynamicSignatureLabels), rejectReasonPatterns (price_exceeds_limit, unknown_symbol, market_closed), Enterprise Infrastructure Stream (Application.log), Text normalisation to bounded label set

### Community 125 - "test_UBS_104_outage_isolation.py"
Cohesion: 0.29
Nodes (7): _HangingSink, _make_alert(), _make_snapshot(), UBS-104 integration test: `NFR-REL-003` -- a backend outage must never affect…, Stands in for a backend that never responds -- e.g. a dropped connection to a…, _run_scenario(), test_callback_delivery_is_unaffected_by_a_hung_publisher()

### Community 127 - "Rule Engine"
Cohesion: 0.16
Nodes (17): NoLogActivity rule, Multi-tier severity rule shape, M5 Rules, alerts, callbacks, Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, rules.config_loader (FR-RUL-008/009), Dependent suppression (FR-RUL-021), Rule Engine (+9 more)

### Community 129 - "effective_reject_reason"
Cohesion: 0.33
Nodes (7): effective_reject_reason(), Single precedence: ordRejReason → rejectReasonText label → unspecified. For…, FR-PRS-024 rejection precedence tests., test_FR_PRS_024_ord_rej_reason_wins(), test_FR_PRS_024_session_reject_for_msg_type_reject(), test_FR_PRS_024_text_label_when_no_ord_rej(), test_FR_PRS_024_unspecified_when_missing()

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 137 - "PipelineStats"
Cohesion: 0.33
Nodes (3): PipelineStats, Queue depths and drop counters for heartbeat/metrics (FR-PIP-005)., test_pipeline_stats_expose_prometheus_metric_names()

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 195 - "IngestionService"
Cohesion: 0.10
Nodes (36): BatchAccepted, IngestionService, Apply the backend-side allowlists and bucket cardinality cap. Pydantic has…, Undo an admission reservation when the bounded queue is full., Keep store work off FastAPI's request path. A single consumer preserves the…, Owns a bounded queue and one background consumer., _CardinalityBucketKey, fastapi_routing (+28 more)

### Community 201 - "AlertStore"
Cohesion: 0.11
Nodes (30): AlertStoreConfig, Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)., AlertStore, _InstanceAlerts, Lock, Merge one alert update (`FR-QRY-016`, `FR-QRY-017`)., Per-instance active alerts and a bounded resolved history., _StoredAlert (+22 more)

### Community 205 - "metrics.py"
Cohesion: 0.29
Nodes (5): field_serializer, Gauges, Decimal, Shared contract: the Metrics Aggregator's snapshot output (MA-04). Built by…, Instance-wide state, not grouped by dimension — matching spec 004 §3 where…

### Community 212 - "demo_reload.py"
Cohesion: 0.24
Nodes (12): _show_alerts(), _banner(), _instructions(), main(), Path, Live walkthrough of SIGHUP rule reloading (`FR-RUL-008`/`009`). uv run python…, The watched file may be mid-edit or deliberately broken; a failed read here…, _run() (+4 more)

### Community 214 - "MultiLogMonitor"
Cohesion: 0.07
Nodes (32): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+24 more)

### Community 216 - "pytest"
Cohesion: 0.13
Nodes (14): classify_publish_response(), PublishOutcome, UBS-103: HTTP response -> publish action classification (spec 007 §2.1's…, DryRunPublishSink, PublishSink, Logger, Protocol, Log the intended publish, never open a socket. Use this while there's no real… (+6 more)

### Community 217 - "metrics_event.py"
Cohesion: 0.07
Nodes (40): _fixed_now(), main(), Minimal walkthrough of parser/metrics_event.py: the same three-order story as…, _step(), FixFields, Fixed-shape allowlisted field set. No attribute here may hold a raw, non-…, Remove raw tag 58 text from egress (FR-PRS-022)., _strip_sensitive_fields() (+32 more)

### Community 228 - "AlertRouter"
Cohesion: 0.15
Nodes (12): AlertRouter, AlertEvent, CounterRegistry, datetime, Logger, UBS-109/110: routes Rule Engine alerts to the Backend Publisher and the…, Run one path's enqueue so its failure stays on that path., Enqueues alerts for publication, rejecting any that would poison the batch they… (+4 more)

### Community 234 - "Rule Engine demo runbook"
Cohesion: 0.14
Nodes (13): 1. `make rules-test`, 2. `make rules-quickstart`, 3. `make rules-reload-demo`, Going deeper, if asked, If someone asks, Metric reference — what each rule reads, and where its number came from, Pre-flight, Rule Engine demo runbook (+5 more)

### Community 235 - ".__init__"
Cohesion: 0.20
Nodes (7): CounterRegistry, Logger, BackendUnreachableCallback, DropCallback, HeartbeatProvider, PublishConfig, PublishSink

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **180 isolated node(s):** `1. What the Health Reporter is for`, `2.1 One heartbeat tick, as a sequence`, `5.1 The window — `health/window.py``, `9. How to verify / demo`, `Also touched, and why` (+175 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1263 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **92 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `config/rules.yaml live rule set` to `MetricsAggregator ring buffer`, `Implementation Status live document`, `snapshot`, `Rule Engine`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `ParsedMessageEvent` connect `ParsedMessageEvent` to `test_MA_05_agent_counters.py`, `AggregatorConfig`, `LatencyCorrelator`, `test_MA_02_counters.py`, `snapshot`, `derive_counters`, `test_metrics_event.py`, `MetricsAggregator`, `Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)`, `services/demo_quickstart.py`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `Telemetry Schema — ParsedMessageEvent and the Metrics Aggregator` connect `Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)` to `ParsedMessageEvent`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 55 INFERRED edges - model-reasoned connections that need verification._