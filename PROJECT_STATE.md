# PROJECT STATE

## Done — Phase 2 (Foundation)
- Monorepo `backend/` + `frontend/`, both build & run clean.
- **Backend:** FastAPI app, CORS, lifespan-seed. SQLAlchemy models
  (Case, Evidence, Analysis[JSON payload], IndexedMedia). Pydantic contract
  (`schemas/case.py`). Routers: `/api/health`, `/api/config`, `/api/cases`,
  `/api/cases/{id}`. Serializer builds `CaseDetail`.
- **Real** core services: `sha256_file`, `phash_image`, `hamming_distance`,
  metadata extraction (Pillow + ffprobe w/ graceful degrade), `match_phash`
  against indexed library (verified: real Hamming distances).
- **Demo case** `TT-2026-0818-00057` seeded with EXACT prototype values
  (score 91, AI 91%, Face Swap 87%, Not Original 86%, 5 matches/94%, pHash
  9d7f 3ac1 b2e8 7f91, SHA 8A7D…, tracing @NewsFlash_India 10:12, full
  propagation graph + timeline, 6 report sections). Frontend fallback mirrors it.
- **Frontend:** Vite+TS+Tailwind theme (dark navy #080b14, blue #4f8cff,
  purple #a855f7, status colors), router shell w/ working nav + demo fallback,
  shared `types/case.ts`, `api.ts`, `useCase`.

## Key decisions
- Analysis payload stored as JSON on `Analysis` row (simple, PG-migratable).
- `data_source` tag on every section drives demo/indexed/live UI badges.
- Vite dev proxy `/api` -> :8000 (no CORS pain in dev).
- Detector is a stub interface now; matching/hashing/metadata are genuinely real.

## Files changed this phase
- backend/: requirements.txt, app/{main,core/config,core/hashing,core/metadata,
  db/database,models/models,schemas/case,services/{serialize,matching},
  api/{meta,cases},data/{demo_case,seed}}.py
- frontend/: package.json, vite/ts/postcss/tailwind configs, index.html,
  src/{main,App,index.css,types/case,lib/api,hooks/useCase,data/demoCase}

## TODO
### Phase 3 — UI (visual fidelity, priority)
Replace shell with pixel-close components:
Sidebar (logo, Dashboard/New Analysis, MODULES x6, MANAGE x4, org footer,
"Powered by TRUTH TRACE v1.0") · Header (case id + Completed badge + icons +
officer) · EvidenceHeader (thumb, file facts, SHA-256) · ForensicScore (gauge
+ HIGH CONFIDENCE) · 4 AnalysisCards (colored bars) · ManipulationAnalysis
(heatmap + signal list) · TemporalChart (Recharts + anomaly band) ·
FingerprintPanel · ProvenanceOverview · OriginPathGraph (React Flow) ·
ExplainableForensics · ConfidenceChart (radar) · MediaSpreadTimeline ·
ForensicReport. Data-source badges on simulated panels.

### Phase 4 — Functionality
Upload+validate → real sha256/metadata/phash → `pipeline.py` (stub detector +
real match_phash) → provenance → assemble payload → create case. Wire New
Analysis, Cases list, Evidence Library, View All Matches, View Full Graph.

### Phase 5 — Report
Real PDF via ReportLab: `GET /api/cases/{id}/report.pdf` (exec summary,
findings, confidence, hash, graph snapshots).

### Phase 6 — QA
Build both, test every route/button/upload/chart/graph/report, then visual
diff vs prototype and refine.
