# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root. It is created lazily by `/domain-modeling`; until it exists, use the specs below as the vocabulary source.
- **`docs/specs/`**: the authoritative requirements, numbered by area. Read the ones that touch your work:
  `000-overview`, `001-architecture` (its §2 component table holds the canonical module names), `002-agent`,
  `003-fix-parsing`, `004-telemetry-data-model`, `005-alerting-and-callbacks`, `006-backend`, `007-api-contracts`,
  `008-nl-query`, `009-nfr-and-security`, `010-configuration`, `011-observability-and-runbooks`, `012-testing-strategy`.
  Requirement IDs (`FR-PUB-001`, `NFR-SEC-002`, …) are stable: cite them in issues, proposals and tests.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.
- `docs/plan/` holds working notes and story drafts. It's context, not authority; the specs win on conflict.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

Single-context repo:

```
/
├── GLOSSARY.md            ← created lazily
├── docs/
│   ├── adr/               ← 0001-agent-in-go.md … 0006-agent-in-python.md
│   └── specs/             ← 000-overview.md … 012-testing-strategy.md
├── apps/
└── packages/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `GLOSSARY.md`, or in `docs/specs/001-architecture.md` §2 until the glossary exists. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR and spec conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0005 (in-memory metric store), but worth reopening because…_

The same applies to a spec requirement: name its ID.

> _Contradicts FR-ING-006 (ingestion-side cardinality defence), but…_
