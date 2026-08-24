# 003 — Parser Engine and FIX Parsing

Status: Draft · Owner: TBD · Last updated: 2026-07-31

Day-1 supports FIX 4.2 and 4.4 tag=value messages embedded in text log lines. The parser
interface is designed so a binary protocol parser can be added on Day-2 without touching
the rest of the pipeline.

## 1. Line classification

`FR-PRS-010`: Each line MUST be classified before parsing, in this order:

1. **`fix`** — the line contains a `8=FIX` (or `8=FIXT`) token followed by a delimiter and a
   `35=` tag within `fixDetectWindow` bytes (default 256).
2. **`app_log`** — the line matches a configured application log pattern (level, timestamp,
   message). Used for error-signature rules and log-activity liveness only.
3. **`unsupported`** — anything else. Counted in `parser.unsupported_lines`, then discarded.

`FR-PRS-011`: Classification MUST be substring/prefix based and MUST NOT run a regex over
every line at full throughput. Regexes are permitted only on lines already classified
`app_log`, and only for the configured signature set.

## 2. Framing and delimiters

| ID | Requirement |
| --- | --- |
| `FR-PRS-012` | MUST support SOH (`0x01`) as the field delimiter, and the common log-safe substitutions `\|`, `^A`, and `;` — configurable per file set as `fixDelimiter: auto\|soh\|pipe\|caret\|semicolon`. `auto` sniffs the delimiter from the first 100 successfully framed messages and then locks it. |
| `FR-PRS-013` | MUST tolerate a log prefix before `8=FIX` (timestamp, thread, level) and a suffix after the checksum field; parsing starts at `8=` and ends at the `10=` field or end of line. |
| `FR-PRS-014` | MUST handle a FIX message split across multiple log lines by joining continuation lines until a `10=` field is seen or `maxJoinLines` (default 4) is exceeded; on exceed, emit `parse.error` reason `incomplete_message`. |
| `FR-PRS-015` | MUST NOT trust `9` (BodyLength). Length mismatch is recorded as a soft validation warning, not a parse failure, because log lines are frequently altered by the logging framework. |
| `FR-PRS-016` | Checksum (`10`) validation MUST be off by default (`validateChecksum: false`) for the same reason; when enabled, a mismatch produces reason `checksum_mismatch`. |

## 3. Validation

`FR-PRS-017`: A message is **valid** when it has a parseable `8` (BeginString) and a non-empty
`35` (MsgType). Everything else is optional and its absence is reported as a per-field
`missing` count, not a message-level failure.

`FR-PRS-018`: Parse error reason codes (closed set — these become metric dimensions):

| Reason | Meaning |
| --- | --- |
| `no_begin_string` | `8=` not found where classification promised it |
| `no_msg_type` | `35` absent or empty |
| `malformed_field` | a token had no `=`, or a non-numeric tag |
| `incomplete_message` | never reached `10=` within `maxJoinLines` |
| `unknown_msg_type` | `35` value not in the known set (message is still counted) |
| `bad_timestamp` | tag 52/60 present but unparseable |
| `checksum_mismatch` | only when `validateChecksum: true` |
| `line_truncated` | line exceeded `maxLineBytes` |
| `internal_error` | parser bug or panic (recovered) |

`FR-PRS-019`: The parser MUST recover from panics per line, count `parser.internal_errors`,
and continue. A single bad line MUST NOT terminate the agent.

## 4. Field allowlist

`FR-PRS-020` **(security-critical)**: The parser MUST extract **only** the tags below. All
other tags MUST be discarded without being copied into any event, metric label, or log
message. This allowlist is the enforcement point for "no sensitive data leaves the host"
(`NFR-SEC-002`) and MUST be a compile-time constant table, not configuration.

| Tag | Name | Use | Emitted as |
| --- | --- | --- | --- |
| 8 | BeginString | protocol version | `fixVersion` |
| 35 | MsgType | classification, counters | `msgType` |
| 34 | MsgSeqNum | gap detection | `seqNum` (event only) |
| 49 | SenderCompID | session identity | `senderCompId` |
| 56 | TargetCompID | session identity | `targetCompId` |
| 52 | SendingTime | latency, bucketing | `sendingTime` |
| 60 | TransactTime | latency | `transactTime` |
| 11 | ClOrdID | correlation only — **hashed before emission** | `clOrdIdHash` |
| 41 | OrigClOrdID | cancel/replace correlation — hashed | `origClOrdIdHash` |
| 37 | OrderID | correlation only — hashed | `orderIdHash` |
| 17 | ExecID | de-duplication — hashed | `execIdHash` |
| 150 | ExecType | execution analytics | `execType` |
| 39 | OrdStatus | order state analytics | `ordStatus` |
| 55 | Symbol | dimension (cardinality-capped) | `symbol` |
| 54 | Side | dimension | `side` |
| 40 | OrdType | dimension | `ordType` |
| 38 | OrderQty | volume metrics | `orderQty` |
| 32 | LastQty | fill metrics | `lastQty` |
| 14 | CumQty | fill progress | `cumQty` |
| 151 | LeavesQty | fill progress | `leavesQty` |
| 103 | OrdRejReason | rejection dimension | `ordRejReason` |
| 58 | Text | rejection detail — **normalised, never raw** (see §5) | `rejectReasonText` |
| 45 | RefSeqNum | session reject context | `refSeqNum` |
| 372 | RefMsgType | session reject context | `refMsgType` |
| 373 | SessionRejectReason | session reject dimension | `sessionRejectReason` |

Explicitly **excluded**, and MUST NOT be extracted on Day-1: 44 (Price), 31 (LastPx),
6 (AvgPx), 1 (Account), 448/447/452 (party IDs), 448-group contents, 21, 528/529, 581,
and any tag not in the table. Price fields are excluded because they carry no Day-1 metric
value and materially increase sensitivity; adding any of them requires an ADR.

`FR-PRS-021`: Identifier hashing MUST be HMAC-SHA256 truncated to 16 hex characters, keyed
with a per-deployment secret from the environment. The hash gives correlation and
de-duplication without exposing client order identifiers.

## 5. Text field normalisation

`FR-PRS-022`: Tag 58 (Text) MUST NOT be emitted verbatim. It is mapped to a bounded label:

1. Trim, lowercase, collapse whitespace.
2. Replace digit runs with `#`, and quoted strings / long alphanumeric tokens with `*`.
3. Match against the configured `rejectReasonPatterns` list; on match emit the pattern's
   canonical label (e.g. `price_exceeds_limit`).
4. On no match, emit `unclassified` and increment `parser.unclassified_reject_text`. The
   normalised form is **not** emitted.
5. Cap the resulting label set at `maxRejectReasonLabels` (default 50); excess → `__other__`.

This keeps free-text out of the telemetry stream while still answering "why are orders
rejecting". Growing the pattern list is a config change, not a code change (`FR-CFG-020`).

## 6. Known value sets

`FR-PRS-023`: The parser MUST recognise these values and map them to stable names. Unknown
values are passed through as `unknown_<raw>` with the raw value restricted to `[A-Za-z0-9]`
and 8 characters, and counted in `parser.unknown_enum_values`.

**MsgType (35)** — `0` Heartbeat, `1` TestRequest, `2` ResendRequest, `3` Reject,
`4` SequenceReset, `5` Logout, `A` Logon, `D` NewOrderSingle, `F` OrderCancelRequest,
`G` OrderCancelReplaceRequest, `8` ExecutionReport, `9` OrderCancelReject,
`AB` NewOrderMultileg, `AC` MultilegOrderCancelReplace.

**ExecType (150)** — `0` New, `3` DoneForDay, `4` Canceled, `5` Replaced,
`6` PendingCancel, `7` Stopped, `8` Rejected, `9` Suspended, `A` PendingNew,
`C` Expired, `E` PendingReplace, `F` Trade, `G` TradeCorrect, `H` TradeCancel.

**OrdStatus (39)** — `0` New, `1` PartiallyFilled, `2` Filled, `3` DoneForDay,
`4` Canceled, `5` Replaced, `6` PendingCancel, `7` Stopped, `8` Rejected,
`9` Suspended, `A` PendingNew, `C` Expired, `E` PendingReplace.

**OrdRejReason (103)** — `0` BrokerOption, `1` UnknownSymbol, `2` ExchangeClosed,
`3` OrderExceedsLimit, `4` TooLateToEnter, `5` UnknownOrder, `6` DuplicateOrder,
`7` DuplicateOfVerballyCommunicated, `8` StaleOrder, `9` TradeAlongRequired,
`10` InvalidInvestorId, `11` UnsupportedOrderCharacteristic, `12` SurveillanceOption,
`13` IncorrectQuantity, `14` IncorrectAllocatedQuantity, `15` UnknownAccount,
`99` Other.

**SessionRejectReason (373)** — `0` InvalidTagNumber, `1` RequiredTagMissing,
`2` TagNotDefinedForMessageType, `3` UndefinedTag, `4` TagSpecifiedWithoutValue,
`5` ValueIsIncorrect, `6` IncorrectDataFormat, `9` CompIdProblem,
`10` SendingTimeAccuracyProblem, `11` InvalidMsgType, `99` Other.

`FR-PRS-024`: The effective rejection reason for metrics is `ordRejReason` when tag 103 is
present, else the normalised `rejectReasonText` label, else `unspecified`. This precedence
MUST be implemented in one place and unit-tested.

## 7. Timestamps

`FR-PRS-025`: FIX timestamps (`YYYYMMDD-HH:MM:SS`, optionally `.sss` / `.ssssss`) MUST be
parsed as UTC. Failure yields reason `bad_timestamp` and the log line's read time is used
instead, with `timeSource=log`.

`FR-PRS-026`: If a FIX timestamp is more than `maxClockSkew` (default `5m`) away from agent
wall-clock time, the agent MUST use its own clock, count `parser.clock_skew_events`, and
raise the `ClockSkew` rule (spec 005). Trusting a badly skewed timestamp corrupts bucketing.

## 8. Sequence gap detection

`FR-PRS-027`: Per session (`senderCompId`/`targetCompId`/direction), the parser MUST track the
last seen `MsgSeqNum` and count gaps (`fix.seq_gap`, with gap size) and regressions
(`fix.seq_regression`). A `SequenceReset` (35=4) or `Logon` (35=A) resets the expectation
without counting a gap. Gaps indicate either genuine FIX resends or that the agent missed log
content — both are operationally interesting.

## 9. Parser plugin interface

`FR-PRS-030`: All parsers MUST satisfy one interface so Day-2 binary support requires no
pipeline change:

```go
// Parser converts one framed input unit into zero or more telemetry events.
// Implementations must be safe for concurrent use and must not retain the input slice.
type Parser interface {
    // Name is the value used in configuration (e.g. "fix", "magic-binary").
    Name() string

    // Classify reports whether this parser claims the input.
    Classify(line []byte) Confidence

    // Parse returns derived events. It must never return raw input content
    // inside an event, and must return a ParseError rather than panicking.
    Parse(line []byte, meta SourceMeta) ([]Event, error)
}
```

`FR-PRS-031`: Parsers are selected per file set by name in configuration, with an ordered
`parsers: [fix, applog]` chain; the first parser returning `ConfidenceHigh` wins.

`FR-PRS-032`: A parser MUST be registerable without modifying the pipeline, via a registry
populated at init time. Dynamic loading of parsers from user-supplied paths is prohibited
(no plugin `.so` loading), because it would allow arbitrary code execution on a trading host.

## 10. Test obligations

Each requirement in this spec MUST have at least one table-driven test case in the parser
corpus described in [012-testing-strategy.md](./012-testing-strategy.md) §3, including:
SOH and pipe delimiters, prefixed log lines, split messages, missing tags, unknown enums,
truncated lines, skewed clocks, sequence gaps, and a fuzz target over arbitrary bytes that
asserts no panic and no allocation blow-up.
