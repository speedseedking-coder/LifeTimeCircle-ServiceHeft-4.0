
```md
# docs/99_MASTER_CHECKPOINT.md
# LifeTimeCircle – Service Heft 4.0
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
✅ P0 Uploads-Quarantäne: Uploads werden **quarantined by default**, Approve nur nach Scan=**CLEAN**  
✅ Fix Windows-SQLite-Locks: Connections sauber schließen (Tempdir/cleanup stabil)  
✅ PR #27: `Fix: sale-transfer status endpoint participant-only (prevent ID leak)`  
- `GET /sale/transfer/status/{transfer_id}`: object-level Zugriff nur **Initiator ODER Redeemer** (sonst **403**)  
✅ PR #24: `Test: moderator blocked on all non-public routes (runtime scan)`  
- Runtime-Scan über alle registrierten Routes, Moderator außerhalb Allowlist → **403**  
✅ PR #33: **Public: blog/news endpoints**  
- Public Router: `GET /blog(/)`, `GET /blog/{slug}`, `GET /news(/)`, `GET /news/{slug}`  
✅ PR #36: `Fix: OpenAPI duplicate operation ids (documents router double include)`  
- Documents-Router in `server/app/main.py` nur **einmal** registriert (keine Duplicate Operation ID Warnungen mehr)  
✅ PR #37: `Feat: public landing page (/public/site) + docs/07 MVP gates + scripts`  
✅ PR #38: `Fix: /favicon.ico returns 204 (no 404 noise on public site)`  
✅ Tests grün: `poetry run pytest` → **78 passed**  

---

## Public Oberfläche (minimal, backend-served)
- `GET /public/site` (Landingpage)
- `GET /favicon.ico` → **204**
- `GET /docs` (Swagger UI)
- `GET /redoc` (ReDoc)
- `GET /openapi.json`
- `GET /blog/`, `GET /blog/{slug}`
- `GET /news/`, `GET /news/{slug}`

---

## OpenAPI / Router Wiring — DONE (main)
Thema:
- FastAPI OpenAPI-Warnungen: **"Duplicate Operation ID ... documents.py"**

Ursache:
- Documents-Router wurde in `server/app/main.py` doppelt registriert:
  - einmal via `documents_router` (`from app.routers.documents import router as documents_router`)
  - zusätzlich nochmal über `from app.routers import documents` (und dann `documents.router`)

Fix (PR #36):
- `server/app/main.py`: Documents-Router **nur 1x** via `include_router(...)`
- `server/app/routers/__init__.py`: Exporte bereinigt (documents nicht mehr im `__all__` / nicht mehr importiert)

Verifikation (lokal):
- Route-Dedupe-Check: `DUP_ROUTES_COUNT = 0` (via `from app.main import app`, unique route signature check)
- `curl http://127.0.0.1:8000/openapi.json` triggert keine Duplicate-Warnungen mehr im Server-Fenster

---

## P0: Uploads Quarantäne (Documents) — DONE (main)
**Ziel:** Uploads werden serverseitig **niemals** automatisch ausgeliefert, bevor Admin-Freigabe erfolgt.

Workflow:
- Upload → `approval_status=QUARANTINED`, `scan_status=PENDING`
- Admin kann `scan_status` setzen: `CLEAN` oder `INFECTED`
- `INFECTED` erzwingt `approval_status=REJECTED`
- Admin `approve` nur wenn `scan_status=CLEAN` (sonst **409 not_scanned_clean**)

Download-Regeln:
- **User/VIP/Dealer**: nur wenn `APPROVED` **und** Scope/Owner passt (object-level)
- **Admin/Superadmin**: darf auch QUARANTINED/PENDING downloaden (Review)

RBAC/Guards:
- `/documents/*` ist **nicht-public** → Actor erforderlich (**401** ohne Actor)
- Moderator ist auf Documents überall **403**
- Admin-Endpoints (Quarantine/Approve/Reject/Scan) sind **admin-only** (nicht-admin: **403**)

---

## Sale/Transfer Status (ID-Leak Fix) — DONE (main)
Endpoint:
- `GET /sale/transfer/status/{transfer_id}`

Regeln:
- Role-Gate: nur `vip|dealer` (alle anderen **403**)
- Zusätzlich object-level: nur **Initiator ODER Redeemer** darf lesen (sonst **403**)

---

## RBAC (SoT)
- Default: **deny-by-default**
- **Actor required**: ohne Actor → **401**
- **Moderator**: strikt nur **Blog/News**; sonst überall **403**

### Allowlist für MODERATOR (ohne 403)
- `/auth/*`
- `/health`
- `/public/*`
- `/blog/*`
- `/news/*`

Alles andere: **403**.

---

## Public-QR Trust-Ampel (Pflichttext)
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## Tests / Lokal ausführen
> Env-Hinweis: Export/Redaction/HMAC benötigt `LTC_SECRET_KEY` (>=16). Für DEV/Tests explizit setzen.

```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"
poetry run pytest -q
poetry run python .\scripts\check_openapi_duplicates.py
poetry run uvicorn app.main:app --reload`