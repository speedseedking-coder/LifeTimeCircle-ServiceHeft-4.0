/**
 * ConsentRequired Page
 * Blocking page when user needs to accept AGB/Datenschutz
 */

import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

type ConsentRequiredPageProps = {
  onConsent?: () => void;
  returnTo?: string;
};

export function ConsentRequiredPage({ onConsent, returnTo }: ConsentRequiredPageProps) {
  return (
    <div className="ltc-system-error" style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "var(--ltc-space-4)" }}>
      <Card>
        <div style={{ textAlign: "center", maxWidth: "400px" }}>
          <div style={{ fontSize: "48px", marginBottom: "var(--ltc-space-4)" }}>📋</div>
          <h1 style={{ fontSize: "var(--ltc-h2-size)" }}>Zustimmung erforderlich</h1>
          <p style={{ color: "var(--ltc-color-text-secondary)", margin: "var(--ltc-space-4) 0" }}>
            Du musst den Allgemeinen Geschäftsbedingungen und der Datenschutzrichtlinie zustimmen, um fortzufahren.
          </p>
          <div style={{ display: "flex", gap: "var(--ltc-space-3)", justifyContent: "center", marginTop: "var(--ltc-space-6)", flexDirection: "column" }}>
            <Button
              variant="primary"
              onClick={() => {
                const target = returnTo ? `#/consent?returnTo=${encodeURIComponent(returnTo)}` : "#/consent";
                window.location.hash = target;
                onConsent?.();
              }}
            >
              Jetzt akzeptieren
            </Button>
            <Button variant="secondary" onClick={() => window.location.hash = "#/"}>
              Abbrechen
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
