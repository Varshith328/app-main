AI Document Summarizer
A small full‑stack app that accepts PDF/TXT, calls an LLM to produce section-wise and overall summaries, and stores results in MongoDB.

Quick Start

Prereqs: Install Python 3.8+, Node.js & npm, and run a local MongoDB instance.

Backend (run):
cd C:\Users\91995\Downloads\app-main\app-main\backend
pip install -r requirements.txt
# create backend/.env from backend/.env.example and fill keys
python server.py

Frontend (run):
cd C:\Users\91995\Downloads\app-main\app-main\frontend
npm install --legacy-peer-deps
npm start

Environment Variables

Backend (.env):
MONGO_URL — MongoDB connection (e.g. mongodb://localhost:27017)
DB_NAME — DB name (e.g. test_database)
CORS_ORIGINS — Allowed origins (e.g. * for dev)
GEMINI_API_KEY — Google Gemini API key (or your LLM provider key)
Frontend (.env if used):
REACT_APP_BACKEND_URL — e.g. http://localhost:8000
Key Files

server.py: upload handling, text extraction, chunking, LLM call, Mongo persistence.
requirements.txt: Python deps.
frontend/src/pages/HomePage.js: upload UI and API integration.
craco.config.js and frontend/plugins/*: dev tooling (visual edits, health-check).
index.html: static HTML (branding).
backend/list_models.py: helper to list available Gemini models.
Architecture (short)
Browser (React) → POST /api/summarize → FastAPI backend → LLM provider (Google Gemini) → MongoDB. Dev-only: CRACO dev server with visual-edits and health-check plugins.

Demo (what to show)

Start backend + frontend.
Open http://localhost:3000, upload a PDF/TXT, click Summarize.
Inspect network request to /api/summarize and show returned sections + overall summary.

