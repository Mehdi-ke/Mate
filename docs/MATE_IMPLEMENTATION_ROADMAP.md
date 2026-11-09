# Mate implementation roadmap

## Document role and relationship to existing plans

This is the execution sequence for the product and architecture defined in [`MATE_PRODUCT_UNIVERSE.md`](MATE_PRODUCT_UNIVERSE.md) and [`MATE_TECHNICAL_ARCHITECTURE.md`](MATE_TECHNICAL_ARCHITECTURE.md). It preserves [`phase-1-daywork-record-mvp.md`](phase-1-daywork-record-mvp.md) as the first-workflow requirements document and does not replace [`MATE_MASTER_ROADMAP.md`](MATE_MASTER_ROADMAP.md), which contains fuller cross-functional reasoning and risk detail.

The numbered phases in this document are **delivery phases**. They are not the
same as the Product Universe's “Phase 2” and “Phase 3” market-expansion labels:
those labels describe when future capability categories should be considered,
whereas this document describes the order in which engineering work happens.

## Dependency order

```text
Approval / baseline
  -> identity, company, project and access controls
      -> manual persistent SiteRecord + versions/audit
          -> secure evidence
          -> AI capture
              -> review/save polish and Site Record PDF
                  -> history, reliability and production hardening
                      -> commercial/QS workflow and project intelligence
```

Security and test coverage begin with identity and are strengthened continuously; they are not a final bolt-on phase.

## Phase 0 — product and architecture foundation

**Objective:** approve product boundary, target architecture and operational choices before code changes.

**User outcome:** the team builds one evidence workflow rather than adding prototype tools.

**Technical work:** choose auth, managed Postgres/storage/queue, environments, Python support policy, supported browsers and AI data policy; establish app-factory/migration/test approach.

**Database / AI / UI:** no feature implementation.

**Dependencies:** none.

**Testing/security:** define CI minimum, secrets/environment policy and tenant-test strategy.

**Completion criteria:** product-owner decisions listed in the technical architecture are approved; first pilot success metric is agreed.

## Phase 1 — identity and project foundation

**Objective:** create secure companies, people and projects.

**User outcome:** users sign in, create/join a company and work only in authorised projects.

**Technical/database work:** app factory/config separation; migrations; User, Company, CompanyMembership, Project and only-if-needed ProjectMembership; policy/service layer; auth/session/CSRF/rate-limit baseline.

**UI:** sign-in/onboarding, company setup, project list/create, clear empty/error states.

**AI:** none.

**Testing:** migration tests; login/session; Owner/Manager/Foreman policy matrix; Company A vs Company B and direct-ID isolation tests.

**Security:** default-deny scoped queries and production-safe cookies/secrets.

**Completion criteria:** no user can read, modify, upload to or enumerate another company's project data.

## Phase 2 — persistent manual SiteRecord

**Objective:** create the product core without depending on AI.

**User outcome:** a foreman can manually create a Draft, review it, save it, reopen it and see who/when created it.

**Technical/database work:** SiteRecord, child resource entities, SiteRecordVersion, AuditEvent, record number allocation, Draft/Saved transition, optimistic locking, transactional service methods.

**UI:** mobile-first manual capture/review/save, project record list and basic date/type/status filtering.

**AI:** none; original text account may be retained as supporting context.

**Testing:** validation/bounds/state-transition/record-number tests; cross-tenant child-resource tests; save rollback/version integrity tests; mobile E2E manual journey.

**Security:** server owns author/company/project/status; client cannot submit arbitrary ownership IDs.

**Completion criteria:** a saved manual record persists across login sessions with immutable initial version and audit event.

## Phase 3 — evidence

**Objective:** make photos/files durable, private and record-linked.

**User outcome:** a foreman captures photo evidence without losing its context.

**Technical/database work:** object-storage adapter; EvidenceItem model; generated storage keys; upload processing/status; thumbnails; deletion/retention job; private PDF/evidence access path.

**UI:** camera/gallery input, file progress, retry/remove, optional captions, unavailable/failed states.

**AI:** evidence may be listed as support; do not create unconfirmed visual observations.

**Testing:** byte/MIME/size validation; upload interruption/retry; signed URL/authz; cross-tenant storage denial; deletion/audit tests.

**Security:** private bucket, short-lived signed URLs, configurable limits, no original-filename storage keys.

**Completion criteria:** failed evidence never appears saved; authorised record users alone can access it.

## Phase 4 — AI capture

**Objective:** speed capture with voice/text-to-structured draft while preserving manual fallback.

**User outcome:** a foreman dictates what happened and receives an editable draft plus only material questions.

**Technical/database work:** dedicated AI service/config; versioned strict extraction schema; provenance/draft metadata; provider retry/backoff/timeouts; idempotency; usage/spend telemetry and limits.

**UI:** editable transcript, draft-processing status, targeted questions, Recorded/Needs confirmation/Not recorded states, retry/manual continuation.

**AI:** extraction/classification/missing-field detection only. No direct persistence of AI fields as facts.

**Testing:** gold fixtures, hallucination traps, malformed JSON repair, provider outage, quota/limit and prompt-injection tests.

**Security:** redacted logs, server-only credentials and privacy-approved provider configuration.

**Completion criteria:** absent data remains not recorded; user can save manually during an AI outage; provider call is blocked at company allowance.

## Phase 5 — review and reporting

**Objective:** make review authoritative and create the first professional output.

**User outcome:** users correct/confirm the draft and export a trustworthy Site Record PDF.

**Technical/database work:** review/save service hardening, version conflict handling, server-side report service/template, private generated PDF metadata/storage.

**UI:** grouped mobile review form, explicit confirmation/save, accessible validation, export progress/error/success actions.

**AI:** no AI during PDF generation; output uses reviewed saved version only.

**Testing:** compare saved data/version against PDF mapping; visual A4 regression scenarios; review E2E with removal/correction of AI output.

**Security:** download/export authorisation and no guessable public files.

**Completion criteria:** an exported PDF contains only reviewed data, correct record/version identity and legible evidence sections.

## Phase 6 — history, reliability and production hardening

**Objective:** make records findable, service behaviour reliable and production operation safe.

**User outcome:** teams recover work after poor connectivity and can find/change-history records confidently.

**Technical/database work:** indexed history/search; read-only version/audit views; local browser draft recovery/idempotency; initial PWA cache; error monitoring, backups/restore drill, health checks, operational runbook, dependency/security scans.

**UI:** record history, filters, audit/version display; honest not-saved/pending/failed/retry states.

**AI:** optional queued request only after explicit action; never show completion until validated response.

**Testing:** offline/interrupted workflow, duplicate save, local recovery, restore, security regression and load/latency smoke tests.

**Security:** data retention/deletion, production/staging separation, file lifecycle review and published privacy/support materials.

**Completion criteria:** production readiness checklist in the technical architecture is complete, including tenant tests and tested backup restore.

## Phase 7 — commercial and manager workflow

**Objective:** organise trusted record evidence into commercial workflows after pilot validation.

**User outcome:** QS/manager can build registers, packs and accountable reviews from source records.

**Technical/database work:** delivery/approval/dispute/register concepts linked to records; no ambiguous status overloading.

**UI:** manager queue, daywork/variation/delay views, evidence pack selection, export and controlled share flow.

**AI:** optional editable summaries from reviewed sources with citations.

**Testing/security:** approval/version/audit and external-share expiry/revocation tests.

**Dependencies:** Phases 1–6 and successful real pilot use.

**Completion criteria:** every commercial output traces back to reviewed records/evidence; no system action claims legal validity or approval.

## Phase 8 — project intelligence

**Objective:** search and answer over a secure, accumulated project evidence graph.

**User outcome:** teams find instructions/events/evidence and receive source-cited summaries or document answers.

**Technical/database work:** project document model, private storage/indexing, tenant/project-scoped vector retrieval, searchable record/event timeline.

**UI:** project search, source opening, answer basis labels: Document-based, Record-based, General guidance, Unable to answer.

**AI:** cited retrieval/summarisation only; no uncited definitive contract/legal conclusion.

**Testing/security:** document/chunk scope tests, citations/page tests, embedded prompt-injection fixture tests.

**Completion criteria:** a project query cannot retrieve another company's data; every document claim carries a source/page reference.

## Milestones and release gates

| Milestone | Required phases | Gate |
| --- | --- | --- |
| Secure record foundation | 1–2 | Manual records are persistent, isolated and audited |
| First usable MVP | 3–5 | Foreman can capture/review/save/export with manual fallback |
| Production MVP | 6 | Security, reliability, history and operations pass release checklist |
| Commercial beta | 7 | Pilot proves repeated capture quality and office value |
| Intelligence expansion | 8 | Document/evidence retrieval supports, not distracts from, core product |

## First implementation slice

Build **the application foundation plus a manually entered Draft/Saved SiteRecord**, not AI capture.

Scope:

1. Testable Flask app configuration and migrations.
2. User, Company, CompanyMembership and Project with Owner/Manager/Foreman authorisation.
3. SiteRecord with project/date/type/work summary, Draft/Saved, author/timestamps, immutable first version and audit event.
4. One mobile manual create/review/save/reopen journey and project list.
5. Access-control and state-transition tests.

Deliberately leave untouched: Anthropic prompt redesign, voice changes, evidence upload replacement, PDF generation, full offline queue, document Q&A redesign, billing and manager approval. This slice is low-risk, directly useful and establishes the durable system of record that every later feature needs.

## Current technical debt to retire in sequence

- Before Phase 1: README local-start/port mismatch; no app factory/test/migration tooling.
- Before customer documents/evidence: `instance/` local uploads, shared Chroma collection and legacy unscoped `doc_qa`.
- With Phase 4: hard-coded model/client calls, free-form report output, unhandled provider failures/cost checks.
- With Phase 5: browser-print-as-report output and dispersed inline workflow styling.
- Before production invitation: missing monitoring/backups/restore, retention/deletion process, security scans and incident runbook.
