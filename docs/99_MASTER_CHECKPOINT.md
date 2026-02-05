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
✅ PR #24 gemerged: `Test: moderator blocked on all non-public routes (runtime scan)`  
✅ CI/pytest (pull_request) grün  
✅ `main` pulled, Branch aufgeräumt  
✅ Test ist in `server/tests/test_moderator_block_coverage_runtime.py` vorhanden (Runtime-Scan über alle registrierten Routes)  
✅ Regel: außerhalb `/auth`, `/health`, `/public` und `/blog|/news` muss MODERATOR **403** bekommen  
ℹ️ Blog/News Assertions sind bewusst **skipped**, bis `/blog|/news` Routes existieren

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