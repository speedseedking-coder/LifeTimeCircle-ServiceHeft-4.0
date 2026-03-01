# LifeTimeCircle – Service Heft 4.0
## Masterplan zur Finalisierung
**Stand: 2026-02-28 (Europe/Berlin)**

---

## 📊 EXECUTIVE SUMMARY

### Status Quo
- ✅ **Backend:** 100% produktionsreif (FastAPI, RBAC deny-by-default, Tests grün)
- ✅ **Security/Policies:** Vollständig implementiert (Moderator-Gates, Consent, Export-Control)
- ✅ **Design System & Components:** Komplett aufgebaut (Tokens, UI-Kit, Layouts)
- 🔄 **Web-Frontend:** App-Shell vorhanden, Pages teilweise fertig, Landingpage noch zu bauen
- 🔄 **Public-QR:** Backend fertig, Frontend zu haerten
- 🔄 **Admin-Pages:** Grundstruktur da, aber auf Finalisierung wartend

### Ziel
**Produktives MVP** (keine Demo):
- Frontend zu 100% mit API verdrahtet
- Alle kritischen User Flows sauber UX-erfahren
- Trust-Ampel, Documents, Vehicles, Timeline funktional
- Public-QR druckbar/shareable
- Admin-Flows für Rollen/Moderator/Export funktional

### Timeline
| Phase | Dauer | Zielatum |
|-------|-------|----------|
| **P0 Webseite** | 5–7 Tage | ~2026-03-06 |
| **P1 MVP Flows** | 7–10 Tage | ~2026-03-16 |
| **P2 Polish & QA** | 5–7 Tage | ~2026-03-23 |
| **→ Release Ready** | — | **~2026-03-30** |

---

## 🎯 DETAILLIERTER ARBEITSPLAN

### **PHASE P0: Webseite + Fundament (5-7 Tage)**

**Ziel:** Landingpage, öffentliche Seiten, Basis-Navigation

| Nr. | Aufgabe | Beschreibung | Voraussetzung | DoD | Aufwand |
|-----|---------|-------------|---------------|-----|---------|
| **W1** | Landing Page | Home mit CTA "Eintritt", Feature-Highlights | Design-System ✅ | • Responsive ✅ • Disclaimer-Text exakt ✅ • CTA → #/entry ✅ | 6-8h |
| **W2** | Entry/Rolle-Wahl | Privat vs Gewerblich Selektor | W1 | • Beide Optionen klickbar ✅ • → Signup/Login Redirect ✅ | 4-6h |
| **W3** | Public Navigation | Header + Footer für alle Public-Seiten | Design-System ✅ | • Links zu FAQ/Blog/News/Impressum ✅ • Logo → #/ ✅ | 3-4h |
| **W4** | FAQ/Impressum/Datenschutz | Statische Public Seiten | W1-W3 | • Lesbar ✅ • Links funktionieren ✅ • Mobile OK ✅ | 5-6h |
| **W5** | Blog-/News-List (Read-Only) | Public Blogbase vorabgreifbar | W3 | • GET /blog, /news auf API verdrahtet ✅ • EmptyState wenn leer ✅ | 4-5h |
| **W6** | Design System Polishing | Tokens, Komponenten-Docs finalisieren | Design-System ✅ | • Figma oder Styleguide-Seite ✅ • Alle Varianten dokumentiert ✅ | 3-4h |

**P0 Subtotal Effort:** ~25–33 Hours

**Test-Checklist P0:**
- [ ] `npm run build` grün, keine Warnings
- [ ] Lighthouse Score >80 auf Landing Page
- [ ] Responsive auf Mobile (375px), Tablet (768px), Desktop (1920px)
- [ ] Public-QR Disclaimer exakt + unmodifizierbar
- [ ] E2E: Public Flows ohne Auth funktionieren
- [ ] All Design Tokens genutzt (0 Hardcoded Values)

---

### **PHASE P1: MVP Flows (7-10 Tage)**

**Ziel:** Auth → Vehicles → Documents → Public-QR funktional

#### **P1.1: Authentication & Consent (3-4 Tage)**

| Nr. | Aufgabe | Beschreibung | Voraussetzung | DoD | Aufwand |
|-----|---------|-------------|---------------|-----|---------|
| **A1** | Auth-Page Finalisierung | Signup/Login, Error-Handling, Loading States | Auth API ✅ | • Formular valdiert lokal ✅ • API-Fehler angezeigt ✅ • Links zu Datenschutz/AGB ✅ | 6-8h |
| **A2** | Consent-Page Flow | AGB/Datenschutz Read + Accept Button | Consent API ✅ | • Beide Docs lesbar ✅ • Accept → Redirect zurück zur Zielroute ✅ • Version+Timestamp gespeichert ✅ | 5-6h |
| **A3** | Token Persistence | localStorage/sessionStorage Handling | A1, A2 | • Token nach Refresh noch vorhanden ✅ • Logout räumt auf ✅ • Token-Expiry gehandhabt ✅ | 3-4h |
| **A4** | Auth Guard in Routes | 401 → Auth, consent_required → Consent, 403 → Forbidden | A1-A3 | • Guards funktionieren ✅ • Redirect-URL erhalten bleiben ✅ • Moderator hat 403 auf /vehicles etc ✅ | 4-5h |

**P1.1 Subtotal:** ~18–23 Hours

#### **P1.2: Vehicles Core (4-5 Tage)**

| Nr. | Aufgabe | Beschreibung | Voraussetzung | DoD | Aufwand |
|-----|---------|-------------|---------------|-----|---------|
| **V1** | Vehicles List Page | GET /vehicles, Grid-Display, Add-Button | Vehicles API ✅ | • List rendert ✅ • EmptyState gezeigt ✅ • Infinite Scroll oder Pagination ✅ • VIN maskiert ✅ | 6-8h |
| **V2** | Vehicle Detail Header | VIN maskiert, Trust-Ampel, Fahrzeugdaten | Vehicles API ✅ | • Header zeigt korrekt ✅ • Trust-Ampel (T1/T2/T3) mapped ✅ • Badges für Status ✅ | 5-7h |
| **V3** | Timeline/Entries Tab | Chronologische Liste Serviceeinträge | Entries API ✅ | • Sorted by Datum ✅ • Entry-Add Button ✅ • Versionierung angezeigt ✅ • Pagination gezeigt ✅ | 6-8h |
| **V4** | Entry-Form Modal | Pflichtfelder: Datum, Typ, km, Durchgeführt-von | Entries API ✅ | • Formular validiert ✅ • Submit disabled bis valid ✅ • Success/Error Message ✅ | 6-8h |
| **V5** | Documents Tab Übersicht | Count + Status (Quarantined/Approved/etc) | Documents API ✅ | • Counts vorhanden ✅ • Status-Badge farbig ✅ • Link zu Upload ✅ | 4-5h |
| **V6** | Create Vehicle Flow | ADD button → Modal, Fahrzeugdaten, VIN | Vehicles API ✅ | • Modal öffnet ✅ • Validierung ✅ • Redirect zu Vehicle Detail ✅ | 5-6h |

**P1.2 Subtotal:** ~32–42 Hours

#### **P1.3: Documents (3-4 Tage)**

| Nr. | Aufgabe | Beschreibung | Voraussetzung | DoD | Aufwand |
|-----|---------|-------------|---------------|-----|---------|
| **D1** | Upload UX | Drag&Drop, Filepicker, Progress-Bar | Documents API ✅ | • Upload funktioniert ✅ • Progress visual ✅ • Validierung (PDF/JPG/PNG) ✅ | 6-8h |
| **D2** | Document Status Badges | QUARANTINED/PENDING/CLEAN/APPROVED anzeigen | Documents API ✅ | • Status korrekt mapped ✅ • Farben logisch (rot=bad, grün=ok) ✅ • Tooltips optional ✅ | 3-4h |
| **D3** | Download Link | Nur für APPROVED, Icon-Button | Documents API ✅ | • Nur genehmigte docs ✅ • Fehler bei Zugriff ✅ | 2-3h |
| **D4** | Document List | Alle Dokumente für Fahrzeug, Filter/Sort optional | Documents API ✅ | • List rendert ✅ • EmptyState ✅ | 4-5h |

**P1.3 Subtotal:** ~15–20 Hours

#### **P1.4: Public-QR Page (2-3 Tage)**

| Nr. | Aufgabe | Beschreibung | Voraussetzung | DoD | Aufwand |
|-----|---------|-------------|---------------|-----|---------|
| **Q1** | Public-QR View | datenarm (VIN maskiert, Trust-Ampel, Badge) | Public API ✅ | • VIN maskiert ✅ • Disclaimer exakt ✅ • Print-ready ✅ • Kein Auth needed ✅ | 6-8h |
| **Q2** | QR-Code Generierung | QR-Code rendert auf Seite | QR Library | • Code lesbar ✅ • Verlinkt auf public View ✅ | 3-4h |
| **Q3** | Print/Share Controls | Print Button + Share-Link kopieren | Q1 | • Print sieht gut aus ✅ • Share-Link funktioniert ✅ | 3-4h |

**P1.4 Subtotal:** ~12–16 Hours

**P1 Total Effort:** ~77–101 Hours

**Test-Checklist P1:**
- [ ] All Auth/Consent flows funktionieren
- [ ] Vehicles CRUD (Create, Read, Update, Delete) sauber
- [ ] Entries erstellen + versioning sichtbar
- [ ] Documents Upload + Status korrekt
- [ ] Public-QR Print/Share funktioniert
- [ ] E2E (Playwright): Kompletter User Flow Auth → Vehicles → Documents
- [ ] Moderator hat überall 403 (außer Blog/News)
- [ ] Mobile responsive alle Pages

---

### **PHASE P2: Admin & Polish (5-7 Tage)**

#### **P2.1: Admin Pages (2-3 Tage)**

| Nr. | Aufgabe | Beschreibung | Voraussetzung | DoD | Aufwand |
|-----|---------|-------------|---------------|-----|---------|
| **AD1** | Admin Rollen-Verwaltung | User-Liste, Role-Setter, Moderator-Akkreditierung | Admin API ✅ | • Users aufgelistet ✅ • Role-Change funktioniert ✅ • Feedback ✅ | 6-8h |
| **AD2** | Document Quarantine Review | Admin sieht PENDING/INFECTED, kann Approve/Reject | Admin API ✅ | • List vorhanden ✅ • Approve/Reject funktioniert ✅ | 4-6h |
| **AD3** | Export-Full mit Step-Up | Full-Export nur SUPERADMIN, UI-Flow | Admin API ✅ | • Step-Up-Dialog ✅ • Nur SUPERADMIN sieht ✅ • Export lädt ✅ | 5-6h |

**P2.1 Subtotal:** ~15–20 Hours

#### **P2.2: Trust & To-Dos (2-3 Tage)**

| Nr. | Aufgabe | Beschreibung | Voraussetzung | DoD | Aufwand |
|-----|---------|-------------|---------------|-----|---------|
| **T1** | Trust Widget Design | To-Dos anzeigen, Reason-Codes, Hints | Trust API ✅ | • Widget rendert ✅ • To-Dos klar ✅ • Keine technischen Claims ✅ | 6-8h |
| **T2** | Trust-Ampel Reason-Codes | Mapping: block/cap/warn → Farbe + Hint | Trust Service ✅ | • Ampel korrekt: Grün/Gelb/Rot/Grau ✅ • Hints aussagekräftig ✅ | 4-5h |

**P2.2 Subtotal:** ~10–13 Hours

#### **P2.3: Quality & Polish (2-3 Tage)**

| Nr. | Aufgabe | Beschreibung | Voraussetzung | DoD | Aufwand |
|-----|---------|-------------|---------------|-----|---------|
| **Q1** | Error Handling überall | Alle API-Fehler sauber angezeigt | All Flows | • keine weißen Screens ✅ • Retry-Möglichkeiten ✅ • User weiß, was falsch ist ✅ | 6-8h |
| **Q2** | Loading States & Skeleton | alle async Operationen zeigen Loading | All Pages | • Skeleton sichtbar ✅ • kein Flash ✅ | 4-5h |
| **Q3** | Mobile Responsive Final Pass | alle Breakpoints testen | all pages | • 375px OK ✅ • 768px OK ✅ • 1920px OK ✅ | 5-6h |
| **Q4** | Lighthouse & Performance | minify, lazy-load, kritisches CSS | All | • Score >80 ✅ • Load <3s ✅ | 4-5h |
| **Q5** | E2E Coverage erweitern | Playwright Tests für admin/exports | All Flows | • E2E grün ✅ • Coverage >80% ✅ | 6-8h |

**P2.3 Subtotal:** ~25–32 Hours

**P2 Total Effort:** ~50–65 Hours

---

## 📋 KRITISCHE PFADE & ABHÄNGIGKEITEN

```
        Land + Roles
            ↓
    ┌───────┴──────────┐
    ↓                  ↓
  Auth →           Public-QR
    ↓                  ↓
 Consent             (Read-Only)
    ↓
 Vehicles (Gate: Consent + Role)
    ├── Entries (Timeline)
    ├── Documents (Upload)
    └── Trust-Status
       ↓
    Admin (nur für admin/superadmin)
       ├── Rollen-Management
       ├── Quarantine-Review
       └── Export-Full
```

**Kritisch = Blocking für mehrere andere Tasks:**
- ✅ Design System (= erledigt, nicht blockiert mehr)
- ✅ Auth/Consent (= Gating für alles)
- ⚠️ Vehicles Page (= Kern des Produkts)
- ⚠️ Documents Upload (= verlinkt mit Vehicles)
- ⚠️ Admin Pages (= letzte Mile, aber nicht blockierend)

---

## 🔧 NÄCHSTE KONKRETE SCHRITTE (Morgen starten)

### **Tag 1 (Montag, 2026-03-01):**
1. Landing Page aufbauen (W1, 6-8h)
   - PublicLayout + Header + Footer nutzen
   - DesignSystemReference als Inspiration
   - CTA zu #/entry

2. Entry/Role-Wahl implementieren (W2, 4-6h)
   - Simple Choice-Button zwischen "Privat" und "Gewerblich"
   - Redirect zu #/auth

**Commit:** `feat(web): landing page + entry role choice (P0-W1-W2)`

### **Tag 2 (Dienstag, 2026-03-02):**
1. Public Navigation finalisieren (W3, 3-4h)
2. FAQ/Impressum Seiten (W4, 5-6h) → Statisches Markdown + Rendering
3. Blog-/News-List verdrahten (W5, 4-5h)

**Commit:** `feat(web): public pages + blog/news list (P0-W3-W5)`

### **Tag 3 (Mittwoch, 2026-03-03):**
1. Auth Page fertigstellen (A1, 6-8h)
   - Signup/Login-Form
   - Error-Handling
   - Token-Speicherung

2. Consent Page (A2, 5-6h)
   - AGB/Datenschutz PDF oder HTML
   - Accept-Button

**Commit:** `feat(web): auth + consent pages (P1-A1-A2)`

### **Tag 4-5 (Do-Fr, 2026-03-04-05):**
1. Vehicles List (V1, 6-8h)
2. Vehicle Detail Header (V2, 5-7h)
3. Timeline/Entries Tab (V3, 6-8h)

**Commit:** `feat(web): vehicles + entries timeline (P1-V1-V3)`

---

## 📊 EFFORT SUMMARY

| Phase | Min | Max | Gesamt | Persons |
|-------|-----|-----|--------|---------|
| **P0: Webseite** | 25h | 33h | ~28h | 1 Dev × 7 Tage (4h/Tag) |
| **P1: MVP Flows** | 77h | 101h | ~89h | 1 Dev × 10 Tage (9h/Tag) |
| **P2: Admin/Polish** | 50h | 65h | ~57h | 1 Dev × 7 Tage (8h/Day) |
| **GESAMT** | 152h | 199h | **174h** | ~24 Tage 1 Dev |

### Mit 2 Devs parallel (P1 & P2):
- **Timeline auf ~17 Tage reduzierbar**
- Scenario: 1 Dev macht Frontend, 1 Dev macht Backend-Integration/Admin-APIs

---

## ✅ RELEASE READINESS CHECKLIST

### Voraussetzungen (alle ✅):
- [x] Backend produktionsreif (Tests 100% grün)
- [x] RBAC serverseitig enforced
- [x] Design System complete
- [x] Error Pages ready

### Frontend (bis ~2026-03-30):
- [ ] Landing + Public Pages
- [ ] Auth + Consent Flow sauber
- [ ] Vehicles + Entries + Documents funktional
- [ ] Public-QR druckbar
- [ ] Admin-Pages basisfunktional
- [ ] E2E Tests >80% Coverage
- [ ] Mobile responsive
- [ ] Lighthouse >80

### DevOps:
- [ ] CI/CD Pipeline konfiguriert
- [ ] Staging Environment (optional)
- [ ] Monitoring/Error Tracking
- [ ] Backup Strategy

### Legal/Compliance:
- [ ] Disclaimer-Text exakt in Public-QR (✅ SoT confirmed)
- [ ] AGB/Datenschutz final reviewed
- [ ] DSGVO Compliance audit
- [ ] Haftungsfreistellung für Trust-Ampel

---

## 📞 SUPPORT & BLOCKER HANDLUNG

Wenn Blocker auftauchen:

| Blocker | Lösung |
|---------|--------|
| **API ändert sich** | Sync mit Backend-Dev, API-Contract aktualisieren |
| **Design-Decision offen** | Verwende bestehende Komponenten, Fallback schreiben |
| **Performance Issue** | Lazy-load, Code-split, Image-optimize |
| **Browser-Kompatibilität** | Polyfill hinzufügen oder Feature-Detection |
| **Time Crunch** | Priorisiere P1, P2 verschieben auf Phase 2 |

---

## 📝 DOKUMENTATION zu aktualisieren

Nach jeder Phase:

```bash
# Docs updaten
docs/02_BACKLOG.md          # Status der epics aktualisieren
docs/99_MASTER_CHECKPOINT.md  # neuer Checkpoint hinzufügen
packages/web/WEBDESIGN_GUIDE.md # Falls neue Patterns entstanden
```

---

## 🎯 DEFINITION OF DONE (GLOBAL)

Für jeden Commit/PR:

- ✅ Code ist TypeScript-safe (`npx tsc --noEmit`)
- ✅ Keine PII/Secrets in Code/Screenshots
- ✅ Design Tokens überall genutzt (kein Hardcoding)
- ✅ Mobile responsive (min 375px)
- ✅ Error States sauber
- ✅ Loading States gezeigt
- ✅ E2E Test für den Flow geschrieben
- ✅ `npm run build` grün
- ✅ Docs aktualisiert wenn nötig

---

## 🚀 FINISH LINE

**Zielatum: ~2026-03-30**

Am Zieldatum sollte das Projekt:
1. ✅ 100% Web-Frontend mit API verdrahtet
2. ✅ Alle kritischen User Flows funktional
3. ✅ E2E Tests grün
4. ✅ Staging/Prod-Ready
5. ✅ Monitoring/Logging aktiv
6. ✅ Team-Training abgeschlossen

**Dann:** Go-Live oder weitere Optimierungen basierend auf Nutzer-Feedback.

---

**Kontakt:** lifetimecircle@online.de  
**Repo:** https://github.com/.../LifeTimeCircle-ServiceHeft-4.0
**Source of Truth:** `/docs` Folder (nicht dieses Dokument als Primary)
