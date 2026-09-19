# Telemetry Schema — ParsedMessageEvent and the Metrics Aggregator

Status: Proposed · Owner (Metrics Aggregator): TBD · Owner (Parser Engine): TBD
Agreed with: _pending — Parser Engine owner to confirm before real events are emitted_

`ParsedMessageEvent` is the contract between the Parser Engine and the Metrics
Aggregator. It's defined once, in code, at
`packages/telemetry_shared/src/telemetry_shared/models/parsed_message.py` —
this document explains the shape and the counter/histogram derivation built
on top of it; the code is the enforceable version of the contract itself.

Ground truth for everything below is spec 004 (telemetry data model) and
spec 003 (FIX parsing), not the MA-01/02/03 ticket wording — where the
tickets used different names or a looser scope than the specs, the specs won
and the tickets' *intent* (not their exact wording) was preserved. Deviations
from spec are called out explicitly, not silently absorbed.

## Shape: a base class plus one subclass per message category

`ParsedMessageEvent` is both the common base type and the concrete type for
administrative messages (Logon, Logout, Heartbeat, session-level Reject, or
any `msg_type` not listed below) — those carry no order-lifecycle fields, so
the base class alone is the right shape for them. For every other message,
the parser should construct the matching subclass instead of the base class
directly, using `EVENT_CLASS_BY_MSG_TYPE` to pick it:

| `msg_type` | Class | Fields it makes required (beyond the envelope) |
| --- | --- | --- |
| `NewOrderSingle` (35=D) | `NewOrderEvent` | `cl_ord_id`, `symbol`, `side`, `ord_type`, `order_qty` |
| `OrderCancelRequest` (35=F) | `CancelRequestEvent` | `cl_ord_id`, `orig_cl_ord_id`, `symbol`, `side`, `order_qty` |
| `OrderCancelReplaceRequest` (35=G) | `CancelReplaceEvent` | `cl_ord_id`, `orig_cl_ord_id`, `symbol`, `side`, `ord_type`, `order_qty` |
| `ExecutionReport` (35=8) | `ExecutionReportEvent` | `cl_ord_id`, `order_id`, `exec_id`, `exec_type`, `ord_status`, `symbol`, `side`; and `last_qty` specifically when `exec_type == "Trade"` |
| `OrderCancelReject` (35=9) | `CancelRejectEvent` | `cl_ord_id`, `orig_cl_ord_id` |
| anything else | `ParsedMessageEvent` (base) | nothing beyond the envelope |

Because every subclass **is a** `ParsedMessageEvent`, the aggregator only
ever type-hints against the base class and reads `event.symbol`,
`event.side`, etc. uniformly regardless of which subclass it received.

## Fields

| Field | Type | Source (spec 003 §4) |
| --- | --- | --- |
| `event_time_utc` | `datetime` | tag 52 SendingTime, falling back to log read time per `FR-PRS-025` |
| `instance_id` | `str` | configured per file set, not a FIX tag |
| `session_id` | `str` | `senderCompId`/`targetCompId` pair, tags 49/56 |
| `msg_type` | `str` | tag 35, normalised name per `FR-PRS-023` |
| `transact_time_utc` | `datetime \| None` | tag 60 TransactTime — an *alternative* timestamp basis for MA-03's latency calc; distinct from `event_time_utc`, which answers a different question (spec 003 FR-PRS-025) |
| `cl_ord_id` / `orig_cl_ord_id` / `order_id` / `exec_id` | `str \| None` | tags 11/41/37/17 |
| `symbol` / `side` / `ord_type` / `ord_status` / `exec_type` | `str \| None` | tags 55/54/40/39/150, normalised |
| `order_qty` / `last_qty` | `Decimal \| None` | tags 38/32 — **`Decimal`, never `float`** (MA-02 AC): FIX quantities must not accumulate binary floating-point error across many fills |
| `cum_qty` / `leaves_qty` | `Decimal \| None` | tags 14/151, "fill progress" — in spec 003's original allowlist but missing from the first cut of this schema; `leaves_qty` is what fills_full/fills_partial actually key on (see below), `cum_qty` is carried for allowlist completeness even though no counter derives from it yet |
| `reject_reason_code` / `reject_reason_text` | `str \| None` | tag 103 / tag 58 normalised (`FR-PRS-022`) — see reason precedence below |

`event_time_utc`, `instance_id`, `session_id`, `msg_type` are required on
every message (`FR-PRS-017`). Everything else's required-ness depends on
which subclass is constructed, per the table above.

**Open point for the Parser Engine owner:** identifier fields here are
unhashed, unlike the wire event sent to the backend (spec 004 §2, hashed per
`FR-PRS-021`) — correct for this internal handoff, but confirm the parser
isn't hashing before this boundary. Also: `reject_reason_code` on
`CancelRejectEvent` (35=9) is sourced from **CxlRejReason (tag 102)**, not
OrdRejReason (103) — same field slot, different source tag depending on
`msg_type`. Tag 102 is not in spec 003's original field allowlist §4;
enabling its extraction is a coordination item for the Parser Engine owner,
not a schema widening on this side (scaffold.md's working agreement #4).

## Deliberately not a field: `reject_reason`

The Metrics Aggregator groups by `reject_reason` as one dimension, but there
is no single `reject_reason` field on the contract — the parser emits the
raw signals (`reject_reason_code`, `reject_reason_text`) separately, and the
aggregator derives the effective reason using `FR-PRS-024`'s precedence:
coded reason, else normalised text, else `"unspecified"`.

## Counters (spec 004 §4.1 — names match the spec verbatim)

`apps/agent/src/telemetry_agent/metrics/counters.py`'s `derive_counters` is
one dispatch producing all of these from a single event walk:

| Counter | Condition |
| --- | --- |
| `messages_total` | every event (not in spec 004; a convenience total) |
| `unclassified_messages` | `msg_type` outside spec 003 §6's known set — counted, never dropped silently |
| `orders_submitted` | `NewOrderSingle` (35=D) |
| `order_qty` | sum of `order_qty` on 35=D |
| `orders_cancel_requested` | `OrderCancelRequest` (35=F) |
| `orders_replaced` | `OrderCancelReplaceRequest` (35=G) |
| `orders_acked` | `ExecutionReport`, `exec_type == "New"` |
| `executions` | `ExecutionReport`, `exec_type == "Trade"` |
| `executed_qty` | sum of `last_qty` on Trade |
| `fills_full` / `fills_partial` | Trade, split on **`leaves_qty == 0` / `> 0`** — spec 004 keys this on LeavesQty, not OrdStatus; `ord_status` (`"Filled"`/`"PartiallyFilled"`) is used only as a fallback when the parser didn't populate `leaves_qty` |
| `orders_canceled` | `ExecutionReport`, `exec_type == "Canceled"` |
| `orders_expired` | `ExecutionReport`, `exec_type == "Expired"` |
| `orders_rejected` | `ExecutionReport`, `ord_status == "Rejected"` **or** `exec_type == "Rejected"` (spec: "ExecType/OrdStatus Rejected", either signal) |
| `cancel_rejects` | `OrderCancelReject` (35=9) |
| `session_rejects` | `Reject` (35=3) — kept apart from `orders_rejected`/`cancel_rejects`: a session-level reject is a FIX plumbing problem, not a trading problem, and merging it in would give a Rule Engine a misleading reject rate |
| `rejects_total` | sum of the three reject counters above — not a spec 004 counter, a convenience addition; the three components remain independently available |

Every counter carries the same active dimension set (`instance_id`,
`session_id`, `symbol`, `side`, `ord_type`; reject counters additionally
carry `reject_reason`) — see `COUNTER_DIMENSIONS`, the `FR-MET-030` "one
shared table" declaration.

**Not implemented (out of MA-01/02/03's scope):** spec 004 §4.2 (protocol/
session counters — `fix_messages_by_type`, `seq_gaps`, `logons`, ...) and §4.3
(agent self counters — `parse_errors`, `publish_attempts`, ...) belong to the
Parser Engine, Publisher, and Health components respectively, not the
Metrics Aggregator.

## Reason normalisation

`ReasonNormalizer`'s default map is **identity**, seeded from spec 003 §6's
own `OrdRejReason`/`SessionRejectReason` canonical names (`OrderExceedsLimit`,
`UnknownSymbol`, ... `Other`). The parser already normalises the raw FIX code
to one of these strings (`FR-PRS-023`) before the aggregator ever sees it, so
the *default* behaviour here is pass-through, not a second renaming layer —
a deployment that wants prettier display labels (e.g. `OrderExceedsLimit` →
"Price Exceeds Limit") passes its own `reason_map`, it isn't baked in as
ground truth. `"Other"` is already spec 003's own fallback name (code 99 on
both enums), so it doubles cleanly as this normaliser's unmapped-fallback
label too. Unmapped raw reasons are recorded, truncated to a configured max
length, capped at 50 distinct entries, so the map can be extended from what's
actually seen.

## Histograms (spec 004 §4.4 — the two MA-03 was asked for, plus one the spec
also defines that the ticket didn't mention)

| Histogram | Scope | Definition |
| --- | --- | --- |
| `ack_latency_ms` | `NewOrderSingle` origin only | 35=D → first 35=8 with `exec_type == "New"` for the same ClOrdID |
| `exec_latency_ms` | `NewOrderSingle` origin only | 35=D → first 35=8 with `exec_type == "Trade"` |
| `cancel_latency_ms` | `OrderCancelRequest` / `OrderCancelReplaceRequest` origin | 35=F (or 35=G) → 35=8 `exec_type == "Canceled"`, or 35=9 (`OrderCancelReject`) |

Spec 004 §4.4 scopes `ack_latency_ms`/`exec_latency_ms` specifically to
`35=D` — an earlier draft of this correlator lumped cancel/replace requests
into the same tracking bucket for these two histograms, which doesn't match
the spec (and doesn't match real FIX behaviour either: a successful
cancel/replace confirms with `ExecType=Replaced`, not `New`, so that code
path would never have actually fired). Cancel/replace requests are still
tracked in the correlation map — so their eventual response isn't
misclassified as an orphan — but only `cancel_latency_ms` is recorded for
them; a replace's own confirmation (`ExecType=Replaced`) has no
spec-defined histogram and none is invented for it.

Fixed boundaries: `1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, +Inf` ms
(`FR-MET-025`), `count`/`sum`/`min`/`max` alongside every histogram
(`FR-MET-026`), percentiles interpolated at query time and `null` under
`minSampleSize` (`FR-QRY-007`/`FR-QRY-012`) — implemented as
`Histogram.percentile()`.

## Cardinality control (spec 004 §5)

Two caps, both enforced **per bucket** (reset when a bucket is reused, not
held for the aggregator's whole process lifetime — an earlier draft used a
process-lifetime registry, which would have grown unboundedly on a
long-running agent even though bucket *data* expires):

- `max_label_sets` (default 5000, `FR-MET-029`) — distinct label-sets per
  *metric* per bucket.
- `max_series_per_bucket` (default 2000, `FR-MET-030`) — total series summed
  across *every* metric per bucket, a separate and often tighter guard: two
  metrics can each be comfortably under their own cap and still sum past this
  one.

Either cap folds overflow into `__other__` and increments
`MetricsAggregator.cardinality_folded` (`FR-MET-029`: "...and
`metrics.cardinality_folded` is incremented" — a real observability signal
that folding is happening, not just a silent relabel).

**Known simplification, not yet built:** spec 004 §5's dimension table also
specifies *per-dimension-value* caps (symbol ≤ 200, session ≤ 32,
`rejectReason` ≤ 50, ...), independent of the per-metric/per-bucket caps
above. That's a materially different cardinality-control axis (bounding how
many distinct *values* one dimension can ever take, not how many
*combinations* a metric accumulates) and the project's own open question Q-6
("which telemetry dimensions are mandatory") is still unresolved — building
the full per-dimension system now would be guessing at a decision the
project hasn't made. The two caps above are what MA-01's own AC specified
and are implemented; per-dimension caps are a documented gap, not a silent
one.

## Schema evolution

Adding an optional field is safe on either side once merged. Removing or
retyping a field needs a heads-up to both owners before merging — there's no
version negotiation on this internal contract (unlike the wire schema in
spec 004 §7), so a breaking change here breaks the other side's build
immediately: Pydantic's `extra="forbid"` and required-field validation turn
drift into a loud failure at construction time rather than a silent gap in a
snapshot.
