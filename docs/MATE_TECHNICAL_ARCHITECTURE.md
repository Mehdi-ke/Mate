# Mate technical architecture blueprint

## Document role

This document describes the technical target and safety boundaries. It complements the existing master roadmap without overwriting it. Code remains the current-state source of truth; this blueprint is the approved target after product-owner decisions are made.

## Current baseline: code compared with documentation

Mate is a Flask monolith in `app.py` that registers `site_report`, `construction_assistant`, and legacy `doc_qa` blueprints. UI is Jinja/server rendered with a shared CSS token file and large tool-specific inline styles/scripts. `config.py` loads environment values and selects Postgres via `DATABASE_URL`, otherwise SQLite. `extensions.py` creates Flask-SQLAlchemy and a local persistent Chroma collection. `app.py` calls `db.create_all()` at startup.

The implemented `Site Report Generator` accepts text/browser speech transcription and an optional single image, makes Anthropic calls, and renders free-form report text with browser-print CSS. The implemented construction assistant persists session-selected `Conversation`/`Message` data, uploads PDFs to local `instance/uploads`, extracts text by page, retrieves chunks from the shared Chroma collection, and supplies page citations for relevant answers. The legacy document Q&A feature also uploads to the same local directory/collection but is unscoped and not linked from the home page.

There are no users, companies, projects, authentication, role checks, CSRF protection, SiteRecords, record history, audit records, migrations, test suite, background worker, production object storage, server PDF generator, retries, usage limits or error monitoring. The existing Phase 1 product specification is therefore aspirational, not implemented.

### Retain

- Flask/Jinja monolith for the first commercial MVP: it is sufficient and lowers rewrite risk.
- Blueprint/module organisation, expanded with service/domain boundaries.
- Postgres-capable SQLAlchemy configuration.
- Voice/text capture idea and the existing cautious “do not invent facts” product intent.
- PDF text extraction and source/page metadata as a basis for later project document Q&A.
- Existing simple navy/light design tokens, refined rather than replaced wholesale.

### Replace or materially rework

- `db.create_all()` -> migrations and an app factory/test configuration.
- Local disk/original filenames -> private object storage with generated IDs and lifecycle.
- Unscoped Chroma/documents -> project/company-scoped document service, later.
- Inline AI clients/hard-coded model IDs -> configurable dedicated AI service.
- Free-form report generation -> schema-validated SiteRecord draft plus user review.
- Browser print report -> server-generated PDF from saved record version.
- The legacy `doc_qa` route -> disable before real pilots or rebuild as Phase 8 project document Q&A.

## Target application architecture

```text
Mobile web / PWA browser
  -> Flask controllers (HTML + narrowly scoped JSON endpoints)
      -> auth, CSRF, request validation, tenant/resource loading
          -> domain/application services
              -> Postgres: authoritative relational data
              -> private object storage: evidence, documents, generated PDFs
              -> AI extraction service: drafts only
              -> worker/queue: PDFs, thumbnails, uploads, indexing, retries
              -> vector retrieval: later, project-scoped document Q&A
```

### Boundaries

- **Controllers/routes:** parse input, authenticate, authorise and render/serialise. No AI prompts or direct storage logic.
- **Domain/application services:** SiteRecord lifecycle, evidence lifecycle, report creation, permissions, AI drafting and document retrieval.
- **Repositories/models:** persistence and scoped query helpers. Sensitive reads require company/project scope by design.
- **Adapters:** Anthropic, object storage, queue, PDF renderer, email/identity providers. Configuration/model IDs live outside route code.
- **Worker:** only for slow/nonessential work. Manual capture/save does not require AI or a worker.

Use Postgres in production; SQLite remains developer-only. Add Alembic/Flask-Migrate before new persistent entities. Use private S3-compatible storage for customer files; container filesystems are not durable production evidence stores. Introduce a queue only when asynchronous jobs become necessary; its first candidates are thumbnails, PDF generation, document indexing and bounded AI retry.

## Domain model and implementation timing

| Entity | Purpose | Build now? |
| --- | --- | --- |
| User | Identity and login | Yes |
| Company / CompanyMembership | Tenant and roles | Yes |
| Project / optional ProjectMembership | Evidence container and access | Yes; assignment table only if pilots need it |
| SiteRecord | Authoritative reviewed record | Yes |
| SiteRecordVersion / AuditEvent | Versioned accountability | Yes |
| WorkItem, LabourEntry, PlantEntry, MaterialEntry | Structured repeatable record facts | Yes, when SiteRecord is built |
| Instruction, DelayBlocker, SafetyObservation, NextAction | Important factual context | Yes, as record children |
| EvidenceItem | Private linked photo/file metadata | Yes before evidence pilots |
| ProjectDocument / document chunks | Project source material | Later, supporting capability |
| Action | Record-derived follow-up task | Later |
| CommercialEvent/register/approval/dispute | Aggregated commercial workflow | Later, after record quality is proven |
| SubscriptionAccount | Company plan/entitlements | Later, when packaging is validated |

All business objects carry `company_id` directly or are queried through a scoped parent; SiteRecord/Evidence/Document should carry it directly as defence in depth. Use UUID public IDs. Use UTC-aware timestamps, with company/project timezone displayed in UI/PDF.

## Canonical SiteRecord

`SiteRecord` is an authored, reviewable account of a project day/event. It can be a daily record, a daywork/variation-focused record, or a delay/blocker-focused record. It is not a determination of approval, contractual entitlement or valuation.

### Core fields

- Identity: public ID, company, project, record number, record date/time, location/area where supplied, record type, Draft/Saved status.
- Authorship: created by/at, reviewed by/at, saved by/at, updated at, schema version.
- Account: original user text/transcript as protected supporting context.
- Confirmed facts: work items, labour, plant, materials, progress, instructions, delays/blockers, possible extra-work description, safety observations, next actions and notes.
- Evidence: linked EvidenceItems, captions and capture/upload timestamps.
- History: immutable SiteRecordVersion snapshot and AuditEvent rows.

### Fact states and provenance

| State | Meaning | May enter saved authoritative field? |
| --- | --- | --- |
| User stated | Explicitly present in the raw account/form | Yes, after review |
| AI derived / needs confirmation | AI structured or classified wording but user has not confirmed it | No |
| Missing / not recorded | Relevant detail not supplied | Yes, only as `not_recorded`, never a fabricated value |
| User edited / confirmed | User supplied, corrected or accepted review value | Yes |

Store value metadata/provenance in validated draft/version data. Saved child entities contain user-reviewed values. Preserve draft and raw input separately with an approved retention policy so the formation of a final record can be explained without confusing draft content with fact.

## AI boundary

```text
User account + user-selected evidence
  -> AI extraction (versioned JSON schema)
  -> validated draft + bounded missing-information questions
  -> human review/edit/confirm
  -> saved SiteRecord/version
```

The AI may extract, structure, classify a possible event, identify missing information, ask targeted questions, summarise reviewed data and later search cited records/documents. It must never invent facts, quantities, hours, people, dates, instructions, weather, legal/contractual rights or commercial decisions.

Use versioned strict JSON schemas, server-side parsing/validation, one bounded malformed-output repair attempt, provider timeout/backoff for transient errors and per-company usage limits before model calls. Store model/version/cost/outcome telemetry without logging raw sensitive record content. On every AI failure, preserve the user input and allow manual record completion. “Confidence” must guide confirmation UX, not promote a value to fact.

## Multi-tenancy and permissions

The company is the tenant boundary. Roles are Owner, Manager and Foreman.

- Owner: manages company/members/billing, projects and all records.
- Manager: manages permitted projects/records and later commercial workflow; no billing/member authority by default.
- Foreman: creates records, edits own drafts, saves records, views assigned/allowed projects and exports permitted records.

Protected-resource algorithm:

1. Authenticate user.
2. Load resource through a company-scoped query, never by public ID alone.
3. Confirm active membership and project membership if enabled.
4. Evaluate role/action policy.
5. Validate server input and perform a transaction.
6. Append a safe audit event where required.

Database foreign keys, composite uniqueness constraints, direct `company_id` columns and scoped repository methods reinforce—but do not replace—authorisation. Object storage keys include company/project/record/evidence UUIDs; signed URLs are short-lived and issued only after the same permission check. Future APIs use the identical policy layer; client-side role hiding is never a control.

## Evidence and file architecture

`EvidenceItem` records: company/project/record ownership, generated storage key, display filename, content type, size, checksum, uploader/time, optional captured time, caption, processing state and deletion metadata.

- Accept only explicitly supported file types; validate bytes and MIME, not extensions alone.
- Start with bounded image count/size; make limits configurable and test on site devices.
- Store originals and generated PDFs privately; use generated keys, not user filenames.
- Generate previews/thumbnails asynchronously; record `pending`, `available`, `failed` and `deleted` states visibly.
- Authorised deletion is soft-delete plus audit event, followed by retention-controlled object cleanup.
- Treat EXIF location/device metadata as a privacy decision; do not expose it accidentally.
- Project documents and audio are later evidence types, with separate size/extraction/retention policies.

## Incremental offline/mobile strategy

1. **MVP:** online save only; detect likely offline state; store an unsaved local draft; display `Not saved` until server acknowledgement; retry explicitly.
2. **Production MVP:** PWA shell caching, IndexedDB draft recovery, idempotency keys and resumable/direct evidence uploads where storage supports them.
3. **Later:** queued record/API operations and AI requests; bounded background sync; conflict resolution for post-save edits.

The network indicator is advisory. Only an acknowledged server response permits the UI to say `Saved`. Never show an AI draft as completed until it is returned and validated. Conflicts after a saved version are user-visible; never auto-merge evidence deletion/status changes.

## Lifecycle and auditability

### MVP state machine

```text
Local capture -> Draft -> Ready for review -> Saved -> Amended (new version)
```

`Needs evidence` is a presentation/completeness condition, not a blocking status: a user may save an honest `Not recorded` field. `Processing` is a temporary UI/job state, not the canonical record state. Later manager workflows may add Sent, Signed-off and Disputed once delivery/approval/dispute entities exist.

Minimum audit/history: original account reference, AI draft metadata, user changes, evidence add/delete, create/save/amend, actor and timestamps, prior immutable versions, PDF generation/export. Saved record versions are never overwritten. General logs hold safe IDs/action metadata, not raw account/photo contents.

## PDF/reporting architecture

Build a reusable reporting service that maps immutable saved-version data to templates. The first and only MVP output is a Site Record PDF. It includes company identity, project/site, record reference/date, author/reviewer/times, reviewed sections, evidence photos/captions, disclaimer and source version.

Generate server-side from saved data, store privately, and associate each PDF with the source SiteRecordVersion. Do not turn the existing browser-print free-form report into the archive format. Later Daywork, evidence-pack, weekly/monthly and commercial-summary templates reuse the same report data mapper, access control and file lifecycle.

## Security and production readiness

Required before real company production use: secure/session authentication, CSRF, server validation, tenant tests, file validation, private storage, secrets management, no debug mode, rate/spend limits, redacted structured logs, error monitoring, health checks, migrations, backups and restore drills, data retention/deletion process, production/staging/local separation, dependency scanning and documented AI/vendor data handling. UK GDPR/data-processor and legal claims require specialist review; architecture alone does not establish compliance.

## Testing strategy

- Unit: domain validation, state transitions, role policies, record number allocation, schema/provenance parsing, report data mapping.
- Integration: migration paths, Postgres constraints/transactions, storage adapter, provider retry/limit behaviour, authentication/session flow.
- End-to-end: narrow mobile capture -> review -> save -> reopen -> PDF; manual fallback; photo retry; readable errors.
- AI: versioned fixtures including missing facts, ambiguous accounts, prompt-injection text, malformed JSON and provider failures. False fact insertion is release-blocking.
- Security: every company/project/resource/child resource rejects cross-tenant direct-ID attempts; CSRF/rate-limit/signed-URL/file upload tests.
- Reliability: interrupted entry/upload, duplicate idempotent save, local draft recovery, queue/retry/conflict tests as offline work is added.

## Decisions requiring product-owner approval

1. Managed identity provider versus locally implemented email/password authentication.
2. Hosting, managed Postgres, private object storage and job queue provider/budget.
3. Company-wide versus project-assigned access in first pilots.
4. Field labels/conditional prompts after foreman interviews.
5. Retention/deletion, EXIF/privacy and data-processor policy.
6. AI provider/data-use approval, model fallback and spend-limit policy.
7. PDF branding and required sharing mechanism.
8. Browser/PWA offline promise and supported device/browser set.
9. Pilot company and the measurable threshold for moving to commercial workflow/billing.

## Architecture principles

1. Evidence and SiteRecord precede features and screens.
2. AI drafts; people confirm.
3. Never silently transform inference into fact.
4. Every important fact has an author, time and provenance path.
5. Tenant isolation is mandatory at every data/file/query boundary.
6. Manual capture works when AI, voice or connectivity does not.
7. Mobile speed and trustworthy feedback beat breadth.
8. Generated PDFs are immutable outputs of saved versions.
9. Expand through the project evidence graph, not disconnected tools.
10. Do not claim legal/compliance certainty that Mate cannot substantiate.

