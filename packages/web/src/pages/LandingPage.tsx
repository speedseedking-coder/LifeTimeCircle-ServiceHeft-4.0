import { useEffect, useState } from "react";
import { PublicSiteFooter } from "../components/layout/PublicSiteShell";
import { Button, Card } from "../components/ui";

const LANDING_BG_CANDIDATES = [
  "/images/frontpage_LiftimeCicrcle_2.png",
  "/images/frontpage_LiftimeCicrcle_safe.webp",
  "/images/frontpage_LiftimeCicrcle_safe.png",
];

export default function LandingPage(): JSX.Element {
  const [bgUrl, setBgUrl] = useState<string>(LANDING_BG_CANDIDATES[0]);

  useEffect(() => {
    let alive = true;
    let index = 0;

    const probe = () => {
      const src = LANDING_BG_CANDIDATES[index];
      const image = new Image();
      image.onload = () => {
        if (!alive) return;
        setBgUrl(src);
      };
      image.onerror = () => {
        if (!alive) return;
        index += 1;
        if (index < LANDING_BG_CANDIDATES.length) {
          probe();
        }
      };
      image.src = src;
    };

    probe();

    return () => {
      alive = false;
    };
  }, []);

  return (
    <div
      className="ltc-app ltc-app--hero"
      style={{
        ["--ltc-bg" as any]: `url("${bgUrl}")`,
        ["--ltc-bg-op" as any]: "1",
        ["--ltc-bg-size" as any]: "cover",
      }}
    >
      <div className="ltc-container">
        <section className="ltc-hero">
          <div className="ltc-hero__copy">
            <h1 className="ltc-hero__h1">Digitales Fahrzeug-Serviceheft</h1>
            <div className="ltc-hero__sub">Dokumentation, Vertrauen &amp; Zukunft</div>
            <Button
              variant="primary"
              size="lg"
              onClick={() => {
                window.location.hash = "#/entry";
              }}
              className="ltc-hero__cta"
            >
              Eintritt
            </Button>
          </div>
        </section>
        <section className="ltc-features">
          <div className="ltc-features__grid">
            <Card className="ltc-features__card">
              <h3>Uploads &amp; Dokumente</h3>
              <p>Sichere Nachweise speichern und verwalten.</p>
            </Card>
            <Card className="ltc-features__card">
              <h3>Trust-Ampel</h3>
              <p>Bewerte die Dokumentationsqualität deines Fahrzeugs.</p>
            </Card>
            <Card className="ltc-features__card">
              <h3>Public QR</h3>
              <p>Datenarme Fahrzeug-Ansicht mit QR-Code.</p>
            </Card>
          </div>
        </section>
      </div>
      <PublicSiteFooter />
    </div>
  );
}
