# LifeTimeCircle – Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-05**

Projekt:
- Brand: **LifeTimeCircle**
- Hauptmodul (Core): **Service Heft / Servicebook 4.0**
- Ziel: **produktionsreif (keine Demo)**
- Sicherheits-Prämisse: **deny-by-default + least privilege**, RBAC **serverseitig** enforced
- Source of Truth: **./docs** (keine Altpfade/Altversionen)

---

## Status (Hauptmodul zuerst)
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

---

## Core-Prinzip (Wichtig)
**Servicebook ist das Core-Modul / System of Record.**  
Alle weiteren “Module/Prozesse” sind **Producer**, die bei Durchführung **Service-Ereignisse erzeugen** und als **Entries im Servicebook** ablegen.  
→ Ownership bleibt beim Core: **Servicebook**.

---

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

---

## Export-Hardening (Quarantine-by-default)
✅ `export_servicebook_redacted` filtert Dokument-Refs strikt auf **APPROVED**  
✅ Test beweist, dass `pending/unapproved` Docs im **redacted Export** nicht auftauchen

---

## CI / GitHub Actions (Workflow)
✅ Workflow `CI` aktiv (trigger: `push`/`pull_request` auf `main`)  
✅ Python 3.12 + Poetry, `server/` Working-Directory, `poetry run pytest -q`  
✅ Runtime Dirs: `mkdir -p data` (Runner)  
✅ GitHub Secret `LTC_SECRET_KEY` gesetzt

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

## Tests / Lokal ausführen
```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"

# für Export/Redaction/Secret-Checks
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"

poetry run pytest -q