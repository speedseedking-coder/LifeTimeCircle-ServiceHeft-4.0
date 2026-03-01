# Release Candidate - 2026-03-01

Stand: **Sonntag, 2026-03-01** (Europe/Berlin)
Repo: `C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0`
Branch: `wip/add-web-modules-2026-03-01-0900`

## 1) Zweck
Dieses Dokument markiert den aktuell übergabefähigen Release-Candidate im lokalen Workspace.
Es ersetzt keine Spezifikation und keine Git-Historie, sondern bündelt den belastbaren Freigabestand.

## 2) Referenzen
Bei fachlichen oder technischen Konflikten gilt weiterhin:

1. `docs/00_CODEX_CONTEXT.md`
2. `docs/02_PRODUCT_SPEC_UNIFIED.md`
3. `docs/03_RIGHTS_MATRIX.md`
4. `docs/01_DECISIONS.md`
5. `docs/99_MASTER_CHECKPOINT.md`
6. `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md`

Für Betrieb und Prüfungen zusätzlich:

- `docs/05_MAINTENANCE_RUNBOOK.md`
- `docs/98_WEB_E2E_SMOKE.md`

## 3) Verifizierte Gates
Der Release-Candidate gilt als belastbar, wenn diese Gates grün sind:

- `git diff --check`
- `npm run build`
- `npm run e2e`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1`

## 4) Verifizierte Kernpfade
Technisch verifiziert und im Workspace belastbar:

- Öffentliche Routen: Start, Entry, FAQ, Jobs, Kontakt, Datenschutz, Blog, News, Public-QR
- Auth -> Consent -> Vehicles
- Vehicle Detail inkl. Revisionen und Trust-Kontext
- Documents inkl. Upload, Lookup, Statusanzeigen und Admin-Quarantäne
- Trust Folders inkl. Forbidden- und Addon-Gates
- Admin inkl. Rollenwechsel, Step-up, VIP-Business und Export-Grant
- Responsive Web-Layouts bei `375px` und `1920px`

## 5) Inhaltliche Leitplanken dieses RC
- Public-QR bleibt datenarm und ohne technische Diagnose.
- Öffentliche Flächen folgen der Copy-SoT aus `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md`.
- Moderator bleibt strikt auf Blog und News begrenzt.
- Uploads bleiben Quarantäne-by-default.
- Exporte bleiben standardmäßig redacted; sensitive Pfade erfordern Step-up oder Export-Grant.

## 6) Bekannte Nicht-Blocker
Diese Punkte verhindern den aktuellen Release-Candidate nicht, sind aber vor echtem Live-Betrieb separat zu entscheiden:

- Produktive Deployment-, Domain-, Monitoring- und Incident-Routinen
- Organisatorische und rechtliche Freigaben für öffentlichen Rollout
- Nachgelagerte Scope-Themen wie spätere VIP-/Dealer-Verkaufs- und Übergabeflüsse

## 7) Übergabehinweis
Für technische Übergaben oder Reviews immer zusammen heranziehen:

1. `docs/99_MASTER_CHECKPOINT.md`
2. `docs/12_RELEASE_CANDIDATE_2026-03-01.md`
3. `docs/05_MAINTENANCE_RUNBOOK.md`
4. `docs/98_WEB_E2E_SMOKE.md`
