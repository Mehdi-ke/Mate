# Mate pre-implementation review and reconciliation

**Review status:** complete. This is a planning document; no application code, database, migration, dependency or configuration change was made.

## Document authority

| Document | Authoritative purpose |
| --- | --- |
| [`phase-1-daywork-record-mvp.md`](phase-1-daywork-record-mvp.md) | First user workflow, scope and field-level product requirements |
| [`MATE_PRODUCT_UNIVERSE.md`](MATE_PRODUCT_UNIVERSE.md) | Product boundary and justified future expansion |
| [`MATE_TECHNICAL_ARCHITECTURE.md`](MATE_TECHNICAL_ARCHITECTURE.md) | Target architecture, security and domain design |
| [`MATE_IMPLEMENTATION_ROADMAP.md`](MATE_IMPLEMENTATION_ROADMAP.md) | Engineering delivery order and gates |
| [`MATE_MASTER_ROADMAP.md`](MATE_MASTER_ROADMAP.md) | Detailed cross-functional rationale, risks and acceptance criteria |
| This review | Reconciliation, canonical decisions and pre-implementation gates |

## 1. Actual repository baseline

### What Mate can do today

- Render a Flask/Jinja site with three registered blueprints.
- Create a free-form UK-style report from typed/browser voice-dictated notes, with an optional in-memory image and browser print styling.
- Hold a session-selected construction chat conversation in SQLAlchemy.
- Upload PDFs to local disk, extract text and retrieve chunks from a persistent local Chroma collection; the construction assistant can cite filename/page when it finds relevant text.
- Use Postgres if `DATABASE_URL` is present, otherwise local SQLite; deploy with Gunicorn on Railway.

### What Mate cannot do today

- Authenticate users or separate companies, projects, roles or data.
- Create a persistent SiteRecord, project history, record number, version, audit event or user-reviewed business record.
- Safely retain production evidence; uploads use local `instance/uploads` and original filenames.
- Generate a server-side professional PDF, manage delivery/approval/dispute, enforce AI usage limits, or tolerate external-service failure gracefully.
- Run database migrations, a test suite, background jobs, monitoring, backups/restore or production security controls.

### Prototype-quality versus production-ready

The two AI experiences and PDF extraction are useful prototypes. The app's Flask/Blueprint structure, configurable database URL, source-page metadata and cautious report-prompt intent are reusable components. No customer-data feature is production-ready: the absence of authentication, tenant isolation, migrations, secure storage, tests and operations gates real-company use.

### Architectural constraints and debt

- `db.create_all()` is the only schema process; it cannot manage live schema evolution.
- Anthropic clients/model IDs are embedded in routes; no provider abstraction, bounded retry/fallback or cost accounting exists.
- Chroma and document/file data are local and unscoped. The legacy `doc_qa` blueprint lists all documents and must not be exposed to real users until rebuilt or disabled.
- Current UI/report output is generated prose and browser printing, not structured reviewed data and reproducible reports.
- There is no test harness, app factory, migration tool, upload lifecycle, CSRF/rate-limit/authorisation policy, error monitoring or backup model.
- README describes an AI-tool platform and local port 5000; the target product direction and `.flaskenv` local port 5001 differ. The README should be updated during the first developer-experience task, not treated as future-product authority.

## 2. Consistency review

### Product direction

The product documents consistently place **project evidence for UK subcontractors** above a generic AI toolbox. Current code does not yet implement that direction; this is an expected prototype-to-product gap, not a conflict in the target.

The old README and current home page still position Mate as a collection of AI tools. They are descriptions of the present prototype, not the approved target. Product/architecture documents are authoritative for future implementation. Update the README and product copy only when the first implementation work is approved.

### MVP definition

The Phase 1 brief, Product Universe, Technical Architecture and Implementation Roadmap agree on company/project scope, capture, AI draft, review, save, evidence/history and a PDF. The MVP remains appropriately narrow.

One genuine conflict existed: the Phase 1 scope listed `Sent`, `Signed off`, and `Disputed` among MVP statuses while later sections and every roadmap correctly deferred delivery/approval/dispute workflows. This review corrects the Phase 1 wording: MVP has **Draft** and **Saved** only. The later statuses remain a post-MVP commercial workflow.

### Technical architecture and roadmap

The target architecture consistently uses Flask initially, Postgres as production source of truth, private object storage, a service boundary, schema-validated AI drafts, review-before-save, versions and audit. This is appropriate without requiring a premature SPA/mobile rewrite.

The word “Phase 2” could mean either product expansion (commercial protection in Product Universe) or delivery phase (manual SiteRecord in Implementation Roadmap). This review adds a clarification: Product Universe phases are **capability horizons**; Implementation Roadmap phases are **engineering sequence**. The numbered delivery roadmap governs build order.

### Current code against plans

No plan claims that accounts, SiteRecords, storage, AI schemas or PDFs currently exist. The documents accurately call them future work. The only current mismatch to correct later is public-facing README/home positioning; it requires no planning-document rewrite now.

## 3. Product universe validation

The expansion strategy is coherent when each feature strengthens the evidence graph.

| Category | Assessment |
| --- | --- |
| SiteRecords, evidence, review, versions, PDFs, project history | Strongly reinforce the core; required foundation |
| Daywork/variation, delay and instruction registers; evidence packs | Strong next commercial layer, but wait for trusted saved records |
| Record-derived actions, progress views, photo timeline | Useful operational extensions; add only from real pilot demand |
| Document Q&A, cited summaries, project search | Valuable intelligence layer after scoped documents/evidence exist |
| Snags, RFIs, compliance, timesheets, full communications | Potentially separate products; do not add merely because they are construction-related |
| Generic chat, ERP, legal conclusions, autonomous valuation/decisions | Explicitly out of scope |

The core sequence remains: **Capture -> Structure -> Evidence -> Review -> Confirmed Record -> Commercial/Operational Output**. No proposed future capability needs a different central data model, provided later objects link to source SiteRecords rather than replacing them.

## 4. MVP validation

### Required MVP

1. User/company/project tenant boundary with Owner, Manager and Foreman roles.
2. Manual capture of a project record by text; browser voice dictation where supported.
3. A schema-validated AI draft and targeted missing-information prompts.
4. A manual path when AI or voice fails.
5. Review/edit/remove/mark-not-recorded and explicit save.
6. Persistent Draft/Saved SiteRecord with author, project, timestamps, immutable version and audit event.
7. Private photo evidence linked to the record.
8. Project history and one professional Site Record PDF generated from the saved version.

### Useful but optional within MVP

- Multiple images, captions and simple completeness indication.
- Project membership if an early pilot requires restricted projects.
- Browser-local unsaved draft recovery.

### Remove/defer from MVP

- Sent/Signed-off/Disputed statuses; external sharing/approval.
- Full offline sync/queue, manager review queues, evidence packs/registers, document Q&A, summaries, billing and integrations.

### Essential condition

The product must still save an honest manual record if the AI service, microphone or network-assisted upload path fails. AI cannot be a dependency for the system of record.

## 5. Definitive canonical SiteRecord

`SiteRecord` is a project-scoped, user-reviewed account of a day or material site event. It is a record of facts and evidence, never an approval, valuation, contract entitlement or legal conclusion.

| Field/group | Classification | Notes |
| --- | --- | --- |
| Public ID/record number, company, project, type, record date | MVP | Company/project are server-owned; number assigned at first save |
| Author, created/updated/reviewed/saved timestamps | MVP | Auditable identity/lifecycle |
| Work summary / work items | MVP | At least one plain-language work account; repeatable items only if useful in UI |
| Location/area | MVP optional | Capture only where supplied; `Not recorded` is valid |
| Labour entries | MVP conditional | Trade, headcount and hours only if user states/confirms them |
| Plant entries | MVP conditional | Description/quantity/hours only if relevant |
| Materials | MVP conditional | Used/delivered and reference only if supplied |
| Extra/additional work description | MVP conditional | A possible event/fact, not a declared variation |
| Delay/blocker | MVP conditional | Description, impact, time range/ongoing and notification where supplied |
| Instruction | MVP conditional | Source, method/reference only if recorded |
| Safety observation, next action, notes | MVP optional | Keep factual and short; never turn absence into a safety conclusion |
| Evidence links/captions | MVP | Requires secure EvidenceItem architecture |
| Draft/Saved, source-account reference, schema version | MVP | Draft metadata is distinct from reviewed facts |
| Immutable versions and audit events | MVP | At first save and each later amendment |
| Sent/Signed-off/Disputed, deliveries/approvals | Future-ready, not MVP | Need dedicated workflow entities |
| CommercialEvent, register links, evidence-pack membership | Future-ready, not MVP | Aggregate/link records; do not change record's factual core |
| Documents, actions, external correspondence, programme/cost data | Future only | Project objects linked to records when justified |

The minimum structure can support dayworks, variations, delays, instructions and later commercial packs without redesign: a future `CommercialEvent` aggregates and references multiple SiteRecords/EvidenceItems. Do not label every SiteRecord as a commercial event.

## 6. Information provenance: definitive model

| Information state | Technical representation | Save rule |
| --- | --- | --- |
| Raw user evidence | Protected source account/transcript/form input plus user-attached evidence IDs | Retained separately with approved retention policy |
| AI-derived draft | Versioned strict-schema draft JSON, model/schema metadata, field provenance `ai_derived` and uncertainty | Cannot populate authoritative SiteRecord fields without review |
| User-confirmed | Reviewed field/child entity with provenance `user_stated` or `user_confirmed` | May be saved as a fact |
| User-edited | Reviewed field/child entity with provenance `user_edited`, actor/time | May be saved; previous version remains immutable |
| Missing information | Explicit `not_recorded`/absence state and optional reason | Never converted to a guessed value |

Route/controller input must never promote AI draft JSON directly into a saved SiteRecord. The review service accepts only the reviewed payload, validates it, creates a version snapshot and appends an audit event transactionally. The UI labels needs-confirmation and not-recorded fields differently from confirmed ones.

## 7. Domain-model validation

### First implementation entities

- `User`, `Company`, `CompanyMembership`, `Project` and optionally `ProjectMembership`.
- `SiteRecord`, `SiteRecordVersion`, `AuditEvent`.
- A small first set of SiteRecord children: `WorkItem`, `LabourEntry`, `PlantEntry`, `MaterialEntry`, `Instruction`, `DelayBlocker`, `SafetyObservation`, `NextAction`.

The first slice may ship the SiteRecord manual form with only work summary/type/date/status and then add conditional child forms incrementally; schema/model ownership should be planned together so subsequent fields do not require a new root model.

### Wait entities

- `EvidenceItem` must exist before photo evidence is invited, but can follow the manual-record foundation.
- `ProjectDocument`, document chunks, `Action`, `CommercialEvent`, approvals/deliveries/disputes, subscriptions and billing wait for their respective workflows.

### Relationships/lifecycle

Company owns Projects and memberships. Project owns SiteRecords. SiteRecord owns resource/context children and evidence relationships. SiteRecordVersion is immutable; AuditEvent is append-only. Every record/child/evidence/document has a company boundary directly or through a database-enforced parent, preferably both for high-risk resources. Future project intelligence reads reviewed versions/structured records and cited documents—it never becomes the source of record.

## 8. Multi-tenancy validation

Minimum safe first build: company membership is mandatory; every request loads Company -> Project -> SiteRecord using a scoped query; role policy is evaluated server-side; UUID public IDs do not substitute for authorisation. Start company-wide project visibility unless pilots demonstrate assignment restrictions are necessary; introduce `ProjectMembership` then, rather than inventing a complex hierarchy.

Files use private company/project/record storage keys; the server authorises before issuing a short-lived URL. Future APIs and vector retrieval call the same resource-policy service. Database constraints protect relationships, while application policy protects actions; neither alone is sufficient.

## 9. Evidence architecture validation

The planned `EvidenceItem` model is sufficient for photos now and documents/generated PDFs/audio later: ownership IDs, generated storage key, display filename, MIME/byte size/checksum, uploader/timestamps, caption, processing state and deletion metadata. Move from local disk to private object storage before real evidence pilots. Validate bytes/MIME/size, show upload state/retry, use private signed access, audit add/delete and adopt explicit retention/EXIF policies. This changes adapters, not the core SiteRecord domain.

## 10. AI architecture validation

The planned boundary is correct: dedicated provider adapter/service, configured models, strict versioned output schema, server validation, bounded malformed-output repair, transient retry/backoff, usage/spend limits, provenance and manual fallback. Provider abstraction should be pragmatic: an interface/adapter enables a replacement later, but Mate should not build a multi-provider orchestration system before it has one reliable provider. AI requests are explicit/idempotent and no raw sensitive content belongs in generic logs.

## 11. Mobile/site reliability validation

### MVP guarantees

- Typed content is preserved across an AI failure and user receives a manual route.
- Failed uploads and saves show honest retry/error states.
- UI says Saved only after server acknowledgement.
- Idempotency prevents accidental duplicate record creation.
- Voice is optional/editable and unsupported browsers have a clear fallback.

### Later guarantees

- IndexedDB local draft recovery, PWA shell cache and resumable uploads.
- Queued sync, background AI jobs, full offline record creation and deliberate conflict resolution.

This is the correct incremental approach. A native application or full offline sync should not delay validating the core record workflow.

## 12. Reporting/PDF validation

The first output is one professional Site Record PDF. It is generated server-side from a saved immutable version and includes company branding, project/site, record number/date, author/reviewer timestamps, structured reviewed facts, evidence/captions and version/disclaimer. A report service/data mapper makes later Daywork, evidence-pack, weekly, monthly and commercial templates incremental additions rather than separate report systems. Browser print output remains prototype-only.

## 13. Security and production readiness

### Must have before production

- Authenticated users, server-enforced company/project authorisation, CSRF, secure session/password/provider configuration and rate limits.
- Postgres migrations, private object storage, upload validation, tenant tests and deletion/retention lifecycle.
- Schema-validated AI with user review, manual fallback, spend limits and redacted logs.
- No debug mode, secret validation, production/staging separation, error monitoring, health checks, backups and a tested restore.
- Audit/version integrity, secure PDF/evidence download, dependency/security scanning and documented privacy/vendor data handling.

### Can follow an initial controlled pilot

- Full offline synchronisation, deep analytics, external approval portal, full document intelligence, integrations, sophisticated notification/billing systems and third-party penetration testing beyond the risk-appropriate baseline. Retention/privacy commitments and tenant security cannot wait.

## 14. Roadmap validation and implementation gates

The recommended order is correct: identity/tenancy -> manual persistent SiteRecord -> evidence -> AI capture -> review/PDF -> history/reliability/production hardening -> commercial workflows -> intelligence. It avoids anchoring the data model to AI prose and permits the core record to work under provider failure.

| Gate | Must be true before proceeding |
| --- | --- |
| Gate 1 — Foundation | Migration/test framework, authenticated user/company/project, server policy matrix and Company A/B isolation tests pass |
| Gate 2 — Persistent SiteRecord | Manual Draft/Saved record persists; versions/audit/optimistic updates work; user can reopen scoped records |
| Gate 3 — Evidence | Private storage, generated keys, validated upload, retry/delete and evidence authorisation tests pass |
| Gate 4 — AI capture | Schema fixture tests show no fact invention; manual fallback/limits/retries and review provenance work |
| Gate 5 — Reporting | Server PDF reflects immutable reviewed version with secure download and visual test coverage |
| Gate 6 — Production reliability | History, truthful failure states, monitoring, backup restore, security scans, privacy/retention and release checklist pass |
| Gate 7 — Expansion | Pilot proves recurring site/office value; manager/QS/commercial features trace to records rather than introduce a parallel system |

## 15. Decisions requiring product-owner approval

### Product decisions

1. Target pilot company and measurable definition of successful pilot use.
2. Exact foreman-facing wording/field labels and the small set of conditional follow-up questions, validated with target users.
3. Whether initial companies need project-assigned visibility or company-wide project access is acceptable.
4. Evidence retention/deletion period, photo-location/EXIF policy and customer-facing privacy commitments.
5. PDF brand identity and whether MVP requires controlled sharing/email in addition to download.
6. Approved AI data-use policy for customer site data and the initial usage-limit promise.
7. Supported browser/device set and customer-facing offline promise.

### Engineering decisions

1. Managed identity provider versus locally maintained email/password authentication.
2. Managed Postgres, object storage, worker/queue and monitoring providers within the available budget.
3. Server-PDF rendering tool after a small compatibility/visual-quality spike.
4. Exact app-factory/migration/test tooling selection consistent with Flask and deployment.

## 16. Canonical product and architecture decisions

- **Vision:** Mate is a UK subcontractor project-evidence platform, not a generic AI toolbox.
- **Target user:** the working foreman; the buyer is the subcontractor owner, commercial manager or QS.
- **Core workflow:** select Project -> capture text/voice and evidence -> AI structured draft -> human review -> saved SiteRecord -> PDF/history -> later commercial/operational output.
- **MVP boundary:** company/project access, capture/manual fallback, evidence, AI draft, review, Draft/Saved record, version/audit, history and Site Record PDF. No approval/dispute/register/document-Q&A/billing suite.
- **SiteRecord:** a project-scoped, versioned, user-reviewed factual account, with conditional structured work/resources/instruction/delay/evidence data. It is not legal/commercial adjudication.
- **AI boundary:** AI extracts/structures/suggests questions; strict schema and provenance keep it a draft; only reviewed user information becomes authoritative.
- **Evidence principle:** private, validated, project/record-linked evidence with generated IDs and audited lifecycle.
- **Tenancy principle:** Company is the hard boundary; every query, file URL, document/vector retrieval and future API action is server-authorised by company/project membership and role.
- **Auditability principle:** preserve source account/draft provenance appropriately, immutable saved versions, evidence actions, actor and timestamps; do not expose draft inference as fact.
- **Implementation order:** foundation -> manual record -> evidence -> AI -> review/PDF -> history/reliability -> manager/QS -> intelligence.
- **Out of scope:** generic chatbot, ERP/CDE replacement, automated legal/contract/valuation decisions, broad compliance tools and unrelated productivity features.

## 17. Exact first implementation slice after approval

Implement only the secure manual-record foundation:

1. Add a testable Flask application setup, environment-aware configuration and migrations.
2. Add User, Company, CompanyMembership and Project with Owner/Manager/Foreman server-side authorisation.
3. Add a basic SiteRecord with project, date, type, work summary, Draft/Saved status, author/timestamps, initial immutable version and audit event.
4. Build one mobile manual create -> review -> save -> reopen flow plus a project record list.
5. Add authentication, role/state-validation and cross-company isolation tests.

Do not modify AI behaviour, add voice features, accept evidence uploads, generate PDFs, add full offline support, rebuild document Q&A, add manager approvals or introduce billing in this slice.

