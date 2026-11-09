# Phase 1: Daywork & Site Record MVP

## Decision

Mate's first product wedge is an evidence-first **Daywork & Site Record** for UK subcontractors. It is not a general site-management platform and it does not decide contractual entitlement.

**Product promise:** Capture what happened on site today in under two minutes, turn it into a clear record, and preserve the facts needed to support payment or resolve a disagreement later.

The existing Site Report Generator is the starting point. Phase 1 defines the professional workflow it must become before broader tools are added.

## The user and buyer

### Primary user: working foreman

A working foreman is managing labour and doing work, often on a noisy site with poor signal and little time. They are likely using a phone, may wear gloves, and will abandon a form that feels like office paperwork.

They need to capture a change, instruction, delay, or extra work while it is fresh—not reconstruct it at the end of the month.

### Buyer: subcontractor owner, commercial manager, or QS

The buyer wants records that are consistent across teams, easy to find, and credible enough to support an application for payment, a daywork sheet, or an internal commercial review.

### Not the first user

Main contractors, clients, designers, and large enterprise teams may be future users, but Phase 1 does not attempt their approval workflows, integrations, or procurement requirements.

## Problem to solve

On many projects, additional work and disruption are communicated verbally or through fragmented WhatsApp messages. The record is incomplete, photos become detached from the context, and labour/plant/material details are forgotten. When a QS asks for substantiation later, the team must reconstruct the story from memory.

Mate must make a good record easier to create than a bad one. It should prompt for the few details that make an event understandable, while never filling gaps with AI guesses.

## MVP outcome

By the end of a shift, a foreman can:

1. choose the project;
2. speak or type a short account and attach supporting photos;
3. answer only the relevant follow-up questions;
4. review a structured AI draft;
5. correct it and explicitly save it; and
6. export a professional PDF or share it with the office.

The saved record is the foreman's reviewed version. AI output is always a draft.

## Jobs to be done

| Situation | Job | Successful outcome |
| --- | --- | --- |
| Extra work is requested on site | Record what changed, who asked, and what resources were used | Office can price or pursue it without asking the crew to reconstruct events |
| Work is delayed or blocked | Capture the factual cause, time impact, and evidence | Team can see a reliable timeline of blockers |
| Normal progress needs recording | Produce a concise daily site record | Manager has a consistent project history |
| A commercial question is raised later | Find the original reviewed record and photos | Evidence is traceable to a date, project, and author |

## Scope

### In scope

- Account holder selects a company and project.
- Mobile-first record creation from text or browser voice dictation.
- Multiple photo attachments with a clear capture/upload state.
- One optional record type: `daily site record`, `daywork / variation`, or `delay / blocker`.
- AI extraction into a fixed, validated set of fields.
- Short, conditional follow-up prompts for material missing evidence.
- User review, manual editing, and explicit save.
- Timestamped saved history per project.
- Clean A4 PDF export with photos and a record reference.
- MVP statuses: Draft and Saved. Sent, Signed off and Disputed are later
  commercial-workflow statuses, introduced only with real delivery, approval
  and dispute flows.

### Deliberately out of scope

- Determining whether a change is contractually a variation or an entitlement.
- Automatic valuation, invoicing, payment chasing, or adjudication packs.
- Full RAMS, permits, snagging, toolbox talks, timesheets, or programme management.
- OCR of drawings, email/WhatsApp ingestion, and integrations with CDEs/accounting packages.
- Offline-first synchronisation. The UI may preserve entered form content locally after a failed submission, but reliable queued sync is a later capability.
- Complex roles, external approvers, or multi-company project collaboration.

This boundary matters: the MVP creates a stronger factual record; it must not over-promise legal or commercial certainty.

## Core record model

The UI should use structured fields even if the first PDF remains familiar to site teams. Fields marked **Required when relevant** must never be invented; the UI should show `Not recorded` if the user chooses not to provide them.

### Record identity

- Record reference (generated on save, for example `MATE-CRD-000123`)
- Project and site
- Record date (defaults to today; editable)
- Created by
- Created/saved timestamps
- Record type
- Status

### Site account

- Summary of work completed
- Workforce: trade, headcount, hours where provided
- Plant/equipment used
- Materials used or delivered
- Safety observations or incidents
- Next planned action

### Daywork / variation evidence

- What changed or was requested
- Why it was outside the expected work, in the user's own words
- Instruction source: person, company, and verbal/written method where known
- Instruction/reference number **Required when relevant**
- Labour: person/trade, number, hours **Required when relevant**
- Plant: item, quantity, hours **Required when relevant**
- Materials: item, quantity, delivery/supplier reference where known **Required when relevant**
- Supporting photo(s)
- Required action / who needs to respond

### Delay / blocker evidence

- Blocker or delay description
- Start time and end time, or ongoing
- Impact on work, stated factually
- Person/company notified, if known
- Supporting photo(s)
- Required action

## Experience principles

1. **Voice first, form second.** Start with one large “Tell Mate what happened” control. Do not force a tired foreman through a blank multi-section form.
2. **Ask only what earns its place.** Follow-up questions appear only when the account indicates extra work, a delay, labour, plant, materials, safety, or an instruction.
3. **Facts, not conclusions.** “Client asked us to move…” is a fact. “This is an approved variation” is not something Mate may declare.
4. **Review is a real step.** The user sees and can edit every field before Save. “Generate” must not silently create the business record.
5. **Large, forgiving controls.** Minimum 44px touch targets; clear labels; photo and microphone state always visible.
6. **No dead ends.** A failed upload, AI timeout, unsupported voice browser, or poor connection should preserve typed content and explain the next action in plain English.
7. **A PDF is a sharing format, not the database.** The structured record remains the source of truth; the PDF is a snapshot of its reviewed content.

## MVP flow

### 1. Start a record

The home/project screen has one primary action: **New site record**. The foreman chooses a project if more than one is active, then sees:

- record type selector, defaulting to `Daily site record`;
- date, defaulting to today;
- large voice/text input;
- add photo button; and
- `Create draft` button.

Helpful prompt: “For example: what was completed, anything extra requested, anything that stopped work, and what is planned next.”

### 2. Capture the account

The foreman dictates or types naturally. Voice transcription is editable before proceeding. Photos may be added before or after the account. Each photo displays a thumbnail, upload progress, remove control, and an optional short caption.

The system must not analyse a photo as an independent source of site facts. A photo can only support information the user confirms in the record.

### 3. Identify the record type and missing essentials

Mate extracts a structured draft. It may suggest a different record type, but the user chooses the final type.

For a daywork/variation draft, Mate asks compact prompts such as:

- “Who asked for or instructed this work?”
- “How many people and hours were involved?”
- “Was plant or material used? Add it if relevant.”
- “Add a photo or reference if you have one.”

For a delay/blocker draft:

- “When did the issue start, and is it still ongoing?”
- “What work could not proceed?”
- “Who was told?”

Every prompt can be answered, skipped, or marked `Not recorded`. Skipping must not be framed as an error, but records with missing evidence should show a clear completeness indicator.

### 4. Review and edit

The review screen is a clear form, not a wall of generated prose. It groups fields into:

- Today’s work
- Extra work / delay, if applicable
- Resources
- Evidence
- Safety and next actions

Each AI-populated field is editable. Missing values are visibly distinct from confirmed values. The original voice/text account can be retained as supporting context, but it must not be confused with the reviewed record.

Primary actions:

- `Save record`
- `Save and export PDF`
- `Back to edit`

### 5. Save and share

Saving assigns the record reference and retains the reviewed fields, author, timestamps, photos, and current status. The user receives an in-app confirmation—not a browser alert—with actions to view the PDF, share, or return to the project.

`Sent` is not part of the first MVP. It will be introduced with a real delivery
and recipient-tracking workflow rather than acting as an unsupported label.

### 6. Find a previous record

The project screen lists recent records with date, type, reference, status, and a one-line summary. Initial filtering only needs date range, type, and status. This makes saved history useful without prematurely building a dashboard.

## AI and trust requirements

- Use a schema-validated response, not prose parsing, for every draft.
- Each field should carry a simple provenance flag: `user stated`, `user confirmed`, or `not recorded`. Phase 1 does not need to expose technical provenance language to users, but the system needs it for safe behaviour.
- Never infer weather, quality, quantities, labour hours, instruction authority, safety compliance, contractual status, or photo observations.
- AI may convert wording into clear professional language but must preserve the factual meaning.
- If the AI service fails, allow the user to complete and save a manual record. AI improves speed; it must not be the only path to documentation.
- Show a concise disclaimer on daywork records: “This record captures site facts. It does not confirm contractual entitlement, valuation, or approval.”

## First-release permissions

Phase 1 only needs three roles, kept intentionally simple:

| Role | Can do |
| --- | --- |
| Owner | Manage company, projects, members, and all records |
| Manager | Create and edit project records; update status; export |
| Foreman | Create, edit own drafts, save records, and export |

Every project and record must belong to one company. A user must never be able to access a record outside their company/project membership.

## Success measures

Track these from the first pilot, with consent and without storing unnecessary content in logs:

- Median time from new record to save: target under 2 minutes.
- Percentage of records saved after a draft is generated.
- Percentage of daywork/delay records with an instruction/contact, resource detail, and at least one photo when available.
- Weekly active foremen per company.
- Records exported or marked sent per active project.
- Number of AI failures that still result in a manually saved record.

Pilot success is not chat usage. It is whether a team uses Mate for real records on consecutive site days and says the saved records are good enough for office/commercial use.

## Acceptance criteria

The MVP is ready for a small pilot when:

- A foreman can create, review, save, reopen, and export a record on a phone.
- Records are correctly isolated by company and project.
- AI-created drafts are structured, editable, and never silently saved.
- A manual path works when AI or voice input is unavailable.
- Photo upload errors, invalid form data, unauthorised access, and AI failures have useful in-app messages rather than raw server errors.
- A saved PDF shows the reviewed content, record reference, project, author, saved time, status, and attached evidence references.
- The product makes no claim that work is approved, payable, compliant, or contractually valid.

## Implementation sequence after approval

1. Agree the record fields and mobile screen flow with two or three target users.
2. Add accounts, company, projects, memberships, and secure record ownership.
3. Add structured record persistence and manual create/edit/save before adding AI.
4. Adapt the existing voice/site-report capability to produce a schema-validated draft.
5. Add photos, PDF export, history, statuses, and reliable error states.
6. Run a pilot with one small subcontractor, review real records weekly, and only then add sign-off or commercial features.
