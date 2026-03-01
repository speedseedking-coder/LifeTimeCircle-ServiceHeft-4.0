# Start Here - LifeTimeCircle Service Heft 4.0
**Single Entry Point (SoT)**

Stand: **2026-03-01** (Europe/Berlin)

## 1) Erste Referenzen
- Aktueller Master-Status: `docs/99_MASTER_CHECKPOINT.md`
- Release-Candidate / Übergabe: `docs/12_RELEASE_CANDIDATE_2026-03-01.md`
- Produktlogik (bindend): `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Rollen/Rechte (bindend): `docs/03_RIGHTS_MATRIX.md`
- Entscheidungen (bindend): `docs/01_DECISIONS.md`
- Copy-SoT für Website/Web-App: `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md`
- Wartung, Start, Smoke: `docs/05_MAINTENANCE_RUNBOOK.md`
- Codex-Kontext: `docs/00_CODEX_CONTEXT.md`

## 2) 5-Minuten Start
Vollständig und aktuell: `docs/05_MAINTENANCE_RUNBOOK.md`

Kurzfassung für Windows:

Backend:
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\server_start.ps1`

Frontend:
- `cd .\packages\web`
- `npm install`
- `npm run dev`

Alternativ kombiniert:
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\start_dev.ps1`

## 3) IST-Zustandsprüfung
Bei jedem Kontextwechsel im Repo-Root:

- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1`

Der verifizierte Übergabestand liegt in `docs/12_RELEASE_CANDIDATE_2026-03-01.md`.

## 4) Definition of Done
- `deny-by-default` bleibt eingehalten.
- Moderator bleibt außerhalb von `/auth/*`, `/blog/*`, `/news/*` gesperrt.
- Object-level checks bleiben auf Vehicle-, Document- und Trust-Ressourcen serverseitig.
- Keine PII oder Secrets in Logs, Responses oder Exports.
- Public-QR Pflichttext bleibt exakt und unverändert.

## 5) Wenn du nur drei Dinge lesen willst
1. `docs/99_MASTER_CHECKPOINT.md`
2. `docs/12_RELEASE_CANDIDATE_2026-03-01.md`
3. `docs/05_MAINTENANCE_RUNBOOK.md`
