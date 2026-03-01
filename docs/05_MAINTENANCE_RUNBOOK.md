# LifeTimeCircle - ServiceHeft 4.0

**Maintenance / Runbook (SoT)**

Stand: **2026-03-01** (Europe/Berlin)

Ziel: Den aktuellen Workspace reproduzierbar starten, prüfen und vor Push/Review sauber verifizieren.

---

## 1) Source of Truth

Immer zuerst:

- `docs/99_MASTER_CHECKPOINT.md`
- `docs/02_PRODUCT_SPEC_UNIFIED.md`
- `docs/03_RIGHTS_MATRIX.md`
- `docs/01_DECISIONS.md`
- `docs/06_WORK_RULES.md`

Für den laufenden Web-Stand zusätzlich:

- `ACCESSIBILITY_PLAN.md`
- `docs/98_WEB_E2E_SMOKE.md`

---

## 2) Voraussetzungen lokal

- PowerShell 7.x (`pwsh`)
- Python 3.11
- Poetry
- Node.js 20.x + npm
- Git

Optional, aber sinnvoll:

- GitHub CLI (`gh`)
- Playwright Browser binaries via `npx playwright install`

---

## 3) Repo-Start

```powershell
cd C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0
git status -sb
```

Wenn du auf den Arbeitsbranch wechseln willst:

```powershell
git switch wip/add-web-modules-2026-03-01-0900
git pull --ff-only origin wip/add-web-modules-2026-03-01-0900
git status -sb
```

---

## 4) Lokale Dev-Starts

Backend:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\server_start.ps1
```

Frontend:

```powershell
cd .\packages\web
npm install
npm run dev
```

Alternativ für den kombinierten lokalen Start:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\start_dev.ps1
```

Stoppen:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\stop_dev.ps1
```

---

## 5) Schnelle Verifikation

Kleine Repo-Prüfung:

```powershell
git diff --check
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1
```

Vollprüfung:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1
```

Was `test_all.ps1` derzeit abdeckt:

- BOM-Gate
- PowerShell-Param-Gate
- Mojibake-Scan
- Backend-Tests (`poetry run pytest -q`)
- OpenAPI-Duplikat-Audit
- RBAC-Route-Audit
- Web-Build
- Playwright Mini-E2E

---

## 6) Web-only Verifikation

```powershell
cd .\packages\web
npm run build
npm run e2e
```

Die Mini-E2E decken aktuell unter anderem ab:

- App-Gates (`/auth/me`, `/consent/status`)
- Auth- und Consent-Flow
- Vehicles, Vehicle Detail, Documents
- Trust Folders
- Admin
- Blog/News
- Responsive Layouts bei `375px` und `1920px`

---

## 7) Backend-only Verifikation

```powershell
cd .\server
poetry run pytest -q
poetry run python .\scripts\check_openapi_duplicates.py
poetry run python .\scripts\rbac_route_audit.py
```

Wenn lokal kein starker Secret-Key gesetzt ist, verwenden die Repo-Skripte einen sicheren Dev-Key. Für manuelle Serverstarts trotzdem sinnvoll:

```powershell
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"
```

---

## 8) Häufige Fehlerbilder

`ist_check.ps1` rot:

- Prüfen, ob der Working Tree absichtlich dirty ist.
- Prüfen, ob `server\scripts\ltc_verify_ist_zustand.ps1` an einem Folgegate scheitert.

`npm run e2e` mit Proxy-Fehlern gegen `127.0.0.1:8000`:

- Einzelne Vite-Proxy-Logs können Test-Harness-Rauschen sein.
- Relevant ist der Exitcode. Nur bei Testfehlschlag handeln.

`403 consent_required`:

- Erwartetes Gate-Verhalten.
- Flow über `#/consent?next=...` prüfen, nicht gegen die Route "anpatchen".

`403 admin_step_up_required`:

- Erwartetes Verhalten für sensitive Admin-Aktionen.
- Tests und UI müssen erst einen Step-up-Grant anfordern.

---

## 9) Vor Commit / Vor Push

Minimal:

```powershell
git diff --check
cd .\packages\web
npm run build
```

Für produktive Arbeitspakete:

```powershell
cd C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1
git status -sb
```

---

## 10) Push / Review

```powershell
git add <dateien>
git commit -m "<type>(<scope>): <summary>"
git push origin wip/add-web-modules-2026-03-01-0900
```

Wenn Review oder Übergabe ansteht, zusätzlich dokumentieren:

- betroffene Flows
- ausgeführte Verifikation
- bekannte Restpunkte

