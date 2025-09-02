# Integration notes

## Deployment Options and Migration

This service is containerized and supports multiple hosting options. Start with Render for the fastest path, and migrate later if needed.

### Option A: Render (recommended to start)

Pros:

- Zero code changes (works with local filesystem via attached disk)
- One-click deploy via `render.yaml`
- Custom domain, TLS, logs, autoscaling

Steps:

1. Push the repo to GitHub (done: <https://github.com/acaradonna/gumstamp-pro>)
2. In Render, New + → Blueprint → select repo. Confirm service, region, and plan.
3. Ensure disk is mounted at `/data` (5GB starter) and env vars set:

- SECRET_KEY: auto-generated
- BASE_URL: your Render URL (e.g., <https://gumstamp-pro.onrender.com>)
- STORAGE_DIR: /data
- GUMROAD_PRODUCT_ID: (optional) your Gumroad product permalink
- ALLOWED_ORIGINS: your site(s) or `*`

4. Health check path: `/healthz`.
5. Point your custom domain (optional) and set BASE_URL accordingly.

Checklist before going live:

- Confirm CI green on main.
- BASE_URL matches your Render or custom domain.
- ALLOWED_ORIGINS includes your storefront/app domain(s) or `*` during testing.
- Disk mounted at `/data` and visible: check Render Shell `ls -la /data`.
- Smoke test: upload → token → download; verify stamp in the output PDF.

Undo / Migrate from Render:

- Stop service (Suspend) → Detach/Delete disk → Delete service.
- Data export: download `/data` (stamped/source PDFs) via Render shell or temporary endpoint.
- Keep your `.env` secrets for reuse on the target platform.

Notes when undoing:

- If you used a custom domain, update DNS back to your new host.
- Preserve SECRET_KEY to keep previously issued tokens valid (if BASE_URL remains consistent).
- If moving to object storage, copy `/data/stamped` and `/data/source` into your bucket with similar paths.

### Option B: Fly.io + Volume

Pros: global regions, low-level control, volumes.
Steps: `fly launch` (use Dockerfile), `fly volumes create`, set env vars, map domain.
Migration from Render: rsync data from saved archive to volume, update DNS.

### Option C: Azure App Service + Azure Files or Blob

Pros: enterprise monitoring, identity, networking. Recommended if you’re already on Azure.
Two modes:

- Azure Files mounted: minimal code change; point STORAGE_DIR to mount path.
- Blob storage: refactor `app/utils/storage.py` to read/write to Blob (stateless app).
Migration: export `/data`, upload to Files/Blob, update env, redeploy container.

Considerations:

- App Service expects container to listen on `$PORT`; Uvicorn is already set to 8000 but App Service maps ports automatically for custom containers. Validate health endpoint.
- For Blob, add a storage backend and read credentials from env (Account URL + SAS or MSI).

### Option D: Google Cloud Run + Cloud Storage (stateless)

Pros: scale to zero, pay-per-use. Requires changing storage to object store.
Steps: refactor storage to GCS, deploy container, set secrets via Secret Manager.
Migration: upload PDFs to GCS, rewrite paths; BASE_URL points to Cloud Run URL.

Considerations:

- Cloud Run requires listening on `$PORT` env; set `--port` from `$PORT` or use a start script.
- Use Secret Manager for SECRET_KEY; use Workload Identity for GCS access.

### Option E: Heroku + S3/DO Spaces (stateless)

Pros: simple. Ephemeral FS enforces object storage usage.
Steps: add S3 client, store PDFs in bucket; deploy via container registry.

Considerations:

- Heroku’s ephemeral FS enforces S3/Spaces usage; set `STORAGE_BACKEND=s3` and provide credentials.
- Keep `ALLOWED_ORIGINS` tight to your app domain to avoid CORS surprises.

## Refactor path to object storage (later)

When ready to go stateless:

1. Add an interface in `app/utils/storage.py` with two implementations:
	- LocalFSStorage (current)
	- ObjectStorage (S3/GCS/Azure Blob)
2. Add env switch: STORAGE_BACKEND=local|s3|gcs|azure
3. Wire PDF read/write to chosen backend.
4. Migrate existing `/data` to the bucket and adjust BASE_URL if serving files via app.

This preserves API and avoids breaking creators.
