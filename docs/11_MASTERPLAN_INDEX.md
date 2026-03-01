# MASTERPLAN INDEX
## LifeTimeCircle – ServiceHeft 4.0 Finalisierung
**Stand: 2026-03-01 | Heute: Sonntag, 2026-03-01 | Plan-Zielkorridor: März 2026**

---

## Überblick

Das Projekt ist nicht mehr im theoretischen Kickoff, sondern in laufender Umsetzung.

Aktuelle Lage:
- Backend ist produktiv nah und testbar.
- Web-Core-Flows sind real angebunden.
- Accessibility- und Responsive-Hardening auf Kernseiten ist umgesetzt.
- Repo-Gates sind lokal grün verifizierbar.
- Offene Arbeit liegt jetzt stärker in Produktreife, Doku-Konsistenz und Rest-Polish als im Fundament.

Verifizierter Orientierungspunkt:
- `docs/99_MASTER_CHECKPOINT.md`

---

## Lesereihenfolge

Für aktive Arbeit im Repo:

1. `docs/00_CODEX_CONTEXT.md`
2. `docs/03_RIGHTS_MATRIX.md`
3. `docs/02_PRODUCT_SPEC_UNIFIED.md`
4. `docs/99_MASTER_CHECKPOINT.md`
5. `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md`
6. `docs/11_MASTERPLAN_DAILY_CHECKLIST.md`

Wenn du nur schnell einsteigen willst:

1. `docs/11_MASTERPLAN_CODEX_CHEATSHEET.md`
2. `docs/99_MASTER_CHECKPOINT.md`
3. diese Datei

---

## Masterplan-Dokumente

### `00_CODEX_CONTEXT.md`
- Arbeitsbriefing für Devs/Agenten
- Harte Invarianten, RBAC, Source-of-Truth-Hierarchie
- Vor jeder produktiven Änderung relevant

### `11_MASTERPLAN_DAILY_CHECKLIST.md`
- Tägliche Arbeitscheckliste
- sinnvoll als operative Erinnerung, nicht als alleinige Statusquelle

### `11_MASTERPLAN_FINALISIERUNG.md`
- Strategischer Langplan
- nützlich für Milestones, aber auf aktuelle Realität gegen `99_MASTER_CHECKPOINT.md` prüfen

### `11_MASTERPLAN_ROADMAP_VISUAL.md`
- Visualisierung von Phasen und Abhängigkeiten
- ebenfalls als Planungsartefakt lesen, nicht als verifizierten Ist-Zustand

### `11_MASTERPLAN_FIX_CARD.md`
- Task-/Fix-Tracking
- gut für operative Bündelung, aber mit Git- und Teststand abgleichen

### `07_WEBSITE_COPY_MASTER_CONTEXT.md`
- zentrale Copy-Quelle für Website und Web-App
- bei Rollen-/Security-Konflikten technisch nachgeordnet

---

## Aktuelle Prioritäten

Stand Sonntag, 2026-03-01:

1. Workspace stabil und grün halten.
2. Produktische Kernflows weiter härten statt neue Seitenspuren aufmachen.
3. Masterplan-Dokumente an den realen Zustand angleichen.
4. Danach verbleibende Produktpakete mit verifizierten Gates abarbeiten.

---

## Technischer Schnellstart

```bash
# Repo prüfen
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1

# Web lokal
cd packages/web
npm run dev

# Backend lokal
cd server
poetry run uvicorn app.main:app --reload
```

Wichtige lokale URLs:
- Web: `http://localhost:5173`
- Backend OpenAPI: `http://localhost:8000/redoc`

---

## Verifizierte Kernbereiche

### Öffentlich
- Landing / Entry / Kontakt
- Blog / News
- Public-QR Mini-Check mit Pflicht-Disclaimer

### Geschützt
- Auth / Consent
- Vehicles / Vehicle Detail
- Documents / Nachweise
- Admin / Governance

### Qualität
- Build grün
- Backend-Tests grün
- Playwright-Mini-E2E grün
- Mobile 375px abgesichert
- Desktop 1920px für Core-Workspaces abgesichert

---

## Praktische Fragen

Wenn du wissen willst:

- Was ist erlaubt? → `docs/03_RIGHTS_MATRIX.md`
- Was ist fachlich bindend? → `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Was ist der aktuelle Ist-Stand? → `docs/99_MASTER_CHECKPOINT.md`
- Welche Copy gilt? → `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md`
- Welche harten Regeln gelten immer? → `docs/00_CODEX_CONTEXT.md`

---

## Hinweise zur Interpretation

- Alte Sprint-/Kickoff-Texte in anderen Masterplan-Dateien können historisch sein.
- Bei Konflikten zwischen Plan und realem Workspace gilt immer der verifizierte Ist-Zustand.
- Git-Historie, Tests und lokale Gates sind belastbarer als alte Milestone-Notizen.

---

## Kurzfazit

Der Masterplan ist weiterhin nützlich, aber nur dann, wenn Planung und verifizierter Ist-Zustand getrennt gelesen werden.

Für operative Arbeit heute gilt:
- SoT zuerst
- Checkpoint vor Plan
- grüner Workspace vor neuen Features
