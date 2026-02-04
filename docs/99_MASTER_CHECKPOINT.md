docs/99_MASTER_CHECKPOINT.md
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
✅ `main` ist aktuell  
✅ Tests grün: `poetry run pytest -q`  
✅ CI grün: GitHub Actions Workflow `CI` läuft auf `push`/`pull_request` (Branch `main`) und führt `pytest` aus

### Servicebook (Core / System of Record)
✅ Core Servicebook: **Inspection Events + Cases + Remediation** (als Servicebook-Entries/Logs)  
✅ Router sicher über `create_app()` eingebunden

### Core-Querschnitt: Documents/Uploads/Export
✅ P0 Uploads: **Documents Router + Store** (**Quarantine-by-default**)  
✅ `python-multipart` als Dependency ergänzt (FastAPI FormData Uploads)  
✅ Repo-Hygiene: `.gitignore`/Cleanup für Runtime/Cache/DB/Storage  
✅ Export-Hardening: **redacted Export** gibt Dokument-Refs **nur** mit Status **APPROVED** aus (Test vorhanden)

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
### Routes (Documents)
- `POST /documents/upload`
- `GET /documents/{doc_id}`
- `GET /documents/{doc_id}/download`
- `GET /documents/admin/quarantine`
- `POST /documents/{doc_id}/approve`
- `POST /documents/{doc_id}/reject`

### Security / RBAC (FIX)
- **Moderator** darf nur Blog/News → alle `/documents/*` tragen `Depends(forbid_moderator)`
- **Keine public uploads**: Uploads/Storage werden **nicht** als StaticFiles gemounted
- **Quarantine Default**: Uploads sind initial `PENDING/QUARANTINED`
- **Download/Content** für `user/vip/dealer`: **nur** wenn Status **APPROVED** (und Scope passt)
- **Quarantäne-Workflow**:
  - Quarantäne-Liste + Review + `approve/reject`: **nur `admin`/`superadmin`**
  - SoT dazu: `docs/03_RIGHTS_MATRIX.md` Abschnitt **3b**

---

## Export-Hardening (Quarantine-by-default)
✅ `export_servicebook_redacted` filtert Dokument-Refs strikt auf **APPROVED**  
✅ Test beweist, dass `pending/unapproved` Docs im **redacted Export** nicht auftauchen

---

## CI / GitHub Actions (Workflow) — 2026-02-04
### Ziel / SoT
- Produktionsreifer MVP, Security: deny-by-default + least privilege, RBAC serverseitig enforced
- Source of Truth: `./docs` (keine Altpfade)

### Heute erledigt (CI/Workflow)
✅ GitHub Actions CI eingerichtet  
✅ Ordner `.github/workflows/` im Repo-Root angelegt  
✅ Workflow `ci.yml` hinzugefügt (trigger: `push`/`pull_request` für Branch `main`)  
✅ CI nutzt **Python 3.12** + **Poetry** und führt `poetry run pytest -q` im `server/` Working-Directory aus  
✅ GitHub Secret `LTC_SECRET_KEY` im Repo gesetzt (z. B. via `gh secret set LTC_SECRET_KEY`)

### CI-Failure gefixt (SQLite)
- Erstes CI-Run scheiterte mit:
  - `sqlite3.OperationalError: unable to open database file (./data/app.db)`
  - Ursache: im Runner fehlte der Ordner `server/data`
✅ Fix: Workflow ergänzt um Step **“Prepare runtime dirs”** mit `mkdir -p data` (läuft im `server/` Working-Directory)  
✅ Danach: neuer Run **grün**

### Verifiziert
- `gh workflow list` zeigt Workflow **CI** aktiv
- Run `21688348224`: **Success** (Job `pytest` erfolgreich)

### Wichtige Learnings (für nächste Chats)
- Workflows gehören ins Repo-Root: `.github/workflows/...` (nicht unter `server/`)
- YAML nicht in PowerShell “ausführen” — Datei im Editor anlegen
- CI braucht ggf. Runtime-Verzeichnisse (hier `server/data`) explizit

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

## Nächster Schritt (P0 Security): Admin-Gates & Negativ-Tests für Quarantäne
**Ziel:** Nachweisbar, dass normale Rollen niemals Quarantäne-Aktionen ausführen können.  
**DoD:**
- Tests: `user/vip/dealer` bekommen **403** auf:
  - `GET /documents/admin/quarantine`
  - `POST /documents/{id}/approve`
  - `POST /documents/{id}/reject`
- Tests: `moderator` bekommt **403** auf alle `/documents/*` (bleibt strikt nur Blog/News)
- Keine Logs mit PII/Secrets beim Approve/Reject

---

## Next Focus (empfohlen): Branch Protection für `main` (GitHub UI)
**Ziel:** PR-Workflow erzwingen, keine Direkt-Pushes auf `main`.  
Empfohlene Settings:
- Require PR before merge
- Require status checks to pass (**CI/pytest**)
- Require branch up to date
- Optional: no bypass / conversation resolution

---

## Tests / Lokal ausführen
```powershell
cd .\server

# für Export/Redaction Tests (sonst "missing_or_weak_secret_key")
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"

poetry run pytest -q
---

## 2026-02-04 – CI + Branch Protection finalisiert

### Merged PRs
- #5 Tests: RBAC deny für Documents-Quarantäne-Admin-Endpunkte (Non-Admin => 403, Unauth => 401, Moderator auch Read => 403)
- #6 Docs: Master Checkpoint CI/Actions Update
- #7 chore: branch protection smoke (Smoke-Test)
- #8 chore: remove bp smoke artifact (Cleanup)

### CI
- GitHub Actions Workflow: **CI** mit Job **pytest** aktiv.
- Required Status Check final **robust** gesetzt über *required_status_checks.checks* (Check-Run):
  - context: **pytest**
  - app_id: **15368** (GitHub Actions)
  -> vermeidet String-/Space-Mismatch ("CI/..." vs "CI / ...") und PR vs push Context-Fallen.

### Branch Protection (main)
- PR-only enforced (kein Direct Push).
- strict: **true** (up-to-date required)
- linear history: **true**
- enforce admins: **true**
- force pushes: **false**
- deletions: **false**
- require conversation resolution: **true**

### Learnings / Pitfalls (damit wir nicht wieder reinlaufen)
- Branch-Protection REST: allow_force_pushes/allow_deletions im PUT-Body als **BOOLEAN** (nicht {enabled:...}).
- required_conversation_resolution kann nicht per separatem Endpoint gepatcht werden -> im **PUT-Body** setzen.
- Required Check Name muss **exakt** matchen; am stabilsten über **checks + app_id** statt contexts-Strings.

### Aktueller main Stand (letzte Commits)
def0e40 chore: remove bp smoke artifact (#8)
2718dea chore: branch protection smoke (#7)
001dc66 Docs: Master Checkpoint CI/Actions Update (#6)
099cc49 Tests: RBAC deny for documents quarantine admin endpoints (#5)

