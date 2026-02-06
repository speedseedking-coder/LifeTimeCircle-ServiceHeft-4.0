# LifeTimeCircle â€“ Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-06** (Europe/Berlin)

Projekt:
- Brand: **LifeTimeCircle**
- Modul: **Service Heft 4.0**
- Ziel: **produktionsreif (keine Demo)**
- Security: **deny-by-default + least privilege**, RBAC **serverseitig enforced**
- Source of Truth: **./docs** (keine Altpfade/Altversionen)

---

## Aktueller Stand (main)
✅ PR #43 gemerged: Web Trust-Ampel Pflichttext im UI + CI/web workflow_dispatch
âœ… P0 Uploads-QuarantÃ¤ne: Uploads werden **quarantined by default**, Approve nur nach Scan=**CLEAN**  
âœ… Fix Windows-SQLite-Locks: Connections sauber schlieÃŸen (Tempdir/cleanup stabil)  
âœ… PR #27: `Fix: sale-transfer status endpoint participant-only (prevent ID leak)`  
- `GET /sale/transfer/status/{transfer_id}`: object-level Zugriff nur **Initiator ODER Redeemer** (sonst **403**)  
âœ… PR #24: `Test: moderator blocked on all non-public routes (runtime scan)`  
- Runtime-Scan Ã¼ber alle registrierten Routes, Moderator auÃŸerhalb Allowlist â†’ **403**  
âœ… PR #33: **Public: blog/news endpoints**  
- Public Router: `GET /blog(/)`, `GET /blog/{slug}`, `GET /news(/)`, `GET /news/{slug}`  
- Router wired in `server/app/main.py`  
- RBAC-Tests/Allowlist entsprechend erweitert  
âœ… PR #36: `Fix: OpenAPI duplicate operation ids (documents router double include)`  
- Documents-Router in `server/app/main.py` nur **einmal** registriert (keine Duplicate Operation ID Warnungen mehr)  
âœ… PR #40: `Add web skeleton + root redirect + docs updates`
- Web-Frontend Skeleton unter `packages/web` (Vite + React + TS)
- Vite Proxy: `/api/*` â†’ `http://127.0.0.1:8000/*`
- API Root Redirect: `GET /` â†’ 307 â†’ `/public/site`
- `GET /favicon.ico` â†’ 204
âœ… Tests grÃ¼n: `poetry run pytest -q`

---

## Web Frontend (Vite + React + TS) â€” DONE (main)
Paths / URLs:
- API: `http://127.0.0.1:8000`  (/, /public/site, /docs, /redoc)
- Web: `http://127.0.0.1:5173`
- Vite Proxy: `/api/*` â†’ `http://127.0.0.1:8000/*`

Gotchas:
- API braucht `LTC_SECRET_KEY` (>=16), sonst RuntimeError.
- Vite nicht mit `q` beenden, wenn Web laufen soll.
- In Vite-Terminal keine Shell-Commands (Input wird von Vite genutzt). FÃ¼r Commands extra Tab.

Start (2 Tabs/Fenster A=API, B=WEB):
- A (API):
  - `cd C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server`
  - `$env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"`
  - `poetry run uvicorn app.main:app --reload`
- B (WEB):
  - `cd C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\packages\web`
  - `npm install` (einmalig)
  - `npm run dev`
  - Browser: `http://127.0.0.1:5173/` (oder `o`+Enter in Vite)

Checks:
- `Test-NetConnection 127.0.0.1 -Port 8000`
- `Test-NetConnection 127.0.0.1 -Port 5173`
- `Invoke-WebRequest "http://127.0.0.1:5173/api/public/site" -UseBasicParsing | Select-Object StatusCode`

---

## OpenAPI / Router Wiring â€” DONE (main)
Thema:
- FastAPI OpenAPI-Warnungen: **"Duplicate Operation ID ... documents.py"**

Ursache:
- Documents-Router wurde in `server/app/main.py` doppelt registriert:
  - einmal via `documents_router` (`from app.routers.documents import router as documents_router`)
  - zusÃ¤tzlich nochmal Ã¼ber `from app.routers import documents` (und dann `documents.router`)

Fix (PR #36):
- `server/app/main.py`: Documents-Router **nur 1x** via `include_router(...)`
- `server/app/routers/__init__.py`: Exporte bereinigt (documents nicht mehr im `__all__` / nicht mehr importiert)

Verifikation (lokal):
- Route-Dedupe-Check: `DUP_ROUTES_COUNT = 0` (via `from app.main import app`, unique route signature check)
- `curl http://127.0.0.1:8000/openapi.json` triggert keine Duplicate-Warnungen mehr im Server-Fenster

---

## Public: Blog/News â€” DONE (main)
Public Router:
- `GET /blog` + `GET /blog/` + `GET /blog/{slug}`
- `GET /news` + `GET /news/` + `GET /news/{slug}`

Files:
- `server/app/routers/blog.py`
- `server/app/routers/news.py`
- `server/app/routers/__init__.py`
- `server/app/main.py` â†’ `app.include_router(blog.router)` + `app.include_router(news.router)`

---

## P0: Uploads QuarantÃ¤ne (Documents) â€” DONE (main)
**Ziel:** Uploads werden serverseitig **niemals** automatisch ausgeliefert, bevor Admin-Freigabe erfolgt.

Workflow:
- Upload â†’ `approval_status=QUARANTINED`, `scan_status=PENDING`
- Admin kann `scan_status` setzen: `CLEAN` oder `INFECTED`
- `INFECTED` erzwingt `approval_status=REJECTED`
- Admin `approve` nur wenn `scan_status=CLEAN` (sonst **409 not_scanned_clean**)

Download-Regeln:
- **User/VIP/Dealer**: nur wenn `APPROVED` **und** Scope/Owner passt (object-level)
- **Admin/Superadmin**: darf auch QUARANTINED/PENDING downloaden (Review)

---

## Sale/Transfer Status (ID-Leak Fix) â€” DONE (main)
Endpoint:
- `GET /sale/transfer/status/{transfer_id}`

Regeln:
- Role-Gate: nur `vip|dealer` (alle anderen **403**)
- ZusÃ¤tzlich object-level: nur **Initiator ODER Redeemer** darf lesen (sonst **403**)

---

## RBAC (SoT)
- Default: **deny-by-default**
- **Actor required**: ohne Actor â†’ **401**
- **Moderator**: strikt nur **Blog/News**; sonst Ã¼berall **403**

### Allowlist fÃ¼r MODERATOR (ohne 403)
- `/auth/*`
- `/health`
- `/public/*`
- `/blog/*`
- `/news/*`

Alles andere: **403**.

---

## Public-QR Trust-Ampel (Pflichttext)
â€žDie Trust-Ampel bewertet ausschlieÃŸlich die Dokumentations- und NachweisqualitÃ¤t. Sie ist keine Aussage Ã¼ber den technischen Zustand des Fahrzeugs.â€œ

---

## Tests / Lokal ausfÃ¼hren
> Env-Hinweis: Export/Redaction/HMAC benÃ¶tigt `LTC_SECRET_KEY` (>=16). FÃ¼r DEV/Tests explizit setzen.

```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"
poetry run pytest -q
