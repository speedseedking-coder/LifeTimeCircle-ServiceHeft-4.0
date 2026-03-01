# 🔧 START CARD – FIXES ABARBEITEN
## LifeTimeCircle Service Heft 4.0 – Fix-Tracking mit CODEX

**Stand: 2026-02-28 | Abgleich mit realem Web-Stand**

---

## 📊 FIX-STATUS ÜBERBLICK

### Reeller Stand im Repo

- ✅ P0-Webseite ist nicht mehr Startpunkt, sondern weitgehend umgesetzt: Landing, Entry, FAQ, Jobs, Impressum, Datenschutz, Contact und Cookies sind verdrahtet.
- ✅ Public Contact ist vorhanden und per E2E abgesichert.
- ✅ `#/entry` ist vorhanden, live verdrahtet und per E2E abgesichert.
- ✅ `App.tsx` wurde bereits stark entlastet; Public-Seiten sind modularisiert, Cookie-Seite/-Card werden separat geführt.
- ✅ Große Teile von P1 sind bereits im Code vorhanden: Auth/Consent/Gates, Vehicles, Documents, Admin, Trust Folders und Public QR.
- ✅ Verifizierter Web-Stand nach dem Cookie-Refactor: `npm run build` grün, `npm run e2e` grün mit 17/17.
- ⏳ Offener Fokus liegt nicht mehr auf P0-Basisarbeiten, sondern auf Rest-Modularisierung, Abgleich der Plan-Dokumente und den verbleibenden P1/P2-Lücken.

---

## 🚀 QUICK LINKS (Deine täglichen Werkzeuge)

| Was | Wo | Nutzen für |
|-----|-----|-----------|
| **Cheatsheet** | `docs/11_MASTERPLAN_CODEX_CHEATSHEET.md` | RBAC-Checks, Harte Invarianten |
| **Daily Checklist (heute)** | `docs/11_MASTERPLAN_DAILY_CHECKLIST.md` | Konkrete Tasks mit Checkboxes |
| **RIGHTS_MATRIX** | `docs/03_RIGHTS_MATRIX.md` | Route-Checks vor Implementation |
| **PRODUCT_SPEC** | `docs/02_PRODUCT_SPEC_UNIFIED.md` | Was ist die Anforderung? |
| **Diese Card** | `docs/11_MASTERPLAN_FIX_CARD.md` | Overall Fix-Status tracken |

---

## 🟢 P0 PHASE: WEBSEITE (Mo 3/1 – Do 3/4)

### ✅ DONE – Gar nicht mehr anfassen!

**1. Backend-API: Design System + Assets**
- Status: ✅ COMPLETE
- Was: API listet Komponenten, Colors, Tokens
- Wer: Backend-Dev (schon fertig)
- Evidence: `/api/design-system/tokens`, `/api/design-system/components` lädt

**2. Web: React + TypeScript + Build**
- Status: ✅ COMPLETE
- Was: Vite-Setup, npm run build grün, no errors
- Wer: Frontend-Setup (bereits done)
- Evidence: `npm run build` erfolgreich, 53 modules transformed

**3. Web: Design Tokens CSS**
- Status: ✅ COMPLETE
- Was: `tokens.css` mit 300+ CSS Custom Properties
- Colors, Typography, Spacing, Shadows – ALLES TOKEN-BASED
- Wer: Design-System Developer (bereits done)
- Evidence: `packages/web/src/styles/tokens.css` vorhanden + importiert

**4. Web: UI Component Library (8 Components)**
- Status: ✅ COMPLETE
- Was: Button, Input, Card, Badge, Alert, Checkbox, Skeleton, Loading
- Design-React Components mit Variants/Sizes
- Wer: Component Developer (bereits done)
- Evidence: `packages/web/src/components/ui/` mit 8 .tsx files

**5. Web: Layout System**
- Status: ✅ COMPLETE
- Was: PublicLayout, Header, Footer, Layout CSS (400 lines)
- Responsive grid/flex utilities
- Wer: Layout Developer (bereits done)
- Evidence: `packages/web/src/components/layout/` + `layout.css`

### 🔄 CURRENT – Tatsächlicher Fokus 2026-02-28

**Bereits umgesetzt im Web**
- [x] Landing Page mit CTA auf `#/entry`
- [x] Öffentliche Navigation/Footer-Shell
- [x] `#/entry` als funktionale Public-Route
- [x] FAQ, Jobs, Impressum, Datenschutz, Contact und Cookies öffentlich erreichbar
- [x] Public Contact und Entry per E2E abgedeckt
- [x] Build und E2E nach dem Cookie-Refactor erneut grün verifiziert

**Gerade laufende Restarbeiten**
- [x] `CookiesPage` und `CookieSettingsCard` aus `App.tsx` ausgelagert
- [x] Landing, Public-Debug-/Blog-/News-Helfer und App-Shell-CSS aus `App.tsx` ausgelagert
- [x] Routing-/Background-Helfer, Gate-Logik und Scaffold-Shell aus `App.tsx` in `lib`/`hooks`/`components` ausgelagert
- [x] Verbleibende Scaffold-Routen in eigene Pages und zentralen `AppRouteRenderer` ausgelagert
- [x] `AppScaffoldShell` weiter zerlegt und explizite `notFound`-Fallback-Route eingeführt
- [x] System-State-Seiten vereinheitlicht und `notFound` per E2E zusätzlich abgesichert
- [x] `App.tsx` auf Routing, Gate-Logik und Public-/App-Verdrahtung reduziert
- [x] Build/E2E nach den Refactors erneut verifizieren (`18/18`)

**Nächster inhaltlicher Fokus**
- [ ] Dokumentierten IST-Stand weiter an P1/P2-Restlücken angleichen
- [ ] Verbleibende Vehicle/Documents/Public-QR-Vertiefungen priorisieren
- [ ] Zusätzliche E2E-Abdeckung entlang der produktiven Flows ausbauen

---

## 🟡 P1 PHASE: MVP FLOWS (Fr 3/5 – Fr 3/19)

### ⏳ AUTH & CONSENT (11-12h, Fr 3/5 – Do 3/6)

**A1: Auth Page (Signup/Login)** (6-8h)
- [ ] Route: `/auth`
- [ ] Sections:
  - [ ] Signup form (Email, Password, Name, VIN)
  - [ ] Login form (Email, Password)
  - [ ] Link between tabs
- [ ] Validation:
  - [ ] Email format
  - [ ] Password strength
  - [ ] VIN format (if applicable)
- [ ] Errors: Show error cards + messages
- [ ] API calls:
  - [ ] POST `/auth/signup` with payload
  - [ ] POST `/auth/login` with payload
- [ ] Store: Save token to localStorage
- [ ] Route guard: If authenticated → redirect to `/consent` OR dashboard
- [ ] CODEX-Check: Server enforces RBAC, not client
- [ ] Commit: `feat(web): add auth page with signup/login forms (P1-A1)`

**A2: Consent Page** (5-6h)
- [ ] Route: `/consent`
- [ ] Show: AGB, Datenschutz, Impressum (from API OR bundled)
- [ ] MUST: Accept checkbox required
- [ ] Design: Card-based, clear Accept button
- [ ] API: POST `/consent/accept` → set consent flag
- [ ] Redirect: After accept → `/vehicles` (dashboard)
- [ ] CODEX-Check: Server gates with `consent_required`
- [ ] Commit: `feat(web): add consent page with acceptance flow (P1-A2)`

**A3: Token Persistence** (3-4h)
- [ ] localStorage: Save token after login
- [ ] localStorage: Remove token after logout
- [ ] Refresh: Check token on app init
- [ ] Expiry: Show warning if token near expiry
- [ ] Session: Re-authenticate if expired
- [ ] CODEX-Check: No PII stored in localStorage
- [ ] Commit: `feat(web): add token persistence + logout (P1-A3)`

**A4: Auth Guards** (4-5h)
- [ ] Protected routes: Check auth before render
- [ ] Action: Redirect to `/auth` if not authenticated (401 → Guard)
- [ ] Consent gate: Redirect to `/consent` if `consent_required` (403 → Guard)
- [ ] Admin gate: Redirect to `/forbidden` if insufficient role (403 → Guard)
- [ ] Tests: E2E test all guard paths
- [ ] Commit: `feat(web): add auth + role guards (P1-A4)`

### ⏳ VEHICLES CORE (32h, Mo 3/9 – Mo 3/17)

**V1: Vehicle List** (6-8h)
- [ ] Route: `/vehicles`
- [ ] API: GET `/vehicles`
- [ ] Display: Cards with VIN, Make, Model, Year
- [ ] Masking: Show only last 4 of VIN (e.g., "***XXXX")
- [ ] Grid: Responsive 2-column (mobile) → 3-column (desktop)
- [ ] Empty State: Show if user has 0 vehicles
- [ ] Loading State: Skeleton cards while fetching
- [ ] Pagination: If >10 vehicles
- [ ] CODEX-Check: Nur egene Fahrzeuge (object-level)
- [ ] Commit: `feat(web): add vehicle list with grid layout (P1-V1)`

**V2: Vehicle Detail Header** (5-7h)
- [ ] Route: `/vehicles/:id`
- [ ] Header: VIN (masked), Make, Model, Year, Created-date
- [ ] Trust-Ampel: Shows current status (green/yellow/red/gray)
- [ ] Tabs/Sections: Entries, Documents, Timeline, Settings
- [ ] API: GET `/vehicles/:id`
- [ ] Trust-Widget: Shows top reasons for current state
- [ ] CODEX-Check: Moderator 403, Object-level check
- [ ] Commit: `feat(web): add vehicle detail header with trust status (P1-V2)`

**V3: Vehicle Timeline** (6-8h)
- [ ] Entries list sorted by date (newest first)
- [ ] Card per entry: Date, Type, Mileage, Status
- [ ] Add button: Navigate to form
- [ ] Pagination: Show 5 per page
- [ ] Loading: Skeleton while fetching
- [ ] API: GET `/vehicles/:id/entries`
- [ ] CODEX-Check: Only object-owner entries shown
- [ ] Commit: `feat(web): add vehicle entries timeline (P1-V3)`

**V4: Entry Form** (6-8h)
- [ ] Route: `/vehicles/:id/entry/new` OR modal
- [ ] Form Fields:
  - [ ] Date (Pflichtfeld)
  - [ ] Type (selection from enum)
  - [ ] Durchgeführt von (user name)
  - [ ] Kilometerstand (number)
  - [ ] Notes (textarea, optional)
  - [ ] Photos/attachments (optional)
- [ ] Validation: All Pflichtfelder required
- [ ] API: POST `/vehicles/:id/entries` with payload
- [ ] Success: Redirect to `/vehicles/:id` + show success toast
- [ ] Error: Show error card with message
- [ ] CODEX-Check: No PII in form data
- [ ] Commit: `feat(web): add entry creation form (P1-V4)`

**V5: Documents Tab** (4-5h)
- [ ] Show count of documents in header
- [ ] List: Recent documents (3-5 most recent)
- [ ] Empty state: "Keine Dokumente" with upload CTA
- [ ] Upload button: Leads to file picker
- [ ] CODEX-Check: Uploads quarantined by default (show "Scanning..." state)
- [ ] Commit: `feat(web): add documents tab to vehicle detail (P1-V5)`

**V6: Create Vehicle** (5-6h)
- [ ] Route: Modal OR `/vehicles/new`
- [ ] Form:
  - [ ] VIN (required, format validation)
  - [ ] Make/Marke (required)
  - [ ] Model (required)
  - [ ] Year (required)
- [ ] Validation: All required
- [ ] API: POST `/vehicles` with payload
- [ ] Success: Redirect to new vehicle detail
- [ ] CODEX-Check: Form data encrypted in transit (HTTPS only)
- [ ] Commit: `feat(web): add create vehicle form (P1-V6)`

### ⏳ DOCUMENTS (15h, Di 3/11 – Mi 3/12)

**D1: Upload UX** (6-8h)
- [ ] Route: `/vehicles/:id/documents/upload` OR modal
- [ ] Drag-drop zone + file picker
- [ ] Show: File name, size, preview (if image)
- [ ] Validation: File type (image/PDF), max size
- [ ] Progress bar: During upload
- [ ] API: POST `/documents/upload`
- [ ] Status: Success message + list updates
- [ ] Error: Show error card (file too large, invalid type, etc.)
- [ ] CODEX-Check: Server quarantines automatically (show "Scanning..." UI state)
- [ ] Commit: `feat(web): add document upload with drag-drop (P1-D1)`

**D2: Document Status Display** (4-5h)
- [ ] Show status indicator: QUARANTINED (scanning), CLEAN (approved), INFECTED (rejected)
- [ ] Badge variants: yellow/green/red
- [ ] Admin only: See QUARANTINED docs + manual approve/reject
- [ ] User: Only see APPROVED docs
- [ ] API: GET `/documents/:id/status`
- [ ] CODEX-Check: Exports redacted for non-admin (status=INFECTED hidden)
- [ ] Commit: `feat(web): add document status badges (P1-D2)`

**D3: Download + Sharing** (4-5h)
- [ ] Download button: GET `/documents/:id/download`
- [ ] Share link: Copy public URL OR QR
- [ ] Share modal: Show link preview
- [ ] Permissions: Only APPROVED + object-owner + scope OK
- [ ] CODEX-Check: Server enforces download gating
- [ ] Commit: `feat(web): add document download + sharing (P1-D3)`

**D4: Document List** (2-3h)
- [ ] Page: `/vehicles/:id/documents` (list all)
- [ ] Table OR cards: Document name, date, type, status
- [ ] Filter: By type (invoice, service record, etc.)
- [ ] Pagination: 10 per page
- [ ] Empty state: "Keine Dokumente"
- [ ] Commit: `feat(web): add document list view (P1-D4)`

### ⏳ PUBLIC-QR (12h, Mi 3/13 – Do 3/14)

**Q1: Data-Arm Public View** (6-8h)
- [ ] Route: `/public/qr/:qr_token` (NO auth required)
- [ ] Display: VIN (masked), Trust-Ampel, Top 3 reasons
- [ ] Design: Simple, clean, printable
- [ ] MUST: Disclaimer text EXAKT (copy-paste from 00_CODEX_CONTEXT.md):
  > „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."
- [ ] CODEX-Check: No PII (except masked VIN), no metrics, no user data
- [ ] API: GET `/public/qr/:qr_token`
- [ ] Commit: `feat(web): add public qr view with disclaimer (P1-Q1)`

**Q2: QR Code Generation** (3-4h)
- [ ] Library: Use `qrcode.react` or similar
- [ ] Generate: QR from token/URL
- [ ] Size: Adjustable (for print OR screen)
- [ ] Copy: Button to copy URL
- [ ] API: GET `/public/qr/generate` returns token
- [ ] Commit: `feat(web): add qr code generation (P1-Q2)`

**Q3: Print + Share** (3-4h)
- [ ] Print CSS: Print page without UI chrome
- [ ] Share button: Opens share sheet (Email, WhatsApp, etc.)
- [ ] Share URL: Customer-friendly short link
- [ ] Preview: Show what shared URL looks like
- [ ] Commit: `feat(web): add print + share functionality (P1-Q3)`

---

## 🔵 P2 PHASE: ADMIN + QUALITY (Mo 3/22 – Mo 3/30)

### ⏳ ADMIN PAGES (15-20h, Mo 3/22 – Tu 3/23)

**AD1: Rollen-Management** (6-8h)
- [ ] Route: `/admin/roles` (admin-only)
- [ ] List: All roles, member count, actions
- [ ] Create: New role (name, permissions)
- [ ] Edit: Update role permissions
- [ ] Delete: Remove role (with safeguards)
- [ ] CODEX-Check: Superadmin-only gate on backend
- [ ] Tests: Moderator 403 on this route
- [ ] Commit: `feat(web): add admin role management (P2-AD1)`

**AD2: Quarantine Review** (5-7h)
- [ ] Route: `/admin/documents/quarantine`
- [ ] List: All QUARANTINED documents
- [ ] Actions: Approve (→CLEAN) OR Reject (→INFECTED)
- [ ] Reason: Show scan report
- [ ] Bulk actions: Select multiple + batch approve/reject
- [ ] API: PATCH `/documents/:id/scan-result`
- [ ] CODEX-Check: Admin/Superadmin only
- [ ] Commit: `feat(web): add quarantine review page (P2-AD2)`

**AD3: Full Export** (4-5h)
- [ ] Route: `/admin/export` (admin-only)
- [ ] Export formats: JSON, CSV, Excel
- [ ] Scope: All vehicles, all entries, all documents
- [ ] Filters: Date range, user, vehicle
- [ ] Password protection: Optional encryption for export
- [ ] Download: Trigger file download
- [ ] CODEX-Check: Redacted for non-admin (PII removed)
- [ ] Commit: `feat(web): add admin export functionality (P2-AD3)`

### ⏳ TRUST & TO-DOS (10-13h, We 3/24)

**T1: Trust-Widget Display** (6-8h)
- [ ] Show: Top reasons for current Trust status
- [ ] Design: Card with reasons + severity badges
- [ ] Interaction: Click to expand details
- [ ] VIP mode: Show top 3 only
- [ ] Non-VIP mode: Show all
- [ ] API: GET `/trust/:vehicle_id/summary`
- [ ] CODEX-Check: Moderator 403
- [ ] Commit: `feat(web): add trust status widget (P2-T1)`

**T2: To-Do Reason Codes** (4-5h)
- [ ] Show: List of reason codes (e.g., "Oil Change Overdue", "Service Needed")
- [ ] Action: User can mark as resolved
- [ ] UI: Checklist with completion tracking
- [ ] Color coding: By urgency/category
- [ ] API: GET/PATCH `/trust/reason-codes/:id`
- [ ] CODEX-Check: Owner-only access
- [ ] Commit: `feat(web): add to-do reason code tracking (P2-T2)`

### ⏳ QUALITY + FINALIZATION (25-32h, Th 3/25 – Mo 3/30)

**Q1: Error Handling** (6-8h)
- [ ] All 4xx pages: 401, 403, 404, 5xx
- [ ] Design: Consistent error cards with CTA
- [ ] Messages: User-friendly, local language
- [ ] Logging: Error tracking (Sentry/similar)
- [ ] CODEX-Check: No PII in error messages
- [ ] Tests: E2E test error paths
- [ ] Commit: `fix(web): comprehensive error page handling (P2-Q1)`

**Q2: Loading States** (4-5h)
- [ ] Skeleton screens: All data-heavy pages
- [ ] Animations: Smooth transitions
- [ ] Delays: Show after 200ms (not immediate)
- [ ] Timeouts: Show error if >10s loading
- [ ] CODEX-Check: No PII in loading states
- [ ] Commit: `fix(web): add skeleton loading states (P2-Q2)`

**Q3: Mobile Responsive** (6-8h)
- [ ] Test: 375px (iPhone SE), 375px (iPhone 12), 768px (iPad)
- [ ] Touch: Proper button sizes (>44px)
- [ ] Navigation: Mobile menu working
- [ ] Forms: Responsive input layout
- [ ] Images: Scale correctly
- [ ] Commit: `fix(web): ensure full mobile responsiveness (P2-Q3)`

**Q4: Lighthouse + Performance** (5-6h)
- [ ] Performance: >75 (desktop), >60 (mobile)
- [ ] Accessibility: >85
- [ ] Best Practices: >85
- [ ] SEO: >85
- [ ] Optimizations: Code splitting, lazy load, image optimization
- [ ] Commit: `perf(web): lighthouse optimization to >75 (P2-Q4)`

**Q5: E2E Tests + Security Scan** (5-6h)
- [ ] E2E: Playwright tests for critical flows
  - [ ] Auth → Consent → Vehicle List → Create Vehicle
  - [ ] Token expiry + re-auth
  - [ ] Error pages (401, 403, 404)
  - [ ] Public QR access (no auth)
- [ ] Security: Run security audit
  - [ ] no PII in localStorage/cookies
  - [ ] CSP headers correct
  - [ ] Moderator 403 coverage
- [ ] Commit: `test(web): comprehensive e2e + security tests (P2-Q5)`

---

## ✅ RELEASE READINESS CHECKLIST

**Code Quality:**
- [ ] TypeScript: 0 errors, 0 warnings
- [ ] Linting: All files pass ESLint/Prettier
- [ ] Build: `npm run build` succeeds, <1min
- [ ] Bundle: CSS <50KB gzip, JS <300KB gzip
- [ ] Tests: E2E Playwright >80% coverage

**Performance:**
- [ ] Lighthouse: Desktop >80, Mobile >70
- [ ] Load time: <2s initial, <1s SPA navigation
- [ ] Metrics: LCP <2.5s, FID <100ms, CLS <0.1

**Security:**
- [ ] RBAC: Moderator 403 on all non-Allowlist routes ✅
- [ ] PII: No PII in logs, localStorage, exports ✅
- [ ] Tokens: Secure storage, expiry handling ✅
- [ ] Uploads: Quarantined by default ✅
- [ ] QR Disclaimer: EXAKT unverändert ✅

**UX:**
- [ ] Responsive: 375px, 768px, 1024px, 1920px ✅
- [ ] Mobile: Touch-friendly, proper sizes ✅
- [ ] Accessibility: ARIA labels, keyboard nav ✅
- [ ] Error pages: 401, 403, 404, 5xx all styled ✅
- [ ] Loading: Skeleton states, <10s timeouts ✅

**Compliance:**
- [ ] Legal: AGB, Datenschutz, Impressum pages ✅
- [ ] API: All endpoints match OpenAPI spec ✅
- [ ] DB: Migrations tested, backups working ✅
- [ ] Monitoring: Error tracking set up (Sentry) ✅

---

## 🎯 DEIN TÄGLICHES RITUAL

### Jeden Morgen (5 min):
```bash
# 1. Check diese Card (FIX_CARD.md)
# → Welche Phase? Welche Tasks pending?

# 2. Check Daily Checklist
# → Heute's konkreter Task

# 3. Check Status
git status
git fetch origin
# → Local clean? What changed overnight?
```

### Beim Start eines neuen Task (2 min):
```bash
# 1. Lese diese Card für den Task
# → Was ist Definition of Done?

# 2. Lese 03_RIGHTS_MATRIX.md
# → Welche Route? Moderator OK?

# 3. Create branch
git checkout -b feat/web-p1-[taskname]

# 4. Start coding + Checklist abhaken
```

### Vor Commit (5 min):
```bash
# 1. CODEX-Check (Cheatsheet):
# → RBAC? PII? Design Tokens? No hardcoding?

# 2. Test build
npm run build

# 3. Responsive test (DevTools)
# → 375px + 768px + 1024px OK?

# 4. Commit + Push
git commit -m "feat/fix(web): [description] (P[phase]-[task])"
git push origin [branch]
```

---

## 📞 WENN DU FESTSTECKST

| Problem | Lös |
|---------|-----|
| "Welche Route?" | → 03_RIGHTS_MATRIX.md |
| "Moderator OK?" | → CODEX Sektion 1, Punkt 3 |
| "Komponente?" | → packages/web/WEBDESIGN_GUIDE.md |
| "API-Call?" | → http://localhost:8000/redoc |
| "PII-Check?" | → CODEX_CHEATSHEET.md |
| "Build error?" | → npm run build, check TS errors |
| "E2E failing?" | → Check test output, API mocked? |

---

## 🚀 MOMENTUM HALTEN

```
Woche 1 (3/1-3/4):   P0 Webseite       → Landing + Entry → 28h
Woche 2-3 (3/5-3/19): P1 MVP Flows      → Auth + Vehicles + Docs → 89h
Woche 4-5 (3/22-3/30): P2 Admin+Polish  → Quality + Release → 57h

TOTAL: 174h ~= ~22-23 Tage (1 Dev)
        ~= ~12-14 Tage (2 Devs parallel)

🎯 FINISH DATE: 2026-03-30 (Go-Live Ready!)
```

---

**Du packst das! Jeder Fix ein Stück näher zum Release! 🚀**

**Fragen? → Cheatsheet + Daily Standup + #help Slack**
