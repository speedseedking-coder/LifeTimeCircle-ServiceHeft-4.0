# LifeTimeCircle – Quick-Reference Checklist
## Finalisierungs-Projekt 2026-03-01 bis 2026-03-30

---

## ⚠️ CODEX-REGELN (BINDEND) – ERSTMAL LESEN!

**Dieses Kapitel ZUERST komplett lesen (15 min) – Deine Arbeitsbibel!**

### 🔒 Harte Invarianten (NIEMALS brechen):

1. **deny-by-default + least privilege** – jede Route MUSS explizit gated sein
2. **RBAC serverseitig enforced** – auch object-level checks (Owner/Business/Scope)
3. **Moderator hart-blockt** – überall 403 außer: `/auth/*`, `/blog/*`, `/news/*`
4. **Actor missing → 401** (unauth), nicht 403!
5. **Keine PII/Secrets** in Logs/Responses/Exports (auch nicht in Debug-Output!)
6. **Uploads Quarantäne-by-default** – Approve erst nach Scan CLEAN
7. **Exports redacted** – für Nicht-Admins; Dokument-Refs nur APPROVED
8. **Public QR Disclaimer EXAKT** unverändert: 
   > „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."

### 📖 Source of Truth Hierarchie (bei Konflikten nachschlagen):

1. `docs/99_MASTER_CHECKPOINT.md` (aktueller Status + PRs + Scripts)
2. `docs/02_PRODUCT_SPEC_UNIFIED.md` (bindende Produktlogik)
3. `docs/03_RIGHTS_MATRIX.md` (RBAC + Allowlists)
4. `docs/01_DECISIONS.md` (Entscheidungen/Regeln)
5. `server/` (Implementierung)

### ✅ Vor JEDER Änderung checken:

- [ ] `docs/99_MASTER_CHECKPOINT.md` gelesen (Status + PRs + Scripts)
- [ ] `docs/03_RIGHTS_MATRIX.md` geprüft (RBAC + Routes)
- [ ] VIP-Themen verstanden: Moderator Allowlist, Uploads Quarantäne, Exports redacted
- [ ] `docs/00_CODEX_CONTEXT.md` als Referenz bookmarked

### 🔧 Was schon DONE ist (vorfab nutzen!):

- ✅ Web Skeleton + Vite Proxy (API calls via `/api/*`)
- ✅ API Root Redirect: GET / → 307 → /public/site
- ✅ Public QR Disclaimer Script vorhanden
- ✅ Documents Quarantäne-Workflow
- ✅ Actor Source of Truth: `server/app/auth/actor.py`
- ✅ Moderator Runtime-Scan Test: `test_moderator_block_coverage_runtime.py`

---

## 📋 PRE-START CHECKLIST (vor Arbeitsbeginn)

- [ ] Beiden Masterplan-Dokumente gelesen (11_MASTERPLAN_FINALISIERUNG.md + ROADMAP)
- [ ] Dev Server läuft: `npm run dev` im `packages/web`
- [ ] Backend läuft: `python poetry run uvicorn` im `server`
- [ ] WEBDESIGN_GUIDE.md reviewed (Component-Referenz)
- [ ] CI/CD Pipeline schaut grün: `npm run build` erfolgreich
- [ ] Git-Branch erstellt: `feat/web-p0-landing` (oder entsprechend)
- [ ] Editor/IDE geöffnet mit SSH oder local working tree
- [ ] tägliche Daily Standup geplant (9:00 CET)

---

## 📌 IST-STAND 2026-02-28

- [x] Landing/Public Shell ist produktiv verdrahtet.
- [x] Public Contact ist vorhanden und per E2E abgesichert.
- [x] `#/entry` ist vorhanden und per E2E abgesichert.
- [x] FAQ, Jobs, Impressum, Datenschutz und Cookies sind als Public-Seiten aktiv.
- [x] Auth/Consent/Gate-Logik ist bereits im Web verdrahtet.
- [x] Vehicles, Documents, Admin, Trust Folders und Public QR sind bereits als App-/Produktseiten im Code vorhanden.
- [x] `npm run build` und `npm run e2e` sind nach dem aktuellen Cookie-Refactor grün.
- [ ] Nach jeder weiteren Modularisierung im Web erneut `npm run build` und `npm run e2e` ausführen.

### Heute konkret

- [x] `CookiesPage` aus `App.tsx` in eigene Page-Datei ausgelagert.
- [x] `CookieSettingsCard` aus `App.tsx` in eigene Komponenten-Datei ausgelagert.
- [x] LandingPage, Public-Debug-/Blog-/News-Helfer und App-Shell-CSS aus `App.tsx` ausgelagert.
- [x] Routing-/Background-Helfer, Gate-Hook und Scaffold-Shell aus `App.tsx` in eigene Module ausgelagert.
- [x] Debug-/Blog-/News-Scaffold-Routen und zentralen Route-Renderer aus `App.tsx` ausgelagert.
- [x] Scaffold-Shell in Intro-/Gate-Teilkomponenten zerlegt und explizite `notFound`-Route ergänzt.
- [x] 401/403/404-Systemzustände auf gemeinsames Layout umgestellt und `notFound` per E2E abgesichert.
- [x] `App.tsx` weiter auf Routing, Gates und Verdrahtung reduziert.
- [x] Build/E2E nach diesem Refactor erneut bestätigen (`18/18`).

---

## 🚀 PHASE P0: WEBSEITE (Mo 3/1 – Do 3/4)

### Mo 3/1 – W1: Landing Page (6-8h)

**Status heute:** ✅ Bereits umgesetzt.

**Checklist:**
- [ ] Branch erstellt: `feat/web-p0-landing`
- [ ] `PublicLayout` + `Header` + `Footer` Komponenten importiert
- [ ] Landing Page `/src/pages/LandingPage.tsx` erstellt
- [ ] Design-Tokens genutzt (kein Hardcoding)
  - [ ] Spacing via `--ltc-space-*`
  - [ ] Farben via `--ltc-color-*`
  - [ ] Typo via `--ltc-text-*` oder `.ltc-h*`
- [ ] CTA-Button "Eintritt" → `#/entry` Route
- [ ] Feature-Highlights sichtbar (3 x Cards mit Icons)
- [ ] Disclaimer-Text in Footer exakt: "Die Trust-Ampel bewertet..."
- [ ] Mobile responsive Test (375px, 768px, 1920px)
- [ ] `npm run build` grün
- [ ] PR erstellt + Review

**DoD Kriterien:**
- ✅ TypeScript keine Errors
- ✅ Responsive Layout auf allen Breakpoints
- ✅ Design-Tokens 100% genutzt
- ✅ Keine PII/Secrets in Code
- ✅ **CODEX Check:** no PII, deny-by-default (public route), Moderator unreachable

**Commit Message:**
```
feat(web): add landing page with hero section and feature cards (P0-W1)

- PublicLayout with Header and Footer
- CTA to #/entry role selection
- Design Tokens integrated (no hardcoded values)
- Mobile responsive (375px+)
- Disclaimer text in footer
```

---

### Mo 3/1 PM – W2: Entry/Role-Wahl (4-6h)

**Status heute:** ✅ Bereits umgesetzt und per E2E abgedeckt.

**Checklist:**
- [ ] `EntryPage` Komponente erstellt
- [ ] UI mit 2 großen Buttons: "Privat" vs "Gewerblich"
- [ ] Icons für beide Optionen (👤 und 💼)
- [ ] Click-Handler → redirect zu `#/auth`
- [ ] Mobile responsive
- [ ] `npm run build` grün

**Commit Message:**
```
feat(web): add entry role selection page (P0-W2)

- Private vs Commercial role choice
- Redirect to #/auth on selection
- Mobile responsive buttons
```

---

### Di 3/2 – W3: Public Navigation (3-4h)

**Status heute:** ✅ Bereits umgesetzt.

**Checklist:**
- [ ] `Header` Komponente in PublicLayout angepasst
- [ ] Navigation Links: Home | Blog | FAQ | Jobs | Impressum | Datenschutz | Cookies
- [ ] Aktive Route highlighting (`.active` CSS-Klasse)
- [ ] Logo clickable → `#/`
- [ ] Mobile burgerMenu optional (kann in P2 kommen)
- [ ] `npm run build` grün

**DoD:**
- ✅ Alle Links funktionieren
- ✅ Styling konsistent
- ✅ Hover-States vorhanden

---

### Di 3/2 PM – W4: FAQ/Impressum/Datenschutz (5-6h)

**Status heute:** ✅ Bereits umgesetzt.

**Checklist:**
- [ ] 3 neue Pages erstellt:
  - [ ] `/src/pages/FaqPage.tsx`
  - [ ] `/src/pages/ImpressumPage.tsx`
  - [ ] `/src/pages/DatenschutzPage.tsx`
- [ ] Jede Seite nutzt PublicLayout + Markdown-Content
- [ ] Kein PII in Impressum (generisch halten)
- [ ] Datenschutz: DSGVO-Compliance Keywords vorhanden
- [ ] Responsive + Link to other legal pages
- [ ] `npm run build` grün

**Content Struktur (Beispiel):**
```markdown
# Impressum

LifeTimeCircle GmbH
(Generische Adresse + Kontakt)

# FAQ

Q: Wie sicher sind meine Daten?
A: RBAC + Encryption + ...

Q: Kann ich mein Abo kündigen?
A: Jederzeit zum Monatsende...
```

---

### Mi 3/3 – W5: Blog/News List (4-5h)

**Status heute:** ⏳ Teilweise als Debug-/Scaffold-Ansicht vorhanden, kein final redaktioneller Ausbau.

**Checklist:**
- [ ] `BlogListPage` + `NewsListPage` erstellt
- [ ] Calls `apiGet("/blog")` und `apiGet("/news")`
- [ ] EmptyState wenn keine Posts
- [ ] Post-Cards mit:
  - [ ] Title
  - [ ] Date (formatiert)
  - [ ] Author oder Category Badge
  - [ ] Preview/Excerpt
- [ ] Click → Redirect zu `#/blog/{slug}` (no-op ist ok für jetzt)
- [ ] Pagination oder infinite scroll (optional, kann P2 sein)
- [ ] Mobile responsive
- [ ] `npm run build` grün

**DoD:**
- ✅ API-Integration funktioniert
- ✅ EmptyState sichtbar
- ✅ Responsive Layout

---

### Mi 3/3 PM – W6: Design-System Polish (3-4h)

**Status heute:** ⏳ Build/E2E sind grün, weitergehender Polish bleibt optionaler Ausbau.

**Checklist:**
- [ ] `DesignSystemReference.tsx` erweitert mit allen finalen Komponenten
- [ ] Neue Komponenten added (falls welche in P0 gebraucht)
- [ ] Figma-Link oder Style-Guide-Link in README hinzufügt (optional)
- [ ] Komponenten-Doku in `WEBDESIGN_GUIDE.md` aktualisiert falls nötig
- [ ] `npm run build` grün
- [ ] `npm run e2e` lauft (Playwright)

**DoD:**
- ✅ Reference Page zeigt alle Komponenten
- ✅ Code-Snippets korrekt
- ✅ E2E Tests funktionieren

---

### Do 3/4 – P0 COMPLETE & COMMIT

**Final Checklist:**
- [ ] `git status` sauber (keine uncommitted changes)
- [ ] `npm run build` letztes mal → 0 Warnings
- [ ] `npm run e2e` → alle Tests grün
- [ ] Lighthouse Score auf Landing Page ≥75
- [ ] `git diff origin/main` review durchgeführt
- [ ] **PR mit Label `P0-complete` erstellt + gemerged**

**PR Title:**
```
feat(web): P0 complete - landing + public pages + navigation (READY FOR P1)

This PR includes:
- Landing page with CTA to entry
- Entry role selection (Private/Commercial)
- Public navigation (Header/Footer)
- FAQ, Impressum, Datenschutz pages
- Blog/News read-only list

All pages responsive (375px+), Design-Tokens 100% used, no hardcoded values.
E2E tests passing, Lighthouse >75.

Ready for P1: Auth + Vehicles flows.
```

---

## 🔐 PHASE P1: MVP FLOWS (Fr 3/5 – Fri 3/19)

### P1.1: Auth & Consent (Do 3/4 – Fr 3/5)

#### Do 3/4 PM – A1: Auth Page (6-8h)

**Checklist:**
- [ ] `src/pages/AuthPage.tsx` erweitert (existiert teilweise)
- [ ] **Signup Section:**
  - [ ] Email Input + Validation
  - [ ] Password Input + Validation (min 8 chars)
  - [ ] Confirm Password
  - [ ] AGB + Datenschutz Checkbox mit Links
  - [ ] Submit Button (disabled bis all valid)
  - [ ] Loading state beim POST
  - [ ] Success → Token speichern + redirect zu `#/consent`
  - [ ] Error → Alert angezeigt
- [ ] **Login Section (Toggle):**
  - [ ] Email + Password
  - [ ] „Passwort vergessen?" Link (optional für P1, Placeholder ok)
  - [ ] Submit
  - [ ] Error-Handling
- [ ] Form Validation:
  - [ ] Email format ok
  - [ ] Password >8 chars
  - [ ] Passwords match
  - [ ] Checkbox required
- [ ] `npm run build` grün
- [ ] Responsive

**API Calls:**
```
POST /auth/register
Body: { email, password, role_choice }
Response: { access_token, token_type, expires_in }

POST /auth/login
Body: { email, password }
Response: { access_token, token_type }
```

**Error Handling:**
- [ ] 400 Bad Request → zeige spezifischen Fehler
- [ ] 409 Conflict (User exists) → „Email bereits registriert"
- [ ] 500 Server Error → „Fehler beim Server, versuche später"

---

#### Fr 3/5 – A2: Consent Page (5-6h)

**Checklist:**
- [ ] `src/pages/ConsentPage.tsx` erweitert
- [ ] **Layout:**
  - [ ] AGB-Link + Checkbox zum Akzeptieren
  - [ ] Datenschutz-Link + Checkbox zum Akzeptieren
  - [ ] Accept Button (disabled bis beide checked)
  - [ ] Cancel Button → Back
- [ ] AGB/Datenschutz Inhalte:
  - [ ] Können als HTML/Markdown oder Links zu externer Seite sein
  - [ ] Wichtig: GDPR keywords vorhanden
  - [ ] Version + Date angezeigt (z.B. "Version 1.0 vom 2026-02-28")
- [ ] Accept Button klick:
  - [ ] POST `/consent/accept` mit version + timestamp
  - [ ] Token speichert Consent-Status
  - [ ] Redirect zurück zur ursprünglichen Zielroute (z.B. `#/vehicles`)
  - [ ] Falls keine Zielroute → `#/vehicles` default
- [ ] Mobile responsive
- [ ] `npm run build` grün

**API Call:**
```
POST /consent/accept
Body: { agb_version, datenschutz_version }
Response: { consent_accepted_at, next_review_date }
```

---

#### Mo 3/8 – A3: Token Persistence (3-4h)

**Checklist:**
- [ ] Token nach erfolgreichem Login/Signup speichern:
  - [ ] `localStorage.setItem('ltc_auth_token_v1', token)`
- [ ] App-Start: Token aus localStorage laden (falls vorhanden)
- [ ] Token in Request-Header bei jedem API-Call:
  - [ ] `Authorization: Bearer <token>`
- [ ] Token-Expiry handling:
  - [ ] Falls 401 response → Token löschen + redirect zu #/auth
- [ ] Logout Button:
  - [ ] `localStorage.removeItem('ltc_auth_token_v1')`
  - [ ] Redirect zu `#/` (oder `#/auth`)
  - [ ] Clear auth-state in App
- [ ] Teste: Page refresh → Token noch vorhanden ✅

**Code Pattern:**
```tsx
// lib.auth.ts
export function getAuthToken(): string | null {
  return localStorage.getItem('ltc_auth_token_v1');
}

export function setAuthToken(token: string) {
  localStorage.setItem('ltc_auth_token_v1', token);
}

export function clearAuthToken() {
  localStorage.removeItem('ltc_auth_token_v1');
}

// api.ts - bei jedem request
const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {};
```

---

#### Mo 3/8 PM – A4: Auth Guards (4-5h)

**Checklist:**
- [ ] Guard Logic in App.tsx (Main Router):
  - [ ] `if (!isAuthenticated()) return <Unauthorized401Page />`
  - [ ] `if (!hasConsent()) return <ConsentRequiredPage />`
  - [ ] `if (isModerator()) return <Forbidden403Page />` for `/vehicles` etc
- [ ] Routes protected:
  - [ ] `/vehicles`, `/documents`, `/admin` → 401/403 gated
  - [ ] `/auth`, `/consent`, `/public/*`, `/blog`, `/news` → NO gate
- [ ] Error Page Handling:
  - [ ] 401 → Show `Unauthorized401Page` with "Anmelden" Button
  - [ ] 403 → Show `Forbidden403Page` with "Zugriff verweigert" message
  - [ ] consent_required → Show `ConsentRequiredPage` blockierend
- [ ] Redirect-URL preservation:
  - [ ] User klickt auf `/vehicles` ohne Consent
  - [ ] → Er sieht ConsentPage
  - [ ] → Nach Accept → Er wird zurück zu `/vehicles` geleitet

**Test-Szenarios:**
- [ ] No Token + click #/vehicles → 401 + redirect to #/auth ✅
- [ ] After Consent not saved + click #/vehicles → consent_required page ✅
- [ ] Moderator + click #/vehicles → 403 Error ✅

---

### P1.2: Vehicles Core (Do 3/4 – Mo 3/15)

#### Di 3/9 – V1: Vehicles List (6-8h)

**Checklist:**
- [ ] Page Layout:
  - [ ] AppLayout (protected)
  - [ ] Header: "Meine Fahrzeuge"
  - [ ] ADD Button: "Fahrzeug hinzufügen"
- [ ] Fahrzeug-Grid (responsive 1-2-3 cols):
  - [ ] Fahrzeug Card mit:
    - [ ] VIN maskiert (first 3 + last 4, middle ****)
    - [ ] Modell/Marke
    - [ ] Baujahr
    - [ ] Trust-Ampel Badge (Grün/Gelb/Rot/Grau)
    - [ ] Click → Fahrzeug Detail Page
- [ ] EmptyState:
  - [ ] Icon + "Noch keine Fahrzeuge"
  - [ ] "Fahrzeug hinzufügen" Button
- [ ] Loading State:
  - [ ] Skeleton Cards while fetching `/vehicles`
- [ ] Error State:
  - [ ] Alert mit "Fehler beim Laden. Versuche später."
- [ ] Pagination/Infinite:
  - [ ] Show next 10 if >10 vorhanden
- [ ] Mobile responsive

**API Call:**
```
GET /vehicles
Response: [
  {
    id, vin, model, brand, year, trust_status: "t1|t2|t3",
    created_at, updated_at
  }
]
```

---

#### Mi 3/10 – V2: Vehicle Detail Header (5-7h)

**Checklist:**
- [ ] Page Layout:
  - [ ] AppLayout
  - [ ] Back Button → #/vehicles
- [ ] Vehicle Header Section:
  - [ ] VIN (maskiert)
  - [ ] Model/Brand/Year
  - [ ] Trust-Ampel (großes Badge, z.B. 48px)
  - [ ] Last Service date (if available)
  - [ ] Owner/buyer info (anonymized or just "Dein Fahrzeug")
- [ ] Tabs/Sections:
  - [ ] Tab1: **Fahrzeugakte** (Details)
  - [ ] Tab2: **Eintragung** (Timeline/Entries)
  - [ ] Tab3: **Archiv** (Deleted entries)
  - [ ] Tab4: **Rechnungen** (if available)
  - [ ] Tab5: **Dokumentation** (Files)
  - [ ] Tab6: **Galerie** (Photos)
  - [ ] Tab7: **Modul-Ereignisse** (System logs)
- [ ] Trust Widget:
  - [ ] Current Trust Status + Reason + To-Dos
- [ ] Loading/Error for each section

**API Call:**
```
GET /vehicles/{vehicle_id}
Response: {
  id, vin, model, brand, year, km_current,
  trust_status, trust_reasons,
  owner_id, created_at, updated_at
}
```

---

#### Mi 3/10 PM – V3: Timeline/Entries Tab (6-8h)

**Checklist:**
- [ ] Entries List (sorted by date DESC):
  - [ ] Entry Card mit:
    - [ ] Datum
    - [ ] Kategorie/Typ Badge (z.B. "Inspekion", "Reparatur")
    - [ ] km Kilometerstand
    - [ ] Durchgeführt von (z.B. "Fachwerkstatt")
    - [ ] Bemerkung (if exists)
    - [ ] Click → Edit/View Entry Detail (optional for P1)
- [ ] Add Entry Button:
  - [ ] Opens Modal/Form (see V4)
- [ ] EmptyState:
  - [ ] "Noch keine Einträge"
  - [ ] "Eintrag hinzufügen" Button
- [ ] Pagination:
  - [ ] Show 10 entries, Load More button
- [ ] Loading/Error states

**API Call:**
```
GET /vehicles/{vehicle_id}/entries
Response: [
  {
    id, vehicle_id, date, category, km, performed_by,
    remark, version, created_at, updated_at
  }
]
```

---

#### Do 3/11 – V4: Entry-Form Modal (6-8h)

**Checklist:**
- [ ] Form Fields (required if marked with *):
  - [ ] Datum * (Date input, default today)
  - [ ] Kategorie/Typ * (Select dropdown with options)
  - [ ] Kilometerstand * (Number input)
  - [ ] Durchgeführt von * (Select: Fachwerkstatt/Dealer/Eigenleistung/TÜV/...)
  - [ ] Bemerkung (Text textarea, optional)
  - [ ] Kostenbetrag (Number, optional, "wertsteigernd" hint)
  - [ ] Dokumente (File upload, optional)
- [ ] Validation:
  - [ ] All required fields checked
  - [ ] Datum not in future
  - [ ] km must be positive
  - [ ] Submit disabled until all required filled
- [ ] Submit Button:
  - [ ] Loading State
  - [ ] Success → Close modal + refresh entries list
  - [ ] Error → Show error message
- [ ] Cancel Button:
  - [ ] Close modal without saving

**API Call:**
```
POST /vehicles/{vehicle_id}/entries
Body: {
  date, category, km, performed_by, remark, cost_amount
}
Response: { id, ... (created entry) }
```

---

#### Fr 3/12 – V5: Documents Tab Übersicht (4-5h)

**Checklist:**
- [ ] Documents Section in Tabs:
  - [ ] "Dokumentation" tab
  - [ ] Counts anzeigen:
    - [ ] "5 Dokumente insgesamt"
    - [ ] "3 freigegeben" (Approved)
    - [ ] "2 in Überprüfung" (Pending/Quarantined)
  - [ ] Upload Button → opens upload modal (see D1)
  - [ ] Recent Documents list (last 5-10)
  - [ ] Each doc card:
    - [ ] Dateiname
    - [ ] Upload date
    - [ ] Status Badge (Quarantined/Pending/Approved/Infected)
    - [ ] File type icon (PDF, JPG, PNG, etc)
    - [ ] Download link (if Approved)
- [ ] EmptyState:
  - [ ] "Keine Dokumente"
  - [ ] "Dokument hochladen" Button

---

#### Mo 3/15 – V6: Create Vehicle Flow (5-6h)

**Checklist:**
- [ ] ADD Vehicle Button on Vehicles List:
  - [ ] Opens Modal with form
- [ ] Form Fields:
  - [ ] VIN * (Text input)
  - [ ] Marke * (Select)
  - [ ] Modell * (Text input)
  - [ ] Baujahr * (Year input)
  - [ ] Fahrzeugklasse (Select: Hypercar/Sport/Luxus/etc)
  - [ ] Kilometerstand * (Number)
- [ ] Validation:
  - [ ] VIN format check (basic)
  - [ ] All required fields
  - [ ] km >= 0
- [ ] Submit:
  - [ ] POST to `/vehicles`
  - [ ] Success → redirect to `/vehicles/{newId}`
  - [ ] Error → show error
- [ ] Cancel → close modal

**API Call:**
```
POST /vehicles
Body: {
  vin, brand, model, year, vehicle_class, km_current
}
Response: { id, vin, ... (created vehicle) }
```

---

### P1.3: Documents (Di 3/16 – Mi 3/17)

#### Di 3/16 – D1: Upload UX (6-8h)

**Checklist:**
- [ ] Upload Modal/Page:
  - [ ] Drag & Drop Zone (visual feedback on hover)
  - [ ] File Picker Button (fallback)
  - [ ] Progress Bar (while uploading)
  - [ ] File size limit: show max (e.g., 10MB)
  - [ ] Filetypen erlaubt: PDF, JPG, PNG only
  - [ ] Validierung:
    - [ ] Type check
    - [ ] Size check
  - [ ] Upload Status:
    - [ ] "Uploading..." + %
    - [ ] Success → "Dokument akzeptiert" + Close
    - [ ] Error → Show error message + Retry Button
- [ ] Multiple files:
  - [ ] Support drag-drop multiple (optional, single ok for P1)

**API Call:**
```
POST /documents
Headers: { Content-Type: multipart/form-data }
Body: { vehicle_id, file }
Response: {
  id, vehicle_id, filename, file_size,
  upload_date, status: "QUARANTINED",
  scan_status: "PENDING"
}
```

**Error Handling:**
- [ ] 400: Invalid file type → "Nur PDF, JPG, PNG erlaubt"
- [ ] 413: File too large → "Datei zu groß (max 10MB)"
- [ ] 500: Server error → "Fehler beim Upload, versuche später"

---

#### Mi 3/17 – D2-D4: Document Status/List (9-12h)

**Checklist:**

**D2: Status Badges**
- [ ] Status enum:
  - [ ] `QUARANTINED` (rot/orange) – "In Überprüfung"
  - [ ] `PENDING` (gelb) – "Scan läuft"
  - [ ] `CLEAN` (gelb->grün) – "Genehmigt"
  - [ ] `APPROVED` (grün) – "Freigegeben"
  - [ ] `INFECTED` (rot) – "Malware erkannt"
- [ ] Scan Status Mapping:
  - [ ] `PENDING` → Spinner Icon
  - [ ] `CLEAN` → Checkmark
  - [ ] `INFECTED` → X Icon

**D3: Download Link**
- [ ] Nur für `APPROVED` docs
- [ ] Download Button active/disabled
- [ ] Click → `/documents/{doc_id}/download` (with auth token)
- [ ] File downloads to browser

**D4: Document List**
- [ ] Documents for Vehicle:
  - [ ] List all docs
  - [ ] Sorted by upload_date DESC
  - [ ] Columns: Filename | Date | Status | Actions
  - [ ] Actions: Download | Delete (owner only)
- [ ] EmptyState: "Keine Dokumente"
- [ ] Pagination: Show 10 docs, Load More

**API Calls:**
```
GET /vehicles/{vehicle_id}/documents
Response: [
  {
    id, filename, file_size, upload_date,
    status: "QUARANTINED|PENDING|CLEAN|APPROVED|INFECTED",
    scan_status, created_by
  }
]

GET /documents/{doc_id}/download
Response: File blob + attachment headers
```

---

### P1.4: Public-QR Page (Do 3/18)

#### Do 3/18 – Q1-Q3: Public-QR View (12-16h)

**Checklist:**

**Q1: Public-QR View (Data-Arm)**
- [ ] Public URL: `/public/qr/{vehicle_id}`
- [ ] Data displayed:
  - [ ] VIN (maskiert: first 3 + ****, last 4)
  - [ ] Model + Brand + Year
  - [ ] Trust-Ampel (large badge, Grün/Gelb/Rot/Grau)
  - [ ] Trust-Reason (Top reason, no metrics/counts)
  - [ ] Unfallstatus Badge (if applicable)
  - [ ] Last service date (if available)
- [ ] Disclaimer (EXACT, unmodifizierbar):
  ```
  „Die Trust-Ampel bewertet ausschließlich die Dokumentations- 
   und Nachweisqualität. Sie ist keine Aussage über den 
   technischen Zustand des Fahrzeugs."
  ```
- [ ] NO Internal IDs visible
- [ ] NO PII (Adressen, Telefon, Namen)
- [ ] NO Links to private docs without auth
- [ ] NO Metrics (z.B. "80% confidence" → verboten)

**Q2: QR-Code Generierung**
- [ ] QR-Code Library hinzufügen (z.B. `qrcode.react`)
- [ ] QR encodes: `https://app.lifetimecircle.de/#/qr/vehicle_id`
- [ ] QR rendert auf page
- [ ] Size: ~200x200px default
- [ ] Copyable via button

**Q3: Print/Share Controls**
- [ ] Print Button:
  - [ ] Page looks good in print preview
  - [ ] QR lesbar, Disclaimer sichtbar
  - [ ] Keine Navigation headers/footers im Print
- [ ] Share Button:
  - [ ] Copy link to clipboard
  - [ ] Toast confirmation "Link kopiert"
  - [ ] Optional: Share to Social (Facebook/WhatsApp/etc)

**API Call:**
```
GET /public/vehicles/{vehicle_id}
Response: {
  vin_masked, brand, model, year,
  trust_status: "t1|t2|t3",
  trust_reason_top: "Wartung fehlerhaft|...",
  last_service_date,
  accident_history: bool
}
```

**Test-Szenario:**
- [ ] Generate QR-Link, share it
- [ ] Open link in incognito (no auth)
- [ ] See public view ✅
- [ ] Try to access private docs → 404 ✅
- [ ] Print → looks good ✅

---

### Fr 3/19 – P1 COMPLETE & E2E TEST

**Final Checklist P1:**
- [ ] All pages build + compile (0 TS errors)
- [ ] All E2E test scenarios pass:
  - [ ] Landing → Entry → Signup → Consent → Vehicles → Details → Entries → Upload → Download ✅
  - [ ] Public-QR (no auth) ✅
  - [ ] Moderator 403 on /vehicles ✅
  - [ ] 401 redirects to auth ✅
  - [ ] Mobile responsive all pages ✅
- [ ] No console errors
- [ ] No hardcoded values (all tokens)
- [ ] Lighthouse >70 on all key pages
- [ ] git diff clean, ready for PR

**PR Title:**
```
feat(web): P1 complete - MVP flows (Auth, Vehicles, Documents, QR)

This PR includes:
- Complete Auth + Consent flow
  - Signup/Login forms with validation
  - Token persistence + logout
  - Route guards (401/403)
- Vehicles core functionality
  - List, Detail, Create
  - Timeline/Entries CRUD
  - Documents tab with upload
- Public-QR page
  - Data-arm view (VIN masked)
  - Disclaimer exakt + unmodifizierbar
  - QR code + Print/Share
  - No auth required

All pages responsive, E2E >70%, Design-Tokens 100%.
Ready for P2: Admin + Quality.
```

---

## 🎨 PHASE P2: ADMIN & POLISH (Mi 3/24 – Mo 3/30)

### Mo 3/22 – P2.1.AD1-AD3: Admin Pages (15-20h)

**Checklist** (Details in Masterplan Document):
- [ ] Admin Rollen-Verwaltung
  - [ ] User list
  - [ ] Role selector
  - [ ] Moderator toggle
- [ ] Quarantine Review
  - [ ] Pending documents list
  - [ ] Approve/Reject buttons
  - [ ] Reason textarea
- [ ] Export-Full Step-Up
  - [ ] Only SUPERADMIN
  - [ ] UI Step-up flow
  - [ ] Download CSV/JSON

---

### Di 3/23 – P2.2.T1-T2: Trust/To-Dos (10-13h)

**Checklist:**
- [ ] Trust Widget on Vehicle Detail
- [ ] To-Do items (if applicable)
- [ ] Reason-Codes mapping

---

### Mi-Fr 3/24-28 – P2.3.Q1-Q5: Quality/Polish (25-32h)

**Checklist:**
- [ ] **Q1: Error Handling überall**
  - [ ] No blank screens
  - [ ] All API errors caught + displayed
  - [ ] Retry options where relevant
  - [ ] User knows what went wrong
- [ ] **Q2: Loading States**
  - [ ] Skeleton cards visible
  - [ ] No flash/flicker
  - [ ] Spinners in buttons if async
- [ ] **Q3: Mobile Responsive Final Pass**
  - [ ] 375px (iPhone SE)
  - [ ] 768px (iPad)
  - [ ] 1024px (iPad Pro)
  - [ ] 1920px (Desktop)
  - [ ] All layouts work
  - [ ] Touch targets >=44px
- [ ] **Q4: Lighthouse & Performance**
  - [ ] Score >80 (Performance, Accessibility, Best Practices)
  - [ ] LCP <2.5s
  - [ ] TTI <3.5s
  - [ ] CLS <0.1
  - [ ] Bundle <400KB gzipped
  - [ ] Images optimized
  - [ ] CSS critical extracted
- [ ] **Q5: E2E Coverage erweitern**
  - [ ] Admin flows
  - [ ] Export step-up
  - [ ] Trust widget
  - [ ] Mobile edge cases
  - [ ] Coverage >80%

---

### Mo 3/30 – 🚀 RELEASE READY

**Final Release Checklist:**
- [ ] `npm run build` – grün
- [ ] `npm run e2e` – alle tests grün
- [ ] Lighthouse all pages >80
- [ ] Zero console errors on production build
- [ ] All git commits pushed
- [ ] All code reviewed + approved
- [ ] Deployment checklist complete
- [ ] Team sign-off
- [ ] **GO / NO-GO Decision**

---

## 🔗 QUICK LINKS

| Resource | Link |
|----------|------|
| **Masterplan** | `docs/11_MASTERPLAN_FINALISIERUNG.md` |
| **Timeline** | `docs/11_MASTERPLAN_ROADMAP_VISUAL.md` |
| **Web Guide** | `packages/web/WEBDESIGN_GUIDE.md` |
| **Design System** | Visit `http://localhost:5173/#/design-system-reference` |
| **Backend Docs** | `server/README.md` |
| **API Spec** | `http://localhost:8000/redoc` |

---

## 📞 CONTACT & SUPPORT

- **Primary Dev:** Sie
- **Backend Dev:** (falls 2-Dev Team)
- **QA/Testing:** (falls 3-Dev Team)
- **Daily Standup:** 9:00 CET
- **Emergency Contact:** lifetimecircle@online.de

---

**Last Updated:** 2026-02-28  
**Next Review:** Daily standup (9:00 CET)  
**Status:** 🟢 Ready to Start
