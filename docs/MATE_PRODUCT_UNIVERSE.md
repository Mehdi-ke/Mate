# Mate product universe

## Document role and source of truth

This document defines the product boundary and expansion logic for Mate. [`phase-1-daywork-record-mvp.md`](phase-1-daywork-record-mvp.md) remains the authoritative first-workflow specification. [`MATE_MASTER_ROADMAP.md`](MATE_MASTER_ROADMAP.md) is the detailed cross-functional master plan; this document answers **what Mate should become**, while `MATE_IMPLEMENTATION_ROADMAP.md` answers **what to build, in what order**.

## Product vision

Mate helps UK subcontractors capture what happened on site, structure it into reliable records, preserve supporting evidence, and turn that evidence into useful commercial and operational outputs.

Mate is not an AI toolbox. Its value compounds when a project accumulates a trustworthy evidence history: records, photos, resources, instructions, blockers, documents and reviewed outputs all remain connected to the same project.

## Target users

| User | Situation | Mate outcome |
| --- | --- | --- |
| Working foreman | Busy, mobile, often with poor signal; needs to record a shift before leaving site | Creates a credible record with little typing |
| Subcontractor owner | Needs proof of work and fewer reconstructed claims | Sees consistent records across projects/teams |
| Commercial manager / QS | Needs evidence for extra work, delay and payment support | Finds traceable facts, resources and exports |
| Project manager | Needs an accurate operational picture | Reviews patterns and actions from saved records |

The working foreman is the primary design user. The owner, commercial manager and QS are buyers or later workflow users; their needs must not make the creation flow office-heavy.

# MATE PRODUCT UNIVERSE

## A. Core product: the evidence platform

The unbroken core workflow is:

```text
Capture -> Structure -> Evidence -> Review -> Saved SiteRecord -> Output / History
```

| Capability | Classification | Why it belongs |
| --- | --- | --- |
| Project-scoped SiteRecord | Core | The durable unit of product value |
| Voice/text account of the shift/event | Core | Lowest-friction capture mechanism |
| Work, labour, plant and materials | Core | Explains what happened and what resources were involved |
| Instructions, extra work, delays and blockers | Core | Commercially important context, captured as facts not conclusions |
| Photos and captions | Core | Supporting evidence tied to a record |
| Human review/edit/save | Core | The trust boundary between AI draft and business record |
| Versions/audit trail | Core | Makes records traceable and commercially useful |
| Professional Site Record PDF | Core | A portable reviewed snapshot, not the database |
| Project history/search | Core | Lets the evidence become useful after capture |

## B. MVP: the smallest commercially useful product

### MVP required

1. Authenticated company, project and role boundary.
2. A foreman selects a project, speaks or types an account and adds photos.
3. A manual form path that works even if voice or AI does not.
4. AI creates a schema-validated draft and identifies only material missing evidence.
5. User reviews, edits/removes fields, marks facts not recorded where needed, and explicitly saves.
6. A persistent Draft/Saved SiteRecord with author, timestamps, project, evidence, version and audit event.
7. Private evidence storage and a professional PDF generated from the reviewed saved version.
8. Project record history with basic date/type/status filtering.

### MVP useful but optional

- Browser voice dictation where supported; never make it the only capture path.
- Multiple photos and optional captions.
- A simple completeness indicator for daywork/delay records.
- Local browser draft recovery after an interrupted connection.
- Project member assignment if pilots demonstrate not every company member should see every project.

### Not MVP

- External approval/sign-off workflow.
- Variation valuation, invoice generation, payment chasing or legal notices.
- Automated commercial conclusion that something is an approved variation or contractual entitlement.
- Full offline queued synchronisation.
- Weekly/monthly AI summaries, evidence packs, registers or project document Q&A.
- RAMS, permits, snags, timesheets, toolbox talks, RFIs or programme management.

**MVP success definition:** a foreman can create a credible reviewed SiteRecord in under two minutes before leaving site; the office can reopen and trust its project-linked evidence later.

## C. Phase 2: commercial protection

These capabilities should be considered only after pilot teams repeatedly save useful core records.

| Capability | User problem / value | Depends on | Target user | Priority |
| --- | --- | --- | --- | --- |
| Daywork / variation register | Extra work is scattered across records and hard to collate | Reviewed SiteRecords, instructions, labour/plant/material entries | QS / commercial manager | Phase 2, high |
| Delay and blocker register | Disruption timeline is reconstructed too late | Time-stamped blockers and evidence | PM / commercial manager | Phase 2, high |
| Instruction register | Verbal/written directions lack a findable trail | Structured Instruction entity | Foreman / QS | Phase 2, medium |
| Evidence packs | Office needs selected records/photos in one output | Versions, private evidence, PDF service | QS / owner | Phase 2, high once records are trusted |
| Missing-evidence detection | Teams need to improve record quality before a claim | Completeness/provenance fields | Foreman / manager | Phase 2, medium |
| Labour/plant/material summaries | Resource evidence needs aggregation | Normalised entries and reporting | QS / owner | Phase 2, medium |
| Notice/reminder support | Important events are not followed up | Clear event types, users, notifications | Manager | Phase 3; avoid legal notices in Phase 2 |
| Payment/application support | Evidence needs to support an application | Stable commercial workflow and legal/process validation | QS | Later; high consequence |

Phase 2 should organise and report user-confirmed facts. It must not determine contractual rights, valuation or notice validity.

## D. Phase 3: site operations

| Capability | Relation to evidence core | Recommendation |
| --- | --- | --- |
| Site diary / progress tracking | Strong: a daily SiteRecord is the natural source | Evolve from record history, not a separate diary |
| Actions/tasks | Strong when an action originates from a record | Add only record-linked actions initially |
| Site photo log | Strong: views existing EvidenceItems over time | Add timeline/gallery, no parallel photo store |
| Material deliveries | Moderate: can be a structured record entry | Add only if pilots repeatedly need it |
| Labour/plant tracking | Moderate: aggregate existing entries first | Avoid a timesheet/plant-management product initially |
| Meeting records | Moderate: can create instructions/actions | Later; use same evidence/history model |
| Snags/defects | Adjacent but distinct workflow | Later separate module only if customer demand is clear |
| RFIs | Adjacent design-information workflow | Later; do not dilute field capture MVP |
| Toolbox talks / permits / RAMS | Different compliance products | Out of near-term scope |
| Project communications | Broad, difficult to adopt | Do not build a chat/email replacement |

## E. Phase 3+: project intelligence

AI becomes valuable after there is enough structured project evidence. It should query reviewed records and project documents with sources, not create disconnected chat conversations.

| Capability | What it does | Prerequisite |
| --- | --- | --- |
| Project search | Finds records, instructions, evidence and dates | Scoped history and indexing |
| “What happened last week?” | Summarises reviewed records with record citations | Trusted record corpus |
| Commercial event timeline | Groups related instructions, blockers and extra work | Event links/registers |
| Missing-evidence prompts | Identifies gaps before a manager exports an evidence pack | Provenance/completeness data |
| Weekly/monthly summaries | Drafts factual management summaries for review | Complete records and reporting service |
| Project document Q&A | Answers from project documents with page citations | Secure project-scoped documents/retrieval |
| Recurring-problem analysis | Surfaces repeated blockers or site issues | Enough clean historical data |

Every answer must identify its basis: reviewed record(s), cited document(s), general guidance, or insufficient evidence.

## F. Future opportunities

- Accounting/application integrations that link approved commercial packs to the customer's existing financial process.
- Document-management/CDE, cloud-storage and project-management integrations that attach existing evidence rather than replace their systems.
- Controlled email/share workflows and notifications for records requiring attention.
- Native mobile application only if progressive web app reliability and user research show a browser is insufficient.
- Company analytics and anonymised benchmarking only with explicit customer consent and strong data governance.
- Public API/partner integrations after the core permission/audit model is mature.

## G. Explicitly out of scope

Mate should not become:

- a generic construction chatbot or unrelated productivity suite;
- a full ERP, accounting product, CDE or project-management replacement;
- an automated legal-advice, contract-interpretation or adjudication engine;
- a system that confirms variations, entitlement, compliance, approval or value without an accountable human;
- a broad safety/compliance platform merely because it has an AI capability;
- a parallel communication/email/WhatsApp product;
- a feature collection with no connection to project/site evidence.

## Product expansion map

```text
MATE
|
|-- Core Evidence Platform [Core]
|   |-- Project, SiteRecord, reviewed facts, evidence, versions/audit
|   `-- Professional Site Record PDF and project history
|
|-- MVP [MVP]
|   |-- Capture by text/voice + photos
|   |-- Schema-validated AI draft + manual fallback
|   `-- Review, save and retrieve a project record
|
|-- Commercial Protection [Phase 2]
|   |-- Daywork/variation, instruction and delay registers
|   `-- Evidence packs and resource summaries
|
|-- Site Operations [Phase 3]
|   |-- Site diary/progress, record-linked actions, photo timeline
|   `-- Carefully selected delivery/labour/plant views
|
|-- Project Intelligence [Phase 3+]
|   |-- Search, timelines, summaries and missing-evidence detection
|   `-- Project document Q&A with citations
|
|-- Future Opportunities [Future]
|   `-- Integrations, notifications, analytics and API
|
`-- Out of Scope
    `-- Generic chat, ERP, legal conclusions and unrelated tools
```

## Core domain concepts

```text
Company
  -> Project
       -> SiteRecord
            -> WorkItem / LabourEntry / PlantEntry / MaterialEntry
            -> Instruction / DelayBlocker / SafetyObservation / NextAction
            -> EvidenceItem
            -> Version / AuditEvent
       -> ProjectDocument (later)
       -> CommercialEvent / Action (later, linked back to records)
```

`SiteRecord` is the correct central abstraction. It represents an authored account of a moment/day on a project, not a legal claim or a screen-specific form. Repeatable resource data should be child entities. A future CommercialEvent can aggregate several SiteRecords without making each record itself a “variation.” Documents and actions remain separate project objects but must link to relevant records/evidence.

## Product principles

1. Site evidence is the foundation; feature value should strengthen the evidence graph.
2. SiteRecord is a first-class, persistent domain object.
3. AI assists; a user confirms business facts.
4. Missing information is safer than invented information.
5. Evidence remains linked to company, project, record and author.
6. Foreman speed and mobile reliability outweigh feature breadth.
7. Professional outputs are built from reviewed records, not generic AI prose.
8. Commercially important information needs provenance, versions and auditability.
9. Company/project isolation is mandatory, not a premium feature.
10. Build a simple reliable workflow before expanding into commercial or operational products.

