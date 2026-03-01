import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function DatenschutzPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Datenschutz" appStyle={props.appStyle}>
      <p>
<<<<<<< HEAD
        Public-QR bleibt datenarm. Sichtbar sind Ampel und textliche Hinweise, nicht aber Dokumente, Downloads, Halterdaten oder technische Diagnosen.
      </p>
      <h2>Consent</h2>
      <p>
        Produktiver Zugriff setzt die Zustimmung zu AGB und Datenschutz voraus. Den aktuellen Status prüfst du unter <a href="#/consent">#/consent</a>.
      </p>
      <h2>Uploads und Nachweise</h2>
      <p>Nachweise werden im Produkt hochgeladen, standardmäßig geprüft und erst danach wie vorgesehen nutzbar. Öffentliche Downloads gibt es nicht.</p>
=======
        Public/QR ist datenarm (z. B. VIN maskiert). Uploads sind Quarantäne-by-default und werden erst nach Scan freigegeben. Keine PII in
        Mockups/Exports/Logs.
      </p>
      <h2>Consent</h2>
      <p>
        Consent verwaltet die Zustimmung zu Bedingungen/Datenschutz. Seite: <a href="#/consent">#/consent</a>.
      </p>
>>>>>>> origin/main
      <h2>Cookies</h2>
      <p>
        Notwendig ist immer aktiv. Optionales Analytics steuerst du unter <a href="#/cookies">Cookie-Einstellungen</a>.
      </p>
<<<<<<< HEAD
      <h2>Support-Kanal</h2>
      <p>Für allgemeine Fragen kannst du uns per E-Mail kontaktieren. Sensible Daten gehören nicht in E-Mails, sondern nur in die vorgesehenen Produktflüsse.</p>
=======
>>>>>>> origin/main
    </PublicSiteShell>
  );
}
