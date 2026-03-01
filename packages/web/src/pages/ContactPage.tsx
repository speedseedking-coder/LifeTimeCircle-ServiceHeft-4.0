import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function ContactPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Kontakt" appStyle={props.appStyle}>
      <p>Für allgemeine Fragen, Rückmeldungen oder Produktanfragen erreichst du uns unter:</p>
      <p>
        <a href="mailto:lifetimecircle@online.de">lifetimecircle@online.de</a>
      </p>
      <p>Bitte sende keine persönlichen Fahrzeugdaten, Dokumente oder sensiblen Nachweise per E-Mail.</p>
      <p>Für produktive Nachweise ist der vorgesehene Upload im ServiceHeft der richtige Kanal.</p>
    </PublicSiteShell>
  );
}
