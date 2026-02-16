# Start Here – LifeTimeCircle Service Heft 4.0
**Single Entry Point (SoT)**

## 1) Was ist die Wahrheit?
- Master-Status: docs/99_MASTER_CHECKPOINT.md
- Produktlogik (bindend): docs/02_PRODUCT_SPEC_UNIFIED.md
- Rollen/Rechte (bindend): docs/03_RIGHTS_MATRIX.md
- Entscheidungen (bindend): docs/01_DECISIONS.md
- Arbeitsregeln: docs/06_WORK_RULES.md
- Repo-Struktur: docs/04_REPO_STRUCTURE.md
- Wartung/Start/Smoke: docs/05_MAINTENANCE_RUNBOOK.md
- Codex-Kontext: docs/00_CODEX_CONTEXT.md

## 2) 5-Minuten Start (Frontend + API)
Vollständig & aktuell: docs/05_MAINTENANCE_RUNBOOK.md

Kurzfassung (Windows, 2 Tabs):

### TAB A (API)
Repo-Root:
- cd (git rev-parse --show-toplevel)
- cd .\server
- $env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"
- poetry run uvicorn app.main:app --reload

### TAB B (WEB)
Repo-Root:
- cd (git rev-parse --show-toplevel)
- cd .\packages\web
- 
pm install (einmalig)
- 
pm run dev

URLs:
- API: http://127.0.0.1:8000
- Web: http://127.0.0.1:5173

## 3) IST-Zustandsprüfung (bei jedem Kontextwechsel)
Wenn vorhanden: 	ools/ist_check.ps1
- pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1

## 4) Quality Gate (immer vor PR)
Repo-Root:
- pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1

Optional Web Build Smoke (Repo-Root):
- pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_web_toolkit.ps1 -Smoke -Clean

## 5) „Definition of Done“ (Security)
- deny-by-default eingehalten
- Moderator überall 403 außer Blog/News/Public
- object-level checks auf allen Vehicle/Dokument/Trust Ressourcen
- keine PII/Secrets in Logs/Responses/Exports
- Public-QR Pflichttext exakt und unverändert
