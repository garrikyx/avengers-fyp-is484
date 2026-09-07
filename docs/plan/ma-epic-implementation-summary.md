# MAGIC Metrics Aggregator — Implementation Summary

Last updated: 2026-09-04 · Gaps/diagrams: [`ma-epic-implementation-review.md`](./ma-epic-implementation-review.md)

One `ParsedMessageEvent` moves through four stages before it's queryable:
**separated** by type, **grouped** into a label, **written** into a store,
and later **read** back out.

## 1. Separate — what kind of message is this

`derive_counters(event)` dispatches once on `msg_type` (then again on
`exec_type` for `ExecutionReport`) and returns only the counters that
actually fired. Independently, `LatencyCorrelator.ingest(event)` makes its
own classification: a new-order-family message opens a tracked
`OrderContext`; a response message (`ExecutionReport`, `OrderCancelReject`)
looks up a tracked order by `(session_id, cl_ord_id)` and resolves it by
the *tracked order's own origin type* — never by the incoming message's
own type.

| Log (`msg_type`) | Counters fired | Correlation action |
| --- | --- | --- |
| Unrecognised | `unclassified_messages` | — |
| Administrative (`Heartbeat`/`Logon`/`Logout`/`SequenceReset`/`TestRequest`/`ResendRequest`) | none | — |
| `NewOrderSingle` (35=D) | `orders_submitted` (+`order_qty`) | opens tracked order, origin = NewOrderSingle |
| `OrderCancelRequest`/`OrderCancelReplaceRequest` (35=F/G) | `orders_cancel_requested`/`orders_replaced` | opens tracked order, origin = cancel |
| `OrderCancelReject` (35=9) | `cancel_rejects` + `rejects_total` | resolves tracked cancel → `cancel_latency_ms` (once); no match → `orphan_responses` |
| `Reject`, session-level (35=3) | `session_rejects` + `rejects_total` | — |
| `ExecutionReport`, ExecType=New | `orders_acked` | resolves tracked NewOrderSingle → `ack_latency_ms` (once) |
| `ExecutionReport`, ExecType=Trade | `executions` (+`executed_qty`), `fills_full`/`fills_partial` split on `leaves_qty` | resolves tracked NewOrderSingle, first fill only → `exec_latency_ms` (once) |
| `ExecutionReport`, ExecType=Canceled | `orders_canceled` | resolves tracked cancel → `cancel_latency_ms` (once) |
| `ExecutionReport`, ExecType=Expired | `orders_expired` | — |
| `ExecutionReport`, OrdStatus/ExecType=Rejected | `orders_rejected` + `rejects_total` (independent of the rows above) | — |

`messages_total` fires on every row, always, in addition to what's listed.
A duplicate or already-resolved response is a silent no-op; a response
matching no tracked order is an `orphan_responses`, never a fake latency.

## 2. Group — what label does it get

Every counter and every latency metric has a declared, fixed dimension set.
At write time the aggregator builds one label tuple by reading those
fields off the event — `reject_reason` through `ReasonNormalizer.resolve`
(code/text → canonical label → `"Other"` if unmapped, `"unspecified"` if
neither is present), everything else by plain attribute access.

| Dimension set | Fields | Used by |
| --- | --- | --- |
| `BASE_DIMS` | `instance_id`, `session_id`, `symbol`, `side`, `ord_type` | every counter and every latency metric |
| `REJECT_DIMS` | `BASE_DIMS` + `reject_reason` | `orders_rejected`, `cancel_rejects`, `session_rejects`, `rejects_total` only |

The finished label then passes the cardinality gate, scoped per bucket:

| Cap | Scope | On trip |
| --- | --- | --- |
| `max_label_sets` (5,000) | per metric | label folds to `(__other__, …)` |
| `max_series_per_bucket` (2,000) | total, across every metric | same — binds first in practice |

Both reset the moment a bucket is reused. `cardinality_folded` counts every
fold, from either cap.

## 3. Write — landing in the store

Both producers write into the same `MetricsAggregator` ring buffer. The
event's timestamp resolves a bucket (`bucket_start(ts) = ts //
bucket_seconds`, ring index `% capacity`). Counters increment in place —
`bucket.counters[metric][label] += amount`. A resolved latency sample calls
`Histogram.record(value_ms)`, sorting it into one of 11 fixed, exclusive
ranges and updating count/sum/min/max. Correlation state (the open-order
map) lives outside the ring entirely, with its own eviction.

| Mechanism | Trigger | Result | Signal |
| --- | --- | --- | --- |
| Ring bucket reuse | stored `bucket_start` ≠ the one just resolved | bucket cleared — counters, histograms, admitted-set wiped | none, silent |
| Ring bucket expiry (`tick()`) | `bucket_start` older than the retained window | same clear, run opportunistically on every ingest/snapshot | none, silent |
| Correlation TTL | `first_seen_at` older than 15m (default), checked on every `ingest()` | tracked order removed | `ttl_evictions` + `unmatched_orders` |
| Correlation hard cap | a new tracked order arrives at `max_entries` (100,000 default) | single oldest entry (by `first_seen_at`) removed | `cap_evictions` + `unmatched_orders` |
| Cardinality cap | label not yet admitted, either cap already reached | label folds to `__other__` — nothing dropped, just merged | `cardinality_folded` |

## 4. Read — assembling a snapshot

`snapshot(window, group_by)` scans every bucket still inside the window,
and for each metric whose declared dimensions cover the requested
`group_by`, projects its label tuple down to just those positions and
merges it into a result row — summed for counters, bucket-merged for
histograms.

| Input | Validated against | If violated |
| --- | --- | --- |
| `window` | must be a key in the configured windows | raises |
| `group_by` | must be a subset of `known_dimensions` — the union of every metric's declared dims | raises |
| a metric that doesn't declare a requested `group_by` dim | — | not an error — that metric is silently absent from the result |
| a series with value 0 | — | can't exist — every write is a positive increment or a recorded sample |

### What `group_by` supports

| Dimension | Available to |
| --- | --- |
| `symbol`, `side`, `ord_type`, `session_id`, `instance_id` | every counter and every latency histogram |
| `reject_reason` | only `orders_rejected`, `cancel_rejects`, `session_rejects`, `rejects_total` |

Any subset of these six — none, one, or several combined — is a valid
`group_by`. A metric that doesn't declare a requested dim is silently
absent from that row; a dim no metric declares at all raises.

### What comes back — counters and correlated (latency) data together

One `snapshot()` call returns both at once, merged onto the same row:
`MetricRow.counters` (MA-02's order/execution/reject counts) and
`MetricRow.histograms` (MA-03's correlated ack/exec/cancel latency). They're
kept in separate sub-dicts specifically so a caller that only wants one
doesn't have to filter the other out — read `row.counters` alone for pure
counts, `row.histograms` alone for pure latency, or both together (e.g.
"AAPL: 42 fills, p95 ack latency 12ms" from a single call). There is no
separate call to fetch only counters or only latency — the split happens
after the read, not before it.

An `__other__` label always projects to one all-`__other__` row, so folded
overflow stays visible no matter how the query slices it. `tick()` runs at
the top of both the write path and the read path, so a stale bucket is
never included either way — decay isn't something a caller has to
remember to trigger.

## 5. Verified — what 101 tests actually prove

| File | Proves |
| --- | --- |
| `tests/unit/telemetry_shared/test_parsed_message_event.py` | Every subclass's required fields, `Decimal` string-coercion (never float), immutability, `extra="forbid"`, `EVENT_CLASS_BY_MSG_TYPE`'s exact contents. |
| `test_MA_01_aggregator.py` | 10k events/60s window, 61s decay to zero, both cardinality caps (fold + reset-per-bucket-reuse + `cardinality_folded` count), `group_by` validation and multi-dim ordering, an out-of-window event dropped without corrupting a live bucket that shares its ring slot, an unknown window name raising. |
| `test_MA_02_counters.py` | Every counter in `derive_counters()` against a hand-labelled fixture with an independently hand-computed total (`EXPECTED_TOTALS`), reason normalisation (map hit / unmapped→`Other`/`unspecified`, truncation, dedupe, bounded list), `top_reject_reasons`, the fill-full/partial split's `leaves_qty`-over-`ord_status` precedence, `orders_rejected`'s two independent trigger signals, the SessionRejectReason(373)-code path. |
| `test_MA_03_correlation.py` | ack/first-fill/cancel latency, duplicate-response no-op, orphan responses, TTL *and* hard-cap eviction (oldest-first, verified via the evicted order's own later orphan response — not just a counter), the implausible-latency ceiling (positive, distinct from the skewed-clock negative case), both cancel-latency origins (35=F and 35=G), a replace's own confirmation being a documented no-op, and the `transact_time` timestamp source actually being used (not just its anomaly path). |
| `tests/integration/agent/test_MA_integration.py` | The core architecture claim: `derive_counters()` and `LatencyCorrelator` writing into *one* shared `MetricsAggregator`, a counter and a histogram both landing on the same `snapshot()` row. |
| `test_histogram.py` | Exclusive bucket assignment, overflow, bucket-wise `merge`, all three named percentiles (p50/p95/p99) against hand-worked values, interpolation inside the `+Inf` bucket itself. |
| `test_MA_04_snapshot.py` | Indicator formulas against the hand-labelled fixture's `EXPECTED_TOTALS`, null-on-zero-denominator, `lowConfidence` flipping at the sample-size threshold, throughput, grouped breakdown, gauges (pending orders, staleness), window bounds / `generatedAtUtc` using an injected clock. |

Run: `uv run pytest tests/unit tests/integration -v` (101 tests across this
epic's own files; 161 across the whole repo) · lint/types:
`uv run ruff check .` and `uv run mypy apps/agent/src` (both clean on this
package).

## 6. Calculated indicators and snapshot output (MA-04)

`telemetry_agent.metrics.snapshot.snapshot(aggregator, window, group_by, ...)`
wraps `MetricsAggregator.snapshot()` (section 4) with the layer its two real
consumers need — the Rule Engine and the Backend Publisher — without
touching the write path at all. Pure read + arithmetic: no I/O, no locks, so
it can never block a concurrent `ingest_counters`/`observe_latency` call.

Per group, on top of the raw counters: `indicators` (spec 004 §4.5's
`rejectRate`/`fillRate`/`cancelRate`/`parseErrorRate`, each `{value,
denominator, lowConfidence}` — `value` is `null` when `denominator` is 0,
`lowConfidence` is `true` whenever `denominator` is below
`min_sample_size` (default 20, the same `histogram.DEFAULT_MIN_SAMPLE_SIZE`
MA-03's percentiles already use — one shared constant, not a second copy) —
so a single rejected order yields a real value, just flagged low-confidence,
which is what stops a Rule Engine firing `HighRejectRate` off one sample),
`throughput` (orders/sec, not a ratio, always defined), and `latency`
(p50/p95/p99/avg/count per histogram present on that row, via the existing
`Histogram.percentile`). Two new instance-wide `gauges`, sourced from small
additive read methods on the already-existing classes (no change to their
write paths): `pendingOrders`/`oldestPendingAgeSeconds` from
`LatencyCorrelator.pending_order_count()`/`.oldest_pending_age_seconds()`
(tracked orders whose first relevant response hasn't arrived — approximate,
since the correlator never removes a resolved entry, only flags it, so a
rejected order still counts as pending until TTL eviction), and
`secondsSinceLastEvent` from `MetricsAggregator.seconds_since_last_event()`.
Wrapped into `telemetry_shared.models.metrics.MetricsSnapshot` — the
non-functional stub that used to live at this path is gone; the current
model mirrors the backend's `POST /telemetry/query/metrics` response shape
(spec 007 §3) field-for-field so a future relay needs no renaming.

`parseErrorRate` is formula-ready but always reads `value=null,
lowConfidence=true` today: nothing yet emits `parse_errors`/`log_lines_read`
into the aggregator (that's a Log Monitor/Parser Engine wiring task, not
started). The contract already has the field so the Rule Engine doesn't need
a shape change once that wiring lands.

### Alert readiness

The next piece of work is six Rule Engine alerts. What this snapshot already
carries for each, and what still needs to be built elsewhere:

| # | Alert | Served by | Still needed |
| - | --- | --- | --- |
| 1 | HighRejectRate (warn>3%, crit>5% / 5m) | `indicators.rejectRate`, window="5m" | Nothing |
| 2 | >5 execution failures/5m, or pending-order timeout | count half: `counters.orders_rejected`. Timeout half: `gauges.pendingOrders`/`oldestPendingAgeSeconds` | Nothing |
| 3 | >1% parse failure/5m, or ≥10 consecutive failures | rate half: `indicators.parseErrorRate` (formula-ready) | A `parse_errors`/`log_lines_read` producer (Log Monitor/Parser Engine). Consecutive-failure half is a streak counter over raw parse outcomes — Rule Engine's own state, not a windowed-snapshot concept |
| 4 | FIX processing latency (warn p95>500ms, crit p95>1s / 5m) | `groups[].latency["ack_latency_ms"].p95` | Nothing |
| 5 | No heartbeat>30s; no log activity>60s | log-activity half: `gauges.secondsSinceLastEvent` | Heartbeat half is the Health Reporter (spec 004 §6) — a separate, unbuilt component |
| 6 | Same rule+instance → one active alert | — | Entirely Rule Engine's own dedup-key state machine (spec 005) — no snapshot involvement |

**Known gaps, not closed here** (tracked in the review doc, linked above):
ExecID de-duplication is absent system-wide — a retransmitted
`ExecutionReport` double-counts; and `timestamp_source` is recorded on the
correlator but never reaches `MetricRow`, so a `snapshot()` caller can't
tell which clock basis a latency number used. Both are design decisions
(what eviction policy, what schema change) rather than test-coverage gaps,
so neither was made unilaterally in this pass.
