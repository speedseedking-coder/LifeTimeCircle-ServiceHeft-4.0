# 📚 READING ORDER & DOCUMENT MAP

**Start Here!** Diese Datei erklärt, in welcher Reihenfolge Manager/Devs die Dokumentation lesen sollten.

---

## 🚀 EMPFOHLENE READING ORDER

### Szenario 1: Developer (du bist es wahrscheinlich)

```
Sonntag, 2026-03-01, vor 09:00 CET:

1. 📋 11_MASTERPLAN_CODEX_CHEATSHEET.md         (5 min)
   └─ Print + Laminate, auf Desk legen!
   
2. 🔐 00_CODEX_CONTEXT.md                       (20 min)
   └─ Harte Invarianten + RBAC verstehen
   
3. 📊 11_MASTERPLAN_INDEX.md                    (15 min)
   └─ Überblick + QuickStart
   
4. 🛠 11_MASTERPLAN_FIX_CARD.md                (10 min)
   └─ Alle Fixes + Tasks tracken
   
5. 📝 11_MASTERPLAN_DAILY_CHECKLIST.md          (10 min)
   └─ Heute's Tasks durchlesen
   
6. 🎯 11_MASTERPLAN_FINALISIERUNG.md (optional) (30 min)
   └─ Falls mehr Kontext nötig

TOTAL: ~60 min, dann START P0-W1!
```

### Szenario 2: Project Manager / Tech Lead

```
Samstag, 2026-02-28, oder Sonntag, 2026-03-01, früh:

1. 📊 11_MASTERPLAN_INDEX.md                    (15 min)
   └─ Überblick
   
2. 📋 MASTERPLAN_SUMMARY.md                     (5 min)
   └─ Quick TL;DR
   
3. 🎯 11_MASTERPLAN_FINALISIERUNG.md            (45 min - 1h)
   └─ Strategie, Milestones, Ressourcen
   
4. 🔐 00_CODEX_CONTEXT.md (Section 1-3 only)    (15 min)
   └─ Verstehe Invarianten + RBAC (für Mandate)
   
5. 📈 11_MASTERPLAN_ROADMAP_VISUAL.md           (20 min)
   └─ Gantt + Dependencies
   
TOTAL: ~1,5-2h, ready für Kickoff!
```

### Szenario 3: Code Review / QA

```
Vor Review-Session:

1. 📋 11_MASTERPLAN_CODEX_CHEATSHEET.md         (5 min)
   └─ Harte Invarianten im Kopf haben
   
2. 🔐 00_CODEX_CONTEXT.md (Section 9 only)      (5 min)
   └─ Checkliste vor jeder Änderung
   
3. 📊 03_RIGHTS_MATRIX.md                       (15 min)
   └─ Welche Routes in diesem PR?
   
4. 📝 PR self-review checklist:
   └─ Moderator 403? Actor checks? Object-level? No PII?

TOTAL: ~30 min pre-review
```

---

## 📚 DOKUMENT ÜBERSICHT

### CODEX (Übergeordnet)

| Dokument | Typ | Für wen | Länge | Update-Frequenz |
|----------|-----|---------|-------|-----------------|
| **00_CODEX_CONTEXT.md** | 🔐 Arbeitsbriefing | Alle Devs | 490 Zeilen | Rarely (Breaking Changes only) |
| **11_MASTERPLAN_CODEX_CHEATSHEET.md** | 🔐 Quick-Ref | Alle Devs | 300 Zeilen | Rarely |

### MASTERPLAN (Projekt-Fokus)

| Dokument | Typ | Für wen | Länge | Update-Frequenz |
|----------|-----|---------|-------|-----------------|
| **MASTERPLAN_SUMMARY.md** | 📋 Quick-Start | PM + Dev | 150 Zeilen | Weekly |
| **11_MASTERPLAN_INDEX.md** | 📊 Navigation | Alle | 370 Zeilen | Weekly |
| **11_MASTERPLAN_FINALISIERUNG.md** | 🎯 Strategie | PM + Senior | 600 Zeilen | Weekly |
| **11_MASTERPLAN_ROADMAP_VISUAL.md** | 📈 Timeline | PM + Dev | 500 Zeilen | Weekly |
| **11_MASTERPLAN_DAILY_CHECKLIST.md** | ✅ Taktik | Dev täglich | 830 Zeilen | Daily |

### Supporting-Docs (Project Context)

| Dokument | Typ | Für wen | Link |
|----------|-----|---------|------|
| **00_PROJECT_BRIEF.md** | 📖 Context | Alle | `docs/` |
| **02_PRODUCT_SPEC_UNIFIED.md** | 📖 Bindend | Dev/PM | `docs/` |
| **03_RIGHTS_MATRIX.md** | 🔐 RBAC | Dev/QA | `docs/` |
| **01_DECISIONS.md** | 🧠 Why | Alle | `docs/` |
| **99_MASTER_CHECKPOINT.md** | 🔄 Status | Alle | `docs/` |

---

## 🔗 VERLINKUNG MATRIX

```
Wo zu finden:           Referenziert in:

CODEX_CONTEXT.md    ←→ 11_MASTERPLAN_DAILY_CHECKLIST.md
                    ←→ 11_MASTERPLAN_INDEX.md
                    ←→ 11_MASTERPLAN_CODEX_CHEATSHEET.md

03_RIGHTS_MATRIX.md ←→ 00_CODEX_CONTEXT.md (Section 3)
                    ←→ 11_MASTERPLAN_DAILY_CHECKLIST.md (Pre-Start)
                    ←→ 11_MASTERPLAN_CODEX_CHEATSHEET.md (Routing)

02_PRODUCT_SPEC.md  ←→ 00_CODEX_CONTEXT.md (Section 2, 5)
                    ←→ 11_MASTERPLAN_FINALISIERUNG.md (Task Details)

99_MASTER_CHECKPOINT → 00_CODEX_CONTEXT.md (Section 4)
                    ←→ 11_MASTERPLAN_DAILY_CHECKLIST.md (Pre-Start)
```

---

## ✅ CHECKLISTEN ZUM AUSDRUCKEN

### Für Devs (Desk-Tape):

```
☐ CODEX Cheatsheet (laminated 📋)
☐ Daily Checklist Bookmark (11_MASTERPLAN_DAILY_CHECKLIST.md)
☐ RIGHTS_MATRIX saved (03_RIGHTS_MATRIX.md)
```

### Für PM (Meeting):

```
☐ MASTERPLAN_FINALISIERUNG (printed, highlighted)
☐ ROADMAP_VISUAL (printed, timeline handy)
☐ Milestone dates in shared calendar
├─ Do 3/4: P0 COMPLETE
├─ Fr 3/19: P1 COMPLETE
└─ Mo 3/30: Release Ready
```

---

## 🚀 SCHNELLE ANTWORTEN

Wenn developer fragt...

| Frage | Antwort |
|-------|--------|
| "Welche Route?" | → `03_RIGHTS_MATRIX.md` |
| "Moderator OK hier?" | → `00_CODEX_CONTEXT.md` Section 1, Punkt 3 |
| "Wie Auth?" | → `00_CODEX_CONTEXT.md` Section 2 + `server/app/auth/actor.py` |
| "PII wo?" | → `CODEX_CHEATSHEET.md` oder `00_CODEX_CONTEXT.md` Section 1, Punkt 5 |
| "Was ist DONE?" | → `99_MASTER_CHECKPOINT.md` |
| "Was muss ich machen?" | → `11_MASTERPLAN_DAILY_CHECKLIST.md` (heute's section) |
| "Wann fertig?" | → `11_MASTERPLAN_ROADMAP_VISUAL.md` (Gantt Chart) |
| "Fehler?" | → `00_CODEX_CONTEXT.md` Section 6 + 9 (Engineering-Guide + Checkliste) |

---

## 🎯 DER KRITISCHE PATH

Für schnelles Deployment brauchst du MINDESTENS:

```
MUSS VOR CODE-START:
├─ ☑ Dev: CODEX Cheatsheet verstanden (5 min)
├─ ☑ Dev: 03_RIGHTS_MATRIX.md gecheckt (5 min)
├─ ☑ PM: Daily-Checklist für heute gelesen (5 min)
└─ ☑ All: Dev-Env läuft (npm run dev, Backend API running)

TÄGLICH:
├─ ☑ 11_MASTERPLAN_DAILY_CHECKLIST.md (heute's section)
├─ ☑ CODEX Cheatsheet als Bookmark (wenn blockiert)
└─ ☑ Commit messages = Masterplan Format

WEEKLY:
├─ ☑ 99_MASTER_CHECKPOINT.md Statusupdate
├─ ☑ 11_MASTERPLAN_DAILY_CHECKLIST.md nächste woche prep
└─ ☑ Masterplan-Docs aktualisieren (wenn Scope-Changes)
```

---

## 💡 PRO TIPS

1. **Print + Laminate Cheatsheet**
   - Steht auf deinem Desk während dev
   - Schneller als zu googlen
   - Reminds von Harten Invarianten

2. **Bookmark RIGHTS_MATRIX**
   - Tab im Browser
   - Jede Route bevor implementieren
   - Erspart 100 Fragen

3. **Daily Checklist in Editor**
   - VS Code öffnen mit split-view
   - Links: Checklist (markdown)
   - Rechts: dein Code
   - Abhaken während coden

4. **CODEX Section 6 merken** (Checkliste vor Änderung)
   - 5 Items, 2 min check
   - Verhindert 90% der Security-Issues

5. **Team-Slack-Channel**
   - `#blockers` für Stuck-Status
   - `#masterplan` für Updates
   - `#codex` für Fragen
   - Daily Standup dort um 9:00 CET

---

## 📞 WENN VERLOREN

1. **Lese diese Datei** (du bist jetzt hier)
2. **Gehe zu 11_MASTERPLAN_CODEX_CHEATSHEET.md** (schnelle Antworten)
3. **Oder bestimmtes doc-Lookup:**
   - Routes → 03_RIGHTS_MATRIX.md
   - Why decisons → 01_DECISIONS.md
   - Product flow → 02_PRODUCT_SPEC_UNIFIED.md
   - Status → 99_MASTER_CHECKPOINT.md
4. **Frag in #help Slack** (mit konkrete Frage, nicht "unklar")

---

**DEIN HIRN:** Cheatsheet + Daily Checklist
**DEIN BOOKMARK:** RIGHTS_MATRIX + CODEX_CONTEXT
**DEIN DESK:** Gedrucktes Cheatsheet (laminated!)

Du packst das! 🚀
