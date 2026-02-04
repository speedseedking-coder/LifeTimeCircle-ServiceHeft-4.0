# docs/99_MASTER_CHECKPOINT.md
# LifeTimeCircle – Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-04**

Projekt:
- Brand: **LifeTimeCircle**
- Hauptmodul (Core): **Service Heft / Servicebook 4.0**
- Ziel: **produktionsreif (keine Demo)**
- Sicherheits-Prämisse: **deny-by-default + least privilege**, RBAC **serverseitig** enforced
- Source of Truth: **/docs** (keine Altpfade/Altversionen)

---

## Status (Hauptmodul zuerst)
✅ Tests grün: `poetry run pytest -q`  
✅ Branch: **feat/uploads-quarantine-p0**

### Servicebook (Core / System of Record)
✅ Core Servicebook: **Inspection Events + Cases + Remediation** (als Servicebook-Entries/Logs)  
✅ Router sicher über `create_app()` eingebunden (keine unsicheren Patch-Scripts)

### Core-Querschnitt: Documents/Uploads/Export
✅ P0 Uploads: **Documents Router + Store** (**Quarantine-by-default**)  
✅ `python-multipart` als Dependency ergänzt (FastAPI FormData Uploads)  
✅ Repo-Hygiene: `.gitignore`/Cleanup für Runtime/Cache/DB/Storage

---

## Core-Prinzip (Wichtig)
**Servicebook ist das Core-Modul / System of Record.**  
Alle weiteren “Module/Prozesse” sind **Producer**, die bei Durchführung **Service-Ereignisse erzeugen** und als **Entries im Servicebook** ablegen.  
→ Ownership bleibt beim Core: **Servicebook**.

---

## Neu gebaut/angepasst (Core: Servicebook – Inspection Events + Cases + Remediation)
### Ziel-Flow (Core-Mechanik)
- Producer (z. B. GPS-Probefahrt / OBD-Auslesung) erzeugt **Inspection Event** im Servicebook.
- Ergebnis **OK / NOT_OK**
- Bei **NOT_OK**: automatisch **Case** (Maßnahmenfall) als Servicebook-Entry
- Remediation dokumentiert; bei **OK**: Case wird **DONE**

### Implementiert
#### Router
`server/app/routers/servicebook.py`
- `GET  /servicebook/{servicebook_id}/entries`
- `POST /servicebook/{servicebook_id}/inspection-events`
- `POST /servicebook/{servicebook_id}/cases/{case_entry_id}/remediation`

#### Security / RBAC / Auth
- Router serverseitig **deny-by-default**
- **Moderator ausgeschlossen**: `Depends(forbid_moderator)` hängt an allen `/servicebook/*` Routen
- Actor erforderlich (ohne Actor → 401)

#### Store / DB (Autodetect + Bootstrap für Test/Dev)
`server/app/services/servicebook_store.py`
- Reflection/Autodetect (analog Export)
- Auto-Bootstrap wenn Tabelle fehlt:
  - **SQLite/Test/Dev**: auto bootstrap
  - Optional Env: `LTC_AUTO_CREATE_SERVICEBOOK_TABLE=1`
  - Sonst auto nur bei SQLite
- Best-effort Mapping (owner/role/status/title/details/etc.)

---

## P0: Uploads Quarantine-by-default (Core-Querschnitt)
### Neue Routes (Documents)
- `POST /documents/upload`
- `GET /documents/{doc_id}`
- `GET /documents/{doc_id}/download`
- `GET /documents/admin/quarantine`
- `POST /documents/{doc_id}/approve`
- `POST /documents/{doc_id}/reject`

### Security / RBAC (FIX)
- **Moderator** darf nur Blog/News → alle `/documents/*` müssen `Depends(forbid_moderator)` haben
- **Keine public uploads**: Uploads/Storage werden **nicht** als StaticFiles gemounted
- **Quarantine Default**: Uploads sind initial `PENDING/QUARANTINED`
- **Download/Content** für `user/vip/dealer`: **nur** wenn Status **APPROVED** (und Scope passt)
- **Quarantäne-Workflow**:
  - `GET /documents/admin/quarantine` + `approve/reject` + Review-Download: **nur `admin`/`superadmin`**
  - SoT dazu: `docs/03_RIGHTS_MATRIX.md` Abschnitt **3b**

---

## Tests (neu/angepasst)
### Servicebook
- Route-Registrierungstest: Routen existieren + `forbid_moderator` auf allen `/servicebook/*`
- Flow-Test: `NOT_OK` → Case erzeugt; Remediation `OK` → Case `DONE`
- Tests setzen `get_actor` via `dependency_overrides` als admin

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

## Nächster Schritt (Core/P0): Export-Hardening passend zu Quarantäne
**Ziel:** `export_servicebook_redacted` gibt Dokument-Refs **nur** mit Status `APPROVED` aus (Quarantäne-by-default).  
**Nachweis:** Test beweist, dass `pending/unapproved` Docs im **redacted Export** nicht auftauchen.

Startsatz für neuen Chat:
- **„weiter mit Export-Servicebook Redaction nur APPROVED“**

---

## Tests / Lokal ausführen
```powershell
cd .\server

# für Export/Redaction Tests (sonst "missing_or_weak_secret_key")
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"

poetry run pytest -q
