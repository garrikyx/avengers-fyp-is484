# MA-01 / MA-02 / MA-03 — Implementation Mechanics

Last updated: 2026-09-02 · Gaps/diagrams: [`ma-epic-implementation-review.md`](./ma-epic-implementation-review.md)

## MA-01 — store

- **Ring:** `capacity = max_window / bucket_seconds` slots (900 @ defaults).
  `bucket_start(ts) = ts // bucket_seconds`; ring index = `bucket_start %
  capacity`. A slot is cleared + restamped the first time it's touched by a
  different `bucket_start` — reuse is detected lazily, not on a timer.
- **`ingest_counters(event, counters)`:** resolve bucket from
  `event.event_time_utc` (drop if outside the retained window) → per metric,
  look up its declared dims → build a label tuple from the event's fields
  (`reject_reason` via an injected resolver, everything else `getattr`) →
  cardinality-gate the label → `bucket.counters[metric][label] += amount`.
- **`observe_latency(...)`:** same path, writes `Histogram.record()`
  instead; bucket and label come from the caller-supplied `at`/`dims_event`.
- **Cardinality gate:** per-bucket, per-metric admitted-label set (cap
  5,000) *and* a bucket-wide total admitted count (cap 2,000, binds first
  in practice). Either cap trips → fold to `__other__`,
  `cardinality_folded += 1`. Resets whenever the bucket is reused.
- **`tick()`:** clears any slot older than the currently retained window.
  Runs inside every `ingest`/`snapshot` call — not an independent timer.
- **`snapshot(window, group_by)`:** gather in-window buckets → per metric,
  skip it if its own dims don't cover `group_by` → project its full label
  tuple down to the requested positions → sum (counters) / bucket-merge
  (histograms) into the result row.

## MA-02 — counters

`derive_counters(event)` returns a sparse dict (only fired keys):

- `messages_total` always; unknown `msg_type` → `unclassified_messages`,
  stop.
- `NewOrderSingle`→`orders_submitted`(+`order_qty`), `CancelRequest`→
  `orders_cancel_requested`, `CancelReplace`→`orders_replaced`,
  `CancelReject`(35=9)→`cancel_rejects`+`rejects_total`, session
  `Reject`(35=3)→`session_rejects`+`rejects_total`.
- `ExecutionReport` by `exec_type`: `New`→`orders_acked`; `Trade`→
  `executions`(+`executed_qty`), then fill split — primarily `leaves_qty`
  (`==0`/`>0`), `ord_status` fallback only if `leaves_qty` absent;
  `Canceled`→`orders_canceled`; `Expired`→`orders_expired`.
- Independently (not exclusive with the above): `ord_status=="Rejected"`
  or `exec_type=="Rejected"` → `orders_rejected`+`rejects_total`.

Reason **label** is resolved separately and later — only for reject-family
metrics, at aggregator label-build time — by the injected
`ReasonNormalizer.resolve`: code-or-text → map lookup → canonical label;
unmapped → truncate + dedupe into `unmapped_seen` (cap 50) → `"Other"`;
neither present → `"unspecified"`.

## MA-03 — correlation and latency

- **Map:** `(session_id, cl_ord_id) → OrderContext{first_seen_at,
  origin_msg_type, ack/fill/cancel_recorded flags}`.
- **Every `ingest()`:** sweep-evict entries past TTL (15m default) →
  `ttl_evictions` + `unmatched_orders`. A new entry past `max_entries`
  evicts the single oldest first → `cap_evictions` + `unmatched_orders`.
- **Response routing** keyed by the *tracked entry's* `origin_msg_type`,
  not the incoming message: `NewOrderSingle` origin + `ExecType`
  New/Trade → `ack_latency_ms`/`exec_latency_ms` (once each, flag-guarded).
  Cancel/replace origin + `ExecType=Canceled` or `OrderCancelReject`(35=9)
  → `cancel_latency_ms` (once, flag-guarded). No tracked entry →
  `orphan_responses`. Already-flagged → silent no-op.
- **Latency value:** exact millisecond delta (integer day/second/
  microsecond arithmetic, never `total_seconds()`) using the configured
  `timestamp_source`. Negative or over the plausibility ceiling →
  `latency_anomaly`, nothing recorded.
- **`Histogram`:** fixed boundaries (`1,5,10,25,50,100,250,500,1000,5000,
  +Inf` ms), exclusive (non-cumulative) bucket assignment +
  count/sum/min/max. `percentile()` linearly interpolates within the
  bucket holding the target rank; `None` below the minimum sample size.
can