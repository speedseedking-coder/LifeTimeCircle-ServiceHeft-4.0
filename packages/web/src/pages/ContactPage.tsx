import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function ContactPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
<<<<<<< HEAD
    <PublicSiteShell title="Kontakt" appStyle={props.appStyle}>
      <p>Für allgemeine Fragen, Rückmeldungen oder Produktanfragen erreichst du uns unter:</p>
      <p>
        <a href="mailto:lifetimecircle@online.de">lifetimecircle@online.de</a>
      </p>
      <p>Bitte sende keine persönlichen Fahrzeugdaten, Dokumente oder sensiblen Nachweise per E-Mail.</p>
      <p>Für produktive Nachweise ist der vorgesehene Upload im ServiceHeft der richtige Kanal.</p>
=======
    <PublicSiteShell title="Contact" appStyle={props.appStyle}>
      <p>Für Support oder allgemeine Anfragen erreichst du uns unter:</p>
      <p>
        <a href="mailto:lifetimecircle@online.de">lifetimecircle@online.de</a>
      </p>
      <p>Bitte verwende diese Adresse nur für generelle Fragen. Persönliche Fahrzeugdaten niemals per E-Mail senden.</p>
>>>>>>> origin/main
    </PublicSiteShell>
  );
}
