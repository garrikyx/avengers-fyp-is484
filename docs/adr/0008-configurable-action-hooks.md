# ADR 0008 — Day-2 configurable action hooks run allowlisted commands, never a shell

Status: Proposed · Date: 2026-10-16 · Deciders: TBD

## Context

Day-1 alerts have one push action: the signed HTTPS callback to Magic (spec 005 §3). On the
2026-10-16 call the sponsor asked for Day-2 hooks where "this event type should also be
configurable" and "the callback function should also be configurable". The example was a disk
full event running "a cleanup job which will clean up the disk space on system".

That example runs a program on a trading host in response to telemetry. Done carelessly, it
lets log content choose what is executed, and it puts the agent in a position to harm the
host it is meant only to observe (spec 000 §3.3).

Options considered:

1. Only HTTPS callbacks, so the cleanup job lives behind a webhook somewhere else.
2. Arbitrary shell commands in config.
3. Allowlisted executables with a fixed argv, no shell, and alert data on stdin.

## Decision

A rule names **actions** (spec 005 §5). An action is either:

- a `callback`, the existing dispatcher with another endpoint; or
- a `command`.

A `command`:

- is an **absolute path listed in `allowedCommands`**;
- runs with a **fixed argv** and **no shell**;
- receives the alert JSON (spec 005 §3.3) on **stdin only**;
- has a timeout;
- runs at most once per alert occurrence;
- defaults to `dryRun: true`.

## Rationale

- **Nothing from telemetry reaches an argument or a shell.** `matchedCondition`, signature
  labels and component names stay data, never code, so a crafted log line cannot become a
  command (`FR-CBK-015`).
- **The allowlist is the operator's decision, not the rule author's.** Adding a rule cannot
  introduce a new executable.
- **Once per occurrence, keyed by `alertId`.** A flapping or renotifying alert cannot run the
  cleanup again and again (`FR-CBK-016`).
- **Callbacks stay first-class.** Option 1 is still available for teams that would rather run
  remediation elsewhere.

## Consequences

- The agent account needs permission to run the listed commands. That is a deployment
  decision for UBS. Executables MUST be owned by an account the agent cannot write as.
- Remediation is best-effort: failures are counted and never change alert state
  (`FR-CBK-017`).
- Day-1 code does not implement this. The config keys are reserved in spec 010.
