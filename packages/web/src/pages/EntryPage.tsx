import { type CSSProperties } from "react";
import { Card } from "../components/ui";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function EntryPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Eintritt" appStyle={props.appStyle}>
      <p>Wähle den passenden Einstieg. Die serverseitige Rechtevergabe bleibt maßgeblich, diese Auswahl führt nur kontrolliert in den Auth-Flow.</p>

      <div className="ltc-featureRow">
        <Card className="ltc-featureCard">
          <div className="ltc-featureCard__head">
            <div>
              <div className="ltc-featureCard__t">Privat</div>
              <p className="ltc-muted">Für Fahrzeughalter, Sammler und Einzelnutzer mit eigenem Fahrzeugbestand.</p>
            </div>
          </div>
          <div className="ltc-actions">
            <a href="#/auth" className="ltc-btn ltc-btn--primary">
              Weiter als Privatnutzer
            </a>
          </div>
        </Card>

        <Card className="ltc-featureCard">
          <div className="ltc-featureCard__head">
            <div>
              <div className="ltc-featureCard__t">Gewerblich</div>
              <p className="ltc-muted">Für Händler, Werkstätten und strukturierte Fahrzeugprozesse mit Business-Kontext.</p>
            </div>
          </div>
          <div className="ltc-actions">
            <a href="#/auth" className="ltc-btn ltc-btn--soft">
              Weiter als Gewerbe
            </a>
          </div>
        </Card>
      </div>
    </PublicSiteShell>
  );
}
