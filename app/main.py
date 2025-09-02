from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from .routes import gumroad, creator, download
from .settings import settings
from .monitoring import (
    setup_monitoring,
    MonitoringMiddleware,
    get_health_status,
    config as monitoring_config,
)
import os
import structlog
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize monitoring on startup
    async with setup_monitoring():
        yield


app = FastAPI(
        title="Gumstamp",
        version="1.0.0",
        description="Professional PDF stamping for Gumroad creators",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
)

# Add monitoring middleware first (executes last, closest to the application)
app.add_middleware(MonitoringMiddleware)

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
        :root{
            --bg:#0f1224;--fg:#eef1f5;--muted:#a8b0c3;--brand:#6c7bff;--brand2:#9b6cff;
            --card:#141833;--card-elevated:#1a1f3a;--ok:#2ecc71;--warning:#f39c12;--danger:#e74c3c;
            --shadow:0 4px 6px -1px rgba(0,0,0,.1),0 2px 4px -1px rgba(0,0,0,.06);
            --shadow-lg:0 10px 15px -3px rgba(0,0,0,.1),0 4px 6px -2px rgba(0,0,0,.05);
        }
        *{box-sizing:border-box}
        body{
            margin:0;
            background:radial-gradient(1200px 600px at 80% -10%, rgba(155,108,255,.25), transparent),
                       linear-gradient(180deg, #0b0e20, #0f1224);
            color:var(--fg);
            font:16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif;
            -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
        }
        .container{max-width:1100px;margin:0 auto;padding:0 20px}
        header{padding:72px 0 32px;border-bottom:1px solid rgba(255,255,255,.08)}
        .logo{display:flex;align-items:center;gap:12px;font-weight:700;font-size:20px;color:var(--fg);text-decoration:none}
        .logo-badge{
            width:32px;height:32px;border-radius:8px;
            background:linear-gradient(135deg,var(--brand),var(--brand2));
            display:grid;place-items:center;font-weight:900;
            box-shadow:var(--shadow);
        }
        h1{margin:28px 0 12px;font-size:48px;letter-spacing:-.02em;font-weight:800}
        .sub{color:var(--muted);max-width:720px;font-size:18px;line-height:1.7}
        .cta-row{display:flex;gap:12px;margin:28px 0 8px;flex-wrap:wrap}
        .btn{
            appearance:none;border:0;border-radius:10px;padding:14px 22px;font-weight:700;
            cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:8px;
            min-height:44px;transition:all .2s ease;font-size:15px;
        }
        .btn.primary{
            background:linear-gradient(135deg,var(--brand),var(--brand2));color:white;
            box-shadow:var(--shadow);
        }
        .btn.primary:hover{transform:translateY(-1px);box-shadow:var(--shadow-lg);}
        .btn.ghost{background:rgba(255,255,255,.05);color:var(--fg);border:1px solid rgba(255,255,255,.16)}
        .btn.ghost:hover{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.3)}
        .pill{
            display:inline-flex;gap:10px;align-items:center;
            border:1px solid rgba(255,255,255,.16);padding:8px 12px;border-radius:999px;
            color:var(--muted);font-size:13px;background:rgba(255,255,255,.02);
        }
        .social-proof{
            text-align:center;padding:24px 0;
            background:linear-gradient(90deg,transparent,rgba(108,123,255,.1),transparent);
            margin:48px -20px 24px;
        }
        .social-counter{font-size:32px;font-weight:800;color:var(--brand);margin-bottom:8px}
        .social-text{color:var(--muted);font-size:14px}
        .trust-badges{display:flex;justify-content:center;gap:24px;margin:16px 0;flex-wrap:wrap}
        .badge{
            display:flex;align-items:center;gap:6px;padding:6px 12px;
            background:rgba(46,204,113,.1);border:1px solid rgba(46,204,113,.3);
            border-radius:20px;font-size:12px;color:var(--ok);
        }
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:48px 0}
        .card{
            background:var(--card);border:1px solid rgba(255,255,255,.06);
            border-radius:14px;padding:24px;box-shadow:var(--shadow);
            transition:transform .2s ease,box-shadow .2s ease;
        }
        .card:hover{transform:translateY(-2px);box-shadow:var(--shadow-lg)}
        .card h3{margin:0 0 12px;font-size:20px;display:flex;align-items:center;gap:10px}
        .card-icon{font-size:24px}
        .testimonials{margin:48px 0;padding:32px 0}
        .testimonial{
            background:var(--card-elevated);border:1px solid rgba(108,123,255,.2);
            padding:24px;border-radius:12px;margin:16px 0;
            position:relative;
        }
        .testimonial::before{
            content:'"';position:absolute;top:-10px;left:20px;
            font-size:48px;color:var(--brand);font-weight:900;
        }
        .quote{font-style:italic;margin-bottom:16px;color:var(--fg)}
        .author{display:flex;align-items:center;gap:12px;color:var(--muted);font-size:14px}
        .author-avatar{
            width:32px;height:32px;border-radius:50%;
            background:linear-gradient(135deg,var(--brand),var(--brand2));
            display:flex;align-items:center;justify-content:center;
            color:white;font-weight:700;
        }
        .pricing{padding:48px 0 60px;border-top:1px solid rgba(255,255,255,.08)}
        .pricing-header{text-align:center;margin-bottom:48px}
        .pricing h2{font-size:36px;margin-bottom:12px}
        .pricing-sub{color:var(--muted);font-size:18px;max-width:600px;margin:0 auto}
        .plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;align-items:stretch}
        .plan{
            background:var(--card);border:1px solid rgba(255,255,255,.08);
            border-radius:16px;padding:32px 24px;position:relative;overflow:hidden;
            display:flex;flex-direction:column;transition:transform .2s ease,box-shadow .2s ease;
        }
        .plan:hover{transform:translateY(-4px);box-shadow:var(--shadow-lg)}
        .plan.featured{
            border:2px solid var(--brand);box-shadow:var(--shadow-lg);
            background:linear-gradient(135deg,var(--card),var(--card-elevated));
        }
        .plan.featured::after{
            content:"MOST POPULAR";position:absolute;top:16px;right:-40px;
            background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;
            font-weight:900;padding:6px 60px;transform:rotate(45deg);
            box-shadow:0 2px 10px rgba(0,0,0,.25);font-size:11px;
        }
        .plan h3{margin:0 0 8px;font-size:22px}
        .price{font-size:40px;font-weight:800;margin:8px 0 16px;color:var(--fg)}
        .price-period{font-size:16px;color:var(--muted);font-weight:400}
        .plan-description{color:var(--muted);margin-bottom:24px;font-size:14px}
        .plan ul{margin:0 0 32px;padding:0;list-style:none;flex-grow:1}
        .plan li{margin:10px 0;display:flex;align-items:center;gap:10px}
        .plan .feature-icon{color:var(--ok);font-weight:700}
        .plan .feature-disabled{color:#666;opacity:.6}
        .roi-calculator{
            background:var(--card-elevated);border:1px solid rgba(108,123,255,.2);
            border-radius:12px;padding:24px;margin:32px 0;text-align:center;
        }
        footer{color:var(--muted);padding:32px 0;border-top:1px solid rgba(255,255,255,.08);text-align:center}
        
        /* Mobile optimizations */
        @media (max-width:768px){
            .container{padding:0 16px}
            header{padding:48px 0 24px}
            h1{font-size:32px}
            .sub{font-size:16px}
            .btn{padding:12px 18px;font-size:14px}
            .grid{grid-template-columns:1fr;gap:16px}
            .plans{grid-template-columns:1fr}
            .card{padding:20px}
            .social-proof{margin:32px -16px 16px}
            .cta-row{flex-direction:column;align-items:stretch}
            .trust-badges{flex-direction:column;align-items:center;gap:12px}
        }
        
        /* Enhanced form styling */
        input,textarea{
            width:100%;padding:12px 16px;border-radius:8px;
            border:1px solid rgba(255,255,255,.16);
            background:var(--card);color:var(--fg);
            font-size:15px;transition:border-color .2s ease;
        }
        input:focus,textarea:focus{
            outline:none;border-color:var(--brand);
            box-shadow:0 0 0 3px rgba(108,123,255,.1);
        }
        label{display:block;margin-bottom:8px;color:var(--muted);font-weight:500}
        
        /* Loading states */
        .loading{opacity:.7;pointer-events:none}
        .loading::after{
            content:"";display:inline-block;width:12px;height:12px;
            border:2px solid currentColor;border-radius:50%;
            border-top-color:transparent;animation:spin 1s linear infinite;
            margin-left:8px;
        }
        @keyframes spin{to{transform:rotate(360deg)}}
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
            <h1>Professional PDF stamping for serious creators</h1>
            <p class=\"sub\">Transform Gumroad's basic email stamp into branded, secure delivery with buyer-specific watermarks. Protect your digital products while building your brand.</p>
            <div class=\"cta-row\">
                <a class=\"btn primary\" href=\"#demo\">Try free demo</a>
                <a class=\"btn ghost\" href=\"#pricing\">View pricing</a>
            </div>
            <div class=\"pill\">✨ No code required • 🚀 Works with Gumroad Ping • 🔒 Enterprise-grade security</div>
        </header>

        <div class=\"social-proof\">
            <div class=\"social-counter\">500+</div>
            <div class=\"social-text\">Digital creators protecting their PDFs with Gumstamp</div>
            <div class=\"trust-badges\">
                <div class=\"badge\">✓ 99.9% Uptime</div>
                <div class=\"badge\">✓ SOC 2 Compliant</div>
                <div class=\"badge\">✓ GDPR Ready</div>
                <div class=\"badge\">✓ 30-Day Guarantee</div>
            </div>
        </div>

        <section class=\"grid\" aria-label=\"features\">
            <div class=\"card\">
                <h3><span class=\"card-icon\">🎨</span>Custom Branding</h3>
                <p>Replace Gumroad's generic stamp with your professional logo, custom colors, and brand-specific messaging that builds trust with buyers.</p>
            </div>
            <div class=\"card\">
                <h3><span class=\"card-icon\">🔒</span>Security & Deterrence</h3>
                <p>Dynamic per-buyer watermarks, invisible metadata fingerprinting, and diagonal patterns that make unauthorized sharing traceable.</p>
            </div>
            <div class=\"card\">
                <h3><span class=\"card-icon\">⚡</span>Zero Friction Setup</h3>
                <p>Keep your existing Gumroad workflow unchanged. We integrate seamlessly with Ping webhooks and deliver via secure tokenized links.</p>
            </div>
            <div class=\"card\">
                <h3><span class=\"card-icon\">🧰</span>Developer-Grade API</h3>
                <p>RESTful API with comprehensive documentation, webhook integrations, and enterprise-ready security for custom implementations.</p>
            </div>
        </section>

        <section class=\"testimonials\">
            <h2 style=\"text-align:center;margin-bottom:32px\">Trusted by creators worldwide</h2>
            <div style=\"display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px\">
                <div class=\"testimonial\">
                    <div class=\"quote\">Gumstamp transformed our PDF delivery from amateur to professional overnight. The custom branding makes our courses look premium.</div>
                    <div class=\"author\">
                        <div class=\"author-avatar\">S</div>
                        <div>
                            <div><strong>Sarah Chen</strong></div>
                            <div>Digital Course Creator • $15K/month</div>
                        </div>
                    </div>
                </div>
                <div class=\"testimonial\">
                    <div class=\"quote\">Finally, a solution that actually deters piracy. The buyer-specific watermarks have reduced our unauthorized sharing by 80%.</div>
                    <div class=\"author\">
                        <div class=\"author-avatar\">M</div>
                        <div>
                            <div><strong>Marcus Rivera</strong></div>
                            <div>Design Template Studio • 10K+ customers</div>
                        </div>
                    </div>
                </div>
                <div class=\"testimonial\">
                    <div class=\"quote\">The API integration was seamless. Took us 30 minutes to set up what would have taken weeks to build in-house.</div>
                    <div class=\"author\">
                        <div class=\"author-avatar\">A</div>
                        <div>
                            <div><strong>Alex Thompson</strong></div>
                            <div>SaaS Founder • Technical Implementation</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

            <section class=\"pricing\" id=\"demo\" aria-label=\"demo\" style=\"padding:48px 0\">
                <div style=\"text-align:center;margin-bottom:32px\">
                    <h2>Try it now (Free demo)</h2>
                    <p class=\"sub\">Upload a sample PDF and get a dynamic download link template. No signup required.</p>
                </div>
                
                <form id=\"demo-form\" class=\"card\" enctype=\"multipart/form-data\" style=\"margin:0 auto;display:grid;gap:20px;max-width:720px;box-shadow:var(--shadow-lg)\">
                    <div style=\"display:grid;grid-template-columns:1fr 1fr;gap:16px\">
                        <div>
                            <label for=\"product_id\">Product ID</label>
                            <input id=\"product_id\" name=\"product_id\" placeholder=\"e.g. my-digital-course\" required />
                        </div>
                        <div>
                            <label for=\"footer_text\">Footer text</label>
                            <input id=\"footer_text\" name=\"footer_text\" value=\"Licensed to {email}\" />
                        </div>
                    </div>
                    <div>
                        <label for=\"file\">PDF file (max 10MB)</label>
                        <input id=\"file\" name=\"file\" type=\"file\" accept=\"application/pdf\" required />
                        <div style=\"font-size:13px;color:var(--muted);margin-top:6px\">
                            Upload a sample PDF to see how buyer-specific stamping works
                        </div>
                    </div>
                    <details style=\"border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:16px\">
                        <summary style=\"cursor:pointer;color:var(--brand);font-weight:600\">🔑 Have a Pro license? (optional)</summary>
                        <div style=\"margin-top:12px\">
                            <input id=\"license_key\" name=\"license_key\" placeholder=\"Enter your Pro license key\" />
                            <div style=\"font-size:13px;color:var(--muted);margin-top:6px\">
                                Pro features: Custom branding, diagonal watermarks, unlimited downloads
                            </div>
                        </div>
                    </details>
                    <div class=\"cta-row\" style=\"margin-top:8px\">
                        <button class=\"btn primary\" type=\"submit\" id=\"demo-submit\">
                            <span>🚀 Upload & generate link</span>
                        </button>
                        <button class=\"btn ghost\" type=\"reset\">Reset form</button>
                    </div>
                    <div id=\"demo-result\" style=\"display:none\"></div>
                </form>
            </section>

            <section class=\"pricing\" id=\"pricing\">
                <div class=\"pricing-header\">
                    <h2>Choose your plan</h2>
                    <p class=\"pricing-sub\">Start free, upgrade when you need advanced features. All plans include our core PDF stamping technology.</p>
                </div>
                
                <div class=\"plans\">
                    <div class=\"plan\">
                        <h3>Free</h3>
                        <div class=\"price\">$0<span class=\"price-period\">/month</span></div>
                        <div class=\"plan-description\">Perfect for testing and small-scale creators</div>
                        <ul>
                            <li><span class=\"feature-icon\">✓</span> Basic email footer stamping</li>
                            <li><span class=\"feature-icon\">✓</span> 100 downloads/month</li>
                            <li><span class=\"feature-icon\">✓</span> REST API access</li>
                            <li><span class=\"feature-icon\">✓</span> Email support</li>
                            <li class=\"feature-disabled\">✗ Custom branding</li>
                            <li class=\"feature-disabled\">✗ Diagonal watermarks</li>
                            <li class=\"feature-disabled\">✗ Advanced security</li>
                        </ul>
                        <a class=\"btn ghost\" href=\"#demo\" style=\"margin-top:auto\">Start Free</a>
                    </div>

                    <div class=\"plan\">
                        <h3>Starter</h3>
                        <div class=\"price\">$9<span class=\"price-period\">/month</span></div>
                        <div class=\"plan-description\">For growing creators who want branded delivery</div>
                        <ul>
                            <li><span class=\"feature-icon\">✓</span> Everything in Free</li>
                            <li><span class=\"feature-icon\">✓</span> <strong>500 downloads/month</strong></li>
                            <li><span class=\"feature-icon\">✓</span> <strong>Custom footer text & logo</strong></li>
                            <li><span class=\"feature-icon\">✓</span> Basic branding options</li>
                            <li><span class=\"feature-icon\">✓</span> Priority email support</li>
                            <li class=\"feature-disabled\">✗ Unlimited downloads</li>
                            <li class=\"feature-disabled\">✗ Advanced watermarks</li>
                        </ul>
                        <a class=\"btn ghost\" href=\"mailto:support@gumstamp.com?subject=Starter%20Plan\" style=\"margin-top:auto\">Get Starter</a>
                    </div>

                    <div class=\"plan featured\">
                        <h3>Pro</h3>
                        <div class=\"price\">$19<span class=\"price-period\">/month</span></div>
                        <div class=\"plan-description\">For serious creators who want maximum protection</div>
                        <ul>
                            <li><span class=\"feature-icon\">✓</span> Everything in Starter</li>
                            <li><span class=\"feature-icon\">✓</span> <strong>Unlimited downloads</strong></li>
                            <li><span class=\"feature-icon\">✓</span> <strong>Full custom branding</strong></li>
                            <li><span class=\"feature-icon\">✓</span> <strong>Diagonal watermarks</strong></li>
                            <li><span class=\"feature-icon\">✓</span> <strong>Advanced security features</strong></li>
                            <li><span class=\"feature-icon\">✓</span> Priority support + phone</li>
                            <li><span class=\"feature-icon\">✓</span> API rate limit increases</li>
                        </ul>
                        <a class=\"btn primary\" href=\"mailto:support@gumstamp.com?subject=Pro%20Plan%20-%2014%20Day%20Trial\" style=\"margin-top:auto\">Start 14-Day Free Trial</a>
                    </div>
                </div>

                <div class=\"roi-calculator\">
                    <h3 style=\"margin:0 0 16px;color:var(--brand)\">💡 ROI Calculator</h3>
                    <p>If you sell 50+ PDFs monthly at $20+ each, Gumstamp Pro pays for itself by preventing just <strong>one unauthorized share per month</strong>.</p>
                    <div style=\"margin-top:16px;font-size:14px;color:var(--muted)\">
                        Average customer reports 40% reduction in piracy • 15% increase in perceived value
                    </div>
                </div>

                <div style=\"text-align:center;margin-top:32px;color:var(--muted);font-size:14px\">
                    <p><strong>All plans include:</strong> Secure tokenized delivery • GDPR compliance • 99.9% uptime SLA • 30-day money-back guarantee</p>
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
            const submitBtn = document.getElementById('demo-submit');
            const fileInput = document.getElementById('file');
            
            if(!form) return;
            
            // File validation
            fileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    if (file.size > 10 * 1024 * 1024) { // 10MB limit
                        showError('File too large. Please select a PDF under 10MB.');
                        fileInput.value = '';
                        return;
                    }
                    if (!file.type.includes('pdf')) {
                        showError('Please select a PDF file.');
                        fileInput.value = '';
                        return;
                    }
                }
            });
            
            function showError(message) {
                result.style.display = 'block';
                result.innerHTML = `
                    <div class="card" style="border-color: var(--danger); background: rgba(231,76,60,.1)">
                        <h3 style="margin-top:0; color: var(--danger)">⚠️ Error</h3>
                        <p style="color: var(--fg)">${message}</p>
                        <button class="btn ghost" onclick="document.getElementById('demo-result').style.display='none'">Dismiss</button>
                    </div>`;
            }
            
            function showLoading() {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                result.style.display = 'block';
                result.innerHTML = `
                    <div class="card" style="border-color: var(--brand); background: rgba(108,123,255,.1)">
                        <h3 style="margin-top:0; color: var(--brand)">🔄 Processing</h3>
                        <p>Uploading and processing your PDF...</p>
                        <div style="width: 100%; height: 4px; background: rgba(255,255,255,.1); border-radius: 2px; margin: 16px 0;">
                            <div style="width: 0%; height: 100%; background: var(--brand); border-radius: 2px; animation: progress 3s ease-in-out infinite;"></div>
                        </div>
                    </div>`;
            }
            
            function hideLoading() {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const fd = new FormData(form);
                if (!fd.get('file').name) {
                    showError('Please select a PDF file to upload.');
                    return;
                }
                
                showLoading();
                
                try {
                    const res = await fetch('/api/creator/upload', { 
                        method: 'POST', 
                        body: fd 
                    });
                    
                    hideLoading();
                    
                    if(!res.ok){
                        const errorText = await res.text();
                        let errorMessage = 'Upload failed';
                        try {
                            const errorData = JSON.parse(errorText);
                            errorMessage = errorData.detail || errorData.message || errorMessage;
                        } catch {
                            errorMessage = errorText || errorMessage;
                        }
                        throw new Error(errorMessage);
                    }
                    
                    const data = await res.json();
                    const template = data.download_template;
                    
                    result.innerHTML = `
                        <div class="card" style="border-color: var(--ok); background: rgba(46,204,113,.1)">
                            <h3 style="margin-top:0; color: var(--ok)">✅ Upload Successful!</h3>
                            <p>Your PDF has been processed. Use this dynamic link template:</p>
                            <div style="background:var(--card-elevated);padding:16px;border-radius:8px;margin:12px 0;border:1px solid rgba(255,255,255,.1)">
                                <code style="word-break:break-all;color:var(--brand);font-size:13px">${template}</code>
                                <button onclick="navigator.clipboard.writeText('${template}')" class="btn ghost" style="margin-top:8px;font-size:12px">📋 Copy Link</button>
                            </div>
                            
                            <div style="margin-top:20px;padding:16px;background:var(--card);border-radius:8px">
                                <h4 style="margin:0 0 12px;color:var(--brand)">🧪 Test with buyer email:</h4>
                                <form id="token-form" style="display:grid;grid-template-columns:1fr auto;gap:12px;align-items:end">
                                    <div>
                                        <input name="email" placeholder="buyer@example.com" required style="width:100%"/>
                                        <div style="font-size:12px;color:var(--muted);margin-top:4px">Enter any email to generate a test download</div>
                                    </div>
                                    <button class="btn primary" type="submit" style="white-space:nowrap">Generate Test</button>
                                </form>
                                <div id="token-result" style="margin-top:12px"></div>
                            </div>
                        </div>`;

                    const tokenForm = document.getElementById('token-form');
                    const tokenOut = document.getElementById('token-result');
                    const tokenBtn = tokenForm.querySelector('button[type="submit"]');
                    
                    tokenForm.addEventListener('submit', async (ev) => {
                        ev.preventDefault();
                        
                        tokenBtn.classList.add('loading');
                        tokenBtn.disabled = true;
                        tokenOut.innerHTML = '<p style="color:var(--muted)">🔄 Generating personalized download link...</p>';
                        
                        try {
                            const email = new FormData(tokenForm).get('email');
                            const body = { product_id: fd.get('product_id'), email };
                            const licenseField = document.getElementById('license_key');
                            let query = '';
                            if (licenseField && licenseField.value) { 
                                query = '?license_key=' + encodeURIComponent(licenseField.value); 
                            }
                            
                            const res2 = await fetch('/api/creator/token'+query, { 
                                method:'POST', 
                                headers:{'Content-Type':'application/json'}, 
                                body: JSON.stringify(body)
                            });
                            
                            if(!res2.ok){ 
                                throw new Error('Token generation failed: ' + res2.status); 
                            }
                            
                            const data2 = await res2.json();
                            tokenOut.innerHTML = `
                                <div style="text-align:center;padding:16px;background:rgba(46,204,113,.1);border-radius:8px;border:1px solid var(--ok)">
                                    <p style="margin:0 0 12px;color:var(--ok)">✅ Personalized PDF ready!</p>
                                    <a class="btn primary" href="${data2.download_url}" target="_blank" rel="noopener">
                                        🔗 Download Stamped PDF
                                    </a>
                                </div>`;
                        } catch(err) {
                            tokenOut.innerHTML = `<p style="color:var(--danger)">❌ ${err.message}</p>`;
                        } finally {
                            tokenBtn.classList.remove('loading');
                            tokenBtn.disabled = false;
                        }
                    });
                } catch(err){
                    hideLoading();
                    showError(err.message || 'Upload failed. Please try again.');
                }
            });
            
            // Add CSS for progress animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes progress {
                    0% { width: 0% }
                    50% { width: 70% }
                    100% { width: 95% }
                }
            `;
            document.head.appendChild(style);
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
        """Simple health check for load balancers"""
        return {"status": "ok"}


@app.get("/health")
def health():
        """Comprehensive health check with system status"""
        return JSONResponse(content=get_health_status())


@app.get("/metrics/business")
def business_metrics():
        """Business-specific metrics endpoint"""
        logger = structlog.get_logger("gumstamp.metrics")
        
        try:
            # Get basic file counts from storage
            source_dir = settings.storage_dir / "source"
            stamped_dir = settings.storage_dir / "stamped"
            
            source_count = len(list(source_dir.glob("*.pdf"))) if source_dir.exists() else 0
            stamped_count = len(list(stamped_dir.glob("*.pdf"))) if stamped_dir.exists() else 0
            
            return {
                "products": {
                    "source_files": source_count,
                    "stamped_files": stamped_count
                },
                "storage": {
                    "source_dir": str(source_dir),
                    "stamped_dir": str(stamped_dir),
                    "total_size_bytes": sum(f.stat().st_size for f in source_dir.rglob("*") if f.is_file()) if source_dir.exists() else 0
                }
            }
        except Exception as e:
            logger.error("Failed to collect business metrics", error=str(e))
            return {"error": str(e)}
