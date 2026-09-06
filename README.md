# CivicFlow

**Smart India Hackathon 2026 — Problem Statement SIH26034**
"Software System to check compliance of Packaged Commodities under Legal Metrology Rules, 2011 by scanning products, images and labels."

An AI-assisted packaged-commodity compliance checking system with an explainable pipeline:

```
Login → Dashboard → New Inspection → Upload/Capture Label Image → Image Quality Check
  → OCR → Structured Field Extraction → Category Detection → Load Applicable Rules
  → Compliance Rule Engine → PASS/FAIL/WARNING/MANUAL_REVIEW → Compliance Score
  → Risk Level → Violations + Explanations → Evidence → Inspector Review
  → Final Preliminary Assessment → PDF Report → Inspection History → Dashboard Analytics
```

This is **not** an OCR demo — the core value is the configurable, explainable rule engine
that turns extracted label text into a preliminary compliance result a human inspector
can verify and act on.

---

## What's real vs. what's demo-mode

Everything in this codebase is a genuine working implementation — the auth system, the
database models, the rule engine, the PDF generation, the analytics — **not stubs**. The
one thing that gracefully degrades is OCR: if the `tesseract` binary isn't installed on
the machine running the backend, `OCR_ENGINE` automatically falls back to a clearly
labelled **DEMO MODE** that returns fixed sample label text, so the rest of the pipeline
stays demoable. The API response and the frontend UI both flag `is_demo_mode: true`
whenever this happens — it is never presented as real OCR output.

The compliance rules shipped in `seed_rules.py` are **illustrative starter rules**
(presence/format checks for common label declarations). They deliberately do not encode
actual Legal Metrology (Packaged Commodities) Rules, 2011 section numbers or penalties —
review and correct them against the real legal text (via `/api/rules`, or directly in
the database) before using this for anything beyond a hackathon demo. Every generated
report is labelled "Preliminary Compliance Assessment," not a legal determination.

## Verified end-to-end (already tested)

Before packaging this, the full stack was actually run and driven through the complete
flow: register → login → create inspection → upload a label image → run OCR (demo mode)
→ run extraction (correctly parsed net quantity, MRP, manufacturer, address, country of
origin, batch number, etc., leaving genuinely-missing fields as `null`) → run compliance
(correctly flagged the missing product name, scored 88/100, MEDIUM risk) → generate a
real PDF report → see it reflected in `/api/analytics/overview`. The backend's 11-test
pytest suite also passes. The frontend was type-checked (`tsc -b`) and built for
production (`vite build`) with zero errors.

What was **not** possible to verify inside the sandbox this was built in: a live
PostgreSQL instance, Docker Compose actually starting all three containers together, and
a real Tesseract binary doing OCR on a real photograph. Those all use standard, widely-
used configurations (see below) but you should do a first run yourself to confirm your
environment.

---

## Quick start — Docker (recommended)

Requires Docker + Docker Compose.

```bash
cd CivicFlow
docker compose up --build
```

This starts PostgreSQL, the backend on `http://localhost:8000`, and the frontend on
`http://localhost:5173`. Then seed the rule base and demo accounts:

```bash
docker compose exec backend python seed_rules.py
```

## Quick start — manual

**Backend**

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# macOS: brew install tesseract
# Ubuntu/Debian: sudo apt-get install tesseract-ocr
# Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
# (If you skip this, the backend automatically runs OCR in demo mode instead.)

# Start a local PostgreSQL (or use Docker just for the DB):
docker run -d --name civicflow-db -e POSTGRES_USER=civicflow -e POSTGRES_PASSWORD=civicflow \
  -e POSTGRES_DB=civicflow -p 5432:5432 postgres:16-alpine

cp .env.example .env   # edit if your DB/Tesseract setup differs

python seed_rules.py   # creates starter rules + demo accounts
uvicorn app.main:app --reload --port 8000
```

API docs (Swagger): **http://localhost:8000/docs**

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

App: **http://localhost:5173**

---

## Demo credentials

Created by `seed_rules.py`:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@civicflow.demo` | `Admin123!` |
| Inspector | `inspector@civicflow.demo` | `Inspector123!` |
| Consumer | `consumer@civicflow.demo` | `Consumer123!` |

The login page is pre-filled with the inspector credentials for a fast demo.

---

## Environment variables

**backend/.env** (see `backend/.env.example`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Long random secret — change before any real deployment |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `UPLOAD_DIR` / `REPORTS_DIR` | Local storage paths |
| `OCR_ENGINE` | `tesseract` or `demo` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `MAX_UPLOAD_SIZE_MB` | Upload size limit |

**frontend/.env** (see `frontend/.env.example`)

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend base URL, e.g. `http://localhost:8000` |

---

## Project structure

```
CivicFlow/
├── backend/
│   ├── app/
│   │   ├── main.py                FastAPI entrypoint, CORS, routers
│   │   ├── core/                  config, JWT/password security, auth deps
│   │   ├── database/               SQLAlchemy engine/session
│   │   ├── models/models.py       all ORM tables (Users, Products, Inspections,
│   │   │                          ProductImages, OCRResults, ExtractedFields, Rules,
│   │   │                          ComplianceChecks, Violations, Reports, Complaints,
│   │   │                          AuditLogs)
│   │   ├── schemas/schemas.py     Pydantic request/response models
│   │   ├── services/              image_service, ocr_service, extraction_service,
│   │   │                          compliance_engine, report_service
│   │   └── api/                   auth, users, products, inspections, images, ocr,
│   │                              extraction, compliance, rules, reports, complaints,
│   │                              analytics
│   ├── tests/                     pytest suite (11 tests, SQLite in-memory, no external deps)
│   ├── seed_rules.py               starter rules + demo accounts
│   ├── requirements.txt, .env.example, Dockerfile
│   └── uploads/, reports/          runtime storage (empty in this download)
├── frontend/
│   ├── src/
│   │   ├── api/client.ts          single axios instance + typed API layer
│   │   ├── types/                 shared TS types mirroring backend schemas
│   │   ├── context/AuthContext.tsx
│   │   ├── components/            Layout, StatusPill, ProtectedRoute, LocationPicker
│   │   └── pages/                 Login, Register, Dashboard, Inspections,
│   │                              InspectionWorkflow (create → upload → OCR →
│   │                              extract → compliance → review → PDF, one flow
│   │                              for both new and existing inspections)
│   ├── package.json, vite.config.ts, tailwind.config.js, Dockerfile, .env.example
└── docker-compose.yml
```

---

## Running tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

---

## Known limitations / what's left to configure

1. **OCR accuracy** depends entirely on Tesseract being installed and on real photo
   quality — the demo-mode fallback exists precisely so the rest of the pipeline is
   always demoable even without it.
2. **Rules are illustrative.** Populate `rules` (via `/api/rules`, protected to ADMIN)
   with content verified against the actual Legal Metrology (Packaged Commodities)
   Rules, 2011 and any amendments before relying on results for anything beyond a demo.
3. **Category detection** is a lightweight keyword heuristic meant to be corrected by an
   inspector, not an authoritative classifier.
4. **Image quality analysis** (blur/resolution) requires OpenCV, which is in
   `requirements.txt`; if it's ever unavailable in a given environment the upload still
   succeeds, just without automated quality scoring.
5. Frontend location (Leaflet/OpenStreetMap) is set by clicking the map on the
   inspection page and saved with "Save notes & location" — it's optional per inspection.
6. No production hardening beyond what's listed (rate limiting, virus scanning on
   uploads, etc.) has been added — this targets an SIH demo, not a production rollout.
