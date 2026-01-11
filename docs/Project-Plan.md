# Vision (one line)

A modular, production-ready **wholesaling automation ecosystem** where an LLM-driven virtual agent handles lead intake and qualification, deterministic engines compute offers & scores, integrations enrich data and notify stakeholders, and humans own legal/negotiation decisions — built for multiple agents across the US and designed for parallel team delivery.

---

# High-level phases 

* **Phase 0 — Foundation & Platform** (infra, repos, auth, DB schema, dev environment)
* **Phase 1 — Basic Intake & Storage** (public intake, lead persistence, admin list)
* **Phase 2 — Conversation + LLM Contract** (chat flow, LLM prompt pack, extraction tests)
* **Phase 3 — Enrichment, Offer Engine & Scoring** (property APIs, ARV/offers, scoring)
* **Phase 4 — Notifications, Calendar & Buyer Flows** (SMS/email, calendar booking, buyer capture & blast)
* **Phase 5 — Admin Polishing & UX** (polished admin UI, editing, approval flows)
* **Phase 6 — Security, Compliance & Observability** (audit, opt-ins, monitoring, runbooks)
* **Phase 7 — Staging Handover & Production Launch Pack** (final artifacts, runbooks, docs, QA)

Each phase contains explicit per-team deliverables below.

---

# Team list & overall responsibilities

* **Frontend Team (React)** — public pages, chat widget, polished admin UI.
* **Backend/API Team (FastAPI)** — core REST/WebSocket API, DB models, auth, workers orchestration.
* **AI/Conversation Team** — prompt engineering, structured extraction JSON schema, LLM adapters, tests for LLM outputs.
* **Data/Enrichment Team** — property API connectors, normalization logic, seeding, enrichment worker.
* **Offer/Scoring Team** — deterministic offer formulas, scoring module, test cases.
* **Integrations Team** — Twilio, SendGrid, Calendly/Google Calendar, CRM connectors.
* **DevOps/Platform Team** — infra (IaC), Docker, CI/CD, secrets, monitoring, backups.
* **QA / Testing Team** — unit/integration/e2e & security tests, test data, acceptance testing.
* **Legal/Compliance (advisor)** — review templates, opt-in phrasing, advertising language, state-specific rules (especially Maryland flagging).

---

# Phase 0 — Foundation & Platform

Goal: create the shared platform teams will build on and the contracts that enable parallel work.

### Deliverables (who → what)

**DevOps**

* Repos created (mono-repo or per-service) with branch policy & code owners.
* Docker Compose dev skeleton (Postgres, Redis, FastAPI, React stub).
* IaC skeleton (Terraform modules placeholders; non-production defaults).
* Secrets management pattern doc (which store, secret names).
* CI pipeline templates (GitHub Actions) for linting, unit tests, build.

**Backend**

* Postgres schema DDL (core tables) and Alembic migration templates (seed to run).
* OpenAPI placeholder (base `/api/v1`) and API versioning policy doc.
* Auth & RBAC contract (JWT claims, roles: admin/agent/bot).

**Frontend**

* React project skeleton (Vite/CRA) with component library choice documented.
* Shared UI style tokens & design system stub.

**QA**

* Seed data CSVs and `seed_leads.py` script (sample leads across many cases).

**Deliverable artifacts**

* Repo links + branch policy doc
* Docker Compose file
* Alembic migration files
* OpenAPI base spec (YAML)
* Seed scripts & sample data

**Acceptance criteria**

* Developers can `docker-compose up` and run a dev stack with DB/Redis and basic endpoints returning 200.
* OpenAPI visible at `/docs` with auth endpoints present.

---

# Phase 1 — Basic Intake & Storage

Goal: accept leads from web form and persist leads; admin list to view persisted leads.

### Deliverables

**Frontend**

* Public landing page + simple “Get cash offer” form (address, phone, email, quick condition).
* Chat widget placeholder that POSTs messages to conversation endpoint (UI only, no LLM).
* Admin lead list page (table with filters: status, source, assigned_to).

**Backend**

* `POST /api/v1/leads` endpoint; validation; returns `lead_id`.
* Lead model, CRUD endpoints: `GET /api/v1/leads`, `GET /api/v1/leads/{id}`.
* Conversation table created; store initial messages.
* Basic business rules: address normalization module interface (contract only; returns normalized address, lat/lon or null).

**DevOps**

* Test DB seeds auto-run in CI for integration tests.

**QA**

* Test cases for lead creation + missing fields + invalid address handling.

**Deliverable artifacts**

* OpenAPI updated with lead endpoints.
* Frontend and backend test stubs demonstrating integration via mocked backend.

**Acceptance criteria**

* Web intake successfully creates lead rows in DB with normalized address field (when resolvable).
* Admin lead list shows leads and basic metadata.

---

# Phase 2 — Conversation + LLM Contract

Goal: implement conversation loop, LLM integration contract (strict JSON), and safety rules.

### Deliverables

**AI/Conversation**

* LLM prompt pack with:

  * System prompts (role, guardrails)
  * Conversation templates (10+ variations)
  * JSON schema for `extracted` fields (address, asking_price, contact, condition, timeline, photos_flag, etc.)
  * Validation tests: unit tests asserting LLM outputs conform to schema (use recorded outputs or provider sandbox).
* LLM Adapter module: abstract interface (e.g., `llm_client.call(prompt, schema)`) with mock implementation for dev.

**Backend**

* `POST /api/v1/conversations/{lead_id}/message` endpoint integrating with LLM adapter.
* Server-side validator for LLM JSON; fallback flows when extraction incomplete.
* Conversation transcript storage with `raw_prompt`, `raw_response`, `extracted_json` fields.

**Frontend**

* Chat widget wired to conversation endpoint; shows bot messages and can upload photos (upload stored to S3 stub).

**QA**

* Contract tests to ensure LLM responses pass JSON schema validation.
* Edge-case tests for hallucinations: ensure fallback when required fields null.

**Deliverables**

* `ai/prompts/` folder + `ai/schema.json`
* Conversation API implemented + tests
* Frontend chat showing LLM-driven bot_message

**Acceptance criteria**

* For 90% of common test utterances, LLM extraction gives valid JSON; otherwise backend flags missing fields and prompts user for clarification.
* All conversation records are stored with raw prompt/response for audit.

---

# Phase 3 — Enrichment, Offer Engine & Scoring

Goal: connect to real property data, calculate ARV/offer ranges, and compute lead score.

### Deliverables

**Data/Enrichment**

* Adapter layer for property providers (abstract class + implementations for at least one real provider).
* Normalize provider outputs into `properties` table schema.
* Enrichment worker that can be triggered per-lead and writes ARV & comps.

**Offer/Scoring**

* Offer engine module with:

  * ARV calculation algorithm (configurable weights).
  * Repair estimate mapping from `condition`.
  * `compute_offer(lead_id)` returns `{arv, repair_estimate, offer_min, offer_max, confidence, engine_version}`.
* Scoring service `compute_score(lead_id)` returns `{score, breakdown}`.

**Backend**

* `POST /api/v1/leads/{lead_id}/enrich` (trigger) & `GET /api/v1/leads/{lead_id}/offer` & `GET /api/v1/leads/{lead_id}/score`.

**Frontend**

* Lead detail page displays:

  * Enriched property data (map, comps, last sale)
  * Offer draft + confidence + breakdown
  * Score + breakdown UI

**QA**

* Unit tests for offer math with varied ARV/condition inputs.
* Integration tests mocking provider responses to ensure stable behavior.

**Deliverables**

* Provider adapter code & config (provider key placeholders)
* `offer_engine.py` and `scoring.py` with test coverage
* Admin UI showing offer & score

**Acceptance criteria**

* Offer engine returns deterministic values for seed data; confidence reflects data completeness.
* Enrichment populates at least 3 property attributes for supported addresses.

---

# Phase 4 — Notifications, Calendar & Buyer Flows

Goal: enable outreach (SMS/email), scheduling, and buyer management + deal blasting.

### Deliverables

**Integrations Team**

* Twilio adapter: send/receive SMS webhook contract; opt-in recording.
* SendGrid adapter: templated emails engine with substitution variables.
* Calendar adapter: Calendly webhook integration or Google Calendar API adapter (bookings create calendar events).
* Rate limiting & throttling logic for blasts.

**Backend**

* `POST /api/v1/followups` to schedule follow-ups; worker executes sends.
* `POST /api/v1/buyers` create buyer profiles & `GET /api/v1/deals/{deal_id}/blast`.
* Match engine (basic) that finds buyers whose criteria intersect deal range & markets.

**Frontend**

* Admin pages:

  * Follow-up workflow builder (simple templates + triggers)
  * Buyer capture form & buyer list UI
  * Deal blast UI: preview & send with throttling controls

**QA**

* Tests for SMS webhook handling, opt-in/out flows.
* End-to-end test: intake → offer → blast sent to matching buyer (mocked).

**Deliverables**

* SMS/email templates (initial set)
* Blast worker with logs & retry mechanism
* Buyer UI + matching logic

**Acceptance criteria**

* Outbound SMS/email sent & logged per follow-up; opt-out results in no further sends.
* Deal blast does not exceed configured throttle limits; matching returns expected buyer lists.

---

# Phase 5 — Admin Polishing & UX

Goal: deliver a polished admin interface with editing, approvals, and human-in-the-loop controls.

### Deliverables

**Frontend**

* Polished admin dashboard:

  * KPIs (leads/day, hot leads, offer sent)
  * Lead detail with edit-in-place for extracted fields
  * Offer approval modal with ‘approve’, ‘reject’, ‘request more info’ actions
  * Human takeover chat option (escalate conversation)
  * Role-based UI (admin vs agent views)

**Backend**

* Endpoints: `POST /api/v1/leads/{lead_id}/approve_offer`, `POST /api/v1/conversations/{lead_id}/takeover`.
* Audit trail for approvals (user_id, timestamp, before/after values).
* Templates storage for SMS/email & admin edit history.

**QA**

* UX acceptance tests (manual checklist + automated e2e where possible).
* Accessibility checks (basic).

**Deliverables**

* Polished UI with deployable frontend build
* Audit & action logs in DB

**Acceptance criteria**

* Admin can approve an offer in <3 clicks; approval recorded in audit log and triggers configured follow-up actions.
* Agents see only assigned leads and cannot access admin settings.

---

# Phase 6 — Security, Compliance & Observability

Goal: make the system secure, auditable, and observable for production use.

### Deliverables

**DevOps / Security**

* HTTPS enforced; HSTS settings in infra config.
* Secrets rotated and stored in secrets manager.
* DB encryption for PII fields (document which fields + encryption scheme).
* Rate limiting & bot protections.
* TCPA compliance pattern & opt-in storage logic (DB schema change to store consent).
* Sentry / Prometheus / Grafana configured with key dashboards (errors, queues, LLM usage).

**QA**

* SAST scan report (bandit, dependency-check).
* Pen-test checklist for external infra.

**Legal**

* Reviewed opt-in/opt-out texts for SMS & email; list of flagged phrases requiring legal review.

**Deliverables**

* Security checklist completed & signed off
* Monitoring dashboards & alerting runbooks
* Data retention policy doc

**Acceptance criteria**

* No high-severity SAST findings unresolved.
* SMS sends are only executed if opt-in present.
* Alerts configured for queue backlogs and LLM error spikes.

---

# Phase 7 — Staging Handover & Production Launch Pack

Goal: provide everything operations & product teams need to run, monitor, and extend the system.

