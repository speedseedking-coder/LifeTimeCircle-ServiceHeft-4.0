from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_HTML = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>LifeTimeCircle – ServiceHeft 4.0</title>
  <style>
    :root { color-scheme: dark; }
    body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background:#0b0f17; color:#e6edf7; }
    .wrap { max-width: 980px; margin: 0 auto; padding: 28px 18px 56px; }
    .card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.10); border-radius: 16px; padding: 18px; }
    h1 { font-size: 28px; margin: 0 0 8px; letter-spacing: 0.2px; }
    p { line-height: 1.5; margin: 10px 0; color: rgba(230,237,247,0.92); }
    .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-top: 14px; }
    a.btn { display:block; padding: 12px 12px; border-radius: 12px; text-decoration:none; color:#e6edf7;
            background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); }
    a.btn:hover { background: rgba(255,255,255,0.10); }
    .muted { color: rgba(230,237,247,0.70); font-size: 13px; }
    .badge { display:inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px;
             background: rgba(80,160,255,0.18); border: 1px solid rgba(80,160,255,0.35); margin-left: 8px; }
    .footer { margin-top: 16px; }
    code { background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 8px; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>LifeTimeCircle – ServiceHeft 4.0 <span class="badge">Backend läuft</span></h1>
      <p>Vom Gebrauchtwagen zum dokumentierten Vertrauensgut.</p>

      <div class="grid">
        <a class="btn" href="/docs">API Docs (Swagger)</a>
        <a class="btn" href="/redoc">API Docs (ReDoc)</a>
        <a class="btn" href="/blog/">Blog (public)</a>
        <a class="btn" href="/news/">News (public)</a>
      </div>

      <div class="footer">
        <p class="muted"><strong>Trust-Ampel Hinweis (Pflichttext):</strong><br/>
        „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“</p>
        <p class="muted">Status-Checks: <code>/openapi.json</code> (keine Duplicate-OperationIds), Tests: <code>pytest -q</code> grün.</p>
      </div>
    </div>
  </div>
</body>
</html>
"""


@router.get("/public/site", include_in_schema=False)
def public_site() -> HTMLResponse:
    return HTMLResponse(content=_HTML, status_code=200)