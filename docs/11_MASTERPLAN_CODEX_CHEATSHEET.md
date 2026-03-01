# 🔐 CODEX CHEATSHEET
## Quick-Reference für tägliche Arbeit

**Benutze diese Seite als Bookmark!** – Wenn etwas unklar ist, schlag hier nach (2-3 min max)

---

## 🚨 HARTE INVARIANTEN (DIESE BRECHEN NIE!)

```
1. deny-by-default + least privilege
   → jede Route MUSS explizit gated sein
   → RBAC runtime enforcement

2. Moderator hart-blockt
   → überall 403 außer: /auth/*, /blog/*, /news/*
   → if moderator + andere route = 403 IMMER

3. Actor missing → 401, nicht 403
   → "nicht authentifiziert" ≠ "nicht autorisiert"
   → Wichtig für Error-Pages + ErrorHandling

4. Keine PII/Secrets in Code
   → kein hardcoded VINs, Emails, User-IDs
   → auch nicht in Debug-Ausgaben!

5. RBAC serverseitig enforced
   → Frontend Guards nur UX (Redirect)
   → Server MUSS nochmal checken!
   → object-level checks (Owner/Business/Scope)

6. Uploads Quarantäne-by-default
   → New upload = QUARANTINED status
   → Approve NUR nach Scan = CLEAN
   → Download erst bei APPROVED + Scope + Object-Level

7. Exports redacted
   → Nicht-Admin = alle Secrets weg
   → Dokument-Refs nur APPROVED

8. Public QR Disclaimer EXAKT
   → "Die Trust-Ampel bewertet ausschließlich die 
      Dokumentations- und Nachweisqualität. Sie ist 
      keine Aussage über den technischen Zustand 
      des Fahrzeugs."
   → Copy-Paste, nicht paraphrasieren!
```

---

## 📖 SOURCE OF TRUTH HIERARCHIE

**Bei Konflikten in dieser Reihenfolge nachschlagen:**

```
1. docs/99_MASTER_CHECKPOINT.md        ← Status quo + PRs + Scripts
2. docs/02_PRODUCT_SPEC_UNIFIED.md     ← Bindende Produktlogik
3. docs/03_RIGHTS_MATRIX.md            ← RBAC + Routes
4. docs/01_DECISIONS.md                ← Warum-Entscheidungen
5. server/ (Code)                      ← Implementierung = Source
```

---

## ✅ CHECKLISTE VOR JEDER ÄNDERUNG

Schnell vor Code-Start durchgehen (2 min):

- [ ] `docs/99_MASTER_CHECKPOINT.md` gelesen (Status + PRs + Scripts)
- [ ] `docs/03_RIGHTS_MATRIX.md` geprüft:
  - [ ] Route hat Gate?
  - [ ] Moderator Allowlist OK?
  - [ ] object-level checks needed?
- [ ] `docs/01_DECISIONS.md` für diese Feature durchsucht
- [ ] Keine PII-Felder im Code werden exposed?
- [ ] Wenn Uploads/Exports: Quarantäne/Redaction OK?

---

## 🛠️ ROUTING/RBAC IN DEUTSCH

### Route-Kategorien & Regeln:

| Route | Allowlist | Who | Notes |
|-------|-----------|-----|-------|
| `/public/*` | Everyone | 🔓 | No auth required |
| `/blog/*` | PUBLIC read + MODERATOR write | 🔓📝 | Moderator ONLY für CMS |
| `/news/*` | PUBLIC read + MODERATOR write | 🔓📝 | Moderator ONLY für CMS |
| `/auth/*` | PUBLIC + Moderator | 🔓 | Signup/Login/Logout |
| `/consent/*` | Authenticated | 🔐 | After auth, before app |
| `/vehicles/*` | Authenticated | 🔐 | User's vehicles only (object-level) |
| `/documents/*` | Scoped + Object-level | 🔐🔒 | Quarantäne/Scan/Approval flow |
| `/trust/*` | Scoped + Object-level | 🔐🔒 | Trust-Ampel + To-dos |
| `/admin/*` | ADMIN + Superadmin | 🔒🔒 | Zones + Exports + Quarantine |
| `/api/..." | (backend routes) | ❌ | Frontend proxy: `/api/*` → backend |

**Legend:**
- 🔓 = Public/no auth
- 🔐 = Auth required
- 🔒 = Admin/role-specific
- 📝 = MODERATOR exclusive

---

## 🔧 WAS SCHON FERTIG IST (nutzen!)

Brauchst du nicht zu implementieren:

```
✅ Web Skeleton (Vite + React + TS)
✅ API Proxy: /api/* → backend :8000
✅ Design System + Components (tokens.css, UI-Kit)
✅ Layout Components (PublicLayout, AppLayout, Header, Footer)
✅ Actor Source of Truth (server/app/auth/actor.py)
✅ Moderator Runtime-Scan Test
✅ Upload Quarantäne Workflow
✅ Documents router include (no duplicate operation IDs)
✅ Public QR Page Template + Disclaimer Patch

→ Diese kannst du direkt verwenden/importieren!
```

---

## 🚀 QUICK STARTS

### Neue Route mit RBAC:

```tsx
// 1. Checke docs/03_RIGHTS_MATRIX.md für diese Route
// 2. Implementiere Gate im React (nur für UX):
if (!actor) return <Unauthorized401Page />;
if (!hasPermission(actor, route)) return <Forbidden403Page />;

// 3. Implementiere echte Gate im Backend (server/app/routers/...)
# Pseudocode:
def my_route(actor: Actor = Depends(get_actor)):
    if not actor:
        raise HTTPException(401)  # Unauth
    if not has_permission(actor, this_route):
        raise HTTPException(403)  # Forbidden
    # ... object-level checks ...
    return result

// 4. Test: pytest checkt Moderator 403 Coverage
// 5. Commit message muss erwähnen: "RBAC: actor + role + object-level checked"
```

### Neue Page mit Design:

```tsx
// 1. Import Layout:
import { PublicLayout } from '@/components/layout';
import { Button, Card, Badge } from '@/components/ui';

// 2. Tokens NUTZEN (nie hardcoded):
<div style={{ padding: 'var(--ltc-space-4)', color: 'var(--ltc-color-text)' }}>

// 3. Responsive testen: 375px, 768px, 1024px
// 4. Commit: "feat(web): add [pagename] (P0-W1)"
```

### Upload/Document mit Quarantäne:

```tsx
// 1. User uploaded file
// 2. Backend: Document created mit status = QUARANTINED
// 3. Show UI: "Wird gescannt..."
// 4. Server scans (async)
// 5. Admin genehmigt nach Scan
// 6. User kann APPROVED document runterladen
// 7. Nicht-Admin sieht nur APPROVED Docs
// 8. Exports: redacted für Nicht-Admin
```

---

## 📞 WENN BLOCKIERT

### Typische Probleme & Lösungen:

| Problem | Lösung | Check |
|---------|--------|-------|
| "Welche Route?" | 03_RIGHTS_MATRIX.md | RBAC column |
| "Actor/Auth unklar?" | server/app/auth/actor.py | Source |
| "Moderator Allowlist?" | Search in 03_RIGHTS_MATRIX | Allowlist column |
| "Uploads wie?" | 02_PRODUCT_SPEC_UNIFIED.md §6 | Upload flow |
| "PII wo vermeiden?" | CODEX Section 1 + 02_PRODUCT_SPEC | Search "PII" |
| "Fehler im Build?" | npm run build errors | TS strict |
| "Tests fail?" | pytest -v | Actor/Moderator coverage |

---

## 📝 BEISPIEL: Landing Page (P0-W1)

**Checkliste vor Code:**
- [ ] Read CODEX Sektion 1-3 (20 min)
- [ ] Check 03_RIGHTS_MATRIX.md: `/public/site` → PUBLIC (kein Gate)
- [ ] Check 02_PRODUCT_SPEC_UNIFIED.md §2: Landing Page Part
- [ ] Check 99_MASTER_CHECKPOINT.md: PublicLayout schon vorhanden ✅

**Während Code:**
- [ ] Nutze PublicLayout (schon importierbar)
- [ ] Design Tokens nutzen (keine hardcoded Farben)
- [ ] Responsive: 375px + 768px + 1024px testen
- [ ] CTA "Eintritt" → `/#/entry`
- [ ] Keine PII

**Vor Commit:**
- [ ] `npm run build` grün?
- [ ] `npm run dev` responsive OK?
- [ ] Moderator kann trotzdem nicht auf unerlaubte Routes?
- [ ] Commit message: `feat(web): add landing page (P0-W1)`

---

## 🎯 DEIN DAILY RITUAL

**Jeden Morgen (5 min):**

```bash
# 1. Git sync
git fetch origin
git status

# 2. Check Status + PRs
# → docs/99_MASTER_CHECKPOINT.md (was changed yesterday?)

# 3. Check Daily Checklist
# → docs/11_MASTERPLAN_DAILY_CHECKLIST.md (today's tasks)

# 4. Start coding
# → This cheatsheet als Bookmark neben IDE
```

**Wenn du feststeckst (5 min):**

```
→ Check this cheatsheet ODER
→ Check 03_RIGHTS_MATRIX ODER  
→ Check 02_PRODUCT_SPEC ODER
→ Slack #help mit konkrete Frage
```

---

## 🔗 LINKS (Ausdruck = A4 + Laminate!)

- **Cheatsheet (dieses Dokument)** → Print, Desk-Tapeieren
- **03_RIGHTS_MATRIX.md** → Bookmark in Browser (oft brauchen!)
- **WEBDESIGN_GUIDE.md** → Neben IDE als Reference
- **11_MASTERPLAN_DAILY_CHECKLIST.md** → Heute's Tasks

---

**Benutzung:** Bookmark dieses Dokument. Daily review (2 min). Die 8 Harten Invarianten sind Non-Negotiable™.

**Immer aktuell?** Ja – wenn Änderungen, werden diese hier + in 00_CODEX_CONTEXT.md + im 99_MASTER_CHECKPOINT dokumentiert.

**Fragen?** → `#help` Slack oder Daily Standup.

---

**Du packst das! 🚀**
