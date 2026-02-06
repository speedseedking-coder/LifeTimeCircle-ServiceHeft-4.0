# docs/99_MASTER_CHECKPOINT.md
# LifeTimeCircle – Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-05**

Projekt:
- Brand: **LifeTimeCircle**
- Modul: **Service Heft 4.0**
- Ziel: **produktionsreif (keine Demo)**
- Security: **deny-by-default + least privilege**, RBAC **serverseitig enforced**
- Source of Truth: **./docs** (keine Altpfade/Altversionen)

---

## Aktueller Stand (main)
✅ Commit `1e6f947`: `P0: documents upload quarantined by default + admin scan/approve (v2)`  
✅ Commit `7c4f318`: `Fix: close sqlite connections to avoid Windows file locks` (Tempdir/cleanup auf Windows stabil)  

✅ PR #27 gemerged: `Fix: sale-transfer status endpoint participant-only (prevent ID leak)`  
✅ Status Endpoint (`GET /sale/transfer/status/{transfer_id}`): object-level Zugriff nur **Initiator ODER Redeemer** (sonst **403**)  
✅ Test-Coverage erweitert in `server/tests/test_sale_transfer_api.py` (vor Redeem: **403**, nach Redeem: **200**)  

✅ PR #24 gemerged: `Test: moderator blocked on all non-public routes (runtime scan)`  
✅ CI/pytest (pull_request) grün  
✅ Test ist in `server/tests/test_moderator_block_coverage_runtime.py` vorhanden (Runtime-Scan über alle registrierten Routes)  
✅ Regel: außerhalb `/auth`, `/health`, `/public` und `/blog|/news` muss MODERATOR **403** bekommen  
ℹ️ Blog/News Assertions sind bewusst **skipped**, bis `/blog|/news` Routes existieren

---

## P0: Uploads Quarantäne (Documents) — DONE (main)
**Ziel:** Uploads werden serverseitig **niemals** automatisch ausgeliefert, bevor Admin-Freigabe erfolgt.

Workflow:
- Upload → `approval_status=QUARANTINED`, `scan_status=PENDING`
- Admin kann `scan_status` setzen: `CLEAN` oder `INFECTED`
- `INFECTED` erzwingt `approval_status=REJECTED`
- Admin `approve` nur wenn `scan_status=CLEAN` (sonst **409 not_scanned_clean**)
- Download-Regeln:
  - **User**: nur wenn `APPROVED` **und** Owner-Match (object-level)
  - **Admin**: darf auch QUARANTINED/PENDING downloaden (Review)

RBAC/Guards:
- `/documents/*` ist **nicht-public** → Actor erforderlich (**401** ohne Actor)
- Moderator ist auf Documents überall **403** (Blog/News only SoT)
- Admin-Endpoints unter `/documents/admin/*` bzw. approve/reject/scan sind **admin-only** (nicht-admin: **403**)

Tests:
- Quarantine-Workflow + Approve-Only-After-CLEAN: `server/tests/test_documents_quarantine_workflow.py`
- Negative RBAC/Moderator/Admin-Gates: `server/tests/test_documents_quarantine_*`

---

## RBAC (SoT)
- Default: **deny-by-default**
- **Actor required**: ohne Actor → **401**
- **Moderator**: strikt nur **Blog/News**; sonst überall **403**

### Allowlist für MODERATOR (ohne 403)
- `/auth/*`
- `/health`
- `/public/*`
- `/blog/*` (falls vorhanden)
- `/news/*` (falls vorhanden)

Alles andere: **403**.

---

## Public-QR Trust-Ampel (Pflichttext)
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## Tests / Lokal ausführen
```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"

# für Export/Redaction/Secret-Checks
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"

poetry run pytest -q
```
