# Pitch deck draft: two-minute animated pitch

Status: Draft for team review · Target runtime: 2:00 (about 270 spoken words)

Working title: **Magic, in plain words** Tagline: _Know what Magic is doing—before
anyone has to ask._

This is a storyboard. Each slide has voiceover, an on-screen visual and animation notes,
so it can go straight into Canva, Figma, After Effects or Lottie. Every number comes
from repo evidence (cited in the last section). Slide text uses sentence case.

## Pitch idea in one line

UBS traders and support teams can't see what Magic is doing during market hours without
digging through raw logs. We give them live answers in Teams, and no sensitive log data
ever leaves the host.

## Story arc

| #   | Time      | Beat         | Slide                           |
| --- | --------- | ------------ | ------------------------------- |
| 1   | 0:00–0:10 | Hook         | A rejected order at 09:31       |
| 2   | 0:10–0:25 | Problem      | Logs are sensitive and reactive |
| 3   | 0:25–0:40 | Solution     | Unified telemetry intelligence  |
| 4   | 0:40–1:00 | How it works | Agent → backend → Teams/Copilot |
| 5   | 1:00–1:15 | Trust        | Derived data only               |
| 6   | 1:15–1:35 | Demo moment  | Ask Teams a question            |
| 7   | 1:35–1:50 | Proof        | Day-1 acceptance numbers        |
| 8   | 1:50–2:00 | Close        | Roadmap and ask                 |

---

## Slide 1 — The 09:31 problem (0:00–0:10)

**Voiceover:** "It's 9:31. Markets are open. Orders are being rejected—and the first
person to notice is a client."

**On screen:** Dark trading-floor palette. Big clock reading 09:31. A red "REJECTED" tag
stamps onto a stream of green order lines.

**Animation:** Order lines scroll upward at speed. Clock ticks forward. Red stamp slams
in with a short screen shake. Everything else dims.

## Slide 2 — Why it's hard today (0:10–0:25)

**Voiceover:** "Today, finding out why means someone opens raw logs on a production
host. It's slow, it's reactive, and those logs hold client orders and FIX messages that
can't be copied anywhere."

**On screen:** Three problem chips: _Slow to spot_, _Reactive to fix_, _Too sensitive to
centralise_. Padlock over a log file.

**Animation:** Chips pop in one at a time on each spoken phrase. Padlock snaps shut over
the log file, which turns to static.

_(Spec 000 problems P-1 to P-5.)_

## Slide 3 — The idea (0:25–0:40)

**Voiceover:** "We built Unified Telemetry Intelligence for Magic. It reads the logs
where they live, turns them into live metrics and alerts, and lets anyone ask questions
in plain English."

**On screen:** Title card with tagline. Log file on the left, a clean dashboard-style
tile set on the right (orders, rejects, latency).

**Animation:** Log lines funnel through a narrow gate and come out the other side as
numbers that count up.

## Slide 4 — How it works (0:40–1:00)

**Voiceover:** "A lightweight agent sits beside Magic, parses FIX traffic and tracks
orders, rejections and latency in real time. It sends only counters to a central
backend. The backend runs the rules, fires alerts, and answers questions through
Microsoft Teams and Copilot."

**On screen:** Architecture flow, left to right: Magic → Telemetry agent → Telemetry
backend → Teams/Copilot. Ollama (local LLM) hangs under the backend as "natural language
fallback". A callback arrow loops from the agent back to Magic.

**Animation:** Draw the pipeline one node at a time, with glowing packets travelling
along each arrow. The callback arrow draws last in amber.

_(Reuse `docs/assets/architecture-overview.png` as the reference diagram; redraw it for
the animation.)_

## Slide 5 — Safe by design (1:00–1:15)

**Voiceover:** "Here's the part that matters to UBS. Raw logs and full FIX payloads
never leave the Magic host. Not stored, not sent. Only hashed, allowlisted, derived
numbers move."

**On screen:** Host boundary drawn as a dashed box. Inside: raw log, FIX payload (greyed
out, locked). Crossing the boundary: only small number badges. Label: _No raw log
persistence (ADR 0004)_.

**Animation:** A FIX message tries to cross the boundary and bounces off a shield. A
tiny counter badge passes straight through with a green tick.

## Slide 6 — Ask it anything (1:15–1:35)

**Voiceover:** "So when that reject spike hits, support doesn't dig. An alert lands in
Teams. They ask, 'Why are orders being rejected?' and get the top reasons, the trend and
the affected session in seconds."

**On screen:** Teams-style chat mockup. Alert card (firing, red), then a user question,
then a bot answer with a small bar chart of rejection reasons. Alert flips to _Resolved_
(green) at the end.

**Animation:** Typewriter effect for the question. Bars grow in on the answer. Alert
card colour transitions red → green.

_(Mock data only. The Day-1 demo uses synthetic simulator logs.)_

## Slide 7 — Proof it works (1:35–1:50)

**Voiceover:** "We tested it hard. Five thousand lines a second. Rejects visible in
about one second. A five-minute backend outage with zero lost orders, and a clean
restart that picks up exactly where it left off."

**On screen:** Four big stat tiles:

| Tile       | Value                   | Source                         |
| ---------- | ----------------------- | ------------------------------ |
| Visibility | ~1 s (target under 5 s) | `visibility_seconds` 1.0–2.0 s |
| Throughput | 5,000 lines/s           | 1.5M lines generated           |
| Outage     | 5 min, 0 orders lost    | `missing_orders: 0`            |
| Restart    | resumed in 0.04 s       | `restart_resume_seconds`       |

**Animation:** Tiles count up from zero. A thin timeline shows the outage as a grey gap
that fills back in after reconnect.

## Slide 8 — Close and ask (1:50–2:00)

**Voiceover:** "Day one is live monitoring. Day two adds history and end-of-day
reporting. We'd like to take this to a pilot on real Magic hosts."

**On screen:** Two-step roadmap (_Day 1: live now_ → _Day 2: history and reporting_).
Final line: tagline plus team name and UBS/SMU logos.

**Animation:** Roadmap arrow draws forward. Everything resolves to the tagline on a
clean background.

---

## Style notes for the animator

- Palette: dark navy background, green for healthy, red for rejects, amber for
  callbacks. Keep red and green distinct for accessibility (add icons, not colour
  alone).
- Pacing: one idea per slide, 10–20 seconds each, hard cuts on the beat of the
  voiceover.
- Keep on-screen text under 12 words per element. Voiceover carries the detail.
- If Autodesk branding applies to the final version, check it against the Autodesk brand
  skills before export. The current draft is project-neutral.

## Voiceover script (clean read, about 270 words)

> It's 9:31. Markets are open. Orders are being rejected—and the first person to notice
> is a client.
>
> Today, finding out why means someone opens raw logs on a production host. It's slow,
> it's reactive, and those logs hold client orders and FIX messages that can't be copied
> anywhere.
>
> We built Unified Telemetry Intelligence for Magic. It reads the logs where they live,
> turns them into live metrics and alerts, and lets anyone ask questions in plain
> English.
>
> A lightweight agent sits beside Magic, parses FIX traffic and tracks orders,
> rejections and latency in real time. It sends only counters to a central backend. The
> backend runs the rules, fires alerts, and answers questions through Microsoft Teams
> and Copilot.
>
> Here's the part that matters to UBS. Raw logs and full FIX payloads never leave the
> Magic host. Not stored, not sent. Only hashed, allowlisted, derived numbers move.
>
> So when that reject spike hits, support doesn't dig. An alert lands in Teams. They
> ask, "Why are orders being rejected?" and get the top reasons, the trend and the
> affected session in seconds.
>
> We tested it hard. Five thousand lines a second. Rejects visible in about one second.
> A five-minute backend outage with zero lost orders, and a clean restart that picks up
> exactly where it left off.
>
> Day one is live monitoring. Day two adds history and end-of-day reporting. We'd like
> to take this to a pilot on real Magic hosts.

## Evidence and caveats (check before presenting)

- **Problem and scope:** `docs/specs/000-overview.md` §1–3.
- **Raw data never leaves the host:** ADR 0004, spec 009.
- **MCP/Copilot:** ADR 0007 is _Accepted_ (sponsor confirmed MCP with Microsoft 365
  Copilot). The MCP server is built and tested, but it hasn't run in a Microsoft 365
  tenant; see `docs/plan/m365-copilot-integration-pack.md`.
- **Natural language layer is partial** (`implementation-status.md`, M6: 8 of 25
  `FR-NLQ-*` IDs cited by tests). The slide 6 demo should use scripted, working intents
  such as `reject_reason_trend`.
- **Numbers in slide 7** come from `docs/plan/ubs140-acceptance-results.json` (macOS
  ARM64, synthetic simulator, 1 s buckets). One of three visibility trials took 2.0 s,
  so "about one second" is typical, not guaranteed. Under 5 s is the requirement.
- **Outage test is a transport outage** with backend memory intact, and the restart is a
  graceful restart, not a crash (see `ubs140-day1-acceptance.md`, boundaries). Don't
  claim more than that.
- **Not yet done:** load and footprint test (UBS-144), data-leak sentinel test
  (UBS-137), operability hardening (M7). Be ready for Q&A on these.
- **Day-2 historical store:** technology not yet selected.
