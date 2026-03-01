/* DEV-SCAFFOLD: Design system reference page — developer-only.\n   This page intentionally exposes internal components and inline styles for visual reference.\n   Do NOT include in production navigation; keep behind a dev-only route or gated flag. */

/**
 * DESIGN SYSTEM REFERENCE
 * LifeTimeCircle – Service Heft 4.0
 * 
 * Diese Datei zeigt alle verfügbaren Komponenten und Tokens.
 * Sie ist ein Referenzmaterial und sollte NICHT in Production deployed werden.
 */

import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Alert } from "../components/ui/Alert";
import { Checkbox } from "../components/ui/Checkbox";
import { EmptyState } from "../components/ui/Skeleton";
import { Skeleton } from "../components/ui/Loading";
import { PublicLayout } from "../components/layout/PublicLayout";
import { Header } from "../components/layout/Header";
import { Footer } from "../components/layout/Footer";

export function DesignSystemReference() {
  return (
    <PublicLayout
      header={
        <Header
          logo="LifeTimeCircle"
          nav={
            <nav className="ltc-nav">
              <a href="#/">Home</a>
              <a href="#/blog">Blog</a>
              <a href="#/faq">FAQ</a>
            </nav>
          }
          actions={
            <div>
              <Button variant="primary" size="sm">
                Anmelden
              </Button>
            </div>
          }
        />
      }
      footer={
        <Footer>
          <div className="ltc-footer-section">
            <h3>Über uns</h3>
            <ul>
              <li><a href="#/">Startseite</a></li>
              <li><a href="#/blog">Blog</a></li>
            </ul>
          </div>
          <div className="ltc-footer-section">
            <h3>Support</h3>
            <ul>
              <li><a href="#/faq">FAQ</a></li>
              <li><a href="#/jobs">Karriere</a></li>
            </ul>
          </div>
        </Footer>
      }
    >
      <main className="ltc-main ltc-main--wide" data-testid="design-system-reference">
        <h1>Design System Reference</h1>
        <p className="ltc-muted">Interne Referenzseite für Komponenten, Zustände und Tokens. Nicht Teil der produktiven Navigation.</p>

        {/* ========== BUTTONS ========== */}
        <div className="ltc-mb-8">
          <h2>Buttons</h2>
          <div className="ltc-token-row">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="danger">Danger</Button>
            <Button variant="ghost">Ghost</Button>
          </div>
          <div className="ltc-token-row ltc-mt-4">
            <Button size="sm">Small</Button>
            <Button size="base">Base</Button>
            <Button size="lg">Large</Button>
          </div>
          <div className="ltc-token-row ltc-mt-4">
            <Button disabled>Disabled</Button>
            <Button loading>Loading</Button>
          </div>
        </div>

        {/* ========== INPUT ========== */}
        <div className="ltc-mb-8">
          <h2>Input</h2>
          <Input label="Name" placeholder="Dein Name" />
          <Input label="E-Mail" type="email" placeholder="deine@email.de" />
          <Input label="Passwort" type="password" placeholder="••••••••" hint="Mindestens 8 Zeichen" />
          <Input label="Fehlerhaft" error="Dieses Feld ist erforderlich" />
        </div>

        {/* ========== CARD ========== */}
        <div className="ltc-mb-8">
          <h2>Card</h2>
          <Card>
            <h3>Diese Komponente ist eine Card</h3>
            <p>Nutze Cards zum Gruppieren von Inhalten.</p>
          </Card>
        </div>

        {/* ========== BADGE ========== */}
        <div className="ltc-mb-8">
          <h2>Badge (Status)</h2>
          <div className="ltc-token-row">
            <Badge variant="neutral">Neutral</Badge>
            <Badge variant="info">Info</Badge>
            <Badge variant="success">Success</Badge>
            <Badge variant="warning">Warning</Badge>
            <Badge variant="error">Error</Badge>
          </div>
          <h3 className="ltc-mt-6">Trust Ampel</h3>
          <div className="ltc-token-row">
            <Badge variant="trust-green">Grün</Badge>
            <Badge variant="trust-yellow">Gelb</Badge>
            <Badge variant="trust-red">Rot</Badge>
            <Badge variant="trust-gray">Grau</Badge>
          </div>
        </div>

        {/* ========== ALERT ========== */}
        <div className="ltc-mb-8">
          <h2>Alert</h2>
          <Alert variant="info" title="Hinweis">
            Dies ist eine Informationsmeldung.
          </Alert>
          <Alert variant="success" title="Erfolg" className="ltc-mt-4">
            Die Aktion war erfolgreich.
          </Alert>
          <Alert variant="warning" title="Warnung" className="ltc-mt-4">
            Bitte beachte diese Warnung.
          </Alert>
          <Alert variant="error" title="Fehler" className="ltc-mt-4" dismissible>
            Es ist ein Fehler aufgetreten.
          </Alert>
        </div>

        {/* ========== CHECKBOX ========== */}
        <div className="ltc-mb-8">
          <h2>Checkbox</h2>
          <Checkbox label="Ich stimme den AGB zu" />
          <Checkbox label="Fehler" error="Du musst zustimmen" />
        </div>

        {/* ========== EMPTY STATE ========== */}
        <div className="ltc-mb-8">
          <h2>EmptyState</h2>
          <EmptyState
            icon="📁"
            title="Keine Fahrzeuge"
            description="Du hast noch keine Fahrzeuge hinzugefügt."
            action={<Button variant="primary">Fahrzeug hinzufügen</Button>}
          />
        </div>

        {/* ========== SKELETON ========== */}
        <div className="ltc-mb-8">
          <h2>Skeleton (Loading)</h2>
          <Skeleton count={3} />
        </div>

        {/* ========== COLORS ========== */}
        <div className="ltc-mb-8">
          <h2>Farben (Tokens)</h2>
          <div className="ltc-design-swatch-grid">
            <div className="ltc-design-swatch ltc-design-swatch--brand">
              Brand
            </div>
            <div className="ltc-design-swatch ltc-design-swatch--success">
              Success
            </div>
            <div className="ltc-design-swatch ltc-design-swatch--warning">
              Warning
            </div>
            <div className="ltc-design-swatch ltc-design-swatch--error">
              Error
            </div>
            <div className="ltc-design-swatch ltc-design-swatch--trust-green">
              Trust: Grün
            </div>
            <div className="ltc-design-swatch ltc-design-swatch--trust-yellow">
              Trust: Gelb
            </div>
          </div>
        </div>
      </main>
    </PublicLayout>
  );
}
