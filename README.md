# LifeTimeCircle – ServiceHeft 4.0

<!-- LTC_START_HERE_LINKS -->
- **Start Here**: docs/07_START_HERE.md
- **Maintenance/Runbook**: docs/05_MAINTENANCE_RUNBOOK.md
<!-- /LTC_START_HERE_LINKS -->


## Source of Truth (verbindlich)
Bei fachlichen Konflikten gilt ausschließlich diese Reihenfolge:

1. `docs/99_MASTER_CHECKPOINT.md`
2. `docs/02_PRODUCT_SPEC_UNIFIED.md`
3. `docs/03_RIGHTS_MATRIX.md`
4. `docs/01_DECISIONS.md`

## Security-Grundsätze
- Security by default: deny-by-default + least privilege.
- RBAC wird serverseitig enforced, inklusive object-level checks.
- Moderatoren dürfen ausschließlich Blog/News; alle anderen geschützten Bereiche liefern `403`.
- Keine PII, Secrets oder Tokens in Logs, Responses oder Exports.

## Public-QR Pflichttext (unverändert)
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität.
Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## Setup (PowerShell 5.1 kompatibel)
Voraussetzungen:
- Python 3.11
- Poetry
- Node.js >= 20.19
- npm

### Backend starten
```powershell
cd .\server
$env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"
poetry install
poetry run uvicorn app.main:app --reload
```

### Backend-Tests
```powershell
cd .\server
$env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"
poetry run pytest -q
```

### Web starten
```powershell
cd .\packages\web
npm ci
npm run dev
```

Hinweis: Wenn `npm ci` lokal wegen Lockfile-Drift fehlschlägt, nutze `npm install`.

### Web-Build
```powershell
cd .\packages\web
npm run build
```
