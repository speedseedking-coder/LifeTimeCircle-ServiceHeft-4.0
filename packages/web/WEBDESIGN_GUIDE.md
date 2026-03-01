/**
 * Web-Frontend Entwickler-Guide
 * LifeTimeCircle – Service Heft 4.0
 * 
 * Stand: 2026-02-28
 */

# Web-Frontend Setup & Komponenten-Guide

## 1) Quick Start

```bash
# Dependencies installieren
cd packages/web
npm ci

# Development starten
npm run dev

# Build testen
npm run build

# E2E Tests laufen
npm run e2e
```

### Browser öffnen
- Dev Server: http://localhost:5173
- Backend API: http://localhost:8000 (CORS already configured)

---

## 2) Projektstruktur

```
packages/web/
├── src/
│   ├── styles/                    # Design System
│   │   ├── tokens.css            # CSS Custom Properties (Farben, Spacing, Typo)
│   │   ├── components.css        # UI-Kit Komponenten (Button, Input, Card, etc.)
│   │   └── layout.css            # Layout (Header, Footer, Grid, Container)
│   │
│   ├── components/
│   │   ├── ui/                    # Reusable UI Components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Alert.tsx
│   │   │   ├── Checkbox.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── layout/                # Layout Components
│   │   │   ├── AppLayout.tsx     # For app pages (protected)
│   │   │   ├── PublicLayout.tsx  # For public pages
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── ForbiddenPanel.tsx    # Error panels
│   │   └── TrustAmpelDisclaimer.tsx
│   │
│   ├── pages/                     # Page Components
│   │   ├── AuthPage.tsx
│   │   ├── ConsentPage.tsx
│   │   ├── VehiclesPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── Unauthorized401Page.tsx
│   │   ├── Forbidden403Page.tsx
│   │   ├── ConsentRequiredPage.tsx
│   │   ├── NotFound404Page.tsx
│   │   └── ...
│   │
│   ├── hooks/
│   │   └── useHash.ts           # Hash-based routing
│   │
│   ├── lib/
│   │   └── lib.auth.ts          # Auth helpers
│   │
│   ├── api*.ts                  # API clients
│   ├── App.tsx                  # Main app shell + routing
│   ├── main.tsx                 # Entry point
│   └── styles.css               # Main stylesheet (imports all)
```

---

## 3) Design System (Tokens)

Alle visuellen Attribute sind als CSS Tokens zentral definiert:

```css
/* In packages/web/src/styles/tokens.css */

:root {
  /* Spacing */
  --ltc-space-2: 0.5rem;      /* 8px */
  --ltc-space-4: 1rem;        /* 16px */
  --ltc-space-6: 1.5rem;      /* 24px */
  
  /* Farben */
  --ltc-color-brand: #7aa2f7;
  --ltc-color-success: #34d399;
  --ltc-color-warning: #fbbf24;
  --ltc-color-error: #f87171;
  
  /* Trust Ampel */
  --ltc-color-trust-green: #34d399;
  --ltc-color-trust-yellow: #fbbf24;
  --ltc-color-trust-red: #f87171;
  
  /* Typo */
  --ltc-text-sm: 0.875rem;
  --ltc-h1-size: 2.25rem;
}
```

**Regel:** Nutze immer Tokens, nie hardcoded values!

---

## 4) UI-Komponenten nutzen

### Button

```tsx
import { Button } from "../components/ui/Button";

<Button variant="primary" size="base">
  Klick mich
</Button>

<Button variant="secondary" disabled>
  Deaktiviert
</Button>

<Button loading>
  Wird geladen...
</Button>
```

**Props:**
- `variant`: "primary" | "secondary" | "danger" | "ghost"
- `size`: "sm" | "base" | "lg"
- `disabled`, `loading`: boolean
- `type`: "button" | "submit" | "reset"

### Input

```tsx
import { Input } from "../components/ui/Input";

<Input
  label="Name"
  placeholder="Dein Name"
/>

<Input
  label="E-Mail"
  type="email"
  error="Ungültige E-Mail"
/>

<Input
  label="Passwort"
  hint="Mindestens 8 Zeichen"
  required
/>
```

**Props:**
- `label`, `error`, `hint`: string
- `icon`: ReactNode
- `loading`: boolean
- Alle standard HTML input attributes

### Card

```tsx
import { Card } from "../components/ui/Card";

<Card>
  <h3>Inhalt</h3>
  <p>Das ist eine Card.</p>
</Card>

<Card interactive hoverable>
  Interaktive Card
</Card>
```

### Badge (Status)

```tsx
import { Badge } from "../components/ui/Badge";

<Badge variant="success">Genehmigt</Badge>
<Badge variant="warning">Überprüfung ausstehend</Badge>
<Badge variant="error">Fehler</Badge>

{/* Trust Ampel */}
<Badge variant="trust-green">Grün</Badge>
<Badge variant="trust-yellow">Gelb</Badge>
<Badge variant="trust-red">Rot</Badge>
```

### Alert

```tsx
import { Alert } from "../components/ui/Alert";

<Alert variant="info" title="Hinweis">
  Informationen für den Nutzer
</Alert>

<Alert variant="error" dismissible onDismiss={() => {}}>
  Fehler, den man schließen kann
</Alert>
```

### Checkbox

```tsx
import { Checkbox } from "../components/ui/Checkbox";

<Checkbox label="Ich stimme zu" />
<Checkbox label="Error" error="Du musst kurieren" />
```

### EmptyState

```tsx
import { EmptyState } from "../components/ui/Skeleton";

<EmptyState
  icon="📁"
  title="Keine Daten"
  description="Du hast noch keine Fahrzeuge."
  action={<Button>Hinzufügen</Button>}
/>
```

### Skeleton (Loading Placeholder)

```tsx
import { Skeleton } from "../components/ui/Loading";

<Skeleton count={3} />
<Skeleton width="200px" height="40px" />
```

---

## 5) Layouts verwenden

## 5.1) Background-Assets

Das Objekt `BG` in `App.tsx` enthält Pfade zu Hintergrundbildern, die wir für
statische Seiten nutzen. Wenn du ein neues Page-Design erstellst, füge hier ein
neues Feld hinzu (z. B. `contact`) und stell sicher, dass das Asset unter
`public/images/` liegt.

Beispiel:

```ts
const BG = {
  ...
  contact: "/images/contact.png", // neues Asset für ContactPage
};
```

(Farbton/Opacity kann in `getBgForRoute()` gesteuert werden.)


### PublicLayout (für öffentliche Seiten)

```tsx
import { PublicLayout } from "../components/layout/PublicLayout";
import { Header } from "../components/layout/Header";
import { Footer } from "../components/layout/Footer";

export function HomePage() {
  return (
    <PublicLayout
      header={
        <Header
          logo="LifeTimeCircle"
          nav={<nav>Links</nav>}
          actions={<Button>Anmelden</Button>}
        />
      }
      footer={<Footer />}
    >
      {/* Seiteninhalt */}
    </PublicLayout>
  );
}
```

### AppLayout (für geschützte Seiten)

```tsx
import { AppLayout } from "../components/layout/AppLayout";

export function VehiclesPage() {
  return (
    <AppLayout
      variant="plain"
      header={/* optional */}
      container
      containerClassName="ltc-container"
    >
      <h1>Meine Fahrzeuge</h1>
      {/* Inhalt */}
    </AppLayout>
  );
}
```

---

## 6) Error Pages

Import the error pages:

```tsx
import { Unauthorized401 } from "../pages/Unauthorized401Page";
import { Forbidden403 } from "../pages/Forbidden403Page";
import { ConsentRequiredPage } from "../pages/ConsentRequiredPage";
import { NotFound404 } from "../pages/NotFound404Page";
```

In routing logic:

```tsx
function renderPage(route) {
  if (route.kind === "auth") {
    return isAuthenticated ? redirect to #/vehicles : <AuthPage />;
  }
  if (!isAuthenticated) {
    return <Unauthorized401 />;
  }
  if (!hasConsent) {
    return <ConsentRequiredPage returnTo={window.location.hash} />;
  }
  if (!hasPermission) {
    return <Forbidden403 reason="Du hast nicht die erforderlichen Rechte." />;
  }
  // ...
}
```

---

## 7) CSS Klassen (Layout Utilities)

```tsx
/* Spacing */
.ltc-mt-2, .ltc-mt-4, .ltc-mt-6, .ltc-mt-8
.ltc-mb-2, .ltc-mb-4, .ltc-mb-6, .ltc-mb-8
.ltc-p-4, .ltc-p-6

/* Grid */
.ltc-grid--2        /* 2 columns, responsive */
.ltc-grid--3        /* 3 columns, responsive */

/* Flex */
.ltc-flex           /* flex container */
.ltc-flex--col      /* flex-direction: column */
.ltc-flex--wrap     /* flex-wrap: wrap */

/* Text */
.ltc-text-muted     /* Muted text color */
.ltc-text-faint     /* Very faint text color */
.ltc-h1, .ltc-h2, .ltc-h3, .ltc-h4

/* Container */
.ltc-container      /* max-width: 1200px */
.ltc-container-small /* max-width: 800px */
```

### Beispiel:

```tsx
<div className="ltc-grid--2 ltc-mt-8">
  <Card>...</Card>
  <Card>...</Card>
</div>
```

---

## 8) API Integration

Alle API Calls gehen über die Helper in `src/api*.ts`:

```tsx
import { apiGet, apiPost } from "../api";

// GET request
const vehicles = await apiGet("/vehicles");

// POST request
const saved = await apiPost("/vehicles", { name: "BMW X5" });
```

Auth-Token wird automatisch als `Authorization: Bearer` Header attached.

---

## 9) Checkliste: Bevor du mit Page-Entwicklung startest

- [ ] Design Tokens verstanden (Token-Naming, Usage)
- [ ] UI-Komponenten getestet (buttons, inputs, cards)
- [ ] Layouts reviewed (PublicLayout vs AppLayout)
- [ ] Error-Flows verstanden (401, 403, ConsentRequired)
- [ ] Build läuft grün (npm run build)
- [ ] E2E Tests passen (npm run e2e)

---

## 10) Nächste Schritte (P1-P2)

**P1 – MVP Pages:**
- [ ] Landing/Home Page mit PublicLayout
- [ ] Vehicles List + Detail Page mit AppLayout
- [ ] Documents Upload UX
- [ ] Entry-Form (Timeline)

**P2 – Vorbereitung:**
- [ ] Trust/To-Dos Widget Struktur
- [ ] Admin Pages scaffold
- [ ] Mobile Responsive checks

---

## 11) Hilfreiche Commands

```bash
# Dev Server
npm run dev

# Build (production)
npm run build

# Private staging preview
npm run preview

# E2E Tests
npm run e2e

# Build sizes
npm run build -- --report=size   # (wenn configured)

# TypeScript Check
npx tsc --noEmit

# Vite Config Check
cat vite.config.ts
```

---

## 12) Best Practices

1. **No Magic Numbers:** Nutze immer `var(--ltc-space-*)`, nicht `16px`
2. **Component Composition:** Nutze kleine, wiederverwendbare Komponenten
3. **Type Safety:** Alle Props haben `type` / `interface` Defs
4. **Accessibility:** ARIA Labels, Keyboard Navigation, Focus States
5. **Error Handling:** Immer Error States in Components zeigen
6. **Loading States:** Skeleton/Spinner bei async data
7. **Mobile First:** CSS Media Queries für responsive Design
8. **No Secrets:** Keine API Keys, Tokens, PII in Code

---

## 13) Troubleshooting

### Build schlägt fehl
```bash
# Clean rebuild
rm -r dist
npm run build
```

### TypeScript Fehler
```bash
npx tsc --noEmit
# Dann Fehler an entsprechenden Files beheben
```

### Import Error
```
Cannot find module '...'
```
→ Prüfe `packages/web/src` paths (keine `../` wenn möglich)

---

**Kontakt:** lifetimecircle@online.de
