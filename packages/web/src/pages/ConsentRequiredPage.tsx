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
    <div className="ltc-system-error" data-testid="consent-required-ui">
      <Card>
        <div className="ltc-system-error__card">
          <div className="ltc-system-error__icon">📋</div>
          <h1 className="ltc-system-error__title">Zustimmung erforderlich</h1>
          <p className="ltc-system-error__message">
            Du musst den Allgemeinen Geschäftsbedingungen und der Datenschutzrichtlinie zustimmen, um fortzufahren.
          </p>
          <div className="ltc-system-error__actions ltc-system-error__actions--column">
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
            <Button variant="secondary" onClick={() => (window.location.hash = "#/")}>Abbrechen</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
