from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from .routes import gumroad, creator, download
from .settings import settings
import os

app = FastAPI(
        title="Gumstamp",
        version="1.0.0",
        description="Professional PDF stamping for Gumroad creators",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
)

app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
)

# Static assets (optional; safe if folder missing)
try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
        pass

# API routers
app.include_router(gumroad.router, prefix="/api/gumroad", tags=["gumroad"])
app.include_router(creator.router, prefix="/api/creator", tags=["creator"])
app.include_router(download.router, tags=["download"])

@app.get("/", response_class=HTMLResponse)
def landing():
        return """
<!doctype html>
<html lang=\"en\"> 
<head>
    <meta charset=\"utf-8\"> 
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> 
    <title>Gumstamp – Professional PDF stamping for Gumroad</title>
    <link rel=\"icon\" href=\"/static/favicon.ico\"> 
        <style>
        :root{--bg:#0f1224;--fg:#eef1f5;--muted:#a8b0c3;--brand:#6c7bff;--brand2:#9b6cff;--card:#141833;--ok:#2ecc71}
        *{box-sizing:border-box}body{margin:0;background:radial-gradient(1200px 600px at 80% -10%, rgba(155,108,255,.25), transparent),linear-gradient(180deg, #0b0e20, #0f1224);color:var(--fg);font:16px/1.6 system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, sans-serif}
        .container{max-width:1100px;margin:0 auto;padding:0 20px}
        header{padding:72px 0 32px;border-bottom:1px solid rgba(255,255,255,.08)}
        .logo{display:flex;align-items:center;gap:12px;font-weight:700;font-size:20px;color:var(--fg);text-decoration:none}
        .logo-badge{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,var(--brand),var(--brand2));display:grid;place-items:center;font-weight:900}
        h1{margin:28px 0 12px;font-size:48px;letter-spacing:-.02em}
        .sub{color:var(--muted);max-width:720px}
        .cta-row{display:flex;gap:12px;margin:28px 0 8px;flex-wrap:wrap}
        .btn{appearance:none;border:0;border-radius:10px;padding:12px 18px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:8px}
        .btn.primary{background:linear-gradient(135deg,var(--brand),var(--brand2));color:white}
        .btn.ghost{background:transparent;color:var(--fg);border:1px solid rgba(255,255,255,.16)}
        .pill{display:inline-flex;gap:10px;align-items:center;border:1px solid rgba(255,255,255,.16);padding:8px 12px;border-radius:999px;color:var(--muted);font-size:13px}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px;margin:36px 0}
        .card{background:var(--card);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:18px}
        .card h3{margin:0 0 6px;font-size:18px}
        .kpi{display:flex;gap:16px;margin-top:8px;color:var(--muted);font-size:14px}
        .pricing{padding:32px 0 60px;border-top:1px solid rgba(255,255,255,.08)}
        .plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}
        .plan{background:var(--card);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:20px;position:relative;overflow:hidden}
        .plan.pro{outline:2px solid rgba(108,123,255,.5)}
        .plan.pro::after{content:"PRO";position:absolute;top:12px;right:-40px;background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;font-weight:900;padding:6px 60px;transform:rotate(45deg);box-shadow:0 2px 10px rgba(0,0,0,.25)}
        .price{font-size:32px;font-weight:800;margin:4px 0 10px}
        ul{margin:0;padding:0;list-style:none}
        li{margin:6px 0}
        .ok{color:var(--ok)}
        footer{color:var(--muted);padding:28px 0;border-top:1px solid rgba(255,255,255,.08)}
        @media (max-width:640px){h1{font-size:36px}}
    </style>
    <meta name=\"description\" content=\"Professional PDF stamping for Gumroad creators with custom branding, watermarks, and secure delivery.\">
    <meta property=\"og:title\" content=\"Gumstamp\">
    <meta property=\"og:description\" content=\"Professional PDF stamping for Gumroad creators.\">
    <meta property=\"og:type\" content=\"website\"> 
    <meta property=\"og:image\" content=\"/static/og.png\"> 
</head>
<body>
        <div class=\"container\">
        <header>
            <a class=\"logo\" href=\"/\"><span class=\"logo-badge\">G</span>Gumstamp</a>
            <h1>Professional PDF stamping for Gumroad</h1>
            <p class=\"sub\">Upgrade Gumroad’s basic stamp with your brand, dynamic buyer info, and optional protections. Simple setup, polished delivery.</p>
            <div class=\"cta-row\">
                <a class=\"btn primary\" href=\"#pricing\">Start free</a>
                <a class=\"btn ghost\" href=\"/api/docs\">API docs</a>
            </div>
            <div class=\"pill\">No code for creators • Works with Gumroad Ping • Ready for custom domains</div>
        </header>

        <section class=\"grid\" aria-label=\"features\">
            <div class=\"card\"><h3>🎨 Brand-forward</h3><p>Replace Gumroad’s logo with your watermark, palette, and layout.</p></div>
            <div class=\"card\"><h3>🔒 Buyer deterrence</h3><p>Per-buyer footer + optional diagonal watermark across all pages.</p></div>
            <div class=\"card\"><h3>⚡ Zero friction</h3><p>Keep your current Gumroad flow. We handle secure stamping + delivery.</p></div>
            <div class=\"card\"><h3>🧰 Developer-friendly</h3><p>Clean REST API, tokenized downloads, and CORS controls.</p></div>
        </section>

            <section class=\"pricing\" id=\"demo\" aria-label=\"demo\">
                <h2>Try it now (Free demo)</h2>
                <p class=\"sub\">Upload a sample PDF and get a dynamic download link template. No signup required.</p>
                <form id=\"demo-form\" class=\"card\" enctype=\"multipart/form-data\" style=\"margin:18px 0;display:grid;gap:12px;max-width:720px\">
                    <div style=\"display:grid;grid-template-columns:1fr 1fr;gap:12px\">
                        <div>
                            <label for=\"product_id\" style=\"display:block;margin-bottom:6px;color:var(--muted)\">Product ID</label>
                            <input id=\"product_id\" name=\"product_id\" placeholder=\"e.g. my-course\" required style=\"width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,.16);background:#0f1224;color:var(--fg)\"/>
                        </div>
                        <div>
                            <label for=\"footer_text\" style=\"display:block;margin-bottom:6px;color:var(--muted)\">Footer text</label>
                            <input id=\"footer_text\" name=\"footer_text\" value=\"Licensed to {email}\" style=\"width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,.16);background:#0f1224;color:var(--fg)\"/>
                        </div>
                    </div>
                    <div>
                        <label for=\"file\" style=\"display:block;margin-bottom:6px;color:var(--muted)\">PDF file</label>
                        <input id=\"file\" name=\"file\" type=\"file\" accept=\"application/pdf\" required style=\"width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,.16);background:#0f1224;color:var(--fg)\"/>
                    </div>
                    <details>
                        <summary style=\"cursor:pointer;color:var(--muted)\">Have a Pro license? (optional)</summary>
                        <div style=\"margin-top:10px\"><input id=\"license_key\" name=\"license_key\" placeholder=\"Enter license key\" style=\"width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,.16);background:#0f1224;color:var(--fg)\"/></div>
                    </details>
                    <div class=\"cta-row\"><button class=\"btn primary\" type=\"submit\">Upload & get link</button><button class=\"btn ghost\" type=\"reset\">Reset</button></div>
                    <div id=\"demo-result\" style=\"display:none\"></div>
                </form>
            </section>

            <section class=\"pricing\" id=\"pricing\">
            <h2>Pricing</h2>
            <div class=\"plans\">
                <div class=\"plan\">
                    <h3>Gumstamp Free</h3>
                    <div class=\"price\">$0<span style=\"font-size:14px\">/mo</span></div>
                    <ul>
                        <li><span class=\"ok\">✓</span> Buyer email footer</li>
                        <li><span class=\"ok\">✓</span> 100 downloads/mo</li>
                        <li><span class=\"ok\">✓</span> API access</li>
                    </ul>
                </div>
                <div class=\"plan pro\">
                    <h3>Gumstamp Pro</h3>
                    <div class=\"price\">$29<span style=\"font-size:14px\">/mo</span></div>
                    <ul>
                        <li><span class=\"ok\">✓</span> Custom branding & diagonal watermark</li>
                        <li><span class=\"ok\">✓</span> Unlimited downloads</li>
                        <li><span class=\"ok\">✓</span> Priority support</li>
                    </ul>
                </div>
            </div>
        </section>

            <footer>
                <small>&copy; 2025 Gumstamp • <a href=\"/api/docs\" style=\"color:#9fb0ff\">API</a> • <a href=\"mailto:support@gumstamp.com\" style=\"color:#9fb0ff\">Support</a> • <a href=\"/terms\" style=\"color:#9fb0ff\">Terms</a> • <a href=\"/privacy\" style=\"color:#9fb0ff\">Privacy</a></small>
            </footer>
    </div>
        <script>
        (function(){
            const form = document.getElementById('demo-form');
            const result = document.getElementById('demo-result');
            if(!form) return;
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                result.style.display='block';
                result.textContent='Uploading...';
                const fd = new FormData(form);
                try {
                    const res = await fetch('/api/creator/upload', { method: 'POST', body: fd });
                    if(!res.ok){
                        const t = await res.text();
                        throw new Error(t || ('Upload failed: '+res.status));
                    }
                    const data = await res.json();
                    const template = data.download_template;
                    result.innerHTML = `
                        <div class="card" style="border-color: rgba(108,123,255,.4)">
                            <h3 style="margin-top:0">Upload complete</h3>
                            <p>Use this dynamic link template with tokens:</p>
                            <pre style="white-space:pre-wrap;background:#0b0e20;padding:12px;border-radius:8px;border:1px solid rgba(255,255,255,.1)">${template}</pre>
                            <div style="margin-top:10px">
                                <form id="token-form" style="display:grid;grid-template-columns:1fr auto;gap:8px">
                                    <input name="email" placeholder="buyer@example.com" required style="padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,.16);background:#0f1224;color:#eef1f5"/>
                                    <button class="btn ghost" type="submit">Generate test token</button>
                                </form>
                                <div id="token-result" style="margin-top:8px"></div>
                            </div>
                        </div>`;

                    const tokenForm = document.getElementById('token-form');
                    const tokenOut = document.getElementById('token-result');
                    tokenForm.addEventListener('submit', async (ev) => {
                        ev.preventDefault();
                        tokenOut.textContent='Generating token...';
                        const email = new FormData(tokenForm).get('email');
                        const body = { product_id: fd.get('product_id'), email };
                        const licenseField = document.getElementById('license_key');
                        let query = '';
                        if (licenseField && licenseField.value) { query = '?license_key=' + encodeURIComponent(licenseField.value); }
                        const res2 = await fetch('/api/creator/token'+query, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
                        if(!res2.ok){ tokenOut.textContent = 'Token failed: '+res2.status; return; }
                        const data2 = await res2.json();
                        tokenOut.innerHTML = `<a class="btn primary" href="${data2.download_url}" target="_blank" rel="noopener">Open stamped PDF</a>`;
                    });
                } catch(err){
                    result.textContent = (err && err.message) ? err.message : 'Upload error';
                }
            });
        })();
        </script>
        </body>
        </html>
    """


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
        return "User-agent: *\nAllow: /\nSitemap: {}/sitemap.xml\n".format(settings.base_url)

@app.get("/version")
def version():
        return {
            "name": "Gumstamp",
            "version": app.version,
            "git_sha": os.getenv("GIT_SHA"),
            "release": os.getenv("RELEASE"),
            "base_url": settings.base_url,
            "health": "ok",
        }


@app.get("/terms", response_class=HTMLResponse)
def terms():
        return (
            "<html><head><title>Terms - Gumstamp</title></head>"
            "<body style='font-family:system-ui;padding:24px;max-width:800px;margin:auto;color:#222'>"
            "<h1>Terms of Service</h1>"
            "<p>Use of Gumstamp constitutes acceptance of these terms. You are responsible for the content you upload. Do not upload unlawful or infringing material. Service is provided “as is”.</p>"
            "<p>Contact: support@gumstamp.com</p>"
            "</body></html>"
        )


@app.get("/privacy", response_class=HTMLResponse)
def privacy():
        return (
            "<html><head><title>Privacy - Gumstamp</title></head>"
            "<body style='font-family:system-ui;padding:24px;max-width:800px;margin:auto;color:#222'>"
            "<h1>Privacy Policy</h1>"
            "<p>We process files you upload to generate stamped PDFs and store them for delivery. We do not sell personal data. Contact us to remove content.</p>"
            "<p>Email: support@gumstamp.com</p>"
            "</body></html>"
        )


@app.get("/healthz")
def healthz():
        return {"status": "ok"}
