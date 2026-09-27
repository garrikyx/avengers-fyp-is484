# Rule Engine demo runbook

How to demo the Rule Engine epic (UBS-7, UBS-72, UBS-73, UBS-74, plus config
reload and the safety valves) from a terminal. Written so someone who didn't
build it can drive it.

Implementation detail lives in `re-epic-implementation-summary.md`; this file is
only about running the thing.

---

## Pre-flight

```bash
uv sync
```

That's it. `MAGIC_TELEMETRY_ID_HASH_KEY` is exported by the `Makefile`, so the
`make` targets below need no environment setup. If you run the modules directly
with `uv run python -m ...`, export it yourself first:

```bash
export MAGIC_TELEMETRY_ID_HASH_KEY=dev-only
```

Total runtime for the full demo: about 3 minutes, most of it you talking.

---

## The 5-minute version

```bash
make rules-test          # 99 tests, ~2s
make rules-quickstart    # the whole alerting story, ~2s
make rules-reload-demo   # interactive: hot-reload without losing alert state
```

If you only have time for one, run `make rules-quickstart`.

`rules-quickstart` prints 17 acts across three parts — complete, but more than
you'd narrate live. **If you have five minutes, talk through these five and let
the rest scroll:**

| Act | Why this one |
| --- | --- |
| 2 + 4 | The UBS-72 vs UBS-7 contrast. A 51-reject burst at a 2.49% rate that a percentage rule would miss, then the rate climbing warning→critical on one `alertId`. This is the most self-explaining thing in the epic. |
| 9 | `FixSessionDown` critical, straight off a `35=5` Logout line printed right above it. |
| 10 | The agent alerting that its *own* alerts aren't reaching Magic. |
| 16 | The storm cap — one meta-alert instead of a flood. |
| 17 | The backend unreachable while Magic keeps trading — alerting carries on locally, nothing is lost, and the alert resolves itself on recovery. |

## UBS-5 coverage

All 11 stories under the Rule Engine epic, and where each one shows up:

| Story | Rules | Shown in |
| --- | --- | --- |
| UBS-7 Elevated Order Reject Rate | `HighRejectRate` | act 4 |
| UBS-17 Elevated Execution Issues | `SessionRejects`, `NoExecutions`, `PendingOrderTimeout` | acts 5, 11, 12 |
| UBS-18 Elevated Parser Failures | `ParseErrorRate` | act 13 |
| UBS-19 Elevated FIX Processing Latency | `AckLatencyBreach` | act 6 |
| UBS-20 Missing Activity | `NoLogActivity` | act 14 |
| UBS-21 Deduplication of Repeated Alerts | dedup + renotify | acts 4 and 15 |
| UBS-72 Order Volume Spikes | `RejectSpike`, `CancelRejectSpike` | acts 2, 3 |
| UBS-73 FIX Session Instability | `FixSessionDown`, `SeqGapDetected`, `ClockSkew` | acts 7, 8, 9 |
| UBS-74 Callback Delivery Failures | `CallbackFailing` | act 10 |
| UBS-75 Backend Publish Failures | `BackendUnreachable` | act 17 |
| UBS-76 Alert Storm Protection | `AlertStorm` | act 16 |

**All 14 configured rules fire during the run.** Act 17 closes the last gap:
it drives a real `BackendPublisher` against a backend answering 503 until the
`consecutive_publish_failures` gauge reaches 5, then brings the backend back
and shows the alert resolve on the same `alertId`.

Hot-reload (`FR-RUL-008`/`009`) isn't in this run at all; it needs a live
process, so it's `make rules-reload-demo` below.

---

## Spoken script — sponsor demo (~3 min)

Run `make rules-quickstart` and let it finish (~2s, ~140 lines), then scroll
back and talk. Five beats, in scroll order. `alertId` values are random per
run — point at `same alertId`, don't read the hex aloud.

**Opening (~15s)**

> This is the Rule Engine running on the agent, next to Magic. It reads raw
> FIX log bytes, derives counters, and evaluates fourteen rules loaded from a
> YAML file. What you're scrolling through is one session going from healthy
> to falling apart. Every alert traces back to a log line printed just above it.

**Beat 1 — acts 2 and 4 (~60s)**

> Act two: fifty-one order rejects inside a minute. But look at the rate —
> 2.49%, against a warning tier of 3%. A purely percentage-based rule stays
> silent here; at two thousand orders, fifty-one rejects just doesn't move the
> ratio. That's the gap, and `RejectSpike` catches it on absolute count.
>
> Act four: now the rate itself climbs. 3.38% trips warning, then 5.44% trips
> critical — and this is the part I'd point at, `same alertId: True`. It raised
> the severity of the alert already open rather than paging a second time. One
> incident, one alert, escalating in place.

**Beat 2 — act 9 (~25s)**

> A `35=5` Logout from the counterparty, right there in the log. The session is
> gone, so this is critical — it's the one that wakes somebody up. Note the two
> above it: a sequence gap of four messages, and eleven messages timestamped two
> hours in the future. Three separate session-health signals, three rules.

**Beat 3 — act 10 (~35s)**

> Here the agent notices that its *own* alerts aren't getting out — four
> callback deliveries to Magic's endpoint failed permanently.
>
> Two things. It only counts a failure after the dispatcher has exhausted its
> retries, so a transient 500 that succeeds on retry never appears here. And the
> whole chain ran locally, with no backend involved.

**Beat 4 — act 16 (~30s)**

> What happens when everything breaks at once. The cap is three here; production
> default is a hundred. Three alerts fire, the cap holds, and you get a single
> `AlertStorm` meta-alert — not one page per suppressed rule. A cascading outage
> can't turn the agent into its own denial-of-service against the on-call engineer.

**Beat 5 — act 17, the close (~50s)**

> Last one, and it's the counterpart to act ten. Here the backend is unreachable
> — five consecutive publish attempts failed — while Magic carries on trading
> normally. The agent alerts on it locally, and the alert resolves itself the
> moment the backend answers again, on the same `alertId`.
>
> Two points worth making. Nothing was lost: every batch is still buffered, so
> the telemetry ships once the link is back. And this is a centrally-hosted
> alerting system's structural blind spot — it cannot tell you that it can't
> reach you. Ours can, because the alerting lives on the agent.
>
> That's fourteen of fourteen rules firing. Every threshold is configurable in
> YAML and reloadable without restarting or losing alert state — I can show you
> that live if it's useful.

**Fallback if something misfires live:** `make rules-test` is 99 tests in about
two seconds and makes the same argument without the narration.

---

## Metric reference — what each rule reads, and where its number came from

Use this if you're asked "how did you pick that threshold" or "what does that
metric actually mean". Provenance is the honest answer in each case:

- **Client-confirmed** — a number UBS gave us. Three rules only.
- **Structural** — not a tuned number. The threshold is "any occurrence at
  all", because one of these events is already an incident.
- **Provisional (Q-5)** — our starting value, flagged in spec 005 §1.2 as
  pending client input. Configurable, and we expect to tune it.
- **Our reasoning** — no spec or client number existed; the rationale is in the
  rule's docstring.

| Rule | Reads | What the metric means | Threshold / window | Provenance |
| --- | --- | --- | --- | --- |
| `HighRejectRate` | `reject_rate` indicator | `orders_rejected / (orders_acked + orders_rejected)` — the share of orders the venue turned down. Recomputed from summed counters, never averaged. | >3% warn, >5% crit; 5m, ≥20 samples, for 2m | **Client-confirmed** |
| `AckLatencyBreach` | `ack_latency_ms` p95 | Time from a `35=D` NewOrderSingle to the first `35=8` ExecutionReport for the same ClOrdID. Percentile interpolated from fixed histogram buckets, so reported as approximate. | p95 >500ms warn, >1000ms crit; 5m, ≥50 samples | **Client-confirmed** |
| `ParseErrorRate` | `parse_error_rate` indicator | `parse_errors / log_lines_read` — the share of log lines the parser could not read. Counts hard failures only, not soft warnings like an unknown MsgType. | >1% warn, >25% crit; 5m, ≥20 samples | **Client-confirmed** |
| `RejectSpike` | `orders_rejected` counter | `35=8` with ExecType or OrdStatus = Rejected. Absolute count, which is why it catches bursts that the percentage rule misses at high volume. | >50 in 1m | Provisional (Q-5) |
| `CancelRejectSpike` | `cancel_rejects` counter | `35=9` OrderCancelReject — a cancel or replace the venue refused. Kept apart from order rejects and session rejects so it can't dilute either. | >20 in 5m | Provisional (Q-5) |
| `SessionRejects` | `session_rejects` counter | `35=3` Reject — a FIX *protocol* problem, not a trading decision. Critical because it usually means malformed traffic or a version mismatch. | >5 in 5m | Provisional (Q-5) |
| `ClockSkew` | `clock_skew_events` counter | Messages whose SendingTime differs from wall-clock read time by more than `maxClockSkew` (default 5m, configurable). Indicates a host clock drifting. | >10 in 5m | Provisional (Q-5) |
| `CallbackFailing` | `callback_failures` counter | Alert deliveries to Magic's callback endpoint that failed *permanently* — counted only after the dispatcher exhausts its retries, so transient errors don't inflate it. | >3 in 5m | Provisional (Q-5) |
| `NoLogActivity` | `messages_total` counter | Every classified FIX message, admin included. Zero for a whole minute means the pipeline is dead, not that trading is quiet. | == 0 over 1m | **Structural** |
| `NoExecutions` | `executions` counter, guarded by `orders_submitted` | `35=8` with ExecType = Trade. The guard matters: no fills while no orders were sent is a quiet market, not a fault, so the rule only applies when orders actually went out. | == 0 while `orders_submitted` > 0, 15m | **Structural** |
| `FixSessionDown` | `logouts` + `heartbeat_timeouts` | `35=5` Logout from the counterparty. (`heartbeat_timeouts` has no producer yet and reads 0 — a timeout is the *absence* of a message, so it belongs to the Health Reporter's tick, not to per-message parsing.) | ≥ 1 in 1m | **Structural** |
| `SeqGapDetected` | `seq_gaps` counter | A MsgSeqNum that skipped ahead — messages were lost in transit. A sequence that goes *backwards* is counted separately as a regression, since it skipped nothing. | > 0 in 1m | **Structural** |
| `PendingOrderTimeout` | `oldest_pending_age_seconds` gauge | Age of the oldest order still awaiting its *first* response — ack or cancel outcome. Deliberately not time-to-fill, so a resting limit order is never penalised. | >30s | **Our reasoning** — typical institutional order-ack SLA |
| `BackendUnreachable` | `consecutive_publish_failures` gauge | Publish attempts that failed in a row since the last successful batch commit; resets to 0 on success. A windowed failure count can't work here — the publisher's exponential backoff spaces attempts further apart, so the count *falls* as the outage lengthens. | ≥ 5 | **Our reasoning** — restores the original "5 consecutive" intent |

Two framing points that usually land well:

- **Ratios are never averaged.** A rate is always recomputed from summed
  numerator and denominator, whether over one agent's window or across every
  agent at the backend. Averaging per-agent percentages would silently weight a
  quiet instance the same as a busy one.
- **A rate returns `null`, not 0, below `minSamples` (default 20).** One reject
  out of one order is not a 100% reject rate, and an idle minute is not a
  perfect one.

---

## 1. `make rules-test`

99 tests covering the FSM, the evaluators, the safety valves, all 14 default
rules, YAML loading and SIGHUP reload. Run it first so the demo isn't the only
evidence anything works.

---

## 2. `make rules-quickstart`

One FIX session's life, start to finish. Every number on screen comes from raw
FIX log bytes fed through the real `FixParser` — nothing is hand-stubbed — and
the 14 rules are read from the live `config/rules.yaml`.

Sixteen acts in three parts. What to say for each:

**Part 1 — order-flow alerts**

| Act | What prints | The point |
| --- | --- | --- |
| 1 | 2000 orders, all acked, `rejectRate = 0.00%`, no alerts | A healthy session is quiet. The engine isn't just firing on everything. |
| 2 | `orders_rejected = 51`, `rejectRate = 2.49%`, `RejectSpike` **warning** | **The reason UBS-72 exists.** 51 rejects is a real incident, but at this volume the *rate* is under `HighRejectRate`'s 3% tier. A percentage-only rule would say nothing. |
| 3 | `cancel_rejects = 21`, `CancelRejectSpike` **warning** | Refusing to *cancel* is a different failure from refusing to trade, so it gets its own counter and rule. |
| 4 | `3.38%` → **warning**, then `5.44%` → **critical**, `same alertId: True` | Multi-tier severity. The alert escalates in place rather than opening a second one — one incident, not two pages. |
| 5 | `session_rejects = 6`, `SessionRejects` **critical** | Session-level rejects are a FIX plumbing problem, deliberately kept out of the order-flow reject rate so they can't dilute it. |
| 6 | `p95=748ms over 2220 samples`, `AckLatencyBreach` **warning** | Needs ≥50 samples before trusting a p95 — a stricter bar than the rate rules' 20, because a percentile is unstable at low counts. |

**Part 2 — session and delivery alerts**

| Act | What prints | The point |
| --- | --- | --- |
| 7 | `MsgSeqNum` jumps, `seq_gaps: 1`, `seq_gap_messages: 4` | Four messages lost in transit. The gap *size* is recorded, not just the fact of a gap. |
| 8 | 11 messages timestamped 2h ahead, `ClockSkew` **warning** | Threshold is `> 10`, so the 11th trips it. Ten would not have. |
| 9 | Logout line, `logouts: 1`, `FixSessionDown` **critical** | The session is gone. Critical, not warning — this one wakes someone up. |
| 10 | `callback_failures: 4`, `CallbackFailing` **warning** | **The best beat.** The agent has just noticed its own alerts aren't reaching Magic. A centrally-hosted alerting system could not report this. |

**Part 3 — absence, parser health, lifecycle, safety**

| Act | What prints | The point |
| --- | --- | --- |
| 11 | 2335 orders submitted, 0 executions, `NoExecutions` **warning** | Guarded on `orders_submitted > 0`, so a genuinely idle instance stays quiet instead of paging about a slow market. |
| 12 | `oldestPendingAge` 0s → 45s, `PendingOrderTimeout` **warning** | Measures time to *first response*, never time to fill — a resting limit order is not a stuck one. |
| 13 | `parseErrorRate` 0.00% → 1.02%, `ParseErrorRate` **warning** | Deliberately *not* suppressed by `NoLogActivity`: it has to keep evaluating when the log pipeline itself is what's breaking. |
| 14 | A second instance reading nothing, `NoLogActivity` **critical** | While this fires, `FR-RUL-021` suppresses order-flow rules for that instance — absence of data is not evidence of absence of rejects. |
| 15 | 1 alert, then 10 evaluations → **0** more, then a renotify on the same `alertId` with `notificationCount 1 → 2` | Dedup. One active alert per rule+instance however often it's evaluated; the renotify is a reminder about one incident, not a second incident. |
| 16 | 3 alerts, then `AlertStorm` **critical**, `AlertStorm events emitted: 1` | Safety valve. At the cap it pages *once*, not once per suppressed alert — a cascading outage can't turn the agent into its own DoS. |
| 17 | `consecutiveFailures=5`, `BackendUnreachable` **warning**, then `resolved` on the same `alertId` once the backend answers 202 | `NFR-REL-003`. Magic keeps trading throughout; only the agent→backend link is down. Batches stay buffered (`FR-PUB-004`), the alert is raised locally with no backend involved, and recovery resolves it without operator action. |

Three acts use a non-default config to make something visible at demo scale, and
each says so on screen: act 15 shortens `renotifyInterval` from 1800s to 60s,
act 16 lowers `maxActiveAlerts` from 100 to 3, and acts 14–16 run their own
instance. Faking a hundred concurrent alerts would be worse than lowering the
cap honestly.

### If someone asks

- **"Why does the demo use a fixed clock?"** The rule windows are 1–15 minutes
  wide. On a wall clock the demo's own events would age out of their windows
  mid-run. Ingest time is pinned; the engine's clock still advances past each
  rule's `for` delay, which is what makes alerts fire.
- **"Why doesn't `heartbeat_timeouts` ever fire?"** Nothing produces it. A
  timeout is the *absence* of a message, which no per-message derivation can
  observe — it belongs to the Health Reporter's periodic tick. `FixSessionDown`
  sums `logouts + heartbeat_timeouts` and treats a missing counter as 0, so the
  rule works correctly without it.
- **"Why is `BackendUnreachable` a gauge and not a windowed count?"** Because a
  windowed count cannot work here. The publisher retries with exponential
  backoff (`FR-PUB-005`), so each failure pushes the next attempt further out —
  a fixed window ends up measuring the retry schedule rather than the outage.
  The rule's earlier `publish_failures > 5` over `1m` form yielded exactly five
  failures in the first minute under default config, so it could never fire, and
  decayed toward one per minute as the backoff hit its cap. Spec 005 §1.2 was
  corrected and the gauge (`FR-MET-031`) restores the original "5 consecutive"
  intent. `test_a_full_minute_of_outage_yields_exactly_five_failures` pins it.
- **"Are these thresholds real? How did you derive them?"** See the **Metric
  reference** table above, which gives the provenance of all fourteen. Short
  version: `HighRejectRate`, `AckLatencyBreach` and `ParseErrorRate` are
  client-confirmed; the absence and session rules are structural rather than
  tuned ("any occurrence is an incident"); the rest are provisional starting
  values pending Q-5. All are configurable.
- **"Why is `ParseErrorRate` only 1%, not the 25% critical tier?"** At ~4,900
  lines read, 25% would mean the log had become mostly unparseable. Also worth
  knowing: the most common failure mode (a FIX line with no checksum) is held by
  `LineJoiner` as a possible continuation and only counted once it gives up
  after four lines — so that mode alone asymptotes just under 25% and can never
  reach critical by itself. `tests/integration/agent/test_RE_parse_error_integration.py`
  pins both behaviours.
- **"Why do acts 14–16 use a different instance?"** Each needs a condition the
  main story can't produce: an aggregator that has read *nothing*
  (`NoLogActivity`), a shortened renotify interval, and a lowered alert cap.
  They print their non-default setting before they run.

---

## 3. `make rules-reload-demo`

The interactive one. Hot-reload can't be shown in a script: it needs a live
process to send a signal to.

It starts, holds one alert firing, and prints its own PID plus the exact command
to paste:

```
  watching : /var/folders/.../rules-reload-demo-xxxx/rules.yaml
  pid      : 61050
  reload   : kill -HUP 61050
```

It watches a **temp copy** of `config/rules.yaml`, so editing it can't leave the
real config dirty. (A drift test compares that file against `DEFAULT_RULES`, and
a stray edit would fail the suite.) Pass `--rules config/rules.yaml` to drive the
real file instead.

Open a second terminal, edit the watched file, then `kill -HUP <pid>` after each
change. Every 1–2 seconds the process reprints the alert's status, so you can see
the effect immediately.

### The four edits

**1. Raise a threshold, still matched.** Under `- name: RejectSpike`, set
`threshold: 55`. There are 60 rejects standing, so 55 is still cleared.

```
[INFO] rules reloaded: 14 rules from /var/.../rules.yaml
RejectSpike: status=firing  alertId=7a30318b (same alert throughout)
```

The rules swapped underneath a firing alert and it kept its `alertId` and
`firstObservedUtc`. **This is `FR-RUL-008`** — the whole point. No restart, no
lost alert state, no duplicate page.

**2. Raise it past the observed value.** Set `threshold: 500`.

```
RejectSpike: status=resolving  alertId=7a30318b (same alert throughout)
```

The new threshold took effect on the very next evaluation. Same alert, now
resolving because the condition stopped matching.

**3. Delete a firing rule.** Remove the whole `- name: RejectSpike` block.

One synthetic `resolved` event. An alert can't stay open for a condition that no
longer has a definition.

**4. Corrupt the file.** On any rule, set `operator: "!!"`.

```
[ERROR] rules reload rejected, keeping last-known-good: rule 'HighRejectRate'
        is invalid: unknown operator '!!', expected one of ['<','<=','==','>','>=']
```

**The process keeps running**, on its last-known-good rules. This is the beat
worth pausing on: a bad config deploy does not take alerting down with it
(`FR-RUL-009`). Check with `ps` if anyone doubts it.

Ctrl-C to stop. The temp copy is removed on exit.

---

## Going deeper, if asked

| Command | Shows |
| --- | --- |
| `make metrics-bridge-quickstart` | Raw FIX bytes → `FixParser` → counters, without the rules layer |
| `make callback-demo` | The Callback Dispatcher's retry/backoff loop live, including a delivery that fails twice then succeeds |
| `make metrics-quickstart` | The Metrics Aggregator alone — windows, indicators, latency percentiles |
| `cat config/rules.yaml` | The live rule set. 14 rules, multi-tier severities, all thresholds configurable |
| `uv run pytest tests/integration/agent -q` | The seams: parser → aggregator → rule engine, and dispatcher → sampler → rule engine |

---

## Known rough edges

Be upfront about these rather than hoping nobody runs them:

- `make lint` is red repo-wide (97 mypy, 82 ruff), all pre-existing and in files
  outside this epic. The rules/ package itself is clean.
- `tests/unit/simulator` fails to collect — `apps/simulator` isn't in the root dev
  dependencies. Run `uv run pytest tests --ignore=tests/unit/simulator`.
- No agent supervisor loop exists yet, so nothing wires the Rule Engine to a
  long-running process in production. `demo_reload.py` is a demo harness standing
  in for that, and says so.
