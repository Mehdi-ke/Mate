# Mate

**One place for AI tools built for the construction industry — by someone who's worked in it.**

Mate is a unified web platform housing a growing set of AI-powered tools for UK construction. Each tool solves a specific, real problem for site teams, estimators, and commercial staff. Everything runs in one place, works on a phone, and requires no installation — a worker just opens a link.

**Live:** [mate-construction.up.railway.app](https://mate-construction.up.railway.app)

---
<img width="1881" height="893" alt="mate3" src="https://github.com/user-attachments/assets/09863aed-7887-4077-9c97-1f892f985ec9" />
<img width="1822" height="888" alt="mate2" src="https://github.com/user-attachments/assets/2d510c7f-58a3-4e24-85e4-fb25983ab7c9" />
<img width="1877" height="556" alt="mate1" src="https://github.com/user-attachments/assets/52c21817-184d-4f4c-b5c4-7dc1ab848a2e" />

---

## The Problem It Solves

Construction teams lose time to admin that could be automated: writing up site reports after a long shift, chasing answers to contract questions, summarising tender documents. Off-the-shelf AI tools don't understand construction — they don't know JCT from NEC, or how a site report should be structured.

Mate brings purpose-built construction tools together under one roof. Instead of separate apps with separate logins and separate looks, a team gets one consistent platform they can open on any device, on site or off.

---

## Who Uses It

- **Site operatives and managers** — generate formal site reports by voice or text at the end of a shift
- **Estimators and commercial staff** — get fast, UK-calibrated answers on contracts, pricing, and procedure
- **Construction businesses** — a single tool their teams can adopt without training or setup

---

## Tools Inside Mate

### Site Report Generator
A worker describes their day in plain English or by voice. Mate generates a formal, structured 16-section site report in seconds — with optional AI analysis of an uploaded site photo. Print-ready A4 output.

### Construction AI Assistant
An AI assistant calibrated to UK construction practice. Ask about JCT/NEC contracts, estimating, BIM, tendering, and site management, and get answers framed around how the industry actually works. Upload PDFs and the assistant will answer from them with page-level source citations, powered by a heading-aware RAG pipeline.

### Document Q&A
Upload a PDF and ask questions against it. Answers are drawn from the document with inline page citations, so you can verify every claim. Built on the same RAG pipeline as the Construction AI Assistant.

*More tools are added over time. The platform is built so new tools plug in without disrupting existing ones.*

---

## Built For Phones

Mate is mobile-first. Site teams work on phones, not desks — so every tool is designed to be fully usable on a phone screen, with touch-friendly controls and layouts that adapt from desktop to mobile automatically.

---

## Architecture

Mate is a single Flask application built around **Flask Blueprints** — each tool is a self-contained module that plugs into a shared application shell (navigation, styling, session handling, API management). This means:

- One deployment, one URL, one consistent look — not several separate apps
- New tools are added as new Blueprints without touching existing ones
- Shared infrastructure (API handling, theming, mobile responsiveness) is written once and reused

### Authentication

All tools sit behind a login boundary. Users register with email and password, and every endpoint (except login, register, and static assets) requires an authenticated session. CSRF protection is enforced on all forms.

### RAG Pipeline

Document-based Q&A uses a retrieval-augmented generation pipeline shared across tools:

1. **Extract** — PyMuPDF extracts text and tables (as markdown) page by page
2. **Chunk** — text is split into 1000-character chunks with heading-aware context (chunks under "Clause 2.3 Extension of Time" get labelled so they never lose their place in the document)
3. **Embed** — chunks are stored in ChromaDB with BAAI/bge-base-en-v1.5 embeddings
4. **Retrieve** — queries are rewritten to resolve pronouns, then 10 candidate chunks are fetched and re-ranked (max 3 per page, best 6 total)
5. **Answer** — relevant excerpts are injected into the system prompt; Claude answers with inline source citations

---

## Technology

- Python / Flask with Blueprints
- Flask-Login (session authentication) + Flask-WTF (CSRF-protected forms)
- Flask-Migrate / Alembic (database migrations)
- SQLAlchemy ORM (PostgreSQL on Railway, SQLite locally)
- Anthropic Claude API (with Vision for image analysis)
- ChromaDB with BAAI/bge-base-en-v1.5 embeddings for document retrieval
- PyMuPDF for PDF text and table extraction
- LangChain text splitters (heading-aware chunking)
- Jinja2 templates
- Web Speech API for voice input
- CSS Grid, mobile-first responsive design, unified theming via CSS variables
- Deployed on Railway with gunicorn

---

## How to Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/Mehdi-ke/Mate
cd Mate

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
# Create a .env file in the project root:
ANTHROPIC_API_KEY=your-key-here
SECRET_KEY=your-stable-secret-key
# Optional: FLASK_CONFIG=development (default), testing, or production

# 5. Apply database migrations
flask db upgrade

# 6. Run the app
flask run
```

Open your browser at `http://127.0.0.1:5001`

To generate a stable `SECRET_KEY`, run:
`python -c "import secrets; print(secrets.token_hex(32))"`

> **Note:** The first `flask run` will download the BAAI/bge-base-en-v1.5 embedding model (~400 MB). Subsequent starts load it from cache (~5 s).

---

## Deployment

Deployed on Railway from this repository. Environment variables are managed via Railway's Variables panel:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API access |
| `SECRET_KEY` | Session signing (must be stable and random) |
| `DATABASE_URL` | PostgreSQL connection string (Railway provides this) |
| `FLASK_CONFIG` | Set to `production` for production mode |

The production server is gunicorn, bound via the `Procfile`.
