# LifeTimeCircle – Service Heft 4.0
## Master Checkpoint (SoT)
Stand: **2026-03-01** (Europe/Berlin)

Dieses Dokument hält nur den aktuellen, relevanten Projektzustand fest.
Historische PR- und Branch-Details bleiben in `git log`, GitHub und den Merge-Commits.

---

## 1) Zweck
- Schnelle Orientierung über den realen Produkt- und Workspace-Stand.
- Einstiegspunkt vor Feature-Arbeit, QA und Reviews.
- Verweis auf die verbindlichen SoT-Dokumente.

Nicht-Ziel:
- Keine fortlaufende PR-Chronik.
- Keine Duplikation kompletter Spezifikationstexte.

---

## 2) Source of Truth
Bei Konflikten gilt diese Reihenfolge:

1. `docs/00_CODEX_CONTEXT.md`
2. `docs/02_PRODUCT_SPEC_UNIFIED.md`
3. `docs/03_RIGHTS_MATRIX.md`
4. `docs/01_DECISIONS.md`
5. `docs/99_MASTER_CHECKPOINT.md`
6. `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md` für Website-/Web-App-Copy

Leitplanken:
- deny-by-default
- RBAC und object-level checks serverseitig
- Moderator strikt nur Blog/News
- keine PII-Leaks in Logs, Exports oder Public-Ansichten
- Uploads standardmäßig Quarantäne
- Public-QR bleibt datenarm und ohne Technikdiagnose

---

## 3) Verifizierter IST-Stand
Verifiziert am **Sonntag, 2026-03-01** im lokalen Workspace:

- Repo: `LifeTimeCircle-ServiceHeft-4.0`
- Aktiver Arbeitsbranch: `wip/add-web-modules-2026-03-01-0900`
- Backend-Stack: FastAPI / Python 3.11
- Frontend-Stack: React / TypeScript / Vite
- Doku-SoT liegt unter `docs/`

Verifikations-Gates:
- `git diff --check`
- `npm run build`
- `npm run e2e`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1`

Der Workspace gilt als belastbar, wenn diese Gates grün sind und der Working Tree clean ist.

---

## 4) Aktueller Produktstand
### Öffentlich
- Start-/Entry-/Kontaktseiten vorhanden.
- Blog und News sind aktiv.
- Public-QR ist angebunden und zeigt nur Ampel + textliche Indikatoren.
- Pflicht-Disclaimer ist im Web-Quellcode verankert.

### Geschützte Kernflows
- Auth- und Consent-Gating vorhanden.
- Vehicles: Liste, Anlage und Detailansicht vorhanden.
- Vehicle Detail: Timeline, Revisionen, Trust-Zusammenfassung und Trust-Folder-Link vorhanden.
- Documents: Upload, Lookup, Download und Admin-Quarantäne-Flow vorhanden.
- Admin: Rollen, Moderator-Akkreditierung, VIP-Businesses und Export-Step-up vorhanden.

### Qualitätsstand Web
- Kernseiten auf Accessibility-Basis gehärtet.
- Fokusführung und feldnahe Validierung auf Auth, Consent, Trust, Admin und Documents sind produktiv abgesichert.
- Mobile-Layouts für 375px abgesichert.
- Desktop-/1920px-Layouts für Core-Workspaces abgesichert.
- Playwright-Mini-E2E deckt die produktiven Kernpfade ab.

### Release-Readiness Kernpfade
- Auth -> Consent -> Vehicles ist technisch verifiziert.
- Vehicle Detail inkl. Revisionen und Trust-Kontext ist technisch verifiziert.
- Documents inkl. Upload, Lookup und Admin-Quarantäne ist technisch verifiziert.
- Trust Folders inkl. Forbidden-/Addon-Gates ist technisch verifiziert.
- Admin inkl. Step-up, VIP-Business und Export-Grant ist technisch verifiziert.

---

## 5) Zuletzt abgeschlossene Arbeitspakete
Stand 2026-03-01:

1. Repo-Gates und Build-/Test-Basis wieder grün gezogen.
2. Content- und Formular-A11y für Kernseiten gehärtet.
3. Mobile-Hardening für `375px` auf Vehicles, Vehicle Detail und Admin umgesetzt.
4. Desktop-/1920px-Finetuning für Vehicles, Vehicle Detail, Admin und Documents umgesetzt.

Diese Punkte sind kein Ersatz für `git log`, sondern nur die aktuelle Lagebeschreibung.

---

## 6) Offene Themen
Die verbleibenden Themen liegen aktuell nicht im Fundament, sondern in Produktreife und Dokumentation:

- Masterplan-Dokumente enthalten teils veraltete Termin- und Planungsannahmen.
- Release-/Deployment-Entscheidungen sind noch nicht als finaler Live-Betrieb dokumentiert.
- Rest-Polish auf Dev-/Referenzflächen und zukünftige Spezialwidgets kann weiter verfeinert werden, blockiert aber den aktuellen Kernstand nicht.

---

## 7) Praktische Einstiegsfragen
Wenn du wissen willst:

- Was fachlich gebaut werden darf: `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Wer was darf: `docs/03_RIGHTS_MATRIX.md`
- Warum Regeln so gesetzt sind: `docs/01_DECISIONS.md`
- Welche Copy für Website/Web-App gelten soll: `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md`
- Ob der Workspace technisch belastbar ist: `tools/test_all.ps1` und `tools/ist_check.ps1`

---

## 8) Pflegehinweis
`99_MASTER_CHECKPOINT.md` bleibt absichtlich kurz.
Sobald PR-/Branch-Listen historisch werden, gehören sie nicht mehr hier hinein, sondern in Git-Historie, Issues oder separate Projektplanung.
