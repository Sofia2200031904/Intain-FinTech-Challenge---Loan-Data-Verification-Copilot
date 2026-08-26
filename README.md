# Loan Data Verification Copilot

Production-style P0 platform for the Intain FinTech Challenge 2026. It ingests CSV/XLSX loan data, profiles and normalizes it, runs deterministic validations, prioritizes persisted exceptions, supports human-in-the-loop correction, recalculates SHA-256 record hashes, writes audit events, and exports verified data/reports.

## Quick start

```bash
docker compose up --build
```

Open http://localhost:5173 and sign in with `reviewer@intain.demo` / `Demo@123`. Click **Load Demo Dataset**, then **Normalize & Validate**, choose an exception, generate AI assistance, and approve/correct it. All dashboard values are computed from the database.

### Local development without Docker

The backend defaults to a local SQLite database (`backend/loan_copilot.db`) when `DATABASE_URL` is not set, so neither PostgreSQL nor Docker is necessary for a demo. Run `python -m pip install -r requirements-local.txt` and `uvicorn app.main:app --reload --port 8000` from `backend`, then run `npm install` and `npm run dev` from `frontend`. PostgreSQL remains the deployment database configured by Docker Compose.

## Architecture

React/Vite supplies the reviewer console. FastAPI owns workflow and authorization. PostgreSQL persists datasets, loans, exceptions, and audit events. The validation engine is deterministic; the AI-assistance endpoint only creates explanations and suggestions—never applies a correction. Every approved correction hashes normalized canonical JSON with SHA-256 and creates an audit event.

Database migrations are included under `backend/alembic`; run `alembic upgrade head` from `backend` in environments that manage schema migrations separately. The application also creates the initial schema on first startup for the one-command Docker demo.

## API

Interactive OpenAPI docs: http://localhost:8000/docs. Upload `multipart/form-data` to `POST /datasets/upload`; all other protected endpoints require `Authorization: Bearer <JWT>`.

## Validation rules

Required identifiers/core fields, positive numeric loan amount, 0–35% interest rate, credit score 300–850, approved status vocabulary, and duplicate `loan_id` detection. Rules are executed after normalization and persisted as individual findings with severity.

## Deployment

Use `backend` on Render/Railway with `DATABASE_URL` and `JWT_SECRET`; deploy `frontend` on Vercel with `VITE_API_URL` pointing at the API. Use managed PostgreSQL (Neon/Supabase) for production. Do not use the demo JWT secret in production.

Set `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`) on the backend to enable OpenAI Responses API assistance; without it, the demo uses clearly labeled local, non-generative reviewer guidance. Data validation never uses an LLM, and AI output can never modify a record by itself.

## Demo script

1. Sign in and load the demo dataset.
2. Profile fields and normalize/validate it.
3. Open critical exception, generate assistance, correct it, and approve.
4. Show refreshed score, audit-backed update/hash, then export reports.
