# Gumstamp Pro

Advanced PDF stamping for Gumroad creators: custom branding, dynamic buyer info, and optional security controls delivered automatically after purchase via Gumroad Ping.

## What it is
 Service that overlays buyer-specific details (name/email/order/timestamp) and your brand watermark on every page of your PDFs.
 Supports diagonal background watermarks, footer stamps, and invisible metadata fingerprinting.
 Integrates with Gumroad via Ping webhooks and License verification.

## Why it can make money
 Gumroad already offers basic stamping (buyer email + Gumroad logo). Many creators want brand-forward, configurable stamping and stronger deterrents.
 We provide premium features (branding, positioning, patterns, copy/print restrictions) with a simple setup. Creators pay subscription or one‑time per product.

See `docs/market-validation.md` for research and competitive analysis.

## MVP scope (this repo)
FastAPI service with endpoints:

- POST /api/gumroad/ping — receive Gumroad sale pings (x-www-form-urlencoded).
- GET /download/{token} — deliver a buyer-stamped PDF by secure token.
- Creator setup (minimal): upload a source PDF and get a product-specific secure link template.
 PDF stamping utilities: text/image watermark, repeated diagonal pattern, metadata tagging.
 Local filesystem storage (S3-ready structure). Simple token signing.
 Tests for stamping output and webhook payload parsing.
 Dockerfile + Make targets.

 
## Quick start
Python 3.11+

- Install: `pip install -r requirements.txt`
- Run: `make dev`
- Open: <http://localhost:8000>

 
## Deploy
 Containerized via Docker. Any platform that runs containers works (Render, Fly.io, Azure App Service, etc.).
 Configure environment variables in `.env` (see below).

 
## Configuration (.env)
SECRET_KEY: token signing secret

- STORAGE_DIR: path for stored files (default: ./storage)
- BASE_URL: public base URL for token links (e.g. <https://yourapp.com>)
- GUMROAD_PRODUCT_ID: optional product permalink to require a valid Gumroad license for creator endpoints

 
## Creator setup (MVP)

1) Upload your original PDF in the web UI at /. Configure stamp text and optional diagonal watermark.
2) Copy the generated dynamic download URL template (e.g. <https://yourapp.com/download/{token}>).
3) In Gumroad, either:
   - Include the link in the “post-purchase” message/email, or
   - Add a small file with a link to the stamped copy, or
   - Use a landing page redirect in your product content advising the stamped download link.
4) Optional: set your Gumroad Ping URL to <https://yourapp.com/api/gumroad/ping> to let us pre‑warm stamped copies.

 
## Limitations (MVP)

 Cannot upload per-sale files back to Gumroad (API does not support unique per-sale attachments). Delivery uses secure external link.
 Buyer identity from Ping is used to prepare and validate tokens. If Ping is not enabled, first download will stamp on demand.

## Monetization

Set `GUMROAD_PRODUCT_ID` to your Gumroad product permalink to gate creator endpoints (`/api/creator/upload` and `/api/creator/token`).
When set, clients must provide a valid `license_key` from their purchase to use the service. Verification uses Gumroad's `/v2/licenses/verify` API (no API key required for this minimal flow).

## API quick reference

- POST /api/creator/upload (multipart)
   - form: product_id, file (PDF), footer_text?, license_key? (required if `GUMROAD_PRODUCT_ID` set)
   - returns: product_id, source_key, download_template

- POST /api/creator/token (json)
   - body: { product_id, email, sale_id? }
   - query/header: license_key when `GUMROAD_PRODUCT_ID` set
   - returns: { token, download_url }

- POST /api/gumroad/ping (form)
   - accepts Gumroad Ping fields, returns: { ok, token, download_url }

- GET /download/{token}
   - returns stamped PDF (application/pdf)

## Create and push a repo

```bash
git init
git add .
git commit -m "feat: gumstamp-pro MVP with tokenized delivery and Gumroad license gating"
git branch -M main
git remote add origin git@github.com:<your-username>/gumstamp-pro.git
git push -u origin main
```

 
## License

This subproject is provided as-is for evaluation. You are responsible for complying with Gumroad’s ToS and your local laws.
