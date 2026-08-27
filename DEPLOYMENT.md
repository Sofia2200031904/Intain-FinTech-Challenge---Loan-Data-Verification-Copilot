# Production Deployment

Recommended prototype hosting:

- MongoDB Atlas for persistent data
- Render for FastAPI
- Vercel for React/Vite

The repository includes `render.yaml` and `frontend/vercel.json`.

## 1. MongoDB Atlas

1. Create a free Atlas project and M0 cluster.
2. Create a database user with read/write access to `loan_copilot`.
3. Permit the Render service in Atlas Network Access. Atlas allows
   `0.0.0.0/0` for a short prototype, but restrictive access is preferred.
4. Copy the driver URI with the database name appended:

```text
mongodb+srv://<user>:<password>@<cluster>/loan_copilot?retryWrites=true&w=majority
```

Never commit or publicly share this URI.

## 2. Render API

1. Choose **New → Blueprint** in Render.
2. Connect this GitHub repository.
3. Render discovers `render.yaml` and creates the API service.
4. Set `MONGODB_URI` to the Atlas URI.
5. Set `CORS_ORIGINS` to the frontend URL when it is known.
6. `OPENAI_API_KEY` is optional; without it the safe demo explanation is used.

Render generates `JWT_SECRET`. Do not use the development secret from Docker
Compose. Verify the deployed endpoints:

```text
https://<render-service>.onrender.com/health
https://<render-service>.onrender.com/docs
```

## 3. Vercel frontend

1. Import the same GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Add the production variable:

```text
VITE_API_URL=https://<render-service>.onrender.com
```

4. Deploy and copy the final Vercel URL.
5. Set Render `CORS_ORIGINS` to that exact URL and redeploy the API.

## 4. Production smoke test

From the Vercel URL:

1. Sign in as Admin and upload CSV/XLSX data.
2. Normalize, validate, and assign the Reviewer.
3. Sign in as Reviewer and claim an exception.
4. Confirm an invalid correction returns HTTP 422 with no mutation.
5. Submit a valid correction and confirm its rule passes.
6. Confirm resolution, verification status, hash change, and audit evidence.
7. Sign in as Viewer and confirm all mutations return HTTP 403.
8. Download verified, exception, and audit CSV reports.

Free Render services may take time to wake after inactivity. Open `/health`
before beginning the judging demonstration.
