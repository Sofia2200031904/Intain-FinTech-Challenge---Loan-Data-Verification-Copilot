# Loan Data Verification Copilot

> **Turn messy loan data into verified, explainable, traceable, and auditable records.**

Loan Data Verification Copilot is a full-stack fintech operations platform built for the **Intain FinTech Challenge 2026 – Full Stack Track**. It helps loan-data teams ingest imperfect CSV or Excel data, apply deterministic validation, prioritize exceptions, assist human review, revalidate corrections, preserve SHA-256 integrity history, and export trustworthy reports.

The product principle is simple: **AI can explain; deterministic rules decide; humans approve.**

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
- Stores before/after values, user actions, timestamps, validation results, and SHA-256 hashes.
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
- Perform an exceptional, fully audited override workflow when it is added to a production policy.

**Admin cannot normally:**

- Claim ordinary exceptions.
- Process the normal Reviewer queue.
- Make routine loan corrections or silently change records.
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
| Correct, reject, and revalidate | Override only | ✅ | ❌ |
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

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@intain.demo` | `Admin@123` |
| Reviewer | `reviewer@intain.demo` | `Demo@123` |
| Viewer | `viewer@intain.demo` | `Viewer@123` |

The demo dataset is synthetic. The application reuses the existing demo dataset to prevent duplicates.

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

## Demo video

Use [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md) to record a 3–5 minute walkthrough:

```text
Admin governs → Reviewer decides → Viewer verifies
```

It covers manual login, deterministic validation, AI explanation, human correction, re-validation, record history, SHA-256 integrity, audit events, viewer transparency, and export.

## Deployment direction

Use a private GitHub repository with:

- MongoDB Atlas for production MongoDB.
- Render or Railway for the FastAPI backend.
- Vercel for the React frontend.

Set production environment variables in the hosting dashboards; never commit secrets. At minimum configure `MONGODB_URI`, `JWT_SECRET`, and the frontend `VITE_API_URL`.
