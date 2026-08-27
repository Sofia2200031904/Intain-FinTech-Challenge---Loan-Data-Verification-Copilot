# Submission Verification Checklist

Record the deployed URL, test date, tester, and evidence link for every item.
Do not mark an item complete from code inspection alone when it describes a UI
or deployed workflow.

## End-to-end demonstration

- [ ] Admin signs in and uploads a valid CSV file.
- [ ] Admin uploads a valid XLSX file.
- [ ] Invalid, empty, oversized, and corrupt files show useful errors.
- [ ] Profile displays row count, fields, missing values, and unique values.
- [ ] Normalize and Validate creates prioritized deterministic exceptions.
- [ ] Admin assigns the dataset to an enabled Reviewer.
- [ ] Reviewer sees the assigned dataset and cannot access an unassigned one.
- [ ] Reviewer atomically claims an exception.
- [ ] A second reviewer cannot claim or decide the claimed exception.
- [ ] AI assistance explains the finding without modifying the record.
- [ ] Reviewer supplies a reason, corrects a value, and triggers revalidation.
- [ ] An unchanged or failing correction returns HTTP 422 and creates no record, hash, correction-history, or audit mutation.
- [ ] A passing correction resolves the finding.
- [ ] Rejection requires a reason and creates an audit event.
- [ ] A record with open or under-review exceptions is never Verified.
- [ ] The correction stores before/after values and previous/new hashes.
- [ ] Viewer can inspect results but cannot call any mutation endpoint.
- [ ] Verified, exception, and audit CSV exports download successfully.

## Authorization API matrix

| Operation | Admin | Assigned Reviewer | Viewer |
| --- | :---: | :---: | :---: |
| Upload / normalize / validate | Yes | No | No |
| Manage users, assignments, rules | Yes | No | No |
| Claim and decide exceptions | No | Yes | No |
| Generate reviewer explanation | Yes | Yes | No |
| View and export permitted datasets | Yes | Yes | Yes |

- [ ] Test every `No` cell directly against the deployed API and retain the
  HTTP 403 response as evidence.

## Deployment

- [ ] A unique production `JWT_SECRET` is configured outside source control.
- [ ] `MONGODB_URI` points to persistent production storage.
- [ ] `CORS_ORIGINS` contains only the deployed frontend origin.
- [ ] Frontend `VITE_API_URL` points to the deployed API.
- [ ] `GET /health` returns `{"status":"ok","database":"mongodb"}`.
- [ ] Restarting containers does not lose uploaded data or audit history.
- [ ] Browser developer tools show no failed requests during the demo.

## Submission package

- [ ] README setup commands work on a clean machine.
- [ ] Architecture and data model are included from `ARCHITECTURE.md`.
- [ ] Synthetic sample data contains no personal or confidential information.
- [ ] API documentation is available at `/docs`.
- [ ] Automated tests and the frontend production build pass.
- [ ] Demo video follows Admin → Reviewer → Viewer in 3–5 minutes.
- [ ] Known limitations and future work are stated honestly.
- [ ] Repository contains no secrets, local databases, or generated credentials.
