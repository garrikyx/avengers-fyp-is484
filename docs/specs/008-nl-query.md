# 008 — Natural Language Query Layer (Copilot / Teams)

Status: Draft · Owner: TBD · Last updated: 2026-07-31

## 1. Design stance

`FR-NLQ-001`: The language model **never** touches the metric store. It only maps a question
to a structured query object, which is then validated and executed by the same query engine
that serves the HTTP API. There is no generated code, no generated query DSL string, and no
dynamic evaluation of model output.

Consequences:

- Answers are always reproducible: `interpretedQuery` can be replayed against
  `POST /telemetry/query/metrics` and MUST yield the same numbers.
- The model's failure mode is "wrong filters", not "arbitrary execution".
- `FR-NLQ-002`: The structured query MUST be validated against the same strict schema as a
  direct API call; anything invalid is a clarification prompt to the user, never a best-effort
  guess that silently drops a filter.

## 2. Intent catalogue

`FR-NLQ-003`: Day-1 supports this closed set. An unmatched question returns a
`clarification` response listing supported intents rather than improvising.

| Intent | Answers | Structured shape |
| --- | --- | --- |
| `rejection_summary` | "Why are orders rejecting?" | reject counts + rate grouped by `rejectReason`, `instanceId` |
| `order_flow_summary` | "How is Magic doing today?" | orders, acks, executions, rejects, fill rate over the range |
| `latency_summary` | "Is Magic slow right now?" | `ack_latency_ms` percentiles + trend vs previous period |
| `alert_status` | "Any alerts open for Magic?" | active alerts with severity and duration |
| `session_status` | "Are the FIX sessions up?" | logons/logouts, heartbeat timeouts, seq gaps per session |
| `symbol_drilldown` | "What's rejecting on ABC?" | metrics filtered to a symbol, grouped by `rejectReason` |
| `agent_health` | "Is telemetry actually working?" | heartbeat age, read lag, parse error rate, dropped counts |
| `parse_health` | "Are we failing to parse anything?" | parse errors grouped by `reason` |
| `compare_period` | "Are rejects worse than yesterday?" | same metrics over two ranges with deltas |
| `trend` | "Show rejects over the last hour" | time series at an appropriate step |

`FR-NLQ-004`: Each intent MUST have a fixed set of required and optional slots
(`timeRange`, `application`, `instanceId`, `session`, `symbol`, `groupBy`, `step`) and a
deterministic default for every optional slot, documented alongside the intent.

## 3. Interpretation pipeline

1. **Normalise** the question (trim, collapse whitespace, cap at `maxQuestionChars`, default
   500 — `FR-NLQ-005`).
2. **Rule-first matching**: a deterministic matcher handles the common phrasings for each
   intent, plus explicit time expressions. `FR-NLQ-006`: if the rule matcher succeeds with
   high confidence, the LLM MUST be skipped entirely — it is faster, free, and predictable.
3. **LLM fallback**: the question plus the intent catalogue and slot schema are sent to the
   model, which MUST return JSON conforming to the slot schema (structured output / function
   calling, not free text). `FR-NLQ-007`.
4. **Validate and clamp**: unknown dimension values, out-of-range windows and unknown metrics
   are rejected or clamped, and every adjustment is recorded in `caveats`. `FR-NLQ-008`.
5. **Execute** via the query engine, plus an alert lookup when the intent needs it.
6. **Render** a summary from a deterministic template populated with the returned numbers.

`FR-NLQ-009` **(critical)**: Rendering MUST be template-based, not model-generated prose over
raw data. The model chooses *what to ask*; the templates state *what was found*. This
eliminates fabricated numbers. A model MAY be used to smooth phrasing only if the numeric
tokens are substituted from the query result afterwards and verified to appear unchanged.

## 4. Time expression handling

| ID | Requirement |
| --- | --- |
| `FR-NLQ-011` | MUST support `last N minutes/hours`, `today`, `this morning`, `since HH:MM`, `yesterday`, `between A and B`. |
| `FR-NLQ-012` | Relative expressions MUST be resolved in the user's timezone (from Teams context, default `Asia/Singapore`, configurable) and converted to UTC before querying. The resolved absolute UTC range MUST be shown in the answer. |
| `FR-NLQ-013` | `today` MUST mean "since local midnight", clamped to the retention window, and the clamp MUST be stated: "showing the last 6 hours; earlier data is not retained". |
| `FR-NLQ-014` | Ambiguous or missing time expressions default to `last 30m` and the default MUST be stated in the answer. |

## 5. Answer format

`FR-NLQ-015`: The answer MUST lead with the number that answers the question, then supporting
breakdown, then any open alert, then caveats. Target length: under 80 words for a summary
intent.

Good:

> Magic recorded 62 rejected orders in the last 30 minutes out of 1,250 submitted, a 5.0%
> reject rate. The largest category was OrderExceedsLimit (35), followed by UnknownSymbol
> (18). The HighRejectRate alert has been active on magic-prod-01 for 12 minutes.

`FR-NLQ-010`: If `dataCompleteness.confidence` is not `complete`, the answer MUST say so
plainly: "1 of 3 agents is not reporting, so these numbers are incomplete."

`FR-NLQ-016`: When a KPI is `null` for insufficient data, the answer MUST say "not enough
activity to compute a reject rate", never "0%".

`FR-NLQ-017`: Every answer MUST include the `interpretedQuery` in the API response, and in
Teams MUST offer a "show the query / show the numbers" affordance.

## 6. Integration surfaces

| Surface | Approach |
| --- | --- |
| Copilot | Declarative agent + API plugin pointed at the generated OpenAPI document, restricted to `POST /telemetry/nl/query`, the metrics query, alert and health read endpoints |
| Teams | Bot that forwards the message text to `/telemetry/nl/query` and renders an Adaptive Card: headline number, breakdown table, alert badge, caveats, "show query" action |
| Direct API | `POST /telemetry/nl/query` for any other tooling |

| ID | Requirement |
| --- | --- |
| `FR-NLQ-018` | Access MUST be authenticated per user (Entra ID) and authorised read-only; the NL layer MUST NOT expose any mutating operation. |
| `FR-NLQ-019` | The user identity MUST be logged with the interpreted query (not the raw question, which may contain pasted sensitive content) for audit. `NFR-SEC-011` |
| `FR-NLQ-021` | Per-user rate limits MUST apply (default 20 questions/minute), and LLM calls MUST have a `2s` timeout with fallback to the rule matcher or a clarification response. |
| `FR-NLQ-022` | Rendered output MUST be escaped for its destination (Adaptive Card text, Markdown, HTML) — user-supplied text is never interpolated unescaped. |

## 7. Prompt-injection and abuse considerations

`FR-NLQ-023`: Question text is untrusted input. It MUST NOT be able to change filters outside
the slot schema, request another application's data, escalate scope, or cause more than one
query execution per request. The slot schema is the security boundary.

`FR-NLQ-024`: Because `rejectReasonText` is normalised to a bounded label set at parse time
(spec 003 §5), no free text from the log stream can reach a prompt. This is deliberate: it
prevents log content from influencing the model.

## 8. Evaluation

`FR-NLQ-025`: A fixed evaluation set of at least 40 question/expected-`interpretedQuery`
pairs MUST live in the repository and run in CI. Intent accuracy and slot exactness MUST be
reported; a drop below the agreed threshold (initially 90% intent, 80% exact slots) fails the
build. Prose is not asserted; the structured interpretation is.
