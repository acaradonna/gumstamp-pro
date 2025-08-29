# Integration notes

- Gumroad Ping: configure a POST endpoint to /api/gumroad/ping; body is x-www-form-urlencoded. Use buyer email/name and product fields for token pre-generation and optional pre-stamping cache.
- Delivery: Gumroad does not attach per-sale unique files via API; use secure external links. Provide download URL in post-purchase message or a small PDF/HTML with link.
- Verification: optionally verify license using Gumroad License Verify API if seller provides a key.
- Retries: design idempotent handling of the ping by sale_id to avoid duplicate work.
