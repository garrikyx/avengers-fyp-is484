# Graph Report - avengers-fyp-is484  (2026-10-06)

## Corpus Check
- 295 files · ~160,003 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 12, .example 1, .typed 1)

## Summary
- 3737 nodes · 9270 edges · 235 communities (145 shown, 90 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 1641 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e70d4b7a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- telemetry_backend/main.py
- frame.py
- publish_fixtures.py
- RuleConfig
- make_snapshot
- Decimal
- HealthReporter
- test_FR_PIP_backpressure.py
- RetryPolicy
- LatencyCorrelator
- derive_counters
- UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth
- test_heartbeat.py
- LogMonitor
- PublishBuffer
- Confidence
- telemetry_agent_metrics_aggregator
- PublishResult
- MetricsAggregator
- SignatureMatcher
- Registry
- MetricStore
- Scaffold and Build Plan
- test_RE_session_integration.py
- AgentHeartbeat wire contract
- Telemetry Backend Service
- AgentHeartbeat
- HeartbeatMonitor
- parse_publish_config
- test_ING_004_008_ingest_guard.py
- DeliveryTracker
- load_health_config
- test_MA_05_agent_counters.py
- FakeClock
- LineClassification
- publishing/sink.py
- test_MA_03_correlation.py
- OffsetTracker
- config/rules.yaml live rule set
- test_health_monitor_e2e.py
- PipelineBridge
- MetricsAggregator ring buffer
- _Clock
- SourceMeta
- test_parse_errors.py
- SlidingWindowCounter
- 001 — Architecture
- CamelModel
- test_metrics_event.py
- callbacks/config.py
- callbacks/demo_quickstart.py
- telemetry_agent_parser_applog_parser
- ParseResult
- telemetry_agent_rules_engine
- test_STM_01_window_alignment.py
- datetime
- StreamProcessor
- _main_async
- from_alert_event
- CallbackDispatcher
- CounterRegistry
- Histogram
- test_queue_depth.py
- services/self_metrics.py
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
- metric_store.py
- json
- 009 — Non-Functional Requirements and Security
- test_STM_02_merge_semantics.py
- test_RE_06_reload.py
- ADR 0001: Telemetry Agent written in Go (Superseded)
- Telemetry System Documentation Index
- Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)
- AlertEvent
- pipeline_demo.py
- test_FR_CBK_005_signing.py
- mock_logger.py
- services/demo_quickstart.py
- test_RE_parse_error_integration.py
- End-to-End Acceptance Scenario (FR-TST-010)
- rules/demo_quickstart.py
- deps.py
- AgentRegistry
- demo_logs.txt FIX test corpus
- FIX Field Allowlist (FR-PRS-020/021, security-critical)
- publishing/__init__.py
- test_buffer_bytes_and_drops.py
- dispatcher.py
- StreamProcessorConfig
- test_STM_04_efficiency.py
- ParsedMessageEvent
- telemetry_agent_logs_multi_log_monitor
- test_FR_PRS_021_identifiers.py
- test_RE_01_fsm.py
- test_QRY_04_concurrency.py
- test_agent_registry.py
- Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)
- test_UBS_109_alert_router.py
- ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1
- health-reporter-overview.md
- load_backend_health_config
- test_FR_PRS_012_frame.py
- AggregatorConfig
- pytest
- telemetry_shared shared schema package
- parse_fix_timestamp
- fix/parser.py
- telemetry_backend/config.py
- test_reporter.py
- test_UBS_109_rule_engine_to_backend.py
- test_heartbeat_roundtrip.py
- test_RE_02_evaluators.py
- ingest_guard.py
- test_degraded_status_flows_into_heartbeat_payload
- Implementation Status live document
- demo_config.yaml (Magic parsing demo config)
- test_UBS_104_outage_isolation.py
- telemetry_agent_parser_applog_signatures
- Rule Engine
- test_log_monitor_status.py
- effective_reject_reason
- ADR 0004: Raw log content is never persisted or transmitted
- Monitor to parser bridge (bounded line queue + parser worker pool)
- 008 — Natural Language Query Layer (Copilot/Teams)
- NFR-REL-003: Backend Outage Must Not Affect Alerting
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
- IngestGuardConfig
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
- Snapshot
- avengers-fyp-is484
- agent callbacks/ module (callback delivery)
- agent health/ module (heartbeat and health)
- agent logs/ module (log monitoring, offsets, rotation - M1)
- agent rules/ module (Day-1 threshold alerts)
- AlertStore
- telemetry_agent_parser_fix_telemetry
- DryRunPublishSink
- telemetry_agent_parser_registry
- ._serialize_counters
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
- outcome.py
- protocol.py
- LogCaptureFixture
- parametrize
- telemetry_agent_logs_log_monitor
- telemetry_agent_logs_offset_tracker
- telemetry_agent_parser_fix_fields
- telemetry_agent_parser_fix_seq_tracker
- telemetry_agent_parser_fix_timestamps
- alert_router.py
- telemetry_shared_models_parsed_message
- Rule Engine demo runbook
- .__init__
- test_UBS45_integration.py

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
10. `create_app()` - 51 edges

## Surprising Connections (you probably didn't know these)
- `Going deeper, if asked` --references--> `FixParser`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/parser/fix/parser.py
- `4.5 Placeholder receiver — `scripts/heartbeat_receiver_stub.py`` --references--> `AgentHeartbeat`  [INFERRED]
  docs/plan/health-reporter-overview.md → packages/telemetry_shared/src/telemetry_shared/models/health.py
- `Placeholder receiver — `scripts/heartbeat_receiver_stub.py`` --references--> `AgentHeartbeat`  [INFERRED]
  docs/plan/ubs58-60-notes.md → packages/telemetry_shared/src/telemetry_shared/models/health.py
- `Not in this change` --references--> `LogMonitor`  [INFERRED]
  docs/plan/ubs69-85-96-notes.md → apps/agent/src/telemetry_agent/logs/log_monitor.py
- `UBS-5 coverage` --references--> `BackendPublisher`  [INFERRED]
  docs/plan/rule-engine-demo.md → apps/agent/src/telemetry_agent/publishing/publisher.py

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

## Communities (235 total, 90 thin omitted)

### Community 0 - "telemetry_backend/main.py"
Cohesion: 0.05
Nodes (56): AppDeps, AlertsQueryParams, _build_parser(), _counts(), create_app(), enqueue_or_full(), get_alert(), ingest_batch() (+48 more)

### Community 1 - "frame.py"
Cohesion: 0.12
Nodes (24): _check_body_length(), _check_checksum(), _contains_tag(), _delimiter_byte(), DelimiterMode, _find_begin_string(), FramedMessage, Framer (+16 more)

### Community 2 - "publish_fixtures.py"
Cohesion: 0.22
Nodes (11): inspect, NoReturn, make_alert(), make_event(), datetime, Shared test support for the publishing package: builds `Snapshot`,…, _NeverCalledSink, _publisher() (+3 more)

### Community 3 - "RuleConfig"
Cohesion: 0.10
Nodes (39): _AlertState, AlwaysActive, _decimal_or_none(), _matched_condition(), _matched_tier(), _metric_context(), datetime, Decimal (+31 more)

### Community 4 - "make_snapshot"
Cohesion: 0.15
Nodes (38): make_gauges(), make_indicator(), make_indicators(), make_snapshot(), datetime, Decimal, Shared test support for the rules package: builds `MetricsSnapshot` fixtures…, `empty=True` builds a snapshot with zero groups (nothing ingested this window… (+30 more)

### Community 5 - "Decimal"
Cohesion: 0.09
Nodes (37): load_rules(), load_rules_from_yaml(), _parse_duration_seconds(), Any, BaseModel, Exception, field_validator, Path (+29 more)

### Community 6 - "HealthReporter"
Cohesion: 0.07
Nodes (43): AgentStatus, HealthThresholds, FR-HLT-002 thresholds. Only the read-lag one has a producer on UBS-58; the rest…, HealthReporter, HealthSignals, is_parse_error(), datetime, Health Reporter: per-file read lag (UBS-30), status rollup and heartbeat… (+35 more)

### Community 7 - "test_FR_PIP_backpressure.py"
Cohesion: 0.22
Nodes (6): _meta(), Integration: block mode prevents drops under backpressure., Artificial CPU-bound parser for backpressure tests., SlowParser, test_block_mode_never_drops_under_backpressure(), flood()

### Community 8 - "RetryPolicy"
Cohesion: 0.13
Nodes (17): FR-CBK-004: exponential backoff with jitter for callback retries. Moved to…, UBS-104: exponential backoff with jitter, shared between the Callback…, Exponential backoff with jitter. Defaults match spec 010's example: base 1s,…, Delay before `attempt` (1-indexed: the Nth retry), in seconds. `retry_after`…, RetryPolicy, random, FR-CBK-004 exponential backoff with jitter tests., test_FR_CBK_004_delay_doubles_per_attempt_with_factor_2() (+9 more)

### Community 9 - "LatencyCorrelator"
Cohesion: 0.11
Nodes (16): CorrelatorStats, LatencyCorrelator, OrderContext, datetime, Decimal, timedelta, MA-03: order correlation and latency. Standalone producer into the shared…, Recorded so consumers of a snapshot know what a latency number means (MA-03 AC)… (+8 more)

### Community 10 - "derive_counters"
Cohesion: 0.11
Nodes (32): derive_counters(), _derive_execution_report_counters(), _derive_fill_split(), Decimal, MA-02: order / execution / reject counters and reject-reason normalisation.…, All four counter families in one event walk., fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not OrdStatus —…, Config-driven raw-reason -> canonical-label mapping. Backs MetricsAggregator's… (+24 more)

### Community 11 - "UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth"
Cohesion: 0.13
Nodes (12): Register (or remove) the Publisher's queue-depth callback., Register (or remove) the Publisher's buffer-bytes callback…, BufferBytesProvider, 6. UBS-60 — publish queue depth, Also touched, and why, How to see it, Missing downstream / upstream (what this branch cannot prove), Placeholder receiver — `scripts/heartbeat_receiver_stub.py` (+4 more)

### Community 12 - "test_heartbeat.py"
Cohesion: 0.10
Nodes (23): HeartbeatEmitter, Event, Tick every `interval_seconds` until `stop` is set. First tick is immediate so a…, Collect, FakeClock, datetime, LogCaptureFixture, UBS-58 / FR-HLT-001: heartbeat emitter and wire format. (+15 more)

### Community 13 - "LogMonitor"
Cohesion: 0.07
Nodes (26): Harvester, LogMonitor, datetime, Path, Spawns a new Harvester bound to the active inode., Open a rotated sibling from before this monitor started. The registry is keyed…, One complete log line with stable byte identity for idempotent ingest., Find retained rotations that were created while the agent was down. This… (+18 more)

### Community 14 - "PublishBuffer"
Cohesion: 0.10
Nodes (24): PublishBuffer, datetime, Put previously-`take`n items back at the front, in original order -- they are…, Bounded FIFO of `PendingItem`s, drop-oldest on overflow, bounded by both…, Drop items older than `max_age_seconds`. The deque is strictly insertion-…, _item(), FR-PUB-004: the byte-and-age-bounded `PublishBuffer` (UBS-104's replacement for…, Drop-oldest still holds after a requeue: the items just put back are the oldest… (+16 more)

### Community 15 - "Confidence"
Cohesion: 0.08
Nodes (26): Confidence, Parser, Enum, Protocol, str, How strongly a parser claims an input line., FR-PRS-030: pluggable parser interface., Configuration name, e.g. 'fix' or 'applog'. (+18 more)

### Community 16 - "telemetry_agent_metrics_aggregator"
Cohesion: 0.10
Nodes (26): UBS-74: bridges the agent's own since-startup counters into the windowed…, main(), ingest(), Minimal walkthrough of the Metrics Aggregator (MA-01–04). uv run python -m…, _step(), _build_gauges(), datetime, MA-04: calculated indicators and snapshot output. Wraps the already-tested… (+18 more)

### Community 17 - "PublishResult"
Cohesion: 0.16
Nodes (29): PublishAction, StrEnum, PublishResult, Outcome of one publish attempt. `status_code` is `None` on a transport error…, make_snapshot(), _FakeSink, _publisher(), LogCaptureFixture (+21 more)

### Community 18 - "MetricsAggregator"
Cohesion: 0.12
Nodes (17): _Bucket, default_resolve_reject_reason(), _dimension_value(), MetricRow, MetricsAggregator, datetime, Decimal, Shared metrics store (spec 004 §3): a time-bucketed ring buffer holding both… (+9 more)

### Community 19 - "SignatureMatcher"
Cohesion: 0.20
Nodes (12): compile_signature_rules(), First-match-wins signature rules with dynamic label templates., resolve_label_template(), _sanitize_capture(), SignatureMatcher, SignatureRule, Applog signature template tests., test_cardinality_overflow_to_other() (+4 more)

### Community 20 - "Registry"
Cohesion: 0.09
Nodes (21): Selects the first parser in a configured chain with Confidence.HIGH., Return unknown parser names in chain., Registry, PipelineConfig, Pipeline bridge sizing (spec 010 §pipeline, FR-PIP-002–004)., MonitorPipelineAdapter, monitors_by_resolved_path(), Yield parsed events until max_lines or idle_rounds with no new data. (+13 more)

### Community 21 - "MetricStore"
Cohesion: 0.13
Nodes (16): _CanonicalBucket, MetricStore, datetime, Lock, In-memory, per-instance ring buffer of canonical buckets (`FR-QRY-001`, scoped…, `None` if the instance has never been touched — but also, safely, if a…, Evict buckets that have aged out of retention within *one* instance's ring —…, Evict stale buckets across every instance's ring and check memory pressure. For… (+8 more)

### Community 22 - "Scaffold and Build Plan"
Cohesion: 0.07
Nodes (36): Open Questions and Decisions Required, Callback Dispatcher, Backend-to-Agent Config Push Deferred to Day-2, Not Built Speculatively From the Diagram, Integration Service (Copilot/Teams Connector), Q-1 — Expected FIX Throughput and Peak Log Volume, Q-10 — Who Receives Alerts Besides Magic, Q-11 — Scope of Callback Audit Under Integration Service, Q-12 — Config/Control Push From Backend to Agent (+28 more)

### Community 23 - "test_RE_session_integration.py"
Cohesion: 0.05
Nodes (72): Sessions that have *just* crossed the threshold, each latched so one silence is…, Stop tracking a session. Called on `Logout`, and the reason this exists: a…, Introspection for demos/debug; not used by the detection path., Flags FIX sessions quiet for longer than `timeout_seconds`. Stateful across…, Internal tracking key, identical in format to `SeqTracker.session_key`.…, Record that a session was heard from at `at`. Any message counts, not just…, SessionHeartbeatTracker, _SessionState (+64 more)

### Community 24 - "AgentHeartbeat wire contract"
Cohesion: 0.10
Nodes (31): health: threshold config block, heartbeat: interval config, AgentHeartbeat wire contract, AgentStatus literal vocabulary, BufferingHeartbeatSink, HealthReporter.build_heartbeat(), derive_status() status rollup, FileReadHealth per-file entry (+23 more)

### Community 25 - "Telemetry Backend Service"
Cohesion: 0.10
Nodes (34): Key Flow 2: Alert & Callback Flow, Alert & Event Store (Alerts, Rule Matches, Delivery Status), Callback Dispatcher (Send Callbacks to Magic, Retry/Backoff, Delivery Tracking), Copilot, Dashboards / Operational Tools, Alert Example: Execution Failures, Health Reporter (Agent Heartbeat, Parse Errors, Queue Depth, Connectivity Status), Alert Example: High Reject Rate (+26 more)

### Community 26 - "AgentHeartbeat"
Cohesion: 0.09
Nodes (27): heartbeat_json(), HttpHeartbeatSink, datetime, `POST /telemetry/heartbeat` (spec 007 §2.3) with the stdlib only. Placeholder…, Build and send one heartbeat. Sink failures are counted, not raised: a dead…, Wire encoding, camelCase per spec 004 §6. `wire="ingestion"` flattens to…, Flatten our heartbeat into UBS-66's ingestion contract. `default_instance_id`…, to_ingestion_heartbeat() (+19 more)

### Community 27 - "HeartbeatMonitor"
Cohesion: 0.14
Nodes (12): AlertingConfig, Backend-owned alerting rules (spec 005 `FR-RUL-030`)., backend_alert_id(), HeartbeatMonitor, datetime, Resolve a backend alert immediately when a fresh heartbeat arrives., Periodically evaluates agent heartbeat staleness., _heartbeat() (+4 more)

### Community 28 - "parse_publish_config"
Cohesion: 0.12
Nodes (31): load_publish_config(), load_publish_token(), parse_publish_config(), PublishConfig, PublishConfigError, _PublishYaml, Any, BaseModel (+23 more)

### Community 29 - "test_ING_004_008_ingest_guard.py"
Cohesion: 0.19
Nodes (18): Accept, Duplicate, RateLimited, FakeClock, guard(), datetime, UBS-85: IngestGuard dedupe (FR-ING-004) and rate limiting (FR-ING-008)., A batch refused downstream (503 queue_full) must be accepted on retry. (+10 more)

### Community 30 - "DeliveryTracker"
Cohesion: 0.11
Nodes (26): DeliveryRecord, DeliveryStatus, DeliveryTracker, datetime, StrEnum, UBS-34: per-alert-occurrence callback delivery status, timestamped at each…, UBS-34 AC: every dispatched callback has exactly one of these five states at…, One alert's current delivery state. `attempt_count` and `last_error` are… (+18 more)

### Community 31 - "load_health_config"
Cohesion: 0.10
Nodes (32): _AgentConfigYaml, _AgentYaml, _drop_none(), HealthConfigError, _HealthYaml, HeartbeatConfig, _HeartbeatYaml, load_health_config() (+24 more)

### Community 32 - "test_MA_05_agent_counters.py"
Cohesion: 0.14
Nodes (25): AgentCounterSampler, datetime, Turns monotonic since-startup counters into per-bucket deltas. Stateful across…, Ingest the increase in each tracked counter since the last call. The first call…, _aggregator(), Decimal, UBS-74: `MetricsAggregator.ingest_agent_counters` and the `AgentCounterSampler`…, A restarted dispatcher's registry drops back to 0. That is a new baseline, not… (+17 more)

### Community 33 - "FakeClock"
Cohesion: 0.15
Nodes (32): FakeClock, hand_labelled_events(), Shared test support for the metrics package: a hand-labelled synthetic FIX-…, A `Clock` (`() -> float`) that only advances when told to — lets a test assert…, make_event(), minimal_aggregator(), Decimal, test_10k_events_in_60s_window_returns_correct_count() (+24 more)

### Community 34 - "LineClassification"
Cohesion: 0.12
Nodes (25): _explain_classification(), Pattern, classify_line(), compile_app_log_patterns(), _looks_like_fix(), Pattern, Line classification (FR-PRS-010, FR-PRS-011)., Classify a log line before parsing (FR-PRS-010). Order: fix → app_log →… (+17 more)

### Community 35 - "publishing/sink.py"
Cohesion: 0.11
Nodes (23): HttpsPublishSink, _maybe_gzip(), _parse_retry_after(), AsyncBaseTransport, UBS-103: the swappable Publisher transport boundary (spec 002 §6). Mirrors…, `FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the compressed…, `FR-PUB-001`/`002`: HTTPS POST with a bearer token, gzip above…, ASGITransport (+15 more)

### Community 36 - "test_MA_03_correlation.py"
Cohesion: 0.25
Nodes (23): ack(), build(), cancel_confirmed(), cancel_rejected(), cancel_replace_request(), cancel_request(), new_order(), datetime (+15 more)

### Community 37 - "OffsetTracker"
Cohesion: 0.10
Nodes (23): OffsetTracker, Path, Registrar subsystem for tracking offsets of log files. Stores file offsets…, Generates internal state ID format (e.g., 'native::16777232-1048201')., Loads state registry into memory Supports Filebeat's native JSON list array…, Retrieves the last known offset for a given (device, inode) pair., Persist committed offset after parse+ingest (FR-PIP-006)., Deprecated alias for commit_offset. (+15 more)

### Community 38 - "config/rules.yaml live rule set"
Cohesion: 0.11
Nodes (28): Agent processing pipeline (monitor to health reporter), publish: Backend Publisher config block, BackendUnreachable rule, CancelRejectSpike rule, ClockSkew rule, FixSessionDown rule, HighRejectRate rule, NoExecutions rule (+20 more)

### Community 39 - "test_health_monitor_e2e.py"
Cohesion: 0.10
Nodes (19): MonkeyPatch, committed_offsets(), FakeClock, fix_lines(), datetime, FastAPI, fixture, Path (+11 more)

### Community 40 - "PipelineBridge"
Cohesion: 0.04
Nodes (43): _build_bridge(), OverflowPolicy, DemoMetricsSink, QueueSnapshot, PipelineCommitter, Drain parsed events, dedupe, ingest, and commit offsets (FR-PIP-006/007)., Consumes ParsedEvent objects and commits file offsets after ingest., LinePosition (+35 more)

### Community 41 - "MetricsAggregator ring buffer"
Cohesion: 0.12
Nodes (21): AckLatencyBreach rule, Parse error rate signal (UBS-59), SlidingWindowCounter, MetricsAggregator.snapshot(window, group_by), Cardinality caps and __other__ folding, derive_counters() message separation, BASE_DIMS / REJECT_DIMS declared dimension sets, Instance-wide gauges (pendingOrders, secondsSinceLastEvent) (+13 more)

### Community 43 - "SourceMeta"
Cohesion: 0.08
Nodes (33): _poll_forever(), Drain each tailed file every 250ms so read lag / offsets stay honest, and feed…, _fixed_now(), main(), Minimal walkthrough of parser/metrics_event.py: the same three-order story as…, _step(), FixParser, derive_parser_counters() (+25 more)

### Community 44 - "test_parse_errors.py"
Cohesion: 0.16
Nodes (18): bad(), FakeClock, make(), ok(), datetime, UBS-59: parse-error rolling count and rate in the Health Reporter., test_clean_lines_give_zero_errors_and_zero_rate(), test_count_decays_as_window_slides() (+10 more)

### Community 45 - "SlidingWindowCounter"
Cohesion: 0.14
Nodes (20): datetime, Bounded sliding-window counter (UBS-59) for the heartbeat's `...Last5Min`…, Count `n` events at `now`. A late timestamp still inside the window lands in…, Events inside the window ending at `now`; decays as the window slides., Live buckets (never exceeds `capacity`)., SlidingWindowCounter, telemetry_agent_health_window, at() (+12 more)

### Community 46 - "001 — Architecture"
Cohesion: 0.10
Nodes (27): Problem P-1: Limited visibility into live trading activity and health, Requirement ID Scheme (FR-<AREA>-<NNN>), Alert Store (component), Backend Publisher (component), Callback Dispatcher (component), Consistent-Hash Routing on instanceId, 001 — Architecture, Failure Degradation Order (queries → freshness → callbacks → alerting) (+19 more)

### Community 47 - "CamelModel"
Cohesion: 0.09
Nodes (37): Wire compatibility with the Ingestion Service's heartbeat contract (UBS-66).…, AlertCounts, AlertDelivery, AlertDetailResponse, AlertsListResponse, AlertTransition, Alert query response models (spec 007 §4, `FR-QRY-016`)., Callback delivery status surfaced in alert query results. (+29 more)

### Community 48 - "test_metrics_event.py"
Cohesion: 0.09
Nodes (40): build_parsed_message_event(), Construct the Metrics Aggregator's event from one framed FIX line. Returns None…, _meta(), _parse(), _parser_counters(), datetime, Decimal, parametrize (+32 more)

### Community 49 - "callbacks/config.py"
Cohesion: 0.12
Nodes (25): CallbackConfigError, CallbacksConfig, _CallbacksYaml, load_callbacks_config(), parse_callbacks_config(), Any, BaseModel, Exception (+17 more)

### Community 50 - "callbacks/demo_quickstart.py"
Cohesion: 0.11
Nodes (19): main(), _make_alert(), _print_counters(), Minimal walkthrough of the Callback Dispatcher (UBS-32/33). uv run python -m…, Stands in for Magic: keys its canned response off the alert ID inside the…, _run_one(), _ScriptedSink, _step() (+11 more)

### Community 52 - "ParseResult"
Cohesion: 0.12
Nodes (39): main(), Telemetry Agent entrypoint., extract_log_level(), Extract [N/E/W/F/I] level from Magic-style log lines., _corpus_files(), _fields_dict(), _format_line_result(), _load_config() (+31 more)

### Community 53 - "telemetry_agent_rules_engine"
Cohesion: 0.31
Nodes (8): telemetry_agent_rules_engine, _counter_rule(), RE-02: suppression and safety (spec 005 §4) — maxActiveAlerts/AlertStorm,…, test_dependent_suppression_when_no_log_activity_is_firing(), test_max_active_alerts_emits_one_alertstorm_and_suppresses_further(), test_schedule_inactive_skips_rule_entirely(), test_silence_suppresses_notification_but_still_tracks_state(), test_storm_clears_once_under_cap_and_the_suppressed_rule_fires()

### Community 54 - "test_STM_01_window_alignment.py"
Cohesion: 0.13
Nodes (20): datetime, FR-STM-001, FR-ING-005, FR-STM-005: canonical window alignment, rejection of…, FR-ING-005: out-of-order snapshots for the same bucket must still merge to the…, A snapshot the StreamProcessor accepts as within maxBucketAge must still be…, A cap below 1 would drop every series as over-cap while `merge()` still marks…, FR-QRY-003: the shed threshold must be strictly above the warn threshold, or…, FR-MET-028 + FR-ING-005 together: gauges are last-write-wins, but this stage…, FR-STM-005: even if something calls MetricStore.merge() directly with a… (+12 more)

### Community 55 - "datetime"
Cohesion: 0.10
Nodes (27): FR-CBK-007: bounded pending queue, drop-oldest on overflow., Live heartbeat demo (UBS-58): tail files, emit heartbeats on an interval. uv…, Heartbeat emitter (UBS-58, FR-HLT-001). Ticks on a fixed interval regardless of…, Log monitoring, rotation and truncation handling., datetime, Multi-file polling and lifecycle management for the Log Monitor., Return offset and read-lag state for every configured file., FileReadStatus (+19 more)

### Community 56 - "StreamProcessor"
Cohesion: 0.10
Nodes (23): align_to_canonical(), datetime, Stream Processor (spec 006 §3): window alignment and the ingest-side half of…, FR-STM-001: floor `bucket_start_utc` onto the canonical grid., Aligns, age-checks, and merges snapshots into a `MetricStore`. Non-blocking and…, Read-only configuration shared with the ingestion boundary., FR-QRY-005: `False` ("warming") until `warmupWindow` has elapsed since this…, SnapshotOutcome (+15 more)

### Community 57 - "_main_async"
Cohesion: 0.17
Nodes (12): _build_parser(), _detect_session_timeouts(), main(), _main_async(), _make_sink(), ArgumentParser, Event, HeartbeatSink (+4 more)

### Community 58 - "from_alert_event"
Cohesion: 0.20
Nodes (15): CallbackAlertPayload, from_alert_event(), datetime, FR-CBK-002/003: the callback JSON payload (spec 005 §3.3)., Matches spec 005 §3.3 exactly. `summary` and `runbook_url` aren't produced…, make_alert_event(), Shared test support for the callbacks package: builds `AlertEvent` fixtures…, FR-CBK-001/002/003 callback payload shape tests. (+7 more)

### Community 59 - "CallbackDispatcher"
Cohesion: 0.14
Nodes (19): CallbackDispatcher, Spawns `maxInflight` workers pulling from the queue. Runs until cancelled by…, Signs and sends `alert`, retrying transient failures with backoff (`FR-…, HttpsCallbackSink, AsyncBaseTransport, `FR-CBK-001`: HTTPS POST to the configured Magic endpoint. Rejects plain HTTP…, `count` alerts to a Magic endpoint that answers 400 every time. A permanent…, _run_dispatcher_against_a_broken_magic() (+11 more)

### Community 60 - "CounterRegistry"
Cohesion: 0.15
Nodes (9): Lightweight in-process counters for callback self-observability (`FR-CBK-009`):…, CounterRegistry, UBS-104: lightweight in-process counters, shared between the Callback…, Plain dict of named counters behind a lock -- increments happen from both async…, UBS-104: `CounterRegistry` at its canonical `common/` location (moved from…, test_callbacks_shim_is_the_same_class(), test_increment_starts_at_zero_and_accumulates(), test_independent_counters_do_not_interfere() (+1 more)

### Community 61 - "Histogram"
Cohesion: 0.10
Nodes (27): Histogram, Decimal, Fixed-boundary latency histogram (spec 004 FR-MET-025/026, FR-QRY-012). Shared…, Constant memory per series regardless of sample count (MA-03 AC)., Bucket-wise addition (FR-ING-005, FR-STM-004) — used both when an agent's…, Interpolated, approximate (FR-QRY-012). None below min_sample_size (FR-QRY-007)…, build_latency_summary(), Histogram-to-API summary (spec 004 §4.4, FR-QRY-012, FR-STM-004). Shared by the… (+19 more)

### Community 62 - "test_queue_depth.py"
Cohesion: 0.12
Nodes (21): BufferingHeartbeatSink, HeartbeatSink, Bounded retry buffer in front of another sink (UBS-60 demo stand-in). Not the…, FakeQueue, Flaky, make(), UBS-60: publish queue depth in the heartbeat, watermark rules, trend., test_at_critical_watermark_is_unhealthy() (+13 more)

### Community 63 - "services/self_metrics.py"
Cohesion: 0.07
Nodes (33): _BoundSourcesCollector, _counter(), _gauge(), datetime, Backend self-metrics (UBS-96; FR-HLT-010, spec 006 s7). `SelfMetrics` owns a…, Prometheus exposition for the backend's own internals (FR-HLT-010)., Recompute per-agent gauges from the registry. Called per scrape so the exporter…, (body, content-type) for `GET /metrics`. (+25 more)

### Community 64 - "DropOldestQueue"
Cohesion: 0.12
Nodes (12): Logger, DropOldestQueue, T, Wraps `asyncio.Queue` with a bounded size and drop-oldest overflow policy (`FR-…, Enqueue `item`, non-blocking. Returns True if an existing item was dropped to…, CallbackSink, Protocol, The transport boundary. `HttpsCallbackSink` is the Day-1 default;… (+4 more)

### Community 65 - "SeqTracker"
Cohesion: 0.23
Nodes (8): timedelta, Per-session MsgSeqNum tracking., SeqTracker, SeqGapEvent, FR-PRS-027 sequence gap tests., test_FR_PRS_027_detects_gap(), test_FR_PRS_027_detects_regression(), test_FR_PRS_027_logon_resets_without_gap()

### Community 66 - "enrich.py"
Cohesion: 0.27
Nodes (15): build_fix_telemetry(), timedelta, normalize_enum(), normalize_exec_type(), normalize_msg_type(), normalize_ord_rej_reason(), normalize_ord_status(), normalize_ord_type() (+7 more)

### Community 67 - "BackendPublisher"
Cohesion: 0.09
Nodes (22): make_pending_item(), Measured once at insert and cached on the `PendingItem` -- re-measuring on…, _size_of(), _drain(), main(), _make_snapshot(), _print_state(), datetime (+14 more)

### Community 68 - "_Demo"
Cohesion: 0.08
Nodes (15): _Demo, AlertEvent, Holds the one parser/aggregator/engine trio the whole story runs on, so each…, Pretend `by` messages were lost in transit., ExecType/OrdStatus 8 = Rejected, OrdRejReason 3 = ExchangeClosed., 35=3, a session-level Reject — a FIX plumbing problem rather than a trading…, 35=9, a rejected cancel/replace — counted as `cancel_rejects`, kept apart from…, An ack whose SendingTime is `delay_ms` after its order. Latency is measured… (+7 more)

### Community 69 - "Telemetry Agent (architecture constraint)"
Cohesion: 0.13
Nodes (20): Day-1 deterministic rules vs Day-2 anomaly detection, Day-2 PostgreSQL historical telemetry, Magic simulator for development, Do not overengineer (development principle), Never persist raw logs or raw FIX payloads, Redis as Day-1 volatile state store, Repository/service abstraction over stores, Microsoft Teams as the only user interface (+12 more)

### Community 70 - "AppDeps"
Cohesion: 0.21
Nodes (23): AppDeps, env(), FakeClock, heartbeat(), post(), datetime, fixture, TestClient (+15 more)

### Community 71 - "BoundedQueue"
Cohesion: 0.09
Nodes (13): BoundedQueue, OverflowPolicy, T, Bounded queue with configurable overflow: block (default) or drop_oldest., Enqueue. Blocks when full if policy is block; returns False on timeout., Non-blocking put; drop_oldest only. Use put() for block mode., Block until an item is available or timeout elapses., OverflowPolicy (+5 more)

### Community 72 - "test_internal_api.py"
Cohesion: 0.16
Nodes (21): env(), FakeClock, heartbeat(), merge_snapshot(), post_heartbeat(), datetime, fixture, TestClient (+13 more)

### Community 73 - "test_RE_publish_integration.py"
Cohesion: 0.20
Nodes (22): _aggregator(), _engine(), _fail_n_times(), _publisher(), UBS-75 integration: BackendPublisher -> consecutive_publish_failures gauge ->…, The whole reason this is a gauge: recovery is observable. A windowed failure…, FR-MET-031. An agent with no publisher must not look like an agent that is…, Regression guard on spec 005 §1.2's withdrawn approximation.… (+14 more)

### Community 74 - "metric_store.py"
Cohesion: 0.19
Nodes (13): _dim_key(), Cross-agent Metric Store (spec 006 §4; FR-STM-002/003/004/006). A per-instance…, _SeriesContribution, DimKey, datetime, FR-STM-006: an agent's post-restart cold-start state is preserved through the…, warmingUp flags incomplete data for the caller to exclude; it does not mean the…, _snapshot() (+5 more)

### Community 75 - "json"
Cohesion: 0.14
Nodes (14): BaseHTTPRequestHandler, http, http_server, json, _AgentRecord, main(), _make_handler(), do_GET() (+6 more)

### Community 76 - "009 — Non-Functional Requirements and Security"
Cohesion: 0.12
Nodes (18): Resource Discipline (§9), Compliance and Operability Constraints (§7), Configurability NFRs (§5), 009 — Non-Functional Requirements and Security, NFR-CFG-004: Documented Config Defaults Must Match Code, NFR-PERF-003: Agent RSS < 150MB, shed load rather than exceed, NFR-SCA-001: Agent Independence/Statelessness, NFR-SEC-004: Secrets from Environment Only (+10 more)

### Community 77 - "test_STM_02_merge_semantics.py"
Cohesion: 0.19
Nodes (17): HistogramPayload, Wire shape of one histogram (`FR-MET-025`/`FR-MET-026`): fixed boundaries…, Reconstruct a mergeable `Histogram`, keyed on the canonical boundary set rather…, _histogram_payload(), FR-STM-002/003/004: counters merge by summation; ratios are recomputed from…, Two agents of unequal volume (FR-STM-003's required test shape): agent A:…, A retried publish that misses batchId-level dedupe (a different ticket's…, _read_one_group() (+9 more)

### Community 78 - "test_RE_06_reload.py"
Cohesion: 0.17
Nodes (20): datetime, Logger, Wires `config/rules.yaml` reloading to SIGHUP for a live `RuleEngine`.…, SighupRuleReloader, _engine(), _fire(), datetime, LogCaptureFixture (+12 more)

### Community 79 - "ADR 0001: Telemetry Agent written in Go (Superseded)"
Cohesion: 0.16
Nodes (18): C++ candidate (rejected: worst-case failure modes), ADR 0001: Telemetry Agent written in Go (Superseded), .NET candidate (rejected for Day-1: deployment size), Go 1.23+ candidate (chosen: static binary, concurrency), Python candidate (rejected: runtime + GIL + memory profile), Rust candidate (rejected: slower build-out), ADR 0002: Telemetry stack is Python 3.12 + FastAPI, .NET alternative (rejected) (+10 more)

### Community 80 - "Telemetry System Documentation Index"
Cohesion: 0.11
Nodes (18): architecture.md, assets/architecture-overview.png diagram, Telemetry System Documentation Index, plan/implementation-status.md, plan/open-questions.md, plan/scaffold.md, Spec 000: Overview, Spec 001: Architecture (+10 more)

### Community 81 - "Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing)"
Cohesion: 0.12
Nodes (18): ADR 0004: No-Raw-Persistence Design, Problem P-2: Rejects/failures/latency spikes slow to identify, Problem P-5: Raw trading logs are sensitive, cannot be centralised, Parser Engine (component), Log Ingestion and Metric Publication Sequence (§8.1), Parser Engine Agent-Level Contract (FR-PRS-001–003), Pipeline Bridge Requirements (FR-PIP-001–007, asymmetric queue sizing), Scaffold Document (plan/scaffold.md) (+10 more)

### Community 82 - "AlertEvent"
Cohesion: 0.19
Nodes (18): Sync, non-blocking — the entry point a future wiring step calls from the same…, AlertEvent, One alert transition or re-notification (`FR-RUL-015`). `severity` reflects the…, _aggregator(), _alert(), _dispatch(), _drain(), _fire() (+10 more)

### Community 83 - "pipeline_demo.py"
Cohesion: 0.14
Nodes (22): _build_registry(), _load_config(), main(), _print_stage(), Path, End-to-end demo: LogMonitor → queue → parse → output → commit., Hands back the `FixParser` alongside the registry it went into. Callers need…, run_happy_path() (+14 more)

### Community 84 - "test_FR_CBK_005_signing.py"
Cohesion: 0.18
Nodes (15): load_callback_secret(), FR-CBK-005: request signing so Magic can verify a callback originated from this…, `v1=<hex HMAC-SHA256(timestamp + "." + body)>` (`FR-CBK-005`)., Read the callback-signing secret from the environment (`NFR-SEC-004`). Raises…, sign(), hashlib, FR-CBK-005 request-signing tests., test_FR_CBK_005_different_body_produces_different_signature() (+7 more)

### Community 85 - "mock_logger.py"
Cohesion: 0.21
Nodes (12): main(), get_timestamps(), Path, Rotate with numbered retained archives, like ``logrotate``.…, rotate_if_needed(), run_harness(), argparse, sys (+4 more)

### Community 86 - "services/demo_quickstart.py"
Cohesion: 0.27
Nodes (15): _accept_and_fill(), _bridge_to_snapshot(), main(), _new_aggregator(), ingest(), datetime, Minimal walkthrough of the Stream Processor & Metric Store — built on the exact…, The exact 3-order story from the Metrics Aggregator quickstart: two accepted… (+7 more)

### Community 87 - "test_RE_parse_error_integration.py"
Cohesion: 0.31
Nodes (12): _fire(), _ingest(), _rate(), UBS-18 integration: raw log bytes -> FixParser -> derive_parser_counters ->…, Needs a failure mode that errors once per line — see `_NO_MSG_TYPE`. The…, Documents the asymptote above as behaviour, not accident: three of every four…, `min_samples` is 20 for this rule. Under that, a single bad line in a handful…, test_a_clean_log_never_fires() (+4 more)

### Community 88 - "End-to-End Acceptance Scenario (FR-TST-010)"
Cohesion: 0.12
Nodes (17): Day-1 Acceptance Definition (5 measurable criteria against a synthetic Magic stream), Open Questions Document (plan/open-questions.md), Log Monitor Requirements (FR-LOG-001–024, identity/digest checkpointing), Offset Checkpointing (state.json), Agent Restart Sequence (§8.2), Text Field Normalisation (FR-PRS-022), Error Response Shape (§7), NL Evaluation Requirements (FR-NLQ-025) (+9 more)

### Community 89 - "rules/demo_quickstart.py"
Cohesion: 0.08
Nodes (27): _alert_storm_act(), _alerts_to_backend_act(), _backend_unreachable_act(), attempt(), _dedup_act(), _FlakyBackendSink, _heartbeat_timeout_act(), main() (+19 more)

### Community 90 - "deps.py"
Cohesion: 0.12
Nodes (22): healthz(), metrics(), get, Response, Operator probes (UBS-96; FR-HLT-010, FR-HLT-012; spec 007 s5.3). Mounted on the…, Liveness only: the process is up and serving. No dependency checks, so a broken…, Readiness incl. warm-up (FR-QRY-005), from the same…, readyz() (+14 more)

### Community 91 - "AgentRegistry"
Cohesion: 0.09
Nodes (24): get_agent(), list_agents(), datetime, get, Agent health read side (UBS-69; spec 007 s5.1, s5.2; FR-ING-010, FR-HLT-011).…, _summary(), AgentRecord, AgentRegistry (+16 more)

### Community 92 - "demo_logs.txt FIX test corpus"
Cohesion: 0.13
Nodes (16): app_log_sample.txt scenario (non-FIX app log line), bad_timestamp.txt scenario (malformed FIX tag 52 timestamp), demo_logs.txt FIX test corpus, delimiter_auto.txt scenario (delimiter auto-detection), garbage.txt scenario (non-FIX / malformed input), log_prefix.txt scenario (FIX message with app-log prefix), logon_reset.txt scenario (FIX Logon/SequenceReset messages), pipe_delimited.txt scenario (pipe-delimited NewOrderSingle) (+8 more)

### Community 93 - "FIX Field Allowlist (FR-PRS-020/021, security-critical)"
Cohesion: 0.16
Nodes (16): FIX Field Allowlist (FR-PRS-020/021, security-critical), Known FIX Value Sets and Reject Reason Precedence (FR-PRS-023/024), Query Engine Requirements (FR-QRY-006–014), Query Metrics Endpoint (POST /telemetry/query/metrics), NL Design Stance: No Dynamic Evaluation of Model Output (FR-NLQ-001/002), NL Interpretation Pipeline (FR-NLQ-005–009), NFR-SEC-001: No Raw Log Persistence/Transmission, NFR-SEC-002: Allowlist Enforcement (sentinel corpus test) (+8 more)

### Community 94 - "publishing/__init__.py"
Cohesion: 0.19
Nodes (14): BatchSequencer, build_batch(), datetime, FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus an…, `FR-PUB-003`: a monotonically increasing `batchSeq` per agent, and a stable…, `FR-PUB-001`: one batch containing whatever snapshots/events/alerts were pulled…, PendingItem, FR-PUB-004: a pending-item buffer bounded by both total bytes and maximum age,… (+6 more)

### Community 95 - "test_buffer_bytes_and_drops.py"
Cohesion: 0.16
Nodes (12): FakeClock, datetime, UBS-104: publish buffer bytes and dropped-event rate in the heartbeat. Mirrors…, A supervisor wiring the Publisher in calls this once at startup so a healthy…, test_buffer_bytes_is_none_without_a_provider(), test_buffer_bytes_is_read_fresh_on_every_snapshot(), test_buffer_bytes_provider_can_be_registered_and_removed(), test_dropped_events_accumulate_within_the_window() (+4 more)

### Community 96 - "dispatcher.py"
Cohesion: 0.24
Nodes (13): UBS-32/33/34: dispatches Rule Engine alerts to Magic's callback endpoint,…, classify_http_status(), StrEnum, FR-CBK-006: HTTP outcome -> retry decision classification., `FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent failure., RetryDecision, parametrize, FR-CBK-006 HTTP status -> retry decision classification tests. (+5 more)

### Community 97 - "StreamProcessorConfig"
Cohesion: 0.17
Nodes (16): StreamProcessorConfig, datetime, FR-QRY-002/003: memory is bounded, estimated, exposed as a gauge, and the store…, Nothing in this repo calls `tick()` on a schedule yet — the real write path…, The write-path check must not cost an `estimated_memory_bytes()` scan on every…, `_get_or_create_instance` eagerly allocates a full-`capacity` ring of real…, At `capacity < 2`, `capacity // 2` is 0 — `_shed_oldest_tier` must still keep…, _snapshot() (+8 more)

### Community 98 - "test_STM_04_efficiency.py"
Cohesion: 0.19
Nodes (10): _CountingRing, datetime, Regression tests for two efficiency fixes: `merge()` must not sweep every…, Wraps a ring's buckets without a `list`'s own `__iter__` — a plain `for x in…, The old `tick()` swept every instance's ring on every merge — O(instances x…, A query over one 10s bucket on a 6h-capacity (2160-bucket) ring must not touch…, _snapshot(), test_merge_evicts_only_the_ring_it_writes_to() (+2 more)

### Community 99 - "ParsedMessageEvent"
Cohesion: 0.12
Nodes (29): CancelRejectEvent, CancelReplaceEvent, CancelRequestEvent, EVENT_CLASS_BY_MSG_TYPE (dispatch table), ExecutionReportEvent, NewOrderEvent, ParsedMessageEvent, BaseModel (+21 more)

### Community 101 - "test_FR_PRS_021_identifiers.py"
Cohesion: 0.13
Nodes (22): extract_allowlisted_fields(), _hash_or_none(), Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004). The tag…, FR-PRS-020: extract only the tags in the compile-time allowlist above.…, hash_identifier(), Identifier hashing (FR-PRS-021)., HMAC-SHA256 of `raw` keyed with `key`, truncated to 16 hex chars., hmac (+14 more)

### Community 102 - "test_RE_01_fsm.py"
Cohesion: 0.35
Nodes (13): _engine(), datetime, RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from any…, _snapshot(), test_alert_id_rotates_after_a_fresh_occurrence(), test_condition_true_again_while_resolving_returns_to_firing_no_notification(), test_condition_true_enters_pending_with_no_event(), test_firing_to_resolving_to_resolved() (+5 more)

### Community 103 - "test_QRY_04_concurrency.py"
Cohesion: 0.13
Nodes (18): FR-QRY-004: the store MUST be safe under concurrent read/write via a per-…, A per-instance lock must still serialise writes *within* one instance — safety…, `dropped_after_retention_total` is a single store-wide counter incremented from…, `StreamProcessor.dropped_buckets_total` is incremented outside any per-instance…, `_get_or_create_instance` sets `_rings[instance_id]` before…, `_shed_oldest_tier` iterates `_rings.items()` and indexed `_instance_locks`…, _snapshot(), test_a_write_to_one_instance_does_not_block_a_write_to_another() (+10 more)

### Community 104 - "test_agent_registry.py"
Cohesion: 0.20
Nodes (16): FakeClock, hb(), make(), datetime, UBS-69 / FR-ING-010: agent registry, backend-side staleness., An agent whose clock is far ahead still goes missing when it stops sending., NTP corrects the agent host back by 5 minutes: sentAtUtc goes backwards on…, test_agent_clock_stepped_backwards_does_not_go_missing() (+8 more)

### Community 105 - "Health Reporter — end-to-end overview (UBS-30 → UBS-58 → UBS-59 → UBS-60)"
Cohesion: 0.11
Nodes (18): LoggingHeartbeatSink, Logger, Emit the wire JSON through `logging` (demo / local runs)., 1. What the Health Reporter is for, 2.1 One heartbeat tick, as a sequence, 2. End-to-end picture, 4.1 Wire contract — `packages/telemetry_shared/models/health.py`, 4.2 Configuration — `health/config.py` (+10 more)

### Community 106 - "test_UBS_109_alert_router.py"
Cohesion: 0.13
Nodes (27): LogCaptureFixture, parametrize, telemetry_agent_publishing_config, telemetry_agent_publishing_sink, _alert(), _publisher(), AlertEvent, BackendPublisher (+19 more)

### Community 107 - "ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1"
Cohesion: 0.15
Nodes (13): ADR 0003: Agent to backend transport is HTTPS/JSON batches on Day-1, gRPC (deferred, not rejected), HTTPS/1.1 JSON gzip batching (every 10s), Publisher interface (transport abstraction), ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1, PostgreSQL/TimescaleDB alternative (rejected for Day-1), Prometheus/VictoriaMetrics alternative (leading Day-2 candidate), Process-local ring buffer (10s buckets, 1m/5m rollups) (+5 more)

### Community 108 - "health-reporter-overview.md"
Cohesion: 0.12
Nodes (16): M1 — Log Monitor and Configuration, UBS-30 Implementation Notes, Health Reporter, MultiLogMonitor (Stopgap), last_read_at Starts as None, Not Zero, to Avoid Misreporting an Unread File as Healthy, UBS-30 — Ingestion Health / Read-Lag Metrics, UBS-48 — Pipeline Bridge (zero-loss, idempotent), UBS-48 — Pipeline Bridge Library (+8 more)

### Community 109 - "load_backend_health_config"
Cohesion: 0.19
Nodes (13): BackendConfigError, BackendHealthConfig, load_backend_health_config(), parse_duration_seconds(), Exception, Path, Raised when `config/backend.yaml` exists but is invalid., Path (+5 more)

### Community 110 - "test_FR_PRS_012_frame.py"
Cohesion: 0.18
Nodes (17): frame_message(), FrameOptions, Frame a single complete log line., Per file-set framing configuration., parametrize, FR-PRS-012–016 framing tests., Regression: the parser used to go blind after exactly `auto_lock_after`…, test_FR_PRS_012_pipe_delimited_framing() (+9 more)

### Community 111 - "AggregatorConfig"
Cohesion: 0.20
Nodes (14): AggregatorConfig, Bucket granularity, retained windows, and the per-metric dimension table (FR-…, _banner(), _implementation(), _line(), main(), Runnable, narrated demo of the Metrics Aggregator epic (MA-01/02/03). uv run…, _result() (+6 more)

### Community 112 - "pytest"
Cohesion: 0.31
Nodes (8): pytest, _batch_with_snapshot(), datetime, TestClient, FR-QRY-005: `/readyz` probes the same StreamProcessor that ingestion feeds.…, test_create_app_rejects_a_processor_the_service_does_not_feed(), test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store(), _wait_for_status()

### Community 113 - "telemetry_shared shared schema package"
Cohesion: 0.21
Nodes (12): docker compose redis service (redis:7-alpine, port 6379), AgentHeartbeat shared schema, AlertEvent shared schema, Magic Simulator (apps/simulator), MetricSnapshot shared schema, Rule: raw Magic logs and full FIX payloads must not be persisted, Redis (Day-1 shared telemetry state), Microsoft Teams Integration (apps/teams) (+4 more)

### Community 114 - "parse_fix_timestamp"
Cohesion: 0.27
Nodes (9): parse_fix_timestamp(), datetime, timedelta, Parse FIX SendingTime/TransactTime as UTC., TimestampResult, FR-PRS-025/026 timestamp tests., test_FR_PRS_025_bad_timestamp_falls_back_to_log(), test_FR_PRS_025_parses_fix_timestamp_utc() (+1 more)

### Community 115 - "fix/parser.py"
Cohesion: 0.21
Nodes (14): compile_reject_patterns(), match_reject_label(), normalize_reject_text(), Steps 1–2 of FR-PRS-022 (matching input only, not emitted)., Return (label, is_unclassified). On no match returns (None, True) — caller…, RejectPattern, Remove raw tag 58 text from egress (FR-PRS-022)., _strip_sensitive_fields() (+6 more)

### Community 116 - "telemetry_backend/config.py"
Cohesion: 0.20
Nodes (12): _AlertingYaml, _BackendConfigYaml, _BackendYaml, _drop_none(), IngestionConfig, _IngestYaml, _Lenient, Any (+4 more)

### Community 117 - "test_reporter.py"
Cohesion: 0.61
Nodes (7): make_monitor(), Path, test_degraded_reasons_flag_files_over_threshold(), test_degraded_threshold_is_configurable(), test_file_statuses_keys_match_monitor_names(), test_overall_read_lag_ignores_files_with_no_reads_yet(), test_overall_read_lag_is_none_when_nothing_has_been_read()

### Community 118 - "test_UBS_109_rule_engine_to_backend.py"
Cohesion: 0.12
Nodes (27): MetricsAggregator, PublishAction, RuleEngine, telemetry_agent_parser_fix_parser, telemetry_agent_parser_metrics_event, telemetry_agent_parser_protocol, telemetry_agent_publishing_outcome, _drain_backend() (+19 more)

### Community 119 - "test_heartbeat_roundtrip.py"
Cohesion: 0.20
Nodes (10): fastapi_testclient, telemetry_agent_health_heartbeat, FakeClock, datetime, Path, Agent Health Reporter (UBS-58/59/60) -> Ingestion (UBS-66) -> health read side…, Agents publish a heartbeat inside the 10s batch (FR-PUB-001), not only through…, test_agent_heartbeat_reaches_the_health_endpoint() (+2 more)

### Community 120 - "test_RE_02_evaluators.py"
Cohesion: 0.16
Nodes (22): StrEnum, FR-RUL-001: Day-1 supports exactly these five., RuleKind, make_latency(), _absence_rule(), _latency_rule(), RE-02: the per-`RuleKind` evaluators, tested directly against hand-built…, FR-MET-031, the gauge BackendUnreachable alerts on. (+14 more)

### Community 121 - "ingest_guard.py"
Cohesion: 0.21
Nodes (9): IngestGuard, datetime, Batch dedupe and per-agent rate limiting (UBS-85; FR-ING-004, FR-ING-008).…, Record a batch that is now on the ingest queue., _utc_now(), deque, math, OrderedDict (+1 more)

### Community 122 - "test_degraded_status_flows_into_heartbeat_payload"
Cohesion: 0.15
Nodes (13): Path, Offset survives a clean shutdown + fresh process, but read-lag knowledge does…, FR-HLT-001: degraded read lag has to survive the actual heartbeat wire format., One file being deleted out from under the agent must not crash the health…, HealthReporter wired to a real MultiLogMonitor, not a hand-built dict., Simulates logrotate: old file renamed away, new file created at the same path., Same inode, smaller size in place - e.g. a logger truncates instead of rotating., test_degraded_status_flows_into_heartbeat_payload() (+5 more)

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
Cohesion: 0.13
Nodes (21): CallbackFailing rule, NoLogActivity rule, Multi-tier severity rule shape, M5 Rules, alerts, callbacks, AgentCounterSampler (UBS-74), Alert lifecycle FSM, RuleEngine.apply_rules() hot swap, rules.config_loader (FR-RUL-008/009) (+13 more)

### Community 128 - "test_log_monitor_status.py"
Cohesion: 0.62
Nodes (6): make_monitor(), Path, test_status_after_read_reports_elapsed_lag(), test_status_before_any_read_has_no_lag(), test_status_missing_file_has_no_size_but_does_not_raise(), test_status_reports_offset_progress_between_polls()

### Community 129 - "effective_reject_reason"
Cohesion: 0.33
Nodes (7): effective_reject_reason(), Single precedence: ordRejReason → rejectReasonText label → unspecified. For…, FR-PRS-024 rejection precedence tests., test_FR_PRS_024_ord_rej_reason_wins(), test_FR_PRS_024_session_reject_for_msg_type_reject(), test_FR_PRS_024_text_label_when_no_ord_rej(), test_FR_PRS_024_unspecified_when_missing()

### Community 130 - "ADR 0004: Raw log content is never persisted or transmitted"
Cohesion: 0.40
Nodes (5): Note: raw log payloads must not be persisted permanently, Blocking CI sentinel test (FR-TST-005), ADR 0004: Raw log content is never persisted or transmitted, Compile-time field allowlist mechanism, Identifier hashing with HMAC key

### Community 131 - "Monitor to parser bridge (bounded line queue + parser worker pool)"
Cohesion: 0.40
Nodes (5): EventQueue (bounded, default size 256), LineQueue (bounded, default size 2048), Monitor to parser bridge (bounded line queue + parser worker pool), Parser worker pool (asyncio + ThreadPoolExecutor, min(2, cpu_count)), agent pipeline/ module (bounded queues + parser worker pool - M1.5)

### Community 132 - "008 — Natural Language Query Layer (Copilot/Teams)"
Cohesion: 0.40
Nodes (5): Problem P-4: No way to ask questions of live telemetry, NL Adapter (component), NL Endpoints (POST /telemetry/nl/query, GET /telemetry/nl/intents), NL Intent Catalogue (FR-NLQ-003/004), 008 — Natural Language Query Layer (Copilot/Teams)

### Community 133 - "NFR-REL-003: Backend Outage Must Not Affect Alerting"
Cohesion: 0.50
Nodes (5): Backend Outage Sequence (§8.3), Backend Publisher Requirements (FR-PUB-001–008), NFR-REL-003: Backend Outage Must Not Affect Alerting, Reliability NFRs (§2), Runbook: Backend Unreachable

### Community 134 - "telemetry-shared"
Cohesion: 0.40
Nodes (5): telemetry-agent, telemetry-backend, telemetry-shared, telemetry-simulator, telemetry-teams

### Community 137 - "PipelineStats"
Cohesion: 0.33
Nodes (3): PipelineStats, Queue depths and drop counters for heartbeat/metrics (FR-PIP-005)., test_pipeline_stats_expose_prometheus_metric_names()

### Community 156 - "IngestGuardConfig"
Cohesion: 0.33
Nodes (6): IngestGuardConfig, UBS-85: batch dedupe (FR-ING-004) and per-agent rate limiting (FR-ING-008).…, parametrize, test_ingest_section_is_loaded_from_yaml(), test_invalid_config_is_refused(), test_missing_ingest_section_uses_spec_defaults()

### Community 159 - "test_data_completeness.py"
Cohesion: 0.30
Nodes (10): hb(), FR-QRY-015: dataCompleteness derived from agent staleness (UBS-69 slice)., registry_with(), test_all_reporting_is_complete(), test_all_stale_is_degraded(), test_bucket_level_gaps_downgrade_complete_to_partial(), test_expected_agent_never_seen_counts_as_stale(), test_no_agents_expected_is_complete_not_degraded() (+2 more)

### Community 195 - "Snapshot"
Cohesion: 0.08
Nodes (47): BatchAccepted, IngestionService, IngestionValidationIssue, Apply the backend-side allowlists and bucket cardinality cap. Pydantic has…, Undo an admission reservation when the bounded queue is full., Keep store work off FastAPI's request path. A single consumer preserves the…, Bound an attacker-controlled key before including it in an error path., One safe, field-level reason an ingestion request was rejected. (+39 more)

### Community 201 - "AlertStore"
Cohesion: 0.08
Nodes (37): AlertStoreConfig, Alert store retention (spec 006 §6, spec 010 `store.recentAlertLimit`)., AlertStore, _InstanceAlerts, _is_active_status(), datetime, Lock, In-memory Alert Store (spec 006 §6; `FR-QRY-016`, `FR-QRY-017`). (+29 more)

### Community 203 - "DryRunPublishSink"
Cohesion: 0.40
Nodes (3): DryRunPublishSink, Logger, Log the intended publish, never open a socket. Use this while there's no real…

### Community 212 - "demo_reload.py"
Cohesion: 0.24
Nodes (12): _show_alerts(), _banner(), _instructions(), main(), Path, Live walkthrough of SIGHUP rule reloading (`FR-RUL-008`/`009`). uv run python…, The watched file may be mid-edit or deliberately broken; a failed read here…, _run() (+4 more)

### Community 214 - "MultiLogMonitor"
Cohesion: 0.10
Nodes (20): print_header(), run_demo(), setup_environment(), main(), main(), poll_available(), print_lines(), print_section() (+12 more)

### Community 216 - "outcome.py"
Cohesion: 0.29
Nodes (8): classify_publish_response(), PublishOutcome, UBS-103: HTTP response -> publish action classification (spec 007 §2.1's…, enum, parametrize, test_429_carries_retry_after_seconds(), test_status_code_classification(), test_transport_error_is_backoff()

### Community 217 - "protocol.py"
Cohesion: 0.09
Nodes (28): Demo metrics sink for parser CLI (mirrors spec 004 counter names)., AppLogParser, Parser plugin for configured application log patterns (Magic format)., AppLogTelemetry, Structured fields extracted from Magic-style application log lines., FixFields, Fixed-shape allowlisted field set. No attribute here may hold a raw, non-…, UBS-106: per-session heartbeat-timeout detection. A heartbeat timeout is the… (+20 more)

### Community 228 - "alert_router.py"
Cohesion: 0.14
Nodes (13): AlertRouter, AlertEvent, BackendPublisher, datetime, Logger, UBS-109: routes Rule Engine alerts to the Backend Publisher.…, Enqueues alerts for publication, rejecting any that would poison the batch they…, Self-observability, same shape as `BackendPublisher.counters` and… (+5 more)

### Community 234 - "Rule Engine demo runbook"
Cohesion: 0.15
Nodes (12): 1. `make rules-test`, 2. `make rules-quickstart`, 3. `make rules-reload-demo`, Going deeper, if asked, If someone asks, Pre-flight, Rule Engine demo runbook, make rules-quickstart (17-act demo) (+4 more)

### Community 235 - ".__init__"
Cohesion: 0.20
Nodes (7): Logger, PublishSink, Protocol, The transport boundary. `HttpsPublishSink` is the Day-1 default (ADR 0003);…, BackendUnreachableCallback, DropCallback, HeartbeatProvider

### Community 237 - "test_UBS45_integration.py"
Cohesion: 0.32
Nodes (7): demo_log_lines(), Path, Return parsed corpus lines, optionally filtered to one source file label., _meta(), Integration-style parser tests for UBS-45 enrich path., test_reject_text_maps_to_label(), test_seq_gap_from_corpus()

## Ambiguous Edges - Review These
- `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` → `Redis (Day-1 shared telemetry state)`  [AMBIGUOUS]
  docs/adr/0005-in-memory-metric-store.md · relation: conceptually_related_to
- `M1 — Log Monitor and Configuration` → `UBS-30 — Ingestion Health / Read-Lag Metrics`  [AMBIGUOUS]
  docs/plan/ubs30-notes.md · relation: implements
- `appLogPatterns regex` → `Enterprise Infrastructure Stream (Application.log)`  [AMBIGUOUS]
  apps/agent/testdata/magic/demo_config.yaml · relation: references

## Knowledge Gaps
- **180 isolated node(s):** `1. What the Health Reporter is for`, `2.1 One heartbeat tick, as a sequence`, `5.1 The window — `health/window.py``, `9. How to verify / demo`, `Also touched, and why` (+175 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1244 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **90 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0005: Backend metric store is in-memory time buckets, no database on Day-1` and `Redis (Day-1 shared telemetry state)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `M1 — Log Monitor and Configuration` and `UBS-30 — Ingestion Health / Read-Lag Metrics`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **What is the exact relationship between `appLogPatterns regex` and `Enterprise Infrastructure Stream (Application.log)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `MA-04: calculated indicators and snapshot output.` connect `config/rules.yaml live rule set` to `MetricsAggregator ring buffer`, `Implementation Status live document`, `FakeClock`, `Rule Engine`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `Spec 004: Telemetry data model` connect `Telemetry Agent (architecture constraint)` to `Telemetry System Documentation Index`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `HealthReporter` connect `HealthReporter` to `UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth`, `test_heartbeat.py`, `LogMonitor`, `Registry`, `AgentHeartbeat`, `DeliveryTracker`, `load_health_config`, `OffsetTracker`, `test_health_monitor_e2e.py`, `SourceMeta`, `test_parse_errors.py`, `SlidingWindowCounter`, `ParseResult`, `datetime`, `_main_async`, `test_queue_depth.py`, `BackendPublisher`, `test_buffer_bytes_and_drops.py`, `test_reporter.py`, `test_heartbeat_roundtrip.py`, `test_degraded_status_flows_into_heartbeat_payload`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `MetricsAggregator` (e.g. with `AgentCounterSampler` and `Histogram`) actually correct?**
  _`MetricsAggregator` has 55 INFERRED edges - model-reasoned connections that need verification._