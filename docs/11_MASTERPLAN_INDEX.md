<<<<<<< HEAD
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
=======
# 📊 MASTERPLAN INDEX
## LifeTimeCircle – ServiceHeft 4.0 Finalisierung
**Stand: 2026-02-28 | Projektstart: 2026-03-01 | Zielatum: 2026-03-30**

---

## 🎯 ÜBERBLICK

Das Projekt ist auf der **Endgeraden**:
- ✅ Backend 100% produktionsreif
- ✅ Design System komplett
- ✅ Webfundament gelegt
- 🔄 Web-Frontend: 4 Wochen bis MVP Release

---

## 📚 MASTERPLAN-DOKUMENTE

### ⚠️ **00_CODEX_CONTEXT.md** ← MANDATORY READING!
   - **Was:** Arbeitsbriefing für Devs/Agenten – Source of Truth, Harte Invarianten, RBAC, Engineering-Guide
   - **Für wen:** ALLE Developer + Agenten
   - **Lesezeit:** 20-30 min (einmalig)
   - **Wichtigste Punkte:**
     - Harte Invarianten: deny-by-default, Moderator Allowlist, no PII, Uploads Quarantäne, Exports redacted
     - RBAC-Routing (wer darf was)
     - Source of Truth Hierarchie (Order bei Konflikten)
     - Was schon DONE ist (vorfab nutzen!)
     - Checkliste vor jeder Änderung
   - **→ Ausführliches Kopieren in 11_MASTERPLAN_DAILY_CHECKLIST.md oben!**

### 1️⃣ **11_MASTERPLAN_FINALISIERUNG.md** ← START HIER
   - **Was:** Strategischer Überblick, Executive Summary, detaillierte Task-Breakdowns
   - **Für wen:** Projektmanager, Teamleiter, Überblicks-Orientation
   - **Wichtigste Infos:**
     - Timeline: ~24 Tage (1 Dev) oder ~17 Tage (2 Devs)
     - Effort: ~174 Stunden total (P0: 28h + P1: 89h + P2: 57h)
     - 3 Phasen: P0 (Webseite), P1 (MVP), P2 (Admin+Polish)
     - Sprint Planning für 5 Wochen
     - Release Readiness Checklist

### 2️⃣ **11_MASTERPLAN_ROADMAP_VISUAL.md** ← FOR VISUALIZATION
   - **Was:** Gantt-Chart, Dependency Matrix, Weekly Milestones, Visual Timeline
   - **Für wen:** Developer, Product Owner, Team für große Übersicht
   - **Wichtigste Infos:**
     - ASCII Gantt mit exakten Daten (Mo 3/1 – Mo 3/30)
     - Hängen-bleibende Dependencies (kritische Pfade)
     - Weekly Checkpoints
     - Risk Matrix + Mitigation
     - Success Criteria

### 3️⃣ **11_MASTERPLAN_DAILY_CHECKLIST.md** ← FOR DAILY WORK
   - **Was:** Task-by-Task Checklisten, konkrete Commits, API-Calls, DoD
   - **Für wen:** Developer (täglich nutzbar)
   - **Wichtigste Infos:**
     - PRE-START Checklist
     - Jeder Task mit Checkboxen breakdowned
     - Konkrete Commit Messages
     - API Calls + Payloads
     - Error Handling Szenarien
     - Test-Szenarien für jede Phase

### 4️⃣ **11_MASTERPLAN_FIX_CARD.md** ← FOR STATUS TRACKING
   - **Was:** Fix-Tracking mit Status, Priorisierung (P0/P1/P2), tägliche Rituale
   - **Für wen:** Developer + PM (tägliche Nutzung)
   - **Wichtigste Infos:**
     - Fix-Status Überblick (visuelle Grafik)
     - Alle 25 Tasks mit Checklisten (P0/P1/P2)
     - Release Readiness Checklist
     - Momentum-Tracking
     - Tägliche Rituale + Blocker-Protokoll

---

## 🚀 SCHNELLER START (TL;DR)

### Für den Dev (Du) – MONTAG FRÜH:
```bash
# 0. (ZUERST!) CODEX Cheatsheet öffnen + Bookmark
#    → docs/11_MASTERPLAN_CODEX_CHEATSHEET.md
#    → Print + Desk neben Monitor!

# 1. CODEX lesen (20 min)
#    → docs/00_CODEX_CONTEXT.md
#    → Verstehe: Harte Invarianten, RBAC, Source of Truth

# 2. Daily Checklist öffnen
#    → docs/11_MASTERPLAN_DAILY_CHECKLIST.md
#    → Bookmark für tägliche Nutzung

# 3. Dev-Umgebung starten
cd packages/web && npm run dev
# → Browser öffnet http://localhost:5173

# 4. Backend API testen
#    → http://localhost:8000/redoc
#    → Alle Endpoints visible?

# 5. Montag 9:00 CET: Standup + P0-W1 Kickoff
```

### Für Projektmanager:
```
CODEX verstehen: docs/00_CODEX_CONTEXT.md (Section 1-3, 15 min)
├─ Harte Invarianten
├─ RBAC/Routing
└─ Status quad

Kickoff: 2026-03-01, 9:00 CET
├─ Team: 1-2 Devs
├─ Lese Masterplan INDEX + FINALISIERUNG zusammen
└─ Checke: Backend API ready, Web Dev-Environment ready

Milestones:
├─ Do 3/4 afternoon: P0 COMPLETE ✅
├─ Fr 3/19 afternoon: P1 COMPLETE ✅
└─ Mo 3/30 afternoon: P2 COMPLETE + Release Ready! 🚀
```

---

## 📋 PHASEN ÜBERBLICK

| Phase | Dauer | Start | End | Effort | Owner | Status |
|-------|-------|-------|-----|--------|-------|--------|
| **P0: Webseite** | 5-7d | Mo 3/1 | Do 3/4 | 28h | Dev1 | 🟡 Ready |
| **P1: MVP Flows** | 7-10d | Fr 3/5 | Fr 3/19 | 89h | Dev1 + Dev2* | 🟡 Ready |
| **P2: Admin+QA** | 5-7d | Mo 3/22 | Mo 3/30 | 57h | Dev1 + Dev2 | 🟡 Ready |
| **Total** | **~24d** | **3/1** | **3/30** | **174h** | **1-2** | 🟢 **GoLive** |

*Dev2 optional, hilft bei P1 parallelisierung

---

## 🎯 KONKRETE NÄCHSTE SCHRITTE

### ✅ HEUTE (Fr 28. Feb 2026):
- [ ] Diesen Masterplan vollständig lesen (~1h)
- [ ] Dev Server testen: `npm run dev` → läuft auf :5173 ✅
- [ ] Backend API checken: `http://localhost:8000/redoc` ✅
- [ ] Deploy setup planung (wo gehen wir live? AWS/Vercel/etc?)

### ✅ MONTAG (Mo 1. März 2026):
- [ ] 9:00 CET: Team Kickoff + Masterplan Review (30 min)
- [ ] Branch erstellen: `feat/web-p0-landing` (5 min)
- [ ] Landing Page entwickeln (6-8h)
- [ ] Commit + Push bis 17:00 CET für Code Review

### ✅ DIENSTAG (Di 2. März 2026):
- [ ] Code Review + Merge feat/web-p0-landing
- [ ] Branch: `feat/web-p0-entry-etc` (W2-W5)
- [ ] Entry-Wahl + Public Nav + Blog (4-6h)
- [ ] Ready für Wednesday Abend

### Usw. → siehe Daily Checklist!

---

## ✨ WAS DU BRAUCHST

### Tools/Setup:
- ✅ Node.js + npm (installed)
- ✅ VS Code + Extensions (EditorConfig, Prettier, TypeScript)
- ✅ Git + GitHub access
- ✅ Docker (optional für lokales Backend)
- ✅ Figma (optional für Design Review)

### Lokal laufen müssen:
- ✅ Backend: `uvicorn app.main:app --reload` (http://localhost:8000)
- ✅ Web: `npm run dev` (http://localhost:5173)
- ✅ Playwright E2E: `npm run e2e` (lokal testing)

### Knowledge erforderlich:
- ✅ React + TypeScript (du machst das wahrscheinlich)
- ✅ CSS Custom Properties (Tokens, no Tailwind!)
- ✅ REST API Integration
- ✅ Git Branching + PRs
- ✅ Design System Pattern

---

## 📊 EFFORT-BUDGETS (für Time-Tracking)

Wenn du täglich trackst:

```
PHASE P0 (Mo-Do, ~6 Tage):
└─ 28h total
   ├─ Mo: 10h (Landing + Entry)
   ├─ Di: 8h (Nav, FAQ)
   ├─ Mi: 6h (Blog, Polish)
   ├─ Do: 4h (QA, Commit)

PHASE P1 (Fr, Mo-Fr, ~14 Tage):
└─ 89h total
   ├─ Wk1-Fr: 14h (Auth/Consent)
   ├─ Wk2: 32h (Vehicles + Entries)
   ├─ Wk3-Mo-Tu: 24h (Documents)
   ├─ Wk3-We: 12h (Public-QR)
   ├─ Wk3-Th+Fr: 7h (E2E, QA)

PHASE P2 (Mo-Mo, ~9 Tage):
└─ 57h total
   ├─ Wk4-Mo-Tu: 18h (Admin Pages)
   ├─ Wk4-We: 10h (Trust/To-Dos)
   ├─ Wk5-Th-Mo: 29h (Quality, E2E, Polish)
```

---

## ⚡ IF THINGS GET TRICKY

### Blocker-Protokoll:
1. **Document it** → in `#blockers` Slack channel
2. **Find workaround** → Check MASTERPLAN mitigation section
3. **Escalate** → Product Manager / Backend Dev
4. **Move on** → Don't get stuck, do parallel work

### Typical Blockers & Solutions:
| Blocker | Solution |
|---------|----------|
| API Endpoint missing | Use mock/stub data + checkbox for "real API incoming" |
| Design Question unclear | Use existing `DesignSystemReference.tsx` as fallback |
| Performance issue | Add lazy-load, defer non-critical, report for P2 phase |
| TypeScript error | Check `WEBDESIGN_GUIDE.md` patterns or ask Backend Dev |
| Security/RBAC unclear | **→ Check CODEX Section 3 (RBAC) + Rights-Matrix** |

---

## 🔐 CODEX RESSOURCEN (Source of Truth)

### Critical Files to Know:

| Datei | Zweck | Wann checken |
|-------|-------|-------------|
| **00_CODEX_CONTEXT.md** | Arbeitsbriefing – Harte Invarianten, RBAC, Engineering-Guide | Montag VOR Arbeitsbeginn lesen (20 min) |
| **03_RIGHTS_MATRIX.md** | RBAC Matrix – explizite Allowlists, 403/401 Rules | Bei Route-Implementierung |
| **99_MASTER_CHECKPOINT.md** | Status quo – Was done, PRs, Scripts | Vor jeder Feature (2 min check) |
| **02_PRODUCT_SPEC_UNIFIED.md** | Bindende Produktlogik – E2E Flows | Wenn unsicher über Requirement |
| **01_DECISIONS.md** | Warum-Entscheidungen – Konsequenzen verstehen | Bei Design-Questions |

### Harte Invarianten (DIESE BRECHEN NIE!):

✅ **deny-by-default** – jede Route gated, Moderator 403 außer Allowlist
✅ **RBAC serverseitig enforced** – object-level checks
✅ **Actor missing → 401**, nicht 403
✅ **Keine PII** in Code/Logs/Exports
✅ **Uploads Quarantäne** – Approve erst nach Scan
✅ **Public QR Disclaimer EXAKT** (siehe oben in CODEX-Sektion)

---

## 🎉 SUCCESS = RELEASE

**Finale Release Readiness (Mo 30. März):**

✅ **Frontend (Web):**
- [ ] All P1 flows working end-to-end
- [ ] Mobile responsive (375px+)
- [ ] Lighthouse >80
- [ ] E2E tests >80% coverage
- [ ] Zero console errors

✅ **Backend:**
- [ ] Tests grün
- [ ] API documented (OpenAPI/Redoc)
- [ ] Monitoring active
- [ ] Logging clean (no PII)

✅ **DevOps:**
- [ ] Staging env ready
- [ ] CI/CD pipeline running
- [ ] Rollback plan documented

✅ **Legal/Compliance:**
- [ ] Disclaimer exakt + unmodifizierbar
- [ ] AGB/Datenschutz reviewed
- [ ] Team trained on Trust-Ampel liability

**→ Then: 🚀 DEPLOY!**

---

## 📞 SUPPORT & CONTACT

- **Your Manager:** (schedule weekly check-ins)
- **Backend Dev:** (for API questions)
- **QA Lead:** (for E2E automation)
- **Team Slack:** `#ltc-serviceheft` or similar
- **Emergency:** lifetimecircle@online.de

---

## 🗺️ FILE MAP

```
docs/
├── 11_MASTERPLAN_FINALISIERUNG.md         ← Strategic Overview
├── 11_MASTERPLAN_ROADMAP_VISUAL.md        ← Timeline + Dependencies
├── 11_MASTERPLAN_DAILY_CHECKLIST.md       ← Task Breakdown (USE THIS!)
└── 11_MASTERPLAN_INDEX.md                 ← You are here!

packages/web/
├── WEBDESIGN_GUIDE.md                     ← Component Reference
├── src/
│   ├── pages/                             ← Build these!
│   ├── components/
│   │   ├── ui/                            ← Use these (50+ components)
│   │   └── layout/                        ← PublicLayout / AppLayout
│   ├── styles/
│   │   ├── tokens.css                     ← USE THESE (no hardcoding!)
│   │   ├── components.css
│   │   └── layout.css
│   └── (existing) App.tsx, pages/*.tsx

server/
├── app/
│   ├── main.py                            ← FastAPI app
│   └── routes/                            ← API endpoints
└── tests/
    └── test_*.py                          ← API tests (run them!)
```

---

## 📝 VERSION HISTORY

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-28 | 1.0 | Initial Masterplan Created |
| TBD | 1.1 | Weekly Updates (Starting 3/6) |

---

## 🎓 QUICK LEARNING PATH

If you're new to the project:

1. **Read in order (3-4h total):**
   - `11_MASTERPLAN_CODEX_CHEATSHEET.md` → 5 min quick reference
   - `00_CODEX_CONTEXT.md` → 20 min working brief (MANDATORY!)
   - This file (INDEX) → 15 min overview
   - `00_PROJECT_BRIEF.md` → 10 min context
   - `02_PRODUCT_SPEC_UNIFIED.md` → 30 min specs
   - `03_RIGHTS_MATRIX.md` → 15 min RBAC understanding
   - `11_MASTERPLAN_FINALISIERUNG.md` → 1h strategic plan

2. **Setup locally (1h):**
   - Clone repo, `npm ci`, `npm run build` 
   - Start dev servers (backend + web)
   - Check `packages/web/WEBDESIGN_GUIDE.md`
   - **Important:** Set `LTC_SECRET_KEY` env var for backend tests

3. **Understand CODEX (30 min):**
   - Harte Invarianten (8 rules, see Cheatsheet)
   - RBAC/Routing Matrix
   - Source of Truth Hierarchy
   - Moderator Allowlist Hard-Block

4. **Look at code (1-2h):**
   - Explore `src/pages/` (existing pages)
   - Check `server/app/auth/actor.py` (Auth source of truth)
   - Check `src/styles/tokens.css` (design system)
   - Review `src/components/ui/` (component library)
   - Notice: ALL spacing/colors use tokens, NO hardcoding

4. **Start first task (from Daily Checklist):**
   - Pick P0-W1 (Landing Page)
   - Follow checklist step-by-step
   - Reference `DesignSystemReference.tsx` for patterns
   - Commit + PR daily

---

## 🏁 FINISH LINE

**Target: Go-Live 2026-03-30**

The MVP is 80% designed, 60% architected, 20% coded.

**Your job:** Code the remaining 80% with quality + speed.

**Timeline:** ~24 days (realistically 3-4 weeks with normal pace).

**Quality:** Lighthouse >80, E2E >80%, Mobile ✅, Zero console errors.

**Then:** User feedback, hotfixes, scale.

---

**Let's build this! 🚀**  
Questions? Check the detailed MASTERPLAN or ask on Slack/Email.

Start: **Monday, March 1, 2026, 9:00 CET**
>>>>>>> origin/main
