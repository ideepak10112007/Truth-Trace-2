# TRUTH TRACE — AI Digital Forensic Platform

Detect AI-generated / AI-altered media, classify manipulation, verify
originality, fingerprint it, and trace its earliest appearance and spread —
turning the TRUTH TRACE prototype into a working product.

*Chandigarh Police Hackathon 2026 · Team Tesseract*

## Integrity note (read this)

This is a **prototype**. To keep results honest:

- **Real:** SHA-256 hashing, media metadata extraction, perceptual
  fingerprint (pHash) generation, and Hamming-distance similarity matching
  against a **local indexed library**.
- **Simulated / pluggable:** AI-detection and manipulation-type scores +
  heatmap are controlled demo results behind a swappable interface (connect a
  real model later).
- **Indexed, not live:** origin & propagation tracing runs over a local
  indexed corpus — **not** a live social-media feed.

Every panel is tagged `data_source` (`demo` / `indexed` / `live`) so the UI can
badge simulated vs. real results. Not legally conclusive forensic evidence.

## Stack

- **Frontend:** React + TypeScript + Vite + Tailwind (Recharts, React Flow,
  Framer Motion, Lucide)
- **Backend:** Python + FastAPI + SQLAlchemy
- **DB:** SQLite (schema is PostgreSQL-ready)

## Run

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.data.seed          # creates truthtrace.db + demo case
uvicorn app.main:app --reload    # http://localhost:8000  (docs at /docs)
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173  (proxies /api -> :8000)
```

Open http://localhost:5173. The default dashboard loads demo case
`TT-2026-0818-00057`. If the backend is down, the frontend falls back to a
bundled copy of the demo case so it's never blank.

## Layout

```
backend/app/
  core/      config, hashing (sha256 + phash), metadata extraction
  db/        SQLAlchemy engine/session
  models/    ORM: Case, Evidence, Analysis, IndexedMedia
  schemas/   Pydantic API contract (mirrors frontend types)
  services/  serialize, matching (real pHash), pipeline (P4)
  api/       routers: meta, cases
  data/      demo_case, seed
frontend/src/
  types/     case.ts — shared contract
  lib/       api.ts — typed client
  hooks/     useCase — fetch + demo fallback
  data/      demoCase.ts — fallback
  components/ pages/  — built in Phase 3+
```

See `PROJECT_STATE.md` for phase status.
