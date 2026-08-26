# Loan Data Verification Copilot — 3–5 Minute Demo Video Script

## Recording setup

Start MongoDB, then start the backend and frontend. Open `http://localhost:5173` in Chrome at 100% zoom. Keep the backend terminal visible on another desktop only if you want to show live API activity; it is not required.

Use these demo accounts:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@intain.demo` | `Admin@123` |
| Reviewer | `reviewer@intain.demo` | `Demo@123` |
| Viewer | `viewer@intain.demo` | `Viewer@123` |

## 0:00–0:20 — Opening

**Screen:** Login page.

**Say:**

> Loan Data Verification Copilot turns messy loan-level data into clean, verified, explainable, and auditable records. The system separates deterministic validation, AI assistance, human review, and SHA-256 integrity controls.

Point to the three demo credentials. Mention that all demo data is synthetic.

## 0:20–1:20 — Admin: system governance

1. Log in as **Admin**.
2. Show the **ADMIN** badge in the header.
3. If no dataset is selected, click **Load Demo Dataset**. If one is already present, select it; the app prevents duplicate demo datasets.
4. Click **Normalize & Validate**.
5. Point to the dashboard cards: quality score, record count, open exceptions, and verified records.
6. Point to the profile table and exception queue.
7. Mention that Admin controls datasets, deterministic validation, users/roles, rule thresholds, audit governance, assignments, and reports.
8. Show one export button briefly.

**Say:**

> Admin governs the system. Admin does not process normal loan corrections. Validation results are created by deterministic rules, not by AI.

## 1:20–2:50 — Reviewer: investigate, correct, revalidate

1. Sign out and log in as **Reviewer**.
2. Show the **REVIEWER** badge and the assigned dataset.
3. Open a critical exception, such as `LN002` interest rate outside the permitted range.
4. Point out the deterministic rule, affected field, actual value, and raw/normalized record values.
5. Click **Generate AI assistance**.
6. Read the AI explanation and suggested next step briefly.
7. Say clearly that the AI did not modify data.
8. Click **Correct & revalidate**.
9. In the modal enter a corrected value such as `8.5` for the `85` interest rate, enter a reason such as `Confirmed from source document`, and add notes such as `Corrected decimal placement in interest rate.`
10. Click **Save & Revalidate**.
11. Show the success notice: correction saved, re-validation outcome, and exception state.
12. Open **Record history**.
13. Show the before/after correction entry, reviewer/reason/notes, previous and new SHA-256 hashes, and audit events.

**Say:**

> The reviewer remains in control. A correction is preserved as history, the affected deterministic rules are re-run, and the record is verified only when all applicable exceptions are resolved.

## 2:50–3:40 — Viewer: transparency without changes

1. Sign out and log in as **Viewer**.
2. Show the **VIEWER** badge.
3. Use the Final Verification Status table.
4. Search a Loan ID and use a status or severity filter.
5. Open a record history view.
6. Point to source row, raw-to-normalized values, correction history, SHA-256 value, and audit history.
7. Briefly show an export button.

**Say:**

> Viewer access is strictly read-only. It provides operational transparency, verification status, source references, and reporting without any ability to alter data or decisions.

## 3:40–4:10 — Closing

**Screen:** Dashboard or record-history page.

**Say:**

> The complete workflow is ingest, profile, normalize, validate, prioritize, explain, human review, revalidate, verify, hash, audit, and export. AI assists the reviewer, but deterministic rules and human approval remain the controls for every decision.

## Recording checklist

- Show three manual logins: Admin, Reviewer, Viewer.
- Show the Admin dashboard and deterministic validation.
- Show Reviewer AI explanation, correction modal, reason, notes, re-validation, and history.
- Show Viewer search/filter, verification status, record history, and read-only exports.
- Do not show passwords for longer than necessary.
- Record at 1080p and keep browser zoom at 100%.
