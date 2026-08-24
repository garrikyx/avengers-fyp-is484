# 012 — Testing Strategy

Status: Draft · Owner: TBD · Last updated: 2026-07-31

Spec-driven development only works if requirements are traceable to tests.
`FR-TST-001`: Every `MUST` requirement in specs 002–010 MUST be covered by at least one
automated test, and the test MUST name the requirement ID in its name or a comment. A CI job
MUST report any requirement ID with no referencing test.

## 1. Test levels

| Level | Scope | Tooling |
| --- | --- | --- |
| Unit | Parser, aggregator, rule evaluation, config validation, query engine | `go test`, `pytest` |
| Property / fuzz | Parser robustness, bucket merge associativity | `testing/quick`, Go fuzzing, `hypothesis` |
| Contract | Agent payloads validate against `/contracts` schemas, and vice versa | Shared JSON Schema, `schemathesis` |
| Component | Agent against a fake log writer and a mock backend; backend against synthetic batches | `go test` + `httptest`, `pytest` + `httpx` |
| End-to-end | Real agent → real backend → query and NL answer | Docker Compose harness |
| Load | Throughput, CPU, RSS, latency targets | Synthetic FIX generator (§5) |
| Chaos | Rotation, truncation, backend outage, restart, slow callback endpoint | Scripted fault injection in the E2E harness |
| Security | Data-leak assertions, dependency scan, secret scan | Custom sentinel test (§4), `govulncheck`, `pip-audit`, `gitleaks` |

## 2. What must be tested, not merely reviewed

The failure modes with the worst consequences are not the obvious ones:

| Risk | Test |
| --- | --- |
| Sensitive data leaves the host | Sentinel corpus test, §4 |
| Rotation loses data | Rotation harness, §3.2 |
| Restart double-counts silently | Restart test asserting `restarted: true` marking and bounded duplication |
| Unbounded memory growth under a reject storm | 30-minute soak with RSS ceiling assertion |
| A zero is reported where data is missing | Query test asserting `null` vs `0` semantics (`FR-QRY-035`) |
| An alert flaps and pages repeatedly | Rule test with an oscillating input asserting one notification per occurrence plus `renotifyInterval` |
| The NL layer fabricates a number | Evaluation set asserting every numeric token in the answer appears in `data` (§6) |
| Config typo silently disables a rule | Config validation test asserting unknown keys fail startup |

## 3. FIX parser corpus

`FR-TST-002`: `agent/testdata/fix/` MUST contain a synthetic, hand-authored corpus. It MUST
NOT contain production data, ever, under any anonymisation claim.

Required cases:

- Clean order lifecycle: `D` → `8` New → `8` Trade (partial) → `8` Trade (full).
- Rejection paths: `8` Rejected with tag 103; with tag 58 only; with both; with neither.
- Cancel paths: `F` → `8` Canceled; `F` → `9` cancel reject.
- Session: `A` Logon, `0` Heartbeat, `5` Logout, `3` Reject with 373, `4` SequenceReset.
- Delimiters: SOH, `|`, `^A`, `;`, and a file that switches delimiter mid-stream (must lock and
  then report errors, not silently misparse).
- Framing: log-prefixed lines, trailing text after `10=`, message split over 2 and 5 lines,
  a 200 KiB line, a line with a lone `\r`, mixed CRLF/LF.
- Malformed: no `35`, tag without `=`, non-numeric tag, empty value, duplicated tag,
  binary garbage, valid UTF-8 with emoji, invalid UTF-8 bytes.
- Enums: unknown `35`, unknown `150`, unknown `103`.
- Timestamps: no fraction, millis, micros, invalid, 10-minute skew, DST boundary.
- Sequence: in-order, gap of 1, gap of 1000, regression, reset then continue.

`FR-TST-003`: A fuzz target MUST run over arbitrary bytes asserting no panic, no unbounded
allocation, and no emission of input bytes into any event field.

### 3.2 Log monitor harness

`FR-TST-004`: A test harness MUST simulate, on both Linux and Windows CI runners:

- append while reading; append during rotation
- rename-and-create rotation; copy-truncate rotation; compressed rotation (`.gz` appears)
- truncation to zero; truncation to a shorter length
- file deleted then recreated; file replaced by a symlink (must be refused per `NFR-SEC-015`)
- glob matching a new file mid-run; a file disappearing mid-run
- a line written in two `write()` calls with a delay across the newline
- permission removed mid-run then restored

Each case asserts exact line counts read, no duplicates beyond documented bounds, and the
expected `log.*` events.

## 4. Data-leak sentinel test

`FR-TST-005` (blocking gate): A test MUST build a FIX corpus in which every
**non-allowlisted** tag carries a unique sentinel string (e.g. `SENTINEL_TAG44_9c1f`), run the
full agent pipeline against it with a recording mock backend, mock callback endpoint, and a
temporary state directory, then assert that **no sentinel appears** in:

1. any request body sent to the backend,
2. any callback body,
3. the agent's own log output,
4. the agent state file,
5. `/metrics` output.

The test MUST also assert that allowlisted-but-hashed fields (`ClOrdID`, `OrderID`, `ExecID`)
never appear in plaintext, and that tag 58 text never appears in any form other than a
configured label or `unclassified`.

This single test is the practical enforcement of `NFR-SEC-001`, `NFR-SEC-002` and
`NFR-SEC-012`. It MUST fail the build.

## 5. Synthetic load generator

`FR-TST-006`: `tools/fixgen` MUST generate realistic FIX log traffic with controllable:
message rate, order/execution/reject mix, symbol cardinality, latency distribution,
malformed-line ratio, multi-line message ratio, burst patterns (reject storms), session
logon/logout, sequence gaps, and rotation cadence.

It is used for load tests, the E2E harness, demos, and the NL evaluation fixtures. It is the
only sanctioned source of test log data (`FR-TST-002`).

## 6. NL evaluation harness

`FR-TST-007`: At least 40 question fixtures with expected `intent` and expected slot values.
CI asserts intent accuracy ≥ 90% and exact slot match ≥ 80% (`FR-NLQ-025`).

`FR-TST-008`: For every fixture, every numeric token in the rendered answer MUST be present in
the structured `data` payload. A number in prose that is not in the data is a build failure —
this is the anti-fabrication gate.

`FR-TST-009`: The LLM MUST be mocked by default. The live-model job runs on a schedule, not on
every commit, and its failure MUST NOT block merges (it reports drift instead).

## 7. End-to-end acceptance scenario

`FR-TST-010`: One scripted scenario MUST cover the Day-1 acceptance definition
([spec 000 §7](./000-overview.md#7-day-1-acceptance-definition)) in a single run:

1. Start backend, agent, mock Magic callback receiver, and `fixgen`.
2. Generate 10 minutes of normal flow (compressed time where possible).
3. Inject a reject burst; assert `HighRejectRate` fires, the callback is received, signature
   verifies, and the alert appears in `GET /telemetry/alerts`.
4. Rotate the log mid-burst; assert no gap beyond `NFR-REL-002`.
5. Kill the backend for 2 minutes; assert alerting and callbacks continue and buffered data is
   published on recovery.
6. Restart the agent; assert resumption and `restarted: true` marking.
7. Stop the burst; assert the alert resolves after `resolveAfter` and a resolution callback
   arrives.
8. Ask the NL endpoint the rejection question; assert intent, slots, and that the numbers match
   a direct metrics query.
9. Assert the sentinel test's guarantees hold for the whole run.

## 8. CI gates

| Gate | Blocking |
| --- | --- |
| Unit + component tests, race detector on (`go test -race`) | yes |
| Contract tests (payloads vs `/contracts`) | yes |
| Data-leak sentinel test | yes |
| Config defaults golden-file diff (`NFR-CFG-004`) | yes |
| Lint (`golangci-lint`, `ruff`, `mypy --strict` on backend) | yes |
| Requirement-coverage report (IDs with no test) | yes |
| Dependency and secret scans | yes on high severity |
| E2E acceptance scenario | yes on main, nightly for branches |
| Load test with CPU/RSS/latency assertions | nightly, blocking on regression > 20% |
| Live-LLM NL evaluation | non-blocking, scheduled |

`FR-TST-011`: Coverage targets are meaningful only where they help: ≥ 85% on the parser,
aggregator and rule engine; no target elsewhere. Do not chase a global percentage.
