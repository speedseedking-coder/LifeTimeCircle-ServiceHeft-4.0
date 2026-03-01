import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function DatenschutzPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Datenschutz" appStyle={props.appStyle}>
      <p>
        Public/QR ist datenarm (z. B. VIN maskiert). Uploads sind Quarantäne-by-default und werden erst nach Scan freigegeben. Keine PII in
        Mockups/Exports/Logs.
      </p>
      <h2>Consent</h2>
      <p>
        Consent verwaltet die Zustimmung zu Bedingungen/Datenschutz. Seite: <a href="#/consent">#/consent</a>.
      </p>
      <h2>Cookies</h2>
      <p>
        Notwendig ist immer aktiv. Optionales Analytics steuerst du unter <a href="#/cookies">Cookie-Einstellungen</a>.
      </p>
    </PublicSiteShell>
  );
}
