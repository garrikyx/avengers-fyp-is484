# Sponsor email — deployment and storage clarifications (Q-13)

Status: Draft · For: Avinash Gopal · From: Avengers FYP team · Date: 2026-09-27

---

**Subject:** Clarification on deployment target — local vs cloud, and database requirement

Hi Avinash,

Thank you for the guidance on the 23 September call regarding hosting and storage. We want to
align our implementation and sprint planning with UBS expectations before we invest further
in cloud deployment work.

**Our current design (for context)**

- The **Telemetry Agent** runs on the Magic host, reads logs locally, and sends only
  **derived metrics** (counters, histograms, allowlisted fields) to the backend — **raw log
  content is never stored or transmitted**.
- The **Telemetry Backend** currently uses an **in-memory store** with roughly 6–24 hours of
  derived metric and alert retention. We have not deployed MongoDB, Postgres, or Redis in the
  backend yet.

**Questions we'd like your help confirming**

1. **Production target:** Should the final/production deployment be a **local or on-prem
   server** (backend + optional local database), rather than public cloud?

2. **FYP vs production:** Is **public cloud acceptable only for FYP demo/midterm** (with
   simulator data), and **not** the intended production architecture?

3. **Database requirement:** Is the in-memory backend (6–24h retention) **sufficient for
   Day-1/FYP delivery**, or do you require a **local MongoDB or Postgres** for derived
   metrics and/or alert history in production?

4. **If a local DB is required:** Do you have a preference between **MongoDB and Postgres**,
   and what should be persisted (metrics, alert audit trail, agent heartbeat history)?

5. **Scope of "no cloud":** Does the restriction apply to **derived telemetry aggregates**
   (e.g. reject rates, session metrics), or only to raw/sensitive log content? (Our design
   already excludes raw logs.)

6. **Integration environment:** Will UBS provide a **local VM or server** for UAT/integration
   testing, or should we continue self-hosting until handover?

7. **High availability:** Is a **single backend server** acceptable initially, or is
   failover/multi-server HA expected within FYP scope?

**Our proposed alignment (pending your confirmation)**

| Environment | Backend | Storage |
| --- | --- | --- |
| FYP demo / midterm | Student cloud or local Docker (simulator data) | In-memory (current design) |
| Production / UAT | UBS local/on-prem server | In-memory, or local MongoDB/Postgres if you require persistence |

If this matches your expectations, we will prioritise integration and demo on a **local
production-shaped deployment** rather than a dedicated cloud-hosting sprint.

We also have several other open items (sanitised log samples, Magic callback endpoint,
Copilot/Teams auth) that we can cover in a follow-up if helpful.

Thanks again for your time and guidance.

Best regards,
Avengers FYP team
