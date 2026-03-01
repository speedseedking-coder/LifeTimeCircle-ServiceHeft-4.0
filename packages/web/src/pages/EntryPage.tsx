import { type CSSProperties } from "react";
import { Card } from "../components/ui";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function EntryPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
<<<<<<< HEAD
    <PublicSiteShell title="Einsteigen" appStyle={props.appStyle}>
=======
    <PublicSiteShell title="Eintritt" appStyle={props.appStyle}>
>>>>>>> origin/main
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
<<<<<<< HEAD
              Weiter als Privat
=======
              Weiter als Privatnutzer
>>>>>>> origin/main
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
<<<<<<< HEAD
              Weiter als Gewerblich
=======
              Weiter als Gewerbe
>>>>>>> origin/main
            </a>
          </div>
        </Card>
      </div>
    </PublicSiteShell>
  );
}
