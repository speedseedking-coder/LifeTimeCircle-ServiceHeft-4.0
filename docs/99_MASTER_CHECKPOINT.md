# docs/99_MASTER_CHECKPOINT.md
# LifeTimeCircle â€“ Service Heft 4.0
**MASTER CHECKPOINT (SoT)**
Stand: **2026-02-07** (Europe/Berlin)
Projekt:
- Brand: **LifeTimeCircle**
- Modul: **Service Heft 4.0**
- Ziel: **produktionsreif (keine Demo)**
- Security: **deny-by-default + least privilege**, RBAC **serverseitig enforced**
- Source of Truth: **./docs** (keine Altpfade/Altversionen)

---

## Produkt-Spezifikation (Unified) â€” SoT
- **Ab jetzt nur noch „LifeTimeCircle Â· Service Heft (Unified)“** (kein Parallelzweig „2.0“)
- Vollständige Spezifikation: `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Spezifikation ist erweitert/finalisiert (E2E-Flow, Trust/Unfalltrust, PII, Module, Transfer/Dealer, PDFs/TTL, Notifications, Import, Packaging) â€“ siehe `docs/02_PRODUCT_SPEC_UNIFIED.md`

---

## Aktueller Stand (main)
✅ PR #79 **gemerged** (squash): CI: harden required 'pytest' check + add guard (#79)
- CI-Workflow bereinigt: keine doppelten Job-Keys; Jobs: pytest (required) + web_build
- Fail-fast Guard gegen Drift/Rename des Required Checks:
  - Script: server/scripts/ci_guard_required_job_pytest.ps1
  - CI-Step im pytest Job → bricht ab, wenn jobs: -> pytest: fehlt (sonst Branch-Protection hängt in „Expected/Waiting“)
- Ergebnis: Branch-Protection bleibt stabil (strict=true + required pytest) und ist lokal verifizierbar via:
  - server/scripts/verify_ci_branch_protection.ps1
✅ PR #74 gemerged: `chore: ignore local tmp scratch folder (#74)`
✅ Branch Protection Fix: Required status check Context von `pytest` auf `CI/pytest` korrigiert (verhindert "Expected"/BLOCKED)
✅ Verifiziert: required_status_checks.contexts => ["CI/pytest"]

✅ PR #70 gemerged: `ci: add web smoke build job`
✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`
✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf
✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)
✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)

✅ PR #60 gemerged: `docs: unify final spec (userflow/trust/pii/modules/transfer/pdfs/notifications/import)`
- Neue SoT Datei: `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Updates: `docs/01_DECISIONS.md`, `docs/03_RIGHTS_MATRIX.md`, `docs/04_REPO_STRUCTURE.md`, `docs/06_WORK_RULES.md`, `docs/99_MASTER_CHECKPOINT.md`
- Script: `server/scripts/patch_docs_unified_final_refresh.ps1` (Validator; idempotent; keine Ã„nderungen an bestehenden Docs)

✅ PR #61 gemerged: `fix(scripts): make docs unified refresh patch script parseable + safe`
- Script: `server/scripts/patch_docs_unified_final_refresh.ps1` ist jetzt parsebar und prüft Pflicht-Disclaimer + Kernanker (keine Doc-Rewrites)
✅ PR #54: `fix(web): add mandatory Public QR disclaimer`
- Pflichttext ist exakt in `packages/web/src/pages/PublicQrPage.tsx`:
  - „Die Trust-Ampel bewertet ausschlieÃŸlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“
- Script: `server/scripts/patch_public_qr_disclaimer.ps1` (idempotent)

✅ PR #53: `chore(web): add web smoke toolkit script`
- Script: `server/scripts/ltc_web_toolkit.ps1`
  - quiet kill-node
  - optional `-Clean`
  - `npm ci` + `npm run build`

✅ PR #57: `docs: master checkpoint 2026-02-06 (PR #53/#54)`
- Script: `server/scripts/patch_master_checkpoint_pr53_pr54.ps1` (idempotent; Single-Quotes fix für Backticks)

✅ PR #58: `chore(web): silence npm cache clean --force warning (stderr redirect)`
- `server/scripts/ltc_web_toolkit.ps1` enthält:
  - `try { & cmd /c "npm cache clean --force" 2>$null | Out-Null } catch { }`
- Script: `server/scripts/patch_ltc_web_toolkit_silence_npm_cache_warn.ps1` (idempotent)

✅ PR #59: `docs: master checkpoint add PR #58`
- Script: `server/scripts/patch_master_checkpoint_pr58.ps1` (idempotent, UTF-8 no BOM, newline/trailing newline stabil)

✅ Docs Refresh: Unified Final Spec (SoT Alignment)
- Updates: `docs/02_PRODUCT_SPEC_UNIFIED.md`, `docs/01_DECISIONS.md`, `docs/03_RIGHTS_MATRIX.md`, `docs/06_WORK_RULES.md`
- Script: `server/scripts/patch_docs_unified_final_refresh.ps1` (idempotent)

✅ P0 Uploads-Quarantäne: Uploads werden **quarantined by default**, Approve nur nach Scan=**CLEAN**  
✅ Fix Windows-SQLite-Locks: Connections sauber schlieÃŸen (Tempdir/cleanup stabil)  
✅ PR #27: `Fix: sale-transfer status endpoint participant-only (prevent ID leak)`  
- `GET /sale/transfer/status/{transfer_id}`: object-level Zugriff nur **Initiator ODER Redeemer** (sonst **403**)  
✅ PR #24: `Test: moderator blocked on all non-public routes (runtime scan)`  
- Runtime-Scan über alle registrierten Routes, Moderator auÃŸerhalb Allowlist ’ **403**  
✅ PR #33: **Public: blog/news endpoints**  
- Public Router: `GET /blog(/)`, `GET /blog/{slug}`, `GET /news(/)`, `GET /news/{slug}`  
- Router wired in `server/app/main.py`  
- RBAC-Tests/Allowlist entsprechend erweitert  
✅ PR #36: `Fix: OpenAPI duplicate operation ids (documents router double include)`  
- Documents-Router in `server/app/main.py` nur **einmal** registriert (keine Duplicate Operation ID Warnungen mehr)  
✅ PR #40: `Add web skeleton + root redirect + docs updates`
- Web-Frontend Skeleton unter `packages/web` (Vite + React + TS)
- Vite Proxy: `/api/*` ’ `http://127.0.0.1:8000/*`
- API Root Redirect: `GET /` ’ 307 ’ `/public/site`
- `GET /favicon.ico` ’ 204
✅ PR #46: **P0 Actor Source of Truth** (serverseitig, DEV-Headers gated)  
- Zentraler Actor ist serverseitig die **Source of Truth** (kein Client-Trust)  
- DEV/Test-Header-Override nur hinter Gate (nicht in Produktion)  
- Files u.a.: `server/app/auth/actor.py`, `server/scripts/patch_actor_source_of_truth_p0.ps1`  
✅ PR #47: **P0 VIP Business Staff-Limit + SUPERADMIN Gate** (serverseitig)  
- VIP-Gewerbe: **max. 2 Staff-Accounts**  
- Staff-Zuordnung/Freigabe/Erhöhung: **nur superadmin**  
- Files u.a.: `server/app/admin/routes.py`, `server/tests/test_vip_business_staff_limit.py`  
✅ Tests grün: `poetry run pytest -q`

---

## Web Frontend (Vite + React + TS) â€” DONE (main)
Paths / URLs:
- API: `http://127.0.0.1:8000`  (/, /public/site, /docs, /redoc)
- Web: `http://127.0.0.1:5173`
- Vite Proxy: `/api/*` ’ `http://127.0.0.1:8000/*`

Gotchas:
- API braucht `LTC_SECRET_KEY` (>=16), sonst RuntimeError.
- In Vite-Terminal keine Shell-Commands (Input wird von Vite genutzt). Für Commands extra Tab.

Start (2 Tabs/Fenster A=API, B=WEB):
- A (API):
  - `cd C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server`
  - `$env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"`
  - `poetry run uvicorn app.main:app --reload`
- B (WEB):
  - `cd C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\packages\web`
  - `npm install` (einmalig)
  - `npm run dev`
  - Browser: `http://127.0.0.1:5173/`

Web Smoke (Build):
- Root:
  - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_web_toolkit.ps1 -Smoke -Clean`

---

## OpenAPI / Router Wiring â€” DONE (main)
Thema:
- FastAPI OpenAPI-Warnungen: **"Duplicate Operation ID ... documents.py"**

Fix (PR #36):
- `server/app/main.py`: Documents-Router **nur 1x** via `include_router(...)`

---

## Public: Blog/News â€” DONE (main)
Public Router:
- `GET /blog` + `GET /blog/` + `GET /blog/{slug}`
- `GET /news` + `GET /news/` + `GET /news/{slug}`

---

## P0: Actor Source of Truth â€” DONE (main)
Regeln:
- Actor wird serverseitig zentral bestimmt.
- Ohne Actor ’ **401**.
- DEV/Test: Header-Override ist **gated** (nicht in Produktion).

---

## P0: Uploads Quarantäne (Documents) â€” DONE (main)
Workflow:
- Upload ’ `approval_status=QUARANTINED`, `scan_status=PENDING`
- Admin setzt `scan_status`: `CLEAN` oder `INFECTED`
- `INFECTED` erzwingt `approval_status=REJECTED`
- Admin `approve` nur wenn `scan_status=CLEAN` (sonst **409**)

Download-Regeln:
- **User/VIP/Dealer**: nur wenn `APPROVED` **und** Scope/Owner passt (object-level)
- **Admin/Superadmin**: darf auch QUARANTINED/PENDING downloaden (Review)

---

## Sale/Transfer Status (ID-Leak Fix) â€” DONE (main)
Endpoint:
- `GET /sale/transfer/status/{transfer_id}`

Regeln:
- Role-Gate: nur `vip|dealer` (alle anderen **403**)
- Zusätzlich object-level: nur **Initiator ODER Redeemer** darf lesen (sonst **403**)

---

## RBAC (SoT)
- Default: **deny-by-default**
- **Actor required**: ohne Actor ’ **401**
- **Moderator**: strikt nur **Blog/News**; sonst überall **403**

Allowlist Moderator (ohne 403):
- `/auth/*`
- `/health`
- `/public/*`
- `/blog/*`
- `/news/*`

---

## Public-QR Trust-Ampel (Pflichttext)
„Die Trust-Ampel bewertet ausschlieÃŸlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## Tests / Lokal ausführen
> Env-Hinweis: Export/Redaction/HMAC benötigt `LTC_SECRET_KEY` (>=16). Für DEV/Tests explizit setzen.

```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"
poetry run pytest -q


- Guard-Test (PR #77): Umbenennung CI-Job pytest → pytest2 ⇒ Required Check pytest wird nicht reported ⇒ Branch Protection blockt Merge (UI).


