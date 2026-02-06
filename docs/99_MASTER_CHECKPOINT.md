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
- Router wired in `server/app/main.py`  
- RBAC-Tests/Allowlist entsprechend erweitert  
✅ Tests grün: `poetry run pytest` → **78 passed**

---

## Public: Blog/News — DONE (main)
Public Router:
- `GET /blog` + `GET /blog/` + `GET /blog/{slug}`
- `GET /news` + `GET /news/` + `GET /news/{slug}`

Files:
- `server/app/routers/blog.py`
- `server/app/routers/news.py`
- `server/app/routers/__init__.py`
- `server/app/main.py` → `app.include_router(blog.router)` + `app.include_router(news.router)`

Tests / Guards:
- `server/tests/test_rbac_guard_coverage.py` angepasst
- `server/tests/test_rbac_moderator_blog_only.py` Allowlist erweitert: `/blog/*`, `/news/*`

Local Dev Scripts:
- `server/scripts/patch_wire_blog_news_in_main.ps1`
- `server/scripts/run_api_local.ps1`
- `server/scripts/smoke_blog_news.ps1`

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

Tests:
- Quarantine-Workflow + Approve-Only-After-CLEAN: `server/tests/test_documents_quarantine_workflow.py`
- Negative RBAC/Moderator/Admin-Gates: `server/tests/test_documents_quarantine_*`

---

## Sale/Transfer Status (ID-Leak Fix) — DONE (main)
Endpoint:
- `GET /sale/transfer/status/{transfer_id}`

Regeln:
- Role-Gate: nur `vip|dealer` (alle anderen **403**)
- Zusätzlich object-level: nur **Initiator ODER Redeemer** darf lesen (sonst **403**)

Tests:
- `server/tests/test_sale_transfer_api.py` deckt ab:
  - vor Redeem: **403**
  - nach Redeem: **200**

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

## Hinweise / Tech-Debt (main)
- Beim Server-Start können FastAPI-Warnings zu **"Duplicate Operation ID"** aus `app/routers/documents.py` erscheinen.
  - Tests laufen grün; später sauber machen (z.B. `operation_id` explizit setzen und/oder Doppel-Decorator/Name-Kollision prüfen).

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
