import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function DatenschutzPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Datenschutz" appStyle={props.appStyle}>
      <p>
        Public-QR bleibt datenarm. Sichtbar sind Ampel und textliche Hinweise, nicht aber Dokumente, Downloads, Halterdaten oder technische Diagnosen.
      </p>
      <h2>Consent</h2>
      <p>
        Produktiver Zugriff setzt die Zustimmung zu AGB und Datenschutz voraus. Den aktuellen Status prüfst du unter <a href="#/consent">#/consent</a>.
      </p>
      <h2>Uploads und Nachweise</h2>
      <p>Nachweise werden im Produkt hochgeladen, standardmäßig geprüft und erst danach wie vorgesehen nutzbar. Öffentliche Downloads gibt es nicht.</p>
      <h2>Cookies</h2>
      <p>
        Notwendig ist immer aktiv. Optionales Analytics steuerst du unter <a href="#/cookies">Cookie-Einstellungen</a>.
      </p>
      <h2>Support-Kanal</h2>
      <p>Für allgemeine Fragen kannst du uns per E-Mail kontaktieren. Sensible Daten gehören nicht in E-Mails, sondern nur in die vorgesehenen Produktflüsse.</p>
    </PublicSiteShell>
  );
}
