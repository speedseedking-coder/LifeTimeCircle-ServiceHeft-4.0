@'
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

Konflikt-Priorität:
1) `docs/99_MASTER_CHECKPOINT.md`
2) `docs/03_RIGHTS_MATRIX.md`
3) `server/`
4) Backlog/sonstiges

Env-Hinweis:
- Export/Redaction/HMAC braucht `LTC_SECRET_KEY` (>=16); Tests/DEV setzen ihn explizit.

---

## Aktueller Stand (main)
✅ P0 Uploads-Quarantäne: Uploads werden **quarantined by default**, Approve nur nach Scan=**CLEAN**  
✅ Fix Windows-SQLite-Locks: Connections sauber schließen (Tempdir/cleanup stabil)  
✅ PR #24: `Test: moderator blocked on all non-public routes (runtime scan)`  
✅ PR #27: `Fix: sale-transfer status endpoint participant-only (prevent ID leak)`  
✅ PR #33: `Public: blog/news endpoints`  
✅ PR #36: `Fix: include documents router only once (remove duplicate routes/OpenAPI warnings)`  
✅ PR #37: `Feat: public landing page (/public/site) + docs/07 MVP gates`  
✅ PR #38: `Fix: /favicon.ico returns 204 (no 404 noise on public site)`  
✅ CI/Tests: `poetry run pytest -q` **grün**

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

## OpenAPI / Duplicate OperationId — DONE (main)
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
- `server/scripts/check_openapi_duplicates.py`:
  - `DUP_ROUTES_COUNT = 0`
  - `DUP_OPERATION_ID_COUNT = 0`
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
poetry run uvicorn app.main:app --reload