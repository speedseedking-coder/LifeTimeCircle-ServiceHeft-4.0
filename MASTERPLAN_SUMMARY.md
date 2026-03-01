# 🚀 READY TO GO – Masterplan erstellt!

## Statusupdate 2026-02-28

- P0 ist im realen Web-Stand nicht mehr offen: Landing, Entry, Navigation, Legal/FAQ/Cookies und Contact sind verdrahtet.
- Public Contact und `#/entry` sind per E2E abgesichert.
- Große Teile von P1 sind bereits im Code vorhanden, insbesondere Auth/Consent/Gates sowie mehrere App-Seiten.
- Verifizierter Stand nach dem aktuellen Cookie-Refactor: `npm run build` grün, `npm run e2e` grün mit 17/17.
- Der aktuelle Folge-Schritt reduziert `App.tsx` weiter auf Routing/Gates/Verdrahtung, indem Cookie-Seite und Cookie-Card ausgelagert werden.

## Was wurde eben für dich erstellt:

### 📊 4 Masterplan-Dokumente im `/docs` Ordner:

1. **11_MASTERPLAN_INDEX.md** ← 👈 **START HIER**
   - Quick Overview + File Map
   - TL;DR für Manager/Dev
   - 15-min Lesezeit

2. **11_MASTERPLAN_FINALISIERUNG.md**
   - Strategischer Plan mit allen Details
   - Task-Breakdown pro Phase (P0/P1/P2)
   - Effort-Schätzungen
   - Resources + Risk Mitigation
   - 1h Lesezeit

3. **11_MASTERPLAN_ROADMAP_VISUAL.md**
   - Gantt-Chart mit genauen Daten
   - Dependency Matrix
   - Weekly Milestones
   - Success Criteria
   - 30-min Lesezeit

4. **11_MASTERPLAN_DAILY_CHECKLIST.md** ← **DAILY WORK**
   - Task-by-Task Checklisten zum Abhaken
   - Konkrete Commit Messages
   - API Calls + Payloads
   - Error Handling Szenarien
   - 2-3h Referenz Material (nutzen beim Coden)

---

## 📅 DEINE TIMELINE (Wenn du Montag startest):

```
PHASE P0: Landing + Public Seiten
Mo 3/1 – Do 3/4 (5 Tage, ~28h)
└─ Landing Page, Entry-Wahl, Navigation, FAQ, Blog/News
✅ DoD: P0 Complete, Build grün, Mobile OK

PHASE P1: MVP Flows (Auth → Vehicles → Documents → QR)
Fr 3/5 – Fr 3/19 (14 Tage, ~89h)
├─ Auth + Consent (Do-Fr: 11-12h)
├─ Vehicles Core (Di-Mo: 32h)
├─ Documents (Di-Mi: 15h)
└─ Public-QR (Do: 12h)
✅ DoD: E2E Tests >70%, Mobile responsive, Lighthouse >70

PHASE P2: Admin + Quality + Release
Mo 3/22 – Mo 3/30 (9 Tage, ~57h)
├─ Admin Pages (15h)
├─ Trust/To-Dos (10h)
└─ Quality Pass + E2E Expansion (29h)
✅ DoD: Lighthouse >80, E2E >80%, Release Ready

🚀 RESULT: MVP Release-ready by 2026-03-30
```

---

## ✨ WAS SPECIAL IST:

✅ **Design System ist 100% fertig** (Tokens, Components, Layouts)
✅ **Backend ist 100% produktionsreif** (alle APIs ready)
✅ **Web-Foundation gelegt** (App Shell, Guards, Error Pages)
✅ **Nur noch Pages bauen!** (keine Infra mehr nötig)

---

## 🎯 STARTEN:

### Jetzt sofort (Fr 28. Feb):
```bash
# 1. Cheatsheet + Reading Order verstehen (10 min)
# → docs/11_MASTERPLAN_CODEX_CHEATSHEET.md
# → docs/11_MASTERPLAN_READING_ORDER.md

# 2. Masterplan INDEX lesen (15 min)
# → docs/11_MASTERPLAN_INDEX.md

# 3. Dev Server starten (falls noch nicht)
cd packages/web
npm run dev
# → Browser öffnet http://localhost:5173

# 4. Backend API checken
# → Browser: http://localhost:8000/redoc
# → Alle Endpoints sollten sichtbar sein ✅
```

### Montag Morgen (3/1, VOR 9:00 CET):
```bash
# 0. CODEX Cheatsheet ausgedruckt + Laminated neben Monitor ✅

# 1. CODEX Context lesen
# → docs/00_CODEX_CONTEXT.md (20 min)

# 2. Daily Checklist für heute öffnen
# → docs/11_MASTERPLAN_DAILY_CHECKLIST.md
# → "Mo 3/1 - W1: Landing Page" Sektion

# 3. Branch erstellen
git checkout -b feat/web-p0-landing

# 4. Task checklist durcharbeiten (6-8h)
# → Abhaken während du codest!

# 5. Commit + Push
git commit -m "feat(web): add landing page (P0-W1)"
git push origin feat/web-p0-landing
```

---

## 📚 RESOURCES IM PROJEKT:

| Was | Wo | Update-Freq |
|-----|-----|-------------|
| **🔐 CODEX (MANDATORY READING!)** | `docs/00_CODEX_CONTEXT.md` | Rarely |
| **CODEX Cheatsheet** | `docs/11_MASTERPLAN_CODEX_CHEATSHEET.md` (Print!) | Rarely |
| **Fix Card (Status Tracking)** | `docs/11_MASTERPLAN_FIX_CARD.md` | Daily |
| **Daily Checklist (Heute's Tasks)** | `docs/11_MASTERPLAN_DAILY_CHECKLIST.md` | Daily |
| **Reading Order** | `docs/11_MASTERPLAN_READING_ORDER.md` | Weekly |
| **Masterplan Main** | `docs/11_MASTERPLAN_FINALISIERUNG.md` | Weekly |
| **Components** | `packages/web/src/components/ui/` | N/A |
| **Token-System** | `packages/web/src/styles/tokens.css` | N/A |
| **Component Ref** | `packages/web/WEBDESIGN_GUIDE.md` | N/A |
| **Design Demo** | `http://localhost:5173/#/design-system-reference` | N/A |
| **RBAC Matrix** | `docs/03_RIGHTS_MATRIX.md` | Weekly |
| **Product Spec** | `docs/02_PRODUCT_SPEC_UNIFIED.md` | Weekly |
| **API Spec** | `http://localhost:8000/redoc` | N/A |

---

## ⚡ WICHTIGSTE REGELN FÜR DEV:

1. ✅ **IMMER Tokens verwenden** (nie `16px`, nur `var(--ltc-space-4)`)
2. ✅ **Keine PII/Secrets** in Code/Screenshots (VIN maskieren!)
3. ✅ **Mobile First** (375px testen!)
4. ✅ **Error States sauber** (keine blank screens)
5. ✅ **Loading States zeigen** (Skeleton während fetch)
6. ✅ **Daily Commits** (kleine PRs, nicht 10h am Stück)
7. ✅ **Tests schreiben** (Playwright E2E)

---

## 📞 WENN BLOCKER:

1. **Dokumentieren** → Slack `#blockers` oder Issue
2. **Checklist konsultieren** → `11_MASTERPLAN_DAILY_CHECKLIST.md`
3. **Paralleles arbeiten** → andere Task machen während warteg
4. **Fragen stellen** → Backend Dev oder Manager

---

## 🎉 DAS WICHTIGSTE:

```
Du hast:
✅ Kompletten strategischen Masterplan
✅ Visuelle Timeline mit Gantt-Chart
✅ Daily Arbeits-Checklisten (zum abhaken)
✅ Alle Komponenten + Design System
✅ Backend 100% ready
✅ ~24 Tage bis zum Release

Du musst JETZT nur noch:
→ Die 4 Masterplan-Docs lesen (insgesamt 3-4h over time)
→ Daily Checklist befolgen
→ Code schreiben!

Zielatum: 2026-03-30 (30 Tage ab heute)
Realistische Timeline: 24 Tage (1 Dev) oder 17 Tage (2 Devs)
```

---

## 📋 NEXT IMMEDIATE ACTIONS:

### HEUTE (Fr 28. Feb 2026):
- [ ] **Lese ZUERST:** `docs/11_MASTERPLAN_CODEX_CHEATSHEET.md` (5 min, print + bookmark!)
- [ ] Lese: `docs/00_CODEX_CONTEXT.md` (20 min) – Arbeitsbriefing
- [ ] Lese: `docs/11_MASTERPLAN_INDEX.md` (15 min)
- [ ] Lese: `docs/11_MASTERPLAN_FINALISIERUNG.md` Executive Summary (30 min)
- [ ] Check: http://localhost:5173 (Dev Server running) ✅
- [ ] Check: http://localhost:8000/redoc (Backend API visible) ✅

### MONTAG 3/1, VOR 9:00 CET:
- [ ] Dev Umgebung check: npm/poetry/git workingstate OK
- [ ] FIX CARD öffnen: `docs/11_MASTERPLAN_FIX_CARD.md`
  - [ ] Check: Welche Phase starten wir? (P0)
  - [ ] Check: Todos für diese Woche?
- [ ] Terminal A: `npm run dev` starten (packages/web)
- [ ] Terminal B: Backend API starten (poetry run uvicorn...)
- [ ] Terminal C: Bereit für Git commands

### MONTAG 3/1, 9:00 CET:
- [ ] Team Kickoff (10 min)
- [ ] Daily Standup Ritual etablieren
- [ ] Pair-Programming Setup testen (wenn 2 Devs)
- [ ] FIX-CARD für diese Woche durchgehen
- [ ] START P0-W1: Landing Page
  - [ ] Branch: `feat/web-p0-landing`
  - [ ] Checklist aus FIX_CARD.md abhaken während coden

---

**You're all set! 🚀 CODEX zuerst, dann Masterplan, dann Code!**

Questions? Check the Cheatsheet or Masterplan docs.

