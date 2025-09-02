# Deploying Gumstamp to gumstamp.com (step‑by‑step)

This guide walks you through deploying this service to production on Render using the provided Dockerfile and render.yaml, and connecting the custom domain <https://gumstamp.com> (and <https://www.gumstamp.com>). If you prefer another platform, see the “Other platforms” notes at the end.

Audience: someone comfortable with GitHub, basic DNS, and container-based deploys.


## What you’ll set up

- A Render Web Service built from this repo (Docker runtime)
- A persistent disk for PDF storage (/data)
- Production env vars (BASE_URL, SECRET_KEY, ALLOWED_ORIGINS, optional GUMROAD_PRODUCT_ID)
- Custom domain (<https://gumstamp.com> and <https://www.gumstamp.com>) with automatic SSL
- Gumroad Ping webhook (optional but recommended)


## 0) Prerequisites

- GitHub repository with this code (branch: main)
- Render account with access to create a Web Service
- Access to your DNS (domain registrar or DNS host for gumstamp.com)
- Decide the canonical domain: <https://gumstamp.com> (apex) with <https://www.gumstamp.com> as an alias


## 1) Review runtime basics

- App server: FastAPI served by Uvicorn (port 8000)
- Health check: GET /healthz returns {"status":"ok"}
- Important env vars (see .env.example):
	- SECRET_KEY: required, strong random string used for token signing
	- STORAGE_DIR: where source/stamped files persist (on Render we’ll use /data)
	- BASE_URL: public base URL used for download links (set to <https://gumstamp.com> in prod)
	- GUMROAD_PRODUCT_ID: optional; if set, creator endpoints require a valid Gumroad license
	- ALLOWED_ORIGINS: CSV of allowed origins for CORS (include your domains)


## 2) Deploy on Render from the repo
This repo includes render.yaml for a Docker-based Web Service and a 5GB persistent disk mounted at /data.

Steps:

1. In Render, click New > Blueprint and point it at your GitHub repo.
2. Review the blueprint preview:

	- Service name: gumstamp (or your choice)
	- Runtime: docker
	- Region: choose close to users (e.g., oregon in the sample)
	- Health check path: /healthz
	- Disk: name=data, mountPath=/data, sizeGB=5 (adjust if needed)
3. Click Apply. Render will build the Docker image from Dockerfile and start the service.

When the service is live you’ll get a Render URL like <https://gumstamp.onrender.com>. We’ll switch to <https://gumstamp.com> after DNS.


## 3) Set production environment variables

In the Render service, go to Settings > Environment.

Set or override the following:

- SECRET_KEY: generate a strong value (don’t use the default)
- BASE_URL: <https://gumstamp.com>
- STORAGE_DIR: /data
- ALLOWED_ORIGINS: `https://gumstamp.com,https://www.gumstamp.com,https://gumstamp.onrender.com`
- GUMROAD_PRODUCT_ID: optional, your Gumroad product permalink if you want license gating
- (Optional) RELEASE / GIT_SHA: set by your CI or manually for version visibility at /version

Save and Deploy to apply changes.


## 4) Smoke test the service

Before wiring DNS, verify core endpoints using the temporary Render URL.

- GET /healthz → {"status":"ok"}
- GET /api/docs → should load Swagger UI
- GET /version → JSON with base_url and health: ok

Optional: try an upload via the homepage demo form to confirm /api/creator/upload works and files are written under /data.


## 5) Add your custom domain(s)

We’ll attach `gumstamp.com` and `www.gumstamp.com` to your Render service.

1. In Render, open your Web Service > Settings > Custom Domains.
2. Add both domains: `gumstamp.com` and `www.gumstamp.com`.
3. Render will show the exact DNS records to create. Create those records at your DNS host:

	- Apex (`gumstamp.com`): typically an ALIAS/ANAME or A record as instructed by Render
	- Subdomain (`www.gumstamp.com`): CNAME to your Render hostname
4. Wait for DNS to propagate. Render will validate and automatically issue SSL certificates.

Notes:
 
- Always follow the DNS values displayed in Render; they may change over time. Avoid hardcoding IPs from guides.
- If you want www → apex (or apex → www) redirect, configure the redirect domain in Render after verification.


## 6) Update BASE_URL and CORS (if you haven’t already)

Once `gumstamp.com` is verified:

- Ensure BASE_URL is exactly <https://gumstamp.com>
- Ensure ALLOWED_ORIGINS includes `https://gumstamp.com` and `https://www.gumstamp.com`
- Redeploy. Check /version to confirm base_url.


## 7) Persistent storage considerations

The service writes to STORAGE_DIR with two subfolders:

- source/: original PDFs you upload
- stamped/: generated, buyer-stamped PDFs

On Render, STORAGE_DIR should be /data (a persistent disk). The render.yaml already mounts a 5GB disk there. You can increase disk size later in Render if needed.


## 8) Configure Gumroad (optional but recommended)

You can let Gumstamp pre‑generate stamped copies and validate buyers.

1. Gumroad Ping webhook

	- In Gumroad, open Settings > Advanced > Ping.
	- Set Ping URL to: <https://gumstamp.com/api/gumroad/ping>
	- Save.

2. License gating for creator endpoints (optional)

	- Set GUMROAD_PRODUCT_ID in your Render env to your product’s permalink.
	- Creator endpoints (/api/creator/upload and /api/creator/token) will then require a valid license_key.


## 9) Final verification checklist

- Domain loads: <https://gumstamp.com>
- SSL green lock (Render-managed certs)
- CORS works from your intended clients (no browser console errors)
- Upload via homepage demo succeeds; a token can be generated; download link returns a stamped PDF
- Health and version endpoints respond


## 10) Operations: logs, scaling, upgrades

- Logs: Render > your service > Logs
- Scaling: Start with the default instance. If you see CPU or memory pressure, pick a larger plan or scale horizontally. Uvicorn is started as a single process; for heavy load consider a process manager like Gunicorn with multiple workers in the Docker image in the future.
- Deploys: AutoDeploy is enabled in render.yaml. Merges to main will redeploy. You can disable auto-deploy and promote manually if desired.


## 11) Rollback

- In Render, open the Deploys tab for your service and roll back to a previous successful deploy.


## 12) Security & backups

- Keep SECRET_KEY secret and rotate if compromised (existing tokens become invalid).
- Consider scheduled exports of /data if you need off-platform backups. Render Disks are persistent but not a backup.
- Limit ALLOWED_ORIGINS to only your production domains.


## 13) Troubleshooting

- 404 on custom domain: DNS not propagated or records not correct—compare with Render’s domain instructions.
- SSL not issued: domain not verified; check that DNS is correct and wait for validation.
- 500 errors on upload/stamp: inspect logs; verify STORAGE_DIR is writeable and has space; confirm SECRET_KEY is set.
- CORS errors in browser: verify ALLOWED_ORIGINS includes your domain(s) exactly, including scheme (https) and no trailing slashes.


## Appendix: Other platforms (brief)

This app is containerized and will run on most hosts:

- Fly.io: map port 8000; attach a volume for /data; set env vars; add custom domains/SSL via Fly certs.
- Docker on a VM: mount a host path to /data; reverse proxy with Nginx/Caddy for TLS; point DNS to your VM.
- Azure App Service / AWS ECS / GCP Cloud Run: use the Docker image, attach persistent storage (where supported), and set env vars. Ensure your reverse proxy forwards to port 8000, and set BASE_URL to your public domain.


## Quick local test (optional)

Run locally before shipping:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="dev_only_change_me"
export BASE_URL="http://localhost:8000"
export STORAGE_DIR="./storage"
uvicorn app.main:app --reload
```

Open <http://localhost:8000> and try the demo form. Health: <http://localhost:8000/healthz>

