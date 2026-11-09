# Mate master product and engineering roadmap

**Status:** planning baseline — no product features implemented by this document.

**Companion requirement:** [`phase-1-daywork-record-mvp.md`](phase-1-daywork-record-mvp.md) remains the authoritative description of the first product wedge. This roadmap translates it into a sequenced, buildable plan; it does not replace it.

## 1. Executive product strategy

Mate will be a **site evidence and daywork record app for UK subcontractors**.

Its core unit is a persistent **SiteRecord**:

```text
Company -> Project -> SiteRecord -> Evidence
                         \-> Versions / audit events
```

The primary user is a working foreman. The commercial buyer is a subcontractor owner, commercial manager, or QS. The product must let a foreman create a credible, reviewed record in under two minutes, using voice where it reduces typing.

AI is an input and structuring service. It can produce a draft and ask concise follow-up questions; it is never the system of record and never confirms a fact the user did not record. The saved record is the user's reviewed submission.

The initial commercial job is not generic paperwork automation or legal advice. It is to preserve a factual, project-linked evidence trail for progress, extra work, instructions, delays, labour, plant and materials.

## 2. Current-state assessment (Phase 0)

### Already built

| Area | Current implementation |
| --- | --- |
| Application | Single Flask app in `app.py`, with three registered blueprints: `site_report`, `construction_assistant`, and older `doc_qa`. |
| Frontend | Server-rendered Jinja templates; shared light/navy CSS tokens in `static/style.css`; individual tools contain substantial inline CSS and JavaScript. |
| Site reporting | Voice via the browser Web Speech API or text; optional single base64 image held in memory; Anthropic produces a free-form, print-oriented report. |
| Construction assistant | Session-selected conversation; SQLAlchemy `Conversation`, `Message`, and `Document`; PDF extraction with PyMuPDF; Chroma retrieval; page-labelled citations when relevant. |
| Document Q&A | Separate older PDF Q&A blueprint using pypdf and the same shared Chroma collection. It is registered but not linked from the home page. |
| Database | Flask-SQLAlchemy; `DATABASE_URL` uses Postgres if supplied, otherwise a local SQLite `mate.db`; tables are created with `db.create_all()`. |
| AI | Anthropic Python SDK, currently instantiated per blueprint; model ID is hard-coded as `claude-haiku-4-5-20251001`. |
| File handling | PDFs are saved under `instance/uploads/<original filename>`; site-report images remain base64 in request/render context. |
| Deployment | Railway-oriented `Procfile`: Gunicorn binds to port 8080. Local Flask port is configured as 5001 in the untracked `.flaskenv`. |

### Needs building

- Product accounts, companies, membership, roles, project access, and tenant isolation.
- Persistent structured SiteRecords, evidence, review/save workflow, and record history.
- Database migrations, fixtures, test suite, CI, error monitoring, and production operations.
- Secure object storage and safe upload lifecycle.
- Schema-validated AI drafting and a manual fallback path.
- Professional server-generated PDFs; the existing browser print layout is not an archival/reporting system.
- Authentication, CSRF protection, authorisation checks, rate/usage limits, and safe error handling.
- Offline-aware draft handling and later background synchronisation.

### Current data model

`Document` may optionally belong to a `Conversation`. `Conversation` has many `Message` records and an optional summary. There is no `User`, `Company`, `Project`, `SiteRecord`, evidence object, ownership column, role, audit event, or SiteRecord status.

### Current technical debt and constraints

- `db.create_all()` cannot safely evolve a production schema; migrations are required before persistent customer data.
- The app has no authentication: all database records and Chroma data are effectively shared by whoever can access the deployment.
- Original filenames are used for filesystem paths; files can collide, persist indefinitely, and have no tenant boundary or deletion flow.
- `doc_qa` lists all documents and has no access controls; it should be removed from production navigation/registration or rebuilt as project-scoped document Q&A.
- Chroma uses a local persistent directory. This is unsuitable as the authoritative production store and is not isolated by company/project.
- Anthropic calls lack central configuration, timeout/retry/backoff, usage accounting, model fallback, and graceful service failure handling.
- The site-report relevance check makes an extra AI request before generating a report, increasing cost and failure points.
- User input is accessed with required form keys and several external calls are uncaught; failures can result in raw 500 responses.
- Existing templates render generated HTML with `|safe` in chat. Markdown output must be sanitised before this can be relied on with real users.
- PDF upload limits, MIME/content validation, malware scanning policy, filename normalisation, deletion, retention, and encryption strategy are absent.
- Requirements are a full environment freeze, including many transitive dependencies; there is no declared supported Python version, lock strategy, linting, formatting or automated test tooling.
- The README says local port 5000 and `python app.py`, while `.flaskenv` specifies port 5001. Documentation should be corrected as part of developer-experience hardening.

## 3. Target architecture

Keep Flask and server-rendered Jinja for the first commercial MVP. A rewrite to a separate SPA/API is not justified: it would delay the evidence workflow without improving its core value. Introduce clear service and repository boundaries inside the Flask monolith so a future API/mobile client can reuse them.

```text
Browser / installable web app
  -> Flask routes + server-rendered views / JSON endpoints
      -> authentication + CSRF + authorisation policy
      -> application services
          -> Postgres (authoritative relational data)
          -> object storage (private original evidence and generated PDFs)
          -> AI extraction service (drafts only)
          -> asynchronous job worker (PDFs, thumbnails, indexing, retries)
          -> optional project-scoped vector store (later document Q&A)
```

### Architectural decisions

- **Database:** Postgres in production; SQLite remains local-development only. Use Alembic/Flask-Migrate migrations from the first new persistent model.
- **Storage:** private S3-compatible object storage, with generated object keys. Railway/container disk must not store customer evidence or generated PDFs.
- **App boundary:** route handlers validate requests and enforce access; services perform business work; models/repositories persist data. Do not put AI prompts, storage calls, and access decisions directly in routes.
- **Asynchronous work:** introduce a worker and queue when PDF generation, image processing, uploads, or AI retries could exceed a normal web request. The initial manual record path must still work synchronously with no AI.
- **AI output:** constrain to a versioned JSON schema, validate server-side, retain raw input/draft separately, and only promote user-confirmed values into the SiteRecord version.
- **Observability:** structured logs with request IDs and no sensitive record content; error monitoring; health checks; metrics for saves, failures, latency and AI spend.

## 4. Product phases

### Phase 0 — current repository and technical baseline

**Objective:** document the prototype accurately and make decisions before adding customer data.

**User value:** avoids building a product on assumptions or exposing shared prototype data to pilots.

**Features / technical work:** inventory the current code, lock the product wedge, add the master roadmap, decide environments and supported Python version, and establish a migration/testing baseline before schema work.

**Data/API/frontend/AI:** no feature data model or UI changes; the present AI/report tools remain prototypes.

**Security:** do not invite real companies while the prototype has no authentication or tenant isolation.

**Testing:** add a test harness before the next phase; initially, an app factory/configurable test database and smoke tests for app creation/routes.

**Acceptance criteria / Definition of Done:** this document is approved; Phase 1 brief is retained; the team has chosen auth, storage, job queue and monitoring approaches; a test command and migration command are documented.

**Dependencies:** none. **Risk:** attempting a redesign before validating the foreman workflow. **Blocking dependency:** human approval of product and technical choices below.

### Phase 1 — product foundation and experience specification

**Objective:** make the existing Phase 1 brief the build contract for the first valuable workflow.

**User value:** a focused app rather than a menu of AI demos.

**Authoritative requirements:** use `phase-1-daywork-record-mvp.md` for the user, buyer, scope, fields, flows, trust principles, roles, success measures and pilot acceptance criteria.

**Clarifications still required:**

- Decide whether a “project” has one named site in MVP or needs a separate Site entity. Recommendation: store `site_name` on Project initially; do not create a Site table unless a company genuinely has multi-site projects.
- Agree the precise initial field labels with 2–3 working foremen before coding.
- Agree the first supported browser/device set and the acceptable no-signal behaviour.
- Decide the brand/logo and PDF identity requirements before PDF design.

**Deliberate sequencing adjustment:** the companion brief lists `Sent`, `Signed off`, and `Disputed` as intended statuses. For the first usable MVP, implement only `Draft` and `Saved`. `Sent` needs delivery tracking; `Signed off` needs an approval model; `Disputed` needs an owner and resolution process. Premature statuses would imply a workflow Mate cannot yet evidence. They remain later Phase 11 work.

**Acceptance criteria / Definition of Done:** the open clarification decisions are approved and translated into field-level acceptance tests. No code feature is required for this planning phase.

**Dependencies:** Phase 0. **Risk:** fields become office-centric and slow the foreman. **Blocking dependency:** target-user review.

### Phase 2 — accounts, companies and projects

**Objective:** create the minimum multi-tenant product foundation.

**User value:** a user sees only their company's projects and can return to their work securely.

**Features:** sign-up/sign-in, password reset/verification as appropriate to chosen provider, company creation, invite/member flow, projects, active/inactive projects, and simple role management.

**Data model:**

- `User`: UUID, email (unique/canonical), display name, password/provider identity, verified state, created/updated/last-login timestamps.
- `Company`: UUID, name, slug/reference, timezone, branding fields added later, created timestamps.
- `CompanyMembership`: company, user, role (`owner`, `manager`, `foreman`), invited/active state, timestamps; unique company/user pair.
- `Project`: UUID, company, name, site_name, reference, active flag, created/updated timestamps.
- `ProjectMembership`: project, company membership; optional in MVP only if not every company member should see every project. Otherwise use company membership plus a future project assignment table.

**Roles:**

| Capability | Owner | Manager | Foreman |
| --- | --- | --- | --- |
| Manage company, members and billing | Yes | No | No |
| Create/archive projects | Yes | Yes | No |
| View project records | All company projects | Assigned/all permitted projects | Assigned projects |
| Create records | Yes | Yes | Yes |
| Edit saved records | Yes | Yes | Own records only in MVP |
| Change later commercial statuses | Yes | Yes | No |
| Export records | Yes | Yes | Own/assigned records |

**API/backend:** central `current_user`, company/project loader and policy helpers; every route/service takes a scoped company/project or record object, never an untrusted raw ID alone. Use UUID public IDs.

**Frontend:** uncomplicated sign-in, company onboarding, project list, create-project flow, member/error/empty states.

**AI:** none.

**Security:** use mature session authentication, secure password hashing or managed identity, HttpOnly/Secure/SameSite cookies, CSRF tokens for every state-changing browser request, login throttling, generic account-recovery responses, and mandatory tenant-scoped queries.

**Testing:** authentication, role matrix, cross-company and cross-project denial tests, invitation lifecycle, validation and migration tests.

**Acceptance criteria / Definition of Done:** a foreman at Company A cannot enumerate, read, upload to, edit, or export Company B data by changing a URL/ID; owner and manager permissions behave as documented; production migrations run cleanly.

**Dependencies:** Phase 0–1; auth/storage provider decisions. **Can run in parallel:** core models and UI shells after schema design. **Risk:** role complexity; retain only three roles.

### Phase 3 — SiteRecord data model and persistence

**Objective:** establish SiteRecord as the durable product core before AI convenience features.

**User value:** records can be manually created, saved, reopened and trusted even during an AI outage.

**Features:** manual structured record creation/edit, Draft and Saved statuses, generated record number at first save, project history list.

**Data model:**

- `SiteRecord`: UUID/public ID, company ID, project ID, record_number, record_date, record_type (`daily`, `daywork_variation`, `delay_blocker`), status (`draft`, `saved`), created_by, reviewed_by, reviewed_at, created/updated/saved timestamps, source account, schema version.
- Normalised child rows: `LabourEntry` (trade, headcount, hours), `PlantEntry` (description, quantity, hours), `MaterialEntry` (description, quantity, unit, delivery/reference), `Instruction` (description, source name/company, method, reference), `DelayBlocker` (description, start/end/ongoing, impact, notified party), `SafetyObservation`, `NextAction`.
- `RecordFieldState` or JSON field metadata: value plus provenance (`user_stated`, `user_confirmed`, `not_recorded`) and draft source. Use a validated JSON column only for flexible draft/extraction metadata, not the authoritative searchable commercial facts.
- `SiteRecordVersion`: immutable snapshot JSON, version number, changed_by, reason, created timestamp. Create on first save and each post-save edit.
- `AuditEvent`: company, actor, action, target type/id, timestamp, safe metadata (not full sensitive content).

**Validation:** record date cannot be unreasonably future-dated without confirmation; hours/headcount/quantities are non-negative and bounded; statuses allow only `draft -> saved` in MVP; record number unique per company; server owns company/project/author fields.

**API/backend:** service methods `create_draft`, `update_draft`, `save_record`, `get_record_for_actor`, `list_records_for_project`; transactional save and record-number allocation; immutable audit/version append.

**Frontend:** fast mobile manual form, draft indicator, explicit `Save record`, saved confirmation, recent-record list with date/type/status filters.

**AI:** none required; retain original free-form account as optional source context only.

**Security:** every child record must inherit the SiteRecord's company/project scope; never accept parent IDs from the client without authorisation.

**Testing:** model validation, save state transition, concurrent record-number allocation, role rules, transactional rollback, record/version integrity, cross-tenant negative cases.

**Acceptance criteria / Definition of Done:** a foreman can save a complete manual record and see it after a new session; the saved version and author/time are recoverable; no external company can access it.

**Dependencies:** Phase 2. **Can run in parallel:** manual capture UI and PDF template prototyping against fixtures. **Risk:** over-normalising early; use child rows for repeatable resources and structured metadata for draft-only flexibility.

### Phase 4 — voice/text capture and AI extraction

**Objective:** make structured drafting quicker than manual entry while preserving factual discipline.

**User value:** foreman speaks naturally; Mate prepares a reviewable record and asks only material follow-ups.

**Features:** editable browser speech transcription; typed input; `Create AI draft`; extraction draft; concise missing-information questions; manual continuation if voice or AI fails.

**AI pipeline:**

```text
raw voice/text -> editable account -> extraction request -> JSON schema validation
-> draft fields + provenance + uncertainty/missing list -> conditional questions
-> user review/edit -> SiteRecord save
```

**Input and schema:** version an `SiteRecordExtractionV1` JSON schema. It contains only observed/stated values, `not_recorded` fields, potential record type, evidence references supplied by the user, and a bounded `follow_up_questions` list. It must reject unknown fields and include no contractual conclusions.

**Rules:** AI must never create labour, hours, materials, plant, dates, people, instructions, references, weather or events. If absent, use `not_recorded`; do not use probability as a fact. AI may label a phrase as “may indicate additional work” for user review, not as a confirmed variation.

**Validation and uncertainty:** validate JSON server-side with Pydantic/JSON Schema; reject/repair malformed output once; display ambiguous values as “Needs confirmation” rather than silently accepting them. Store raw model output only in protected diagnostic/audit data with a retention policy.

**Retries/fallback:** one bounded schema-repair retry; retry transient provider/network failures with exponential backoff and jitter; timeout quickly enough for a site user; show “Drafting is unavailable — continue manually” after final failure. Do not retry non-transient validation or quota errors blindly.

**Cost controls:** one extraction request per explicit user action; debounce/cancel duplicated requests; max input/image count and token size; per-company daily/monthly allowance checked before call; record model, tokens/cost estimate and outcome; configurable model IDs and fallback chain in environment/config.

**API/backend:** dedicated AI service, request idempotency key, asynchronous job if the request exceeds web timeout, status endpoint for pending draft, no model calls in Jinja routes.

**Frontend:** capture/review transition, microphone unsupported state, pending/cancel/retry states, clear distinction among “recorded”, “needs confirmation”, and “not recorded”.

**Security:** never log raw record account or images in provider/error logs; disclose approved AI processor in privacy material; verify provider data-use configuration before live data.

**Testing:** fixture-based extraction contract tests (including hallucination traps), schema tests, malformed response/retry tests, quota tests, manual-fallback E2E test, prompt-injection test text treated solely as record content.

**Acceptance criteria / Definition of Done:** a valid draft is schema-conformant; a missing hour is displayed as not recorded rather than guessed; an AI outage still permits saving a manual record; usage limits prevent the provider call.

**Dependencies:** Phase 3, security baseline, approved data/AI policy. **Can run in parallel:** voice UI and extraction fixture/evaluation suite. **Risk:** prompt quality being mistaken for correctness; schema plus review is mandatory.

### Phase 5 — evidence and photographs

**Objective:** attach reliable, permissioned evidence to SiteRecords.

**User value:** photos remain connected to the event, project and explanation rather than disappearing into a camera roll/WhatsApp thread.

**Features:** multiple image capture/upload, optional user captions, thumbnail/previews, remove-before-save, evidence list on saved record.

**Data model:** `EvidenceItem`: UUID, company/project/record IDs, storage key, original filename (display only), content type, byte size, SHA-256 checksum, captured_at if supplied, uploaded_by/uploaded_at, caption, state (`pending`, `available`, `failed`, `deleted`), deletion timestamps. Evidence belongs to exactly one record in MVP.

**Technical/API work:** use generated storage keys such as `companies/<company-uuid>/projects/<project-uuid>/records/<record-uuid>/<evidence-uuid>`; allow-list JPEG/PNG/HEIC only if processing supports it; inspect bytes/MIME rather than extension; strip or preserve EXIF only after privacy decision; generate thumbnails asynchronously; direct-to-object-storage signed uploads where appropriate.

**Limits:** start with a conservative configurable limit, for example ten images/record and 10 MB/image after compression. The final figures require test-device and cost validation. Reject animated/image formats not needed by the workflow.

**Failure/deletion:** show per-file progress and retry; do not mark record evidence available until storage confirms it; soft-delete user-visible evidence with audit event, then asynchronously remove object after retention window. Prevent deletion of evidence from a later locked/signed workflow when introduced.

**Frontend:** camera-first input, large buttons, upload/pending/error states, accessible captions and remove controls.

**AI:** photos may be referenced in drafting only as supplementary user-supplied evidence; do not automatically manufacture visible observations. Any future vision observation is a clearly labelled suggestion requiring confirmation.

**Security/testing:** private buckets only, short-lived signed URLs, server authorisation before issuing URL, image parser security checks, upload size/type tests, cross-tenant signed-URL denial, failed/retry/deletion tests.

**Acceptance criteria / Definition of Done:** an authorised user can add evidence that is visible only through their scoped record; a failed upload cannot look saved; deleting evidence removes access and creates an audit event.

**Dependencies:** Phase 2–3 and object-storage decision. **Risk:** storage cost/privacy and unreliable mobile networks.

### Phase 6 — review-before-save experience

**Objective:** make the user's review the meaningful trust boundary.

**User value:** they can correct Mate quickly and confidently before creating a business record.

**Features:** grouped editable review form, add/remove resource rows, evidence attachment, record completeness display, explicit confirmation and save.

**Frontend:** show three visually distinct states: **Recorded fact** (user supplied/confirmed), **Needs confirmation** (AI extracted ambiguity), and **Not recorded**. Never present speculative text as a field value. Retain the original account as supporting context behind a disclosure, not as the final report body. Use 44px targets, keyboard/focus support, one clear primary action and in-app confirmations.

**Backend/data:** save only reviewed field values to authoritative SiteRecord child entities; retain draft metadata/source account separately; create an immutable version/audit event at save; use optimistic locking/version number so an old browser tab cannot overwrite a newer edit silently.

**AI:** follow-up question generation is bounded to genuinely material missing fields based on record type; user may skip with `Not recorded`.

**Security/testing:** server repeats all field validation; verify edit ownership and optimistic-lock conflict handling; accessibility/E2E tests on narrow viewport; AI error/manual review tests.

**Acceptance criteria / Definition of Done:** user can remove an incorrect AI extraction, add missing facts and save a version whose visible PDF/data exactly matches reviewed values.

**Dependencies:** Phase 3–5. **Risk:** too many follow-up questions; test real foreman completion time.

### Phase 7 — professional PDF and reporting

**Objective:** produce a consistent, trustworthy Site Record PDF from saved data.

**User value:** office staff can share a professional snapshot without editing AI prose.

**Features:** on-demand PDF export from a saved version; company branding; project/site/record number/date; reviewed-by/created-by/timestamps; structured work/resources/instructions/delay/safety/next-action sections; evidence photos/captions; factual disclaimer; version reference.

**Technical/API:** render from immutable saved-version data, not current browser form or model output. Use a server-side HTML-to-PDF renderer or a purpose-built PDF library after a spike comparing typography, image layout and Railway compatibility. Store generated PDF as private evidence/output with its source version and generation timestamp; regenerate on later version rather than replacing history.

**Frontend:** `Export PDF` only after save; progress/failure state; secure download/share action.

**AI:** no AI at export time.

**Security/testing:** authorise every download; no public guessable URLs; snapshot/visual PDF tests covering page breaks, long text, no-photo and many-photo cases; verify file metadata does not leak tenancy.

**Acceptance criteria / Definition of Done:** every exported PDF has a record number, data/version consistency, legible A4 layout, correct evidence captions, and no unreviewed AI text.

**Dependencies:** Phase 3, 5, 6. **Can run in parallel:** template work using non-production fixtures after Phase 3. **Risk:** browser printing is inconsistent; replace rather than extend the current print CSS.

### Phase 8 — record history and audit trail

**Objective:** make evidence discoverable and changes accountable.

**User value:** a manager/QS can find what was recorded, when and by whom.

**Features:** project record list, date/type/status filters, keyword search over safe structured text, record detail, version history, and audit timeline.

**Minimum audit trail:** creation, field save/version, status change, evidence add/delete, PDF generation/export, and permission-sensitive viewing/download actions where proportionate. Capture actor, timestamp, target/version and safe change summary. Do not write full confidential content into general logs.

**Data/API/frontend:** indexed company/project/date/status/record number; cursor pagination; version diff summaries; read-only previous version/PDF view.

**Security/testing:** all searches start with company/project scope; test IDs in filters cannot bypass scope; audit rows are append-only to ordinary users.

**Acceptance criteria / Definition of Done:** an authorised manager can find a record by project/date/status and explain who saved or changed it, while a foreman cannot alter audit history.

**Dependencies:** Phase 3; PDF/evidence enrich the history but are not prerequisites. **Risk:** audit records becoming a parallel mutable system; append-only service boundary.

### Phase 9 — offline and site reliability

**Objective:** prevent lost work and honestly communicate save state under poor connectivity.

**User value:** a foreman does not lose a shift's account because signal drops.

**Delivery sequence:**

1. First usable MVP: online-only save, offline detection, local encrypted-or-minimised browser draft recovery, clear “Not saved” state, retry button.
2. Production MVP: installable web app/service worker for shell assets; local draft queue and resumable/direct evidence uploads where supported.
3. Later commercial beta: queued record saves and AI draft requests, background sync, conflict UI.

**Technical work:** client-generated draft IDs/idempotency keys; IndexedDB for drafts/queued metadata, not indefinite full sensitive data; connectivity listener is advisory only—server acknowledgement determines saved state; queue states `local`, `uploading`, `pending_sync`, `saved`, `failed`, `needs_attention`; exponential retry with capped attempts.

**Conflict model:** drafts may merge by field only before first save. Once saved, require optimistic concurrency; if remote version differs, show user both values and require a manager/user choice. Never auto-merge evidence deletion or status changes.

**AI:** do not pretend an AI request was sent offline. Queue only explicit draft requests, label them pending, and allow manual form completion; discard queued request if the user edits source account materially.

**Testing:** network-offline/browser storage tests, interrupted upload/restart tests, duplicate idempotent save tests, queue retry/backoff, conflict E2E tests.

**Acceptance criteria / Definition of Done:** the UI never says “Saved” before server acknowledgement; interrupted entry can be recovered; failed items expose an actionable state.

**Dependencies:** Phase 3–6; service-worker/PWA decision. **Risk:** complex conflict handling; do not block first user validation on full offline sync.

### Phase 10 — security and production hardening

**Objective:** meet the baseline required to hold real company evidence.

**Features/technical work:** production/staging/local environment separation; migration deployment; backups and restore test; secrets manager/environment validation; CSP/security headers; CSRF; rate limits; error tracking; health/readiness endpoints; operational runbook; dependency/security updates; data retention and deletion workflows.

**Security model:** default deny; authenticate first; load resource through company/project scope; authorise action by role; validate server-side; emit audit event; issue short-lived storage download/upload URL only after authorisation. Never query a SiteRecord, EvidenceItem, Document or vector chunk by public ID alone.

**AI/API security:** per-user/company rate and spend limit; request size limits; provider keys only server-side; protect against prompt injection by treating user/document text as untrusted data; redact secrets/PII from logs; configurable timeouts and circuit breaker.

**Privacy:** publish data-processing, retention and deletion commitments before pilots; define UK GDPR roles, lawful basis and processor agreements with hosting/AI/storage vendors; provide company-data export/deletion path. Obtain specialist legal advice for formal compliance claims.

**Testing:** SAST/dependency scan, authz regression suite, upload abuse tests, CSRF/rate-limit tests, backup restore drill, penetration test or independent security review before paid rollout.

**Acceptance criteria / Definition of Done:** security checklist is complete, critical/high findings resolved or formally accepted, restore has been tested, telemetry is live, and cross-tenant tests run in CI.

**Dependencies:** begins in Phase 2 and gates real-company production launch. **Risk:** treating it as a final polish phase; the controls must be implemented incrementally.

### Phase 11 — manager and QS workflow (post-MVP)

**Objective:** turn reliable records into a manager/commercial workflow only after capture quality is proven.

**User value:** office teams can review evidence, prepare packs and manage exceptions without replacing site capture.

**Features:** `Sent`, `Signed off`, and `Disputed` statuses; configurable review/approval; share links or controlled recipients; weekly summaries; evidence packs; variation register; CSV/PDF exports.

**Data/API/frontend:** `RecordDelivery`, `Approval`, `Dispute` and `VariationRegisterItem` only when their actual workflow is designed. Do not overload `SiteRecord.status` with ambiguous client actions. Link register items to source records/evidence.

**AI:** optional weekly factual summarisation from reviewed records, clearly labelled and editable; no autonomous commercial/legal conclusions.

**Security/testing:** external shares require expiry, revocation and access logging; role tests; approval immutability/versioning; evidence pack completeness tests.

**Acceptance criteria / Definition of Done:** a manager can trace each register/pack entry to reviewed source records; no status implies approval unless the responsible human explicitly completed the action.

**Dependencies:** Phase 3, 7, 8, 10; validate capture use with pilots first. **Risk:** feature creep into a generic CDE/project-management suite.

### Phase 12 — project document Q&A (supporting capability)

**Objective:** rebuild current document Q&A as a project-scoped, cited support tool.

**User value:** users can locate relevant information in their own project documents without treating chat as authoritative advice.

**Features:** project document upload/list/delete, asynchronous text/OCR extraction policy, chunking with document/page metadata, project-scoped retrieval, inline citations, answer limitations and source-opening experience.

**Data/API:** `ProjectDocument` belongs to company/project; `DocumentChunk`/vector metadata includes company/project/document IDs; retrieval requires all scopes. Replace shared unscoped `Document`/Chroma collection behaviour. Use a durable/vector solution appropriate to selected hosting, or Postgres pgvector if it meets scale/operational needs.

**Answer policy:** label each response as **Document-based**, **General guidance**, or **Unable to answer from the supplied documents**. Legal/contract conclusions require citations and cautious language; never present uncited definitive advice.

**Security/testing:** document virus/content handling policy, per-project query filters tested as isolation controls, citation-to-page correctness tests, prompt-injection fixtures embedded in documents.

**Acceptance criteria / Definition of Done:** no answer can retrieve a chunk from another project/company; every document-derived claim has a document/page citation; no-match response is explicit.

**Dependencies:** Phase 2, 5/10; should not delay SiteRecord MVP. **Risk:** expensive/distracting RAG work.

### Phase 13 — commercialisation

**Objective:** package the proven evidence workflow by company/team, not by AI prompt.

**User value:** predictable plan limits and a clear reason to upgrade as a team adopts Mate.

**Initial packaging:**

| Plan | Intended capability |
| --- | --- |
| Free | One user, one active project, limited saved records/evidence allowance. |
| Paid team | Multiple users/projects, high or unlimited record allowance, branded PDFs, history/export and manager workflow as released. |

**Technical work:** `SubscriptionAccount` associated with Company, plan entitlements, usage meter for records/evidence/AI only as a cost guardrail, soft/hard limit policy, billing-provider integration, invoice/tax/legal review. Keep entitlement checks in one service; do not scatter plan checks through templates.

**Testing/security:** webhook signature/idempotency, entitlement tests, cancellation/downgrade/data-access policy, billing audit. Do not expose billing-provider secrets or trust browser plan flags.

**Acceptance criteria / Definition of Done:** a company cannot accidentally incur uncontrolled AI cost; plan boundaries are understandable; upgrade/downgrade preserves data according to a documented policy.

**Dependencies:** proven Phase 3–8 value and Phase 10 production controls. **Risk:** charging before retention/value are demonstrated.

## 5. Dependency map and milestones

```text
Approved product requirements + technical choices (0/1)
  -> identity, tenancy and projects (2)
      -> durable manual SiteRecord + audit/version core (3)
          -> evidence storage (5) ----\
          -> AI draft/extraction (4) ---+-> review/save experience (6) -> PDF (7) -> history (8)
                                                                  \-> offline reliability (9)
  -> security hardening is continuous from Phase 2 and gates production (10)

Reliable record capture/history + security
  -> manager/QS workflow (11) and commercialisation (13)
Tenancy + secure storage + production controls
  -> project document Q&A (12), independently of the core capture path
```

| Milestone | Included phases | Outcome |
| --- | --- | --- |
| Architecture approved | 0–1 | One focused product contract and chosen stack. |
| Secure record foundation | 2–3 | Real users/projects and manually saved, isolated SiteRecords. |
| First usable MVP | 4–7 | Voice/text-assisted, reviewed records with evidence and professional PDF. |
| Production MVP | 8–10 | Searchable history, safe operations and honest poor-connectivity behaviour. |
| Commercial beta | 11, selected 13 | Manager/QS workflow and team packaging after pilot proof. |
| Supporting expansion | 12 and later | Project document Q&A, only when it reinforces evidence work. |

## 6. Prioritisation

**Must have for first pilot:** Phases 2–7 in their narrow form, including manual fallback, cross-tenant access control, server-side validation, secure evidence storage, saved versions/audit, basic production error handling, and PDF export.

**Should have before broad production invitation:** Phase 8, the initial Phase 9 reliability layer, and Phase 10 controls/operations.

**Could have after evidence workflow retention is proven:** full offline queue/sync, manager approval, evidence packs, variation register, branded PDFs and project document Q&A.

**Later / explicitly do not build now:** contract entitlement engine, automated valuation/invoicing, full construction management suite, complex external client portals, CDE/accounting integrations, general public construction chatbot, computer-vision conclusions, and per-prompt customer billing.

## 7. Technical debt register

| Debt | Address by | Why |
| --- | --- | --- |
| `db.create_all()` without migrations | Before Phase 2 | Customer schema needs repeatable change control. |
| No test suite/app factory | Before Phase 2 | Auth and tenant security require reliable regression tests. |
| Unscoped documents/Chroma | Disable/rebuild before pilots; Phase 12 | Current design can expose data across users. |
| Local `instance/` file storage | Phase 5, before evidence pilots | Container disk is not durable or tenant-safe. |
| Hard-coded AI clients/model IDs | Phase 4 | Enables fallback, costs and safe handling. |
| Raw external exceptions | Phase 2 onwards | Avoids raw failures and data loss. |
| Inline per-tool styles | Incrementally in Phases 3–6 | Needed for consistent mobile/accessibility quality, not a prerequisite rewrite. |
| Browser print as reporting | Phase 7 | Does not create reproducible professional documents. |
| Duplicate/older `doc_qa` blueprint | Before production launch | Avoids unclear, insecure overlapping product behaviour. |
| README/local port mismatch | Phase 0 developer-experience task | Prevents setup confusion. |

## 8. Proposed multi-tenant security model

The tenant boundary is `Company`. Every business object must either contain `company_id` directly or be loaded through a parent that does. `Project` belongs to one Company; `SiteRecord`, evidence, document and audit event retain a direct `company_id` as a defence-in-depth and query-performance measure.

Access algorithm for every protected action:

1. Authenticate the user.
2. Resolve the requested resource from a company-scoped query.
3. Verify active CompanyMembership.
4. Verify ProjectMembership where the project uses assignment restrictions.
5. Check role/action policy.
6. Validate the request server-side.
7. Execute transaction and append required audit event.

Object storage follows the same rule: private object; request authorisation first; then issue a short-lived, constrained signed URL. Vector/document retrieval always filters by company and project before similarity search results are used.

## 9. Proposed entity relationship structure

```text
User --< CompanyMembership >-- Company --< Project
                                      \--< SiteRecord --< EvidenceItem
                                                  |--< LabourEntry
                                                  |--< PlantEntry
                                                  |--< MaterialEntry
                                                  |--< Instruction
                                                  |--< DelayBlocker
                                                  |--< SafetyObservation
                                                  |--< NextAction
                                                  |--< SiteRecordVersion
                                                  \--< AuditEvent

CompanyMembership --< ProjectMembership >-- Project       (only if project assignment is needed)
Project --< ProjectDocument --< DocumentChunk/vector metadata   (later Phase 12)
Company --< SubscriptionAccount                                (later Phase 13)
```

Use internal numeric primary keys if desired, but expose UUID public IDs externally. All timestamps use timezone-aware UTC; format dates/times in the company/project timezone in the UI/PDF. Save the record's source account, schema version and reviewed version so later prompt/schema changes do not rewrite historical meaning.

## 10. AI architecture

AI only runs when a user explicitly requests a draft. It receives the editable account and any user-authorised supporting context. It returns validated structured suggestions, missing facts, and concise questions. It does not write SiteRecord rows directly.

The application owns:

- input validation and size limits;
- the schema/version and hallucination rules;
- JSON validation/repair/retry policy;
- provenance, uncertainty and review UX;
- per-company usage allowance and audit/cost record;
- final save, version, PDF and evidence links.

The user owns confirmation: changing, removing, marking not recorded, or saving every business fact. The manual form remains available in all AI failure modes.

## 11. Offline architecture

Start with data-loss prevention, not a complex offline-first promise. A browser-local draft is explicitly labelled local/not saved; server acknowledgement changes it to saved. Use idempotency keys so a retry cannot create two records. Later, use IndexedDB queue metadata plus service-worker assets and resumable uploads. Conflict resolution is deliberate and user-visible after a record is saved. AI jobs are never represented as complete before the server returns a validated result.

## 12. Testing strategy

| Layer | Required coverage |
| --- | --- |
| Unit | model validation, role policies, state transitions, record numbering, schema parsing, storage-key builder, PDF data mapper. |
| Integration | migrations, Postgres transactions, storage adapter, AI service retries/limits, queue jobs, auth/session flows. |
| API | validation/errors, CSRF, pagination/filtering, idempotent saves, export/download authorisation. |
| Database/access control | company/project isolation for every resource and child resource; role matrix; direct-ID enumeration attempts. |
| AI extraction | curated fixtures for normal reports, ambiguous accounts, absent facts, unsafe/prompt-injection text, malformed model output and provider failure. Track false fact insertion as a release-blocking defect. |
| End-to-end | phone viewport: capture -> draft/manual -> review -> save -> reopen -> PDF; photo failure/retry; no-AI save. |
| Offline | local draft recovery, interrupted upload, retries, duplicate submission, conflicts and truthful UI states. |
| PDF | visual/snapshot rendering, long content/page breaks, all optional sections absent, image-heavy evidence. |
| Security | dependency scanning, SAST, CSRF, authz regression, rate limits, file validation, signed URL scope and restore test. |

CI should run fast unit/API/authz tests on every change; slower visual/E2E/security suites run before release. Use anonymised synthetic construction records only in automated tests.

## 13. Production-readiness checklist

- [ ] Production, staging and local configuration are separated; production refuses debug mode and missing required secrets.
- [ ] Postgres migrations, backup schedule and a tested restore procedure exist.
- [ ] Authentication, CSRF, password/session controls and rate limits are live.
- [ ] Every protected query and storage URL is covered by company/project authorisation tests.
- [ ] Evidence is stored privately under generated keys with size/type/content validation and deletion/retention policy.
- [ ] SiteRecord saving is transactional, versioned, audited and manual fallback works when AI fails.
- [ ] AI output is schema-validated, usage-limited, monitored and cannot silently persist facts.
- [ ] PDFs are generated from reviewed saved versions and download access is authorised.
- [ ] Error monitoring, structured redacted logs, uptime/health checks and incident contact/runbook exist.
- [ ] Accessibility and mobile acceptance tests pass on agreed devices/browsers.
- [ ] Privacy notice, terms, data-processing/subprocessor review, retention/deletion process and customer support contact are ready.
- [ ] Dependency, security and restore checks have passed; critical/high issues are remediated.
- [ ] A pilot company has completed real records successfully and feedback has been triaged.

## 14. Recommended final phase structure and development order

### A. Final phase structure

0. Baseline and technical decisions
1. Product foundation specification
2. Accounts, companies and projects
3. Manual persistent SiteRecord core
4. Voice/text and schema-validated AI draft
5. Secure evidence/photos
6. Review-before-save experience
7. Professional PDFs
8. History and audit trail
9. Offline/site reliability
10. Security and production hardening
11. Manager/QS workflow
12. Project document Q&A
13. Commercialisation

### B. Recommended development order

Build 2 -> 3 -> 5/4 -> 6 -> 7 -> 8 while Phase 10 controls are built continuously. Do not begin Phase 11, 12 or 13 until the pilot demonstrates repeated real use of saved SiteRecords. Phase 9 begins with draft recovery rather than delaying the first pilot for full sync.

### C. First implementation milestone

**Secure manual record foundation:** implement accounts, companies/projects, role policies, migrations, a manually completed Draft/Saved SiteRecord and its basic history. This validates the core business record before adding AI. It is the smallest milestone that changes Mate from a generator into a product with durable customer value.

### D. Exact Codex tasks after approval

1. Add a testable Flask application factory, environment-specific config and developer commands; correct README local launch/port instructions.
2. Add migration tooling and create the initial User, Company, CompanyMembership and Project schema.
3. Implement authentication, onboarding, role-policy helpers, CSRF and tenant-scoped route/service patterns.
4. Add the initial SiteRecord, version and audit schema with only Draft/Saved states.
5. Build the mobile manual record create/review/save/reopen flow and project record list.
6. Add access-control, validation and migration tests; demonstrate Company A/Company B isolation.
7. Choose and integrate private object storage, then add EvidenceItem upload/retry/delete.
8. Add schema-validated AI drafting with fixture evaluations and a manual fallback.
9. Add server-generated PDF export and visual regression tests.
10. Pilot with one subcontractor before manager workflow, document Q&A or billing work.

### E. Decisions requiring human approval

1. Authentication choice: managed identity provider versus local email/password implementation.
2. Hosting/storage/queue choices and budget: Railway services plus S3-compatible storage/managed Postgres, or another stack.
3. Whether all company members initially see all projects, or project membership is required from day one.
4. The exact field labels and mandatory follow-up prompts, after speaking to target foremen.
5. Evidence retention/deletion period, photo metadata policy, and legal/privacy review owner.
6. First pilot company and the definition of a successful pilot (for example, consecutive weekly usage and office acceptance of records).
7. PDF branding/identity requirements and whether PDF sharing must be email/link-based in MVP.
8. The approved AI provider/data-use position for customer site information.

