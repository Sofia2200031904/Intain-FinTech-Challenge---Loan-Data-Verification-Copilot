# Loan Data Verification Copilot

> **Turn messy loan data into verified, explainable, traceable, and auditable records.**

Loan Data Verification Copilot is a full-stack fintech operations platform built for the **Intain FinTech Challenge 2026 – Full Stack Track**. It helps loan-data teams ingest imperfect CSV or Excel data, apply deterministic validation, prioritize exceptions, assist human review, revalidate corrections, preserve SHA-256 integrity history, and export trustworthy reports.

The product principle is simple: **AI can explain; deterministic rules decide; humans approve.**

## Live application

| Resource | URL |
| --- | --- |
| Frontend application | https://frontend-pi-ten-29.vercel.app |
| Backend API | https://loan-verification-copilot-api.onrender.com |
| Backend health check | https://loan-verification-copilot-api.onrender.com/health |
| Interactive API documentation | https://loan-verification-copilot-api.onrender.com/docs |

> The backend uses Render's free service tier. After a period of inactivity, the
> first request may take up to approximately 50 seconds while the service wakes.

## Creator

**Challa Smile Sofia**

- LinkedIn: https://www.linkedin.com/in/smile-sofia-challa/
- GitHub: https://github.com/Sofia2200031904
- CodeChef: https://www.codechef.com/users/gaggle_rose_47

## Product workflow

```text
INGEST → PROFILE → NORMALIZE → VALIDATE → DETECT EXCEPTIONS
      → PRIORITIZE → EXPLAIN WITH AI → HUMAN REVIEW
      → CORRECT / REJECT → RE-VALIDATE → VERIFY → HASH → AUDIT → EXPORT
```

## What the platform does

- Accepts CSV, XLSX, and XLS loan datasets.
- Profiles detected fields, missing values, and unique values.
- Normalizes field names, numeric values, statuses, and dates.
- Runs deterministic loan-data and cross-field validation rules.
- Creates prioritized persisted exceptions by critical, high, medium, and low severity.
- Provides AI explanations and suggested next steps without changing data automatically.
- Requires human reviewer correction reason and optional reviewer notes.
- Re-runs validation after a correction and recalculates the quality score.
- Rejects unchanged or still-invalid corrections before any record, hash, correction-history, or audit mutation.
- Stores before/after values, user actions, timestamps, validation results, and SHA-256 hashes.
- Displays an in-browser table preview of the uploaded or demo loan tape.
- Allows the original dataset to be downloaded without removing the existing report exports.
- Shows visible success and error notifications for administrative and reviewer actions.
- Exports verified records, exception reports, and audit reports as CSV files.

## Role-based responsibilities

### 👑 Admin — system control and governance

Admin manages the platform, not routine loan-data decisions.

**Admin can:**

- Load demo data and upload CSV/Excel datasets.
- Normalize data and run deterministic validation.
- Manage user accounts and assign `admin`, `reviewer`, or `viewer` roles.
- Assign datasets to Reviewers.
- View and configure deterministic validation thresholds.
- View system-wide audit information and export reports.
- Request AI explanations for governance and investigation.

**Admin cannot normally:**

- Claim ordinary exceptions.
- Process the normal Reviewer queue.
- Make routine loan corrections or silently change records.
- Approve, reject, claim, or revalidate exceptions through Reviewer endpoints.
- Bypass validation or audit history.

### 🧑‍💼 Reviewer — human data-quality decision maker

Reviewer owns the operational decision on assigned loan-data exceptions.

**Reviewer can:**

- View only assigned datasets and their profile/exception results.
- Claim an exception and move it into review.
- Inspect deterministic rule, field, actual value, and source row evidence.
- Generate AI explanation and suggested next step.
- Correct a value with a required reason and optional notes.
- Reject an invalid finding with an auditable reason.
- Trigger automatic deterministic re-validation.
- View before/after values, record history, status changes, and SHA-256 hash transitions.

**Reviewer cannot:**

- Upload or delete datasets.
- Create users, change roles, or alter global settings.
- Create or edit validation rules.
- Delete audit history or bypass validation.
- Use AI to automatically change loan values.

### 👀 Viewer — read-only visibility and reporting

Viewer provides transparent monitoring without change authority.

**Viewer can:**

- View datasets, field profiles, quality score, exceptions, and verification status.
- Search Loan ID and filter verification status or exception severity.
- View source row reference, raw → normalized → verified record history.
- View correction history, SHA-256 integrity data, and permitted audit/history information.
- Download verified, exception, and audit reports.

**Viewer cannot:**

- Upload, normalize, or validate a dataset.
- Claim, correct, revalidate, resolve, approve, or reject exceptions.
- Add notes, change rules, manage users, or perform overrides.

## Permission summary

| Capability | Admin | Reviewer | Viewer |
| --- | :---: | :---: | :---: |
| Dashboard and reports | ✅ | ✅ | ✅ read-only |
| Upload / demo / normalize / validate | ✅ | ❌ | ❌ |
| Assigned-dataset exception review | Governance view | ✅ | View only |
| AI explanation | ✅ | ✅ | View existing explanation only |
| Correct, reject, and revalidate | ❌ | ✅ | ❌ |
| User, dataset assignment, and rule management | ✅ | ❌ | ❌ |
| Global audit governance | ✅ | ❌ | ❌ |

## Deterministic validation rules

The validation engine does not use an LLM. Current controls include:

- Required loan identifiers and core fields.
- Duplicate loan identifier detection.
- Positive loan amount.
- Interest rate within the configured range.
- Income positive when supplied.
- Credit score within the configured range (default 300–850).
- Loan term positive and within its configured maximum.
- Approved loan-status vocabulary.
- Loan amount compared against borrower income.
- Closed/Paid-Off loan with positive outstanding balance.

Each finding stores the rule, field(s), actual record value, message, severity, and lifecycle status.

## Exception, verification, and integrity lifecycle

```text
OPEN → UNDER REVIEW → RESOLVED / REJECTED
```

For every correction, the backend stores:

- Loan ID and field name.
- Original value and corrected value.
- Reviewer, timestamp, reason, and notes.
- Previous SHA-256 hash and new SHA-256 hash.
- Re-validation outcome and verification status.
- Audit event linked to the record.

A record becomes **Verified** only when no applicable open or under-review exceptions remain.

The correction endpoint is also the backend enforcement boundary: only the
assigned Reviewer who owns the active claim can submit a decision. A proposed
correction must change an affected field and clear the selected deterministic
rule, otherwise the API returns `422` and preserves the original record and
hash.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@intain.demo` | `Admin@123` |
| Reviewer | `reviewer@intain.demo` | `Demo@123` |
| Viewer | `viewer@intain.demo` | `Viewer@123` |

The demo dataset is synthetic. The application reuses the existing demo dataset to prevent duplicates.

## End-to-end demonstration flow

1. Sign in as **Admin** and load the demo dataset or upload a CSV/XLS/XLSX file.
2. Preview the dataset directly in the browser or download the original dataset.
3. Inspect its field profile, including record count, columns, missing values, and unique values.
4. Run **Normalize & Validate** to standardize values and generate deterministic exceptions.
5. Assign the dataset to the Reviewer from the Admin Console.
6. Sign in as **Reviewer**, select the assigned dataset, and claim an exception.
7. Inspect the source value and optional AI-assisted explanation.
8. Enter a supported correction, reason, and notes, then select **Save & Revalidate**.
9. Confirm that the deterministic rule passes, the exception resolves, and the record status updates.
10. Inspect the before/after values, reviewer identity, timestamps, hash transition, and audit history.
11. Sign in as **Viewer** to confirm the read-only experience and download permitted reports.

An unchanged value or a value that still violates the selected rule is rejected with a clear
validation message. No successful correction audit event or hash transition is recorded for a
rejected correction.

## Local development (no Docker required)

### Prerequisites

- MongoDB running locally at `mongodb://localhost:27017`.
- Python and Node.js installed.

### Backend

```powershell
cd backend
python -m pip install -r requirements-local.txt
uvicorn app.mongo_main:app --reload --port 8000
```

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## API and data storage

- Backend: FastAPI + Pydantic.
- Database: MongoDB via PyMongo.
- Authentication: JWT with role-based authorization.
- Frontend: React, TypeScript, Vite, and Lucide icons.
- Hashing: SHA-256 over deterministic normalized record JSON.
- API documentation: `http://localhost:8000/docs`.

MongoDB is the project's only supported persistence layer. Both
`uvicorn app.main:app` and `uvicorn app.mongo_main:app` resolve to the same
MongoDB application; there is no second SQL runtime.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system and data-model diagrams,
and use [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for deployed
end-to-end verification and evidence collection.

## Important API routes

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/auth/login` | Authenticate a demo or managed user and issue a JWT. |
| `GET` | `/health` | Check API and MongoDB availability. |
| `POST` | `/datasets/upload` | Upload a CSV, XLS, or XLSX loan tape. |
| `POST` | `/datasets/demo` | Load the reusable synthetic demonstration dataset. |
| `GET` | `/datasets/{id}/profile` | Return field-level dataset profiling results. |
| `GET` | `/datasets/{id}/records` | Return rows for the in-browser dataset preview. |
| `POST` | `/datasets/{id}/normalize` | Normalize the dataset. |
| `POST` | `/datasets/{id}/validate` | Execute deterministic validation rules. |
| `PATCH` | `/datasets/{id}/assign-reviewers` | Assign Reviewers to a dataset. |
| `POST` | `/exceptions/{id}/start-review` | Atomically claim an exception. |
| `POST` | `/exceptions/{id}/review` | Correct/reject and revalidate a claimed exception. |
| `POST` | `/exceptions/{id}/ai` | Generate a reviewer-oriented AI explanation. |
| `GET` | `/loans/{id}/history` | Return correction, validation, audit, and hash history. |
| `GET` | `/datasets/{id}/export/{kind}` | Export dataset, verified, exception, or audit CSV data. |

FastAPI's complete OpenAPI contract is available from the live or local `/docs` route.

## Environment variables

### Backend

| Variable | Required | Description |
| --- | :---: | --- |
| `MONGODB_URI` | ✅ | MongoDB connection string, including the `loan_copilot` database. |
| `JWT_SECRET` | ✅ | Private key used to sign authentication tokens. |
| `CORS_ORIGINS` | ✅ | Allowed frontend origin(s), supplied as plain URLs. |
| `OPENAI_API_KEY` | Optional | Enables live AI-assisted explanations. Deterministic validation works without it. |
| `OPENAI_MODEL` | Optional | Model used for explanations; configured by deployment. |

### Frontend

| Variable | Required | Description |
| --- | :---: | --- |
| `VITE_API_URL` | ✅ | Public base URL of the deployed FastAPI backend. |

Never commit real database passwords, JWT secrets, or API keys. Use `.env.example` as the
configuration template and store production secrets in Render/Vercel environment settings.

## Deployment architecture

```text
Browser
   │
   ▼
React + TypeScript frontend (Vercel)
   │ HTTPS / JWT / CORS
   ▼
FastAPI web service (Render)
   │ PyMongo / TLS
   ▼
MongoDB Atlas
```

- `render.yaml` defines the Blueprint-managed Render backend service.
- `backend/Dockerfile` provides a reproducible backend runtime on Render.
- `frontend/vercel.json` and the Vite build configure the Vercel single-page application.
- MongoDB Atlas supplies persistent cloud storage; local MongoDB is used for local development.

## Testing and verification

Run the backend test suite from the repository root:

```powershell
python -m pytest backend/tests -q
```

Build the production frontend:

```powershell
cd frontend
npm install
npm run build
```

The backend tests cover validation behavior and role/authorization boundaries, including the
Reviewer correction workflow. Before submission, also execute the deployed end-to-end checklist
in [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md).

## Repository structure

```text
backend/
  app/mongo_main.py       FastAPI API, RBAC, MongoDB workflows, hashing and audit logic
  tests/                  Backend validation and authorization tests
  Dockerfile              Render container definition
frontend/
  src/main.tsx            React application and role-based workflows
  src/style.css           Responsive application styling
  vercel.json             Vercel SPA configuration
demo_video/               Demo-video generator and rendered video
ARCHITECTURE.md            Architecture and data-model diagrams
DEPLOYMENT.md              Deployment instructions
DEMO_VIDEO_SCRIPT.md       Demonstration sequence and narration
SUBMISSION_CHECKLIST.md    Final evidence and submission checklist
render.yaml                Render Blueprint definition
```

## Security and audit design

- JWT authentication and backend-enforced role authorization protect every privileged action.
- Dataset assignment is checked by the API, not only hidden in the interface.
- Exception claims are atomic and correction decisions require claim ownership.
- Admin and Viewer accounts cannot call Reviewer correction, rejection, claim, or revalidation actions.
- Corrections must change the affected value and pass the selected deterministic rule.
- SHA-256 hashes provide tamper-evident record versions before and after accepted changes.
- Audit events retain the actor, role, action, timestamp, record, reason, and relevant values.
- AI output is advisory and cannot directly mutate loan data or override validation rules.

## Demo video



```text
Admin governs → Reviewer decides → Viewer verifies
```



https://github.com/user-attachments/assets/b970111e-74b5-4466-a115-f6014412d766


