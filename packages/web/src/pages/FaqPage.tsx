import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function FaqPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="FAQ" appStyle={props.appStyle}>
      <h2>Was ist das ServiceHeft 4.0?</h2>
      <p>
        Ein digitales Nachweis- und Dokumentationssystem: Uploads, Historie und Belege werden strukturiert abgelegt, damit Aussagen prüfbar werden.
      </p>

      <h2>Warum ist das beim Autokauf relevant?</h2>
      <p>
        Vertrauen scheitert oft an fehlenden Unterlagen. Saubere Dokumentation reduziert Unsicherheit und kann beim Wiederverkauf helfen, weil Käufer
        weniger Risiko einpreisen.
      </p>

      <h2>Was zeigt Public/QR?</h2>
      <p>Datenarm (z. B. VIN maskiert), aber geeignet für schnelle Checks &amp; Reports.</p>

      <h2>Wo ändere ich Cookies?</h2>
      <p>
        Unter <a href="#/cookies">Cookie-Einstellungen</a>.
      </p>
    </PublicSiteShell>
  );
}
