# docs/99_MASTER_CHECKPOINT.md
# LifeTimeCircle – Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-05**

Projekt:
- Brand: **LifeTimeCircle**
- Hauptmodul (Core): **Service Heft / Servicebook 4.0**
- Ziel: **produktionsreif (keine Demo)**
- Security: **deny-by-default + least privilege**, RBAC **serverseitig** enforced
- Source of Truth: **/docs** (keine Altpfade/Altversionen)

---

## Status (Hauptmodul zuerst)
✅ `main` ist aktuell (lokal clean & synced)  
✅ Lokal Tests grün: `server → poetry run pytest -q` (mit `LTC_SECRET_KEY` gesetzt)  
✅ CI grün: GitHub Actions Workflow **CI** (Job: `pytest`)

---

## Servicebook (Core / System of Record)
✅ Core Servicebook: **Inspection Events + Cases + Remediation** (Servicebook-Entries/Logs)  
✅ Router sicher über `create_app()` eingebunden (`app.include_router(servicebook.router)`)

---

## Core-Querschnitt: Documents / Uploads / Quarantine / Scan / Export

### Router Registration (verifiziert)
✅ `server/app/main.py` enthält:
- `app.include_router(documents_router)`
- `app.include_router(servicebook.router)`

### P0 Uploads: Quarantine-by-default (merged)
✅ Uploads sind initial **PENDING** (deny-by-default)  
✅ `GET /documents/{id}` und `GET /documents/{id}/download` liefern für normale Rollen **nur bei APPROVED**  
✅ Admin-Workflow:
- `GET  /documents/admin/quarantine`
- `POST /documents/{id}/approve`
- `POST /documents/{id}/reject`

### P0 Scan Hook: Approve nur bei CLEAN (merged)
✅ Scan-Hook nach Upload (Env: `LTC_SCAN_MODE=stub|disabled|clamav`)  
✅ DB-Felder: `scan_status`, `scanned_at`, `scan_engine`, `scan_error` (lightweight `ALTER TABLE`)  
✅ Approve ist **nur** erlaubt wenn `scan_status=CLEAN` → sonst **409** `not_scanned_clean`  
✅ Admin Rescan Endpoint:
- `POST /documents/{id}/scan`  
✅ Policy: `INFECTED` → auto-reject (reviewed_by=`scanner`)

### Security / RBAC (SoT)
✅ `moderator` strikt nur Blog/News → **hart geblockt** für `/documents/*`  
✅ Unauthenticated → **401** (require_actor)  
✅ Quarantäne-Aktionen **nur** `admin/superadmin`  
✅ Keine public uploads: Storage wird **nicht** als StaticFiles gemounted  
✅ Exports: **redacted default**, Dokument-Refs nur wenn **APPROVED**

---

## Export-Hardening (Quarantine-by-default)
✅ Redacted Export filtert Dokument-Refs strikt auf **APPROVED** (Test vorhanden)  
✅ Full Export nur nach Freigabe-Flow (SUPERADMIN, Audit/TTL/Secret-Key Checks)

---

## CI / Branch Protection (final)
### GitHub Actions
✅ Workflow: `CI` → Job `pytest` (Python 3.12 + Poetry, `poetry run pytest -q` im `server/` Working Directory)  
✅ Runner Prep: `mkdir -p data` (verhindert SQLite `unable to open database file`)  
✅ Repo Secret: `LTC_SECRET_KEY` gesetzt

### Branch Protection `main` (final)
✅ PR-only enforced (kein direct push)  
✅ strict: true (branch up-to-date required)  
✅ required_linear_history: true  
✅ enforce_admins: true  
✅ allow_force_pushes: false  
✅ allow_deletions: false  
✅ required_conversation_resolution: true  
✅ Required Check robust über `required_status_checks.checks`:
- context: `pytest`
- app_id: `15368` (GitHub Actions)

---

## Repo Hygiene (Gitignore / Cleanup)
Ignorieren (nicht versionieren):
- `__pycache__/`, `.pytest_cache/`
- `server/data/*.db*`
- `server/storage/**`
- `.env*`
- `node_modules/`, `dist/`
- `*.zip`, `*.bak*`

---

## Lokal Tests / Smoke
```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"

# für Export/Redaction/Secret-Checks
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"

poetry run pytest -q

poetry run pytest -q
