# Mate codebase audit — investigation and recommendations

**Date:** 9 November 2026
**Scope:** full read of the application code, templates, migrations, config, deployment files and roadmap docs, plus a live verification run against an isolated copy of the app (in-memory database, test account; no real data touched).
**Baseline commit:** `595357d` ("Run flask db upgrade before gunicorn on Railway to fix missing user table").

---

## 1. Current state

Mate is now a multi-user Flask platform:

- **App factory** (`app.py` / `create_app`) with a config hierarchy (`development` / `testing` / `production`) in `config.py`.
- **Authentication**: Flask-Login with a default-deny `before_request` gate — every endpoint requires sign-in except `auth.login`, `auth.register` and `static`. CSRF protection (Flask-WTF) is enabled globally. Flask-Migrate is bootstrapped.
- **Persistence**: Postgres via `DATABASE_URL` on Railway, SQLite locally; ChromaDB (persistent, `instance/chroma_store`) with BAAI/bge-base-en-v1.5 embeddings and a silent fallback to MiniLM.
- **Three tools** (blueprints):
  1. **Site Report Generator** — voice/text + optional photo → structured UK site report (stateless, no persistence).
  2. **Construction Assistant** — chat with conversation persistence (Conversation/Message tables), 10-message cap with summary handoff, per-conversation PDF upload, RAG with query rewriting, heading-aware chunking, table extraction, re-ranking and inline citations.
  3. **Doc Q&A** — standalone PDF upload + single-document Q&A over the same RAG pipeline.
- **Shared RAG pipeline** in `tools/document_processing.py` — genuinely strong work (page metadata, heading detection for clauses/sections, markdown table extraction, per-page diversification, relevance threshold).
- **Roadmap docs** in `docs/` defining the Phase-1 wedge: an evidence-first **Daywork & Site Record** for UK subcontractors. The product direction is sound.

---

## 2. Critical findings (fix before any new feature)

### 2.1 All three tools are non-functional — CSRF regression (VERIFIED)

Gate 1 enabled `CSRFProtect` globally, but only the auth forms include tokens (`form.hidden_tag()`). The tool forms do **not**:

- site report: generate form
- assistant: chat form and upload-doc form
- doc-qa: upload form and ask form

Verified with a test client: login succeeds, all pages render (200), but `POST /tools/site-report/generate` returns **400 "Your form expired. Please try again."** The only `csrf_token` on each tool page belongs to the logout form in `base.html`. Every submit button in every tool currently fails.

**Fix:** add `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` to each tool form.

### 2.2 Migrations do not create most of the schema

The only migration (`a060314092cf_initial_schema_with_user_table.py`) creates the `user` table. `conversation`, `message` and `document` exist in no migration. The Procfile now relies on `flask db upgrade` at boot, so any **fresh** database (new Railway environment, new developer machine) will be missing three tables and the tools will crash once CSRF is fixed. Production likely only works because an older deploy ran `db.create_all()`.

**Fix:** `flask db migrate -m "add conversation, message, document"`, review the generated script, commit. (Combine with 2.3's `user_id` columns in one migration if done together.)

### 2.3 No per-user data separation — cross-user data leak

`Conversation`, `Message` and `Document` have **no `user_id`** (models.py). Conversations are keyed off the browser session cookie, not the account. Worse, `doc_qa` lists **all** standalone documents to **every** signed-in user (`Document.query.filter_by(conversation_id=None)`): any registered user can see and query documents uploaded by any other user. For a product aimed at contracts and commercial records this is the most important structural gap.

**Fix:** add `user_id` FK to `Conversation` and `Document`; filter every query by `current_user.id`; key the "current conversation" off the user rather than the session cookie (also fixes history not following the user across devices/logins).

### 2.4 Unsafe file uploads

Both upload routes save the raw client filename:
`file.save(os.path.join(UPLOAD_FOLDER, file.filename))` — a crafted filename can escape `instance/uploads` (path traversal), and identical filenames silently overwrite each other. There is no `MAX_CONTENT_LENGTH`, so arbitrarily large uploads are accepted.

**Fix:** `werkzeug.utils.secure_filename`, save under the already-generated `doc_id`, and set `MAX_CONTENT_LENGTH` (e.g. 20 MB) in config with a friendly 413 handler.

### 2.5 Open registration + unmetered AI spend

Anyone can register and make unlimited Claude calls on the project's API key. There is also no rate limiting on login (brute-force exposure). This contradicts the project's own rule: meter what costs money and gate it before the cost is incurred.

**Fix (minimum viable):** a `usage` table with a per-user daily cap checked before each AI call; an env flag to close registration or require an invite code until metering matures; Flask-Limiter on `auth.login` (and optionally on AI endpoints).

### 2.6 A Claude API failure is an unhandled 500

`client.messages.create` in chat, doc-qa and site report has no error handling (only `rewrite_query` has a try/except). An Anthropic outage, rate limit or timeout puts a raw error page in front of the user. `error.html` exists but is wired only to CSRF errors.

**Fix:** wrap AI calls (catch `anthropic.APIError` family), return the page with a friendly "temporarily unavailable, try again" message; add generic 404/500 handlers rendering `error.html`; add a retry with backoff for transient failures.

---

## 3. Important — will bite on Railway

### 3.1 Ephemeral-disk drift (vectors and uploads)

Chroma data (`instance/chroma_store`) and uploaded PDFs (`instance/uploads`) are wiped on every Railway redeploy, while Postgres `document` rows survive. Result: the UI lists documents whose chunks no longer exist; retrieval silently returns "no match" and looks like bad AI.

**Recommendation:** move vectors to **pgvector** on the existing Postgres (removes the drift and most of 3.2), or explicitly treat documents as per-deploy ephemeral and clean up DB rows on boot. Decide deliberately; don't leave the drift.

### 3.2 Heavy embedding stack in the web process

Startup contacts Hugging Face and loads the ~400 MB bge model into RAM at import time (observed during verification) — the reason for `--timeout 120`. Risks: OOM on small instances, slow cold starts, and the silent MiniLM fallback means production retrieval quality can differ from local without anyone noticing (different collection names `mate_documents` vs `mate_documents_v2` mask the difference).

**Recommendation:** pgvector + a hosted embedding API, or at minimum lazy-load the model on first use and log loudly which embedding function is active.

### 3.3 Production config not confirmed

`ProductionConfig` (secure cookies, `DEBUG=False`) only applies if `FLASK_CONFIG=production` is set on Railway. If unset, the default is **development**: `DEBUG=True` and insecure session cookies in production. Verify the Railway variable.

---

## 4. Worth tidying

| Item | Detail |
| --- | --- |
| Hardcoded model IDs | `claude-haiku-4-5-20251001` in 3 files; move to one config var (project rule: model IDs configurable). |
| doc-qa `max_tokens=500` | Truncates real answers; raise or make configurable. |
| Doc Q&A not on home page | Reachable only by URL — but see §5.2 before "fixing" this. |
| No tests | pytest installed, zero tests. The CSRF regression is exactly what a 10-line smoke test (login → POST each tool → expect 200) would have caught. |
| `docs/` untracked | All six roadmap files are uncommitted — commit them; they are the product memory. `.flaskenv` also untracked. |
| `.gitignore` | Duplicate `.pytest_cache/` line; ignores `scripts/` (confirm that's deliberate). |
| Datetime inconsistency | `User` uses timezone-aware defaults; `Conversation`/`Message`/`Document` use naive `datetime.utcnow` / `db.func.now()`. Standardise on timezone-aware. |
| Auth gaps (deferable) | No password reset, no email verification, no session rotation on login. Fine to defer — record as known debt. |
| Requirements bloat | Chroma pulls kubernetes/uvicorn/opentelemetry etc. into the image; a pgvector move slims deploys considerably. |

---

## 5. Recommendations

### 5.1 Step 1 — Stabilise (before any Phase-1 feature; ~1 day)

In order:

1. CSRF tokens in all five tool forms (restores the product).
2. Migration for the missing tables.
3. `user_id` on `Conversation` and `Document`; all queries filtered by `current_user`; conversation keyed off user (one migration can cover 2+3).
4. `secure_filename` + `doc_id`-based storage + `MAX_CONTENT_LENGTH`.
5. Registration gate (env flag / invite code) + per-user daily AI cap + login rate limiting.
6. Error handling around all Anthropic calls + generic 404/500 handlers.
7. A smoke-test suite (auth gate, one POST per tool, upload validation, data isolation) so none of this silently regresses again.

### 5.2 Step 2 — Prune before building

Phase 1 is the Daywork/Site Record. Doc Q&A duplicates the assistant's RAG and is the largest data-leak surface. Fold it into the assistant (same `document_processing` pipeline) or park it behind an admin flag. One tool done professionally beats three half-wired ones, and it shrinks the stabilisation surface.

### 5.3 Step 3 — Make the infrastructure boring

- pgvector migration when documents are next touched.
- Model ID into config; consider current model line-up when revisiting.
- Keep AI behind a thin service layer (one module owning client, model, retries, fallback chain) so providers stay swappable.
- Then build the `SiteRecord` model from the master roadmap on solid ground.

### 5.4 Overall verdict

The product strategy in `docs/` is right and the RAG engineering is above-average for this stage. The gap is that **Gate 1 shipped half-finished**: identity exists, but the tools were never re-wired to it — CSRF, ownership and migrations. Stabilise first; the wedge comes faster on a floor that holds.
