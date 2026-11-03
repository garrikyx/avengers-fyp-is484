# UBS-120 — Notify Teams when an alert fires

Working notes. Requirement source: spec 000 §3.1 ("push notification of firing and
resolved alerts to a Teams chat"), spec 008 §6 POC scope, Q-10. UBS-100 left proactive
messages out of scope, so they are built here.

## Shape

```text
agent alert ─► POST /telemetry/batch ─► IngestionService ─┐
HeartbeatMonitor (AgentHeartbeatMissing) ─────────────────┤
                                                          ▼
                                   NotifyingAlertStore.merge()   (backend)
                                     status before → after
                                          │ transition?
                                          ▼
                                   AlertNotifier: dedupe alertId:kind,
                                   bounded queue, one sender task, retries
                                          │ POST /api/notify (Bearer token)
                                          ▼
                     Teams app: NotifyHandler → Adaptive Card →
                     adapter.continue_conversation(remembered chat)
```

- `NotifyingAlertStore` subclasses `AlertStore` and wraps `merge()`, the one path every
  alert takes, instead of changing the store (UBS-93/94 code is untouched).
- Transitions (`transition_kind`): `firing` when the alert becomes `firing` and was not
  already `firing`/`resolving`. `resolved` when it becomes `resolved` after `firing` or
  `resolving`. Renotifies, severity changes, a `resolving → firing` flap, the heartbeat
  monitor re-merging `firing` every tick, stale updates (FR-QRY-019), synthetic resolves
  and `pending → resolved` all post nothing.
- `merge()` runs on the event loop (ingestion) and in a worker thread (heartbeat
  monitor). The notifier hands off with `call_soon_threadsafe`, so `merge()` never
  blocks or raises because of Teams.
- The backend sends the `AlertRecord` (`telemetry_shared.models.notifications`), and the
  Teams app renders and escapes it. The backend has no Teams card format in it.
- The chat to post into is the first group chat the bot sees (`before_turn` hook, so the
  existing message handler is untouched), saved to `.teams-state/conversation.json`.
  `TEAMS_NOTIFY_CONVERSATION_ID` pins one chat, and `TEAMS_NOTIFY_ALLOW_PERSONAL`
  accepts a 1:1 chat for the local Agents Playground.
- In anonymous dev mode (`ANONYMOUS_ALLOWED`), the proactive send uses an anonymous
  identity. Otherwise the SDK asks Entra ID for a token with the dummy credentials and
  fails.

## Verified

- 48 unit/integration tests (`test_UBS_120_*`), including the real `/telemetry/batch`
  route through `create_app` and the heartbeat monitor through a worker thread.
- Live run with real processes: backend → bot → a fake Bot Connector. Firing and
  resolved cards arrived; the renotify posted nothing; before any chat was known the
  bot answered 409 and the backend logged and counted it.
- **Not verified:** a real Teams tenant. The bot itself (UBS-100) has only run against
  the Agents Playground.

## Known gaps

- **AgentHeartbeatMissing alerts only once per agent** (pre-existing, flagged as a bug
  for next sprint). `HeartbeatMonitor` uses one `alertId` per agent, and the store will
  not reopen a resolved `alertId`, so a second outage stays `resolved`. A strict `xfail`
  test (`test_a_second_outage_of_the_same_agent_posts_again`) marks it, and starts
  failing once the monitor rotates `alertId` per outage.
- Dedupe state is in memory. After a backend restart the store is empty too, so only new
  transitions post: no re-posting of old alerts, and no missed resolve cards for alerts
  that resolved while the backend was down.
- No per-channel rate limit or storm collapsing. A burst of N alerts posts N cards.
  That's fine for the POC chat; revisit before a real on-call channel.
- One chat for all alerts. No per-team routing, quiet hours or escalation (out of POC
  scope per Q-10).
