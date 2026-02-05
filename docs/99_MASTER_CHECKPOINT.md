<<<<<<< HEAD
# docs/99_MASTER_CHECKPOINT.md
=======
>>>>>>> origin/main
# LifeTimeCircle – Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-05**

Projekt:
- Brand: **LifeTimeCircle**
- Hauptmodul (Core): **Service Heft / Servicebook 4.0**
- Ziel: **produktionsreif (keine Demo)**
<<<<<<< HEAD
- Security: **deny-by-default + least privilege**, RBAC **serverseitig** enforced
- Source of Truth: **/docs** (keine Altpfade/Altversionen)
=======
- Sicherheits-Prämisse: **deny-by-default + least privilege**, RBAC **serverseitig** enforced
- Source of Truth: **./docs** (keine Altpfade/Altversionen)
>>>>>>> origin/main

---

## Status (Hauptmodul zuerst)
<<<<<<< HEAD
✅ `main` ist aktuell (lokal clean & synced)  
✅ Lokal Tests grün: `server → poetry run pytest -q` (mit `LTC_SECRET_KEY` gesetzt)  
✅ CI grün: GitHub Actions Workflow **CI** (Job: `pytest`)
=======
✅ `main` ist aktuell (synced)  
✅ Lokal Tests grün: `server → poetry run pytest -q` (für Export/Redaction: `LTC_SECRET_KEY` setzen)  
✅ CI grün: GitHub Actions Workflow `CI`, Job `pytest` (`poetry run pytest -q`)  
✅ Branch Protection `main` final (PR-only, strict, linear, enforce admins, required conversation resolution, required check via `checks[] + app_id`)

---

## Servicebook (Core / System of Record)
✅ Core Servicebook: **Inspection Events + Cases + Remediation** (als Servicebook-Entries/Logs)  
✅ Router sicher über `create_app()` eingebunden  
✅ RBAC deny-by-default, `moderator` via `forbid_moderator` ausgeschlossen, Actor required (ohne Actor → 401)

---

## Core-Querschnitt: Documents/Uploads/Export
✅ P0 Uploads: **Documents Router + Store** (**Quarantine-by-default**)  
✅ `python-multipart` als Dependency ergänzt (FastAPI FormData Uploads)  
✅ Repo-Hygiene: `.gitignore`/Cleanup für Runtime/Cache/DB/Storage  
✅ Export-Hardening: **redacted Export** gibt Dokument-Refs **nur** mit Status **APPROVED** aus (Test vorhanden)  
✅ P0 Scan-Hook: Upload wird gescannt; **Approve nur bei CLEAN**; Admin-Rescan Endpoint
>>>>>>> origin/main

---

## Servicebook (Core / System of Record)
✅ Core Servicebook: **Inspection Events + Cases + Remediation** (Servicebook-Entries/Logs)  
✅ Router sicher über `create_app()` eingebunden (`app.include_router(servicebook.router)`)

---

<<<<<<< HEAD
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
=======
## P0: Uploads Quarantine-by-default (Core-Querschnitt)
### Routes (Documents)
- `POST /documents/upload`
- `GET /documents/{doc_id}`
- `GET /documents/{doc_id}/download`
- `GET /documents/admin/quarantine`
- `POST /documents/{doc_id}/approve`
- `POST /documents/{doc_id}/reject`
- `POST /documents/{doc_id}/scan` (Admin Rescan)

### Security / RBAC
- **Moderator** darf nur Blog/News → alle `/documents/*` tragen `Depends(forbid_moderator)`
- **Actor required**: Ohne Actor → **401**
- **Quarantine Default**: Uploads sind initial `PENDING/QUARANTINED`
- **Quarantäne-Workflow**:
  - Quarantäne-Liste + Review + `approve/reject/scan`: **nur `admin`/`superadmin`**
  - SoT dazu: `docs/03_RIGHTS_MATRIX.md` Abschnitt **3b**
- **Auslieferung/Download** für `user/vip/dealer`: **nur** wenn Status **APPROVED** (und Scope passt)
- **Keine public uploads**: Uploads/Storage werden **nicht** als StaticFiles gemounted

---

## P0: Uploads Scan-Hook + Approve-Gating
### Ziel
Uploads bleiben Quarantäne-by-default. Freigabe (APPROVED) nur, wenn der Upload-Scan **CLEAN** ist.

### Implementiert
- `documents_store`: Scan-Hook nach Upload (Env `LTC_SCAN_MODE`: `stub|disabled|clamav`)
- DB: neue Spalten `scan_status`, `scanned_at`, `scan_engine`, `scan_error` (lightweight migration via `ALTER TABLE`)
- Approve: nur erlaubt bei `scan_status=CLEAN`, sonst **409** `not_scanned_clean`
- Admin: neues Endpoint `POST /documents/{id}/scan` (rescan)
- Policy: `INFECTED` → auto-reject (reviewed_by=`scanner`)
>>>>>>> origin/main

---

## Export-Hardening (Quarantine-by-default)
✅ Redacted Export filtert Dokument-Refs strikt auf **APPROVED** (Test vorhanden)  
✅ Full Export nur nach Freigabe-Flow (SUPERADMIN, Audit/TTL/Secret-Key Checks)

---

<<<<<<< HEAD
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
=======
## CI / GitHub Actions (Workflow)
✅ Workflow `CI` aktiv (trigger: `push`/`pull_request` auf `main`)  
✅ Python 3.12 + Poetry, `server/` Working-Directory, `poetry run pytest -q`  
✅ Runtime Dirs: `mkdir -p data` (Runner)  
✅ GitHub Secret `LTC_SECRET_KEY` gesetzt
>>>>>>> origin/main

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

<<<<<<< HEAD
## Lokal Tests / Smoke
=======
## Tests / Lokal ausführen
>>>>>>> origin/main
```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"

# für Export/Redaction/Secret-Checks
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"

<<<<<<< HEAD
poetry run pytest -q

poetry run pytest -q
=======
poetry run pytest -q
>>>>>>> origin/main
