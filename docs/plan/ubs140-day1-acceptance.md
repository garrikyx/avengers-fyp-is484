# UBS-140 — Day-1 acceptance evidence

## What this ticket means

Magic writes logs on its host. The Telemetry Agent tails and parses those logs,
aggregates counters, evaluates rules and delivers callbacks locally. It publishes
only derived telemetry to the Telemetry Backend, where the metrics query API
answers questions. The simulator supplies synthetic Magic logs for development.

UBS-140 supplies repeatable evidence for spec 000 §7 **#1** (a reject burst becomes
queryable within five seconds) and **#4** (rotation, a five-minute backend outage,
and agent restart in one run). It is not a request for a new dashboard or a new
trading feature, and does not itself complete the other Day-1 acceptance criteria.

Existing UBS-114 exercises the assembled agent, UBS-115 snapshot ingestion,
UBS-104 outage isolation, and log-monitor tests rotation/recovery. Those separate
checks do not establish the combined behavior or timed log-to-query visibility.

## Run it

Python 3.14+ and the usual `uv` workspace dependencies are sufficient:

```sh
# Short integration checks:
make day1-acceptance-test

# Full-duration component scenario: 5,000 lines/s, 300-second outage,
# Day-1 profile's 1-second buckets and publication interval:
make day1-acceptance ACCEPTANCE_ARGS="--output /tmp/ubs140.json"

# Quick manual run with a shortened outage:
make day1-acceptance ACCEPTANCE_ARGS="--rate 100 --outage-seconds 3 --bucket-seconds 1"
```

Both checks run in one invocation. The runner returns **exit code 1** when findings
remain; unexpected harness errors also fail. JSON contains only
aggregate counts/timings, configuration and machine metadata. Synthetic log files
and offset state live in a temporary directory and are removed after the run.

## Scenario and measurements

`scripts/day1_acceptance.py` uses the existing simulator's FIX lifecycle and line
formatting functions, with 100% rejection for exact ground truth: each generated
order produces one order and one rejection line. It uses the real `build_agent` /
`run_agent`, publisher serialization/retry, backend ingestion worker, metric store,
and `POST /telemetry/query/metrics`. It does not inject prebuilt metric snapshots.

1. Establish readiness by observing a generated order through the query API.
2. Write three bursts, each containing at least one second's requested line volume.
   Measure from before the write to the query observing the whole burst, using a
   monotonic clock and a five-second deadline. A missed deadline is `null`, not 5s.
3. Start paced synthetic flow, rename/create the log during traffic, then make
   agent-to-backend requests fail for the requested outage duration. Count lines
   ingested and verify delivery of a newly triggered, HMAC-signed callback during
   the outage. This callback checks outage isolation, not HighRejectRate acceptance.
4. Restore connectivity, stop the writer, and compare both queried counters to
   exact generated totals before restart. Recovery has a bounded wait.
5. Resume writing through graceful agent shutdown/reconstruction, reusing the
   persisted offsets and the same agent ID. Measure resumed ingestion within 5s.
   Compare final API counts and inspect transmitted `restarted` flags.

`stream_lines_per_second` records achieved writer rates for the outage and restart
phases separately. `generated_bytes / generated_lines` gives mean UTF-8 line size.
Writer rate is not proof of parser throughput or CPU/RSS compliance (UBS-144).
The three initial bursts are batched writes, not a sustained-rate latency benchmark.

## Requirements decision and boundaries

- **Five-second visibility retained:** ADR 0010 resolves the former 10-second bucket
  conflict. Day-1 uses one-second wire buckets/publication and 100ms evaluation;
  backend canonical storage remains ten seconds. General library defaults remain
  compatible but do not claim the five-second target.
- **Outage duration:** spec 012 `FR-TST-010` step 5 says two minutes; spec 000 §7 #4
  and UBS-140 say five. The full runner uses the stricter five minutes. The short
  tests compress duration only; they do not establish five-minute buffer capacity.
- **Transport outage, not backend process destruction:** the component harness
  uses ASGI transport and rejects all agent requests while offline. Backend memory
  survives. Killing/recreating the backend would lose its historical in-memory
  store by ADR 0005 / `FR-QRY-005`; this harness does not claim to test that behavior,
  socket/TLS configuration, or a deployed multi-process system.
- **Restart, not crash:** the agent's full runtime is stopped and rebuilt in the
  same Python process using persisted offsets. Abrupt process termination and
  checkpoint-interval replay bounds still need a separate deployment-level test.
- Rename/create rotation is covered here; the full cross-platform rotation matrix
  in `FR-TST-004` remains the responsibility of the existing log-monitor suite.
- This slice does not claim full `FR-TST-010`, sentinel security acceptance,
  malformed-line `NFR-REL-001` coverage, or real Teams demonstration.

## Fixes made during UBS-140

- **Fixed during UBS-140:** at high load, shutdown could leave the log pump
  retrying a full line queue after parser workers stopped. `asyncio.run` then
  waited indefinitely for the pump thread, so the report never finished. The
  monitor adapter now observes the pump's stop signal between lines and enqueue
  retries. Unparsed offsets remain uncommitted (`FR-PIP-006`). A regression test
  stops a pump blocked on a full queue with no workers and checks that it exits
  without acknowledging or dropping the queued lines.
- Late data now republishes a complete higher-revision snapshot. Backend replacement
  is ordered by `(agentId, runId, bucketStartUtc, revision)`, so retries cannot double
  count and a restart in the same bucket cannot overwrite the prior run.
- Graceful shutdown drains queued parsing, exports the open bucket, publishes within
  the remaining grace, checkpoints only fully ingested source-order offsets, and
  marks restart-affected snapshots. Abrupt disconnected loss remains bounded and
  documented by FR-PUB-008 / ADR 0010.
- Reject storms no longer make the latency correlator scan an ever-growing pending
  order map on every line. Rejections are terminal, and expiry uses a bounded heap.
- Metric aggregation no longer scans its full retained ring on every event.

## Validation results (2026-11-14)

Initial smoke run on macOS ARM64 / Python 3.14.7, 100 lines/s, 3-second outage,
one-second buckets: three visibility trials at 1.039s, 1.005s and 1.004s; 299 lines
ingested during outage; one signed callback; one rotation event. Restart resumed
in 0.024s, but 331 generated orders yielded 323 queried orders and 322 rejections,
with zero restarted snapshots. This run failed acceptance as intended.

A separate 10-second-bucket smoke run missed **all three** five-second visibility
deadlines, despite 100ms evaluation and 1s publication. Rotation/recovery counts
matched before restart; final counts lost 10 of 419 orders/rejections. The short
3s outage fell between publish attempts in this profile, so it provided **no outage
isolation evidence**; the report correctly flags this rather than claiming success.

After the shutdown fix, pipeline unit tests, agent integration tests, UBS-114 and
UBS-140 reported **183 passed, 2 xfailed**. That run recovered exact pre-restart
counts; the expected failures were restart marking and final restart counts.
Earlier focused runs also exposed the intermittent pre-restart count failure.
The strengthened queue-cancellation regression was rerun separately and passed.
Repository Ruff lint/format checks and
`mypy apps packages scripts/day1_acceptance.py` passed (196 source files).
Graphify was unavailable, so source inspection was used and the graph was not
refreshed.

The final full **300-second outage** run completed successfully. Machine: macOS
26.6.2 ARM64, 10 logical CPUs, Python 3.14.7. Day-1 one-second buckets,
100ms evaluation and 1s publication:

| Measurement | Result |
| --- | --- |
| Generated lines / orders | 1,527,002 / 763,501 |
| Mean line size | 161.2 UTF-8 bytes |
| Achieved writer rate, outage / restart phases | 5,000.0 / 4,997.4 lines/s |
| Five-second burst trials | 3 of 3: 2.032s, 1.012s, 1.004s |
| Lines ingested during outage | 1,500,004 |
| Failed publish attempts / signed callbacks during outage | 149 / 1 |
| Observed rotation events | 1 |
| Order / rejection deficit before restart | 0 / 0 |
| Final queried orders / rejections | 763,501 / 763,501 |
| Restart resumption | 0.035s |
| Restart-marked snapshots | 4 |

The aggregate report is retained in [ubs140-acceptance-results.json](./ubs140-acceptance-results.json).
The runner reported no findings. It proves this UBS-140 slice under the stated
component-harness boundaries. Full Day-1 completion still depends on the other
spec 000 §7 criteria (sentinel security, real Teams path, HighRejectRate lifecycle,
and NL consistency), which are owned by their respective tickets/tests.
