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
An AI assistant calibrated to UK construction practice. Ask about JCT/NEC contracts, estimating, BIM, tendering, and site management, and get answers framed around how the industry actually works — with full conversation context.

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

  ---

## Technology

- Python / Flask with Blueprints
- Anthropic Claude API (with Vision for image analysis)
- Jinja2 templates
- Flask sessions for conversation state
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

# 5. Run the app
python app.py
```

Open your browser at `http://127.0.0.1:5000`

To generate a stable `SECRET_KEY`, run:
`python -c "import secrets; print(secrets.token_hex(32))"`

---

## Deployment

Deployed on Railway from this repository. Environment variables (`ANTHROPIC_API_KEY`, `SECRET_KEY`) are managed via Railway's Variables panel. The production server is gunicorn, bound via the `Procfile`.
