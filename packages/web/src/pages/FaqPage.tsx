import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function FaqPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="FAQ" appStyle={props.appStyle}>
      <h2>Was ist das ServiceHeft 4.0?</h2>
      <p>
<<<<<<< HEAD
        Ein digitales Nachweis- und Dokumentationssystem. Fahrzeughistorie, Einträge und Nachweise werden so abgelegt, dass Aussagen prüfbar bleiben.
      </p>

      <h2>Bewertet die Trust-Ampel den technischen Zustand?</h2>
      <p>
        Nein. Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des
        Fahrzeugs.
      </p>

      <h2>Warum zeigt Public-QR keine Zahlen?</h2>
      <p>Weil Public bewusst datenarm bleibt. Sichtbar sind Ampel und textliche Indikatoren, nicht aber Kennzahlen, Prozentwerte oder Zeitreihen.</p>

      <h2>Kann ich Dokumente öffentlich teilen?</h2>
      <p>Nein. Public-QR zeigt keine Dokumente, keine Downloads und keine Metadaten.</p>

      <h2>Was hilft für eine belastbare Historie?</h2>
      <p>Klare Einträge mit Datum, Typ, Kilometerstand, durchgeführt von und passenden Nachweisen. Beleg schlägt Behauptung.</p>
=======
        Ein digitales Nachweis- und Dokumentationssystem: Uploads, Historie und Belege werden strukturiert abgelegt, damit Aussagen prüfbar werden.
      </p>

      <h2>Warum ist das beim Autokauf relevant?</h2>
      <p>
        Vertrauen scheitert oft an fehlenden Unterlagen. Saubere Dokumentation reduziert Unsicherheit und kann beim Wiederverkauf helfen, weil Käufer
        weniger Risiko einpreisen.
      </p>

      <h2>Was zeigt Public/QR?</h2>
      <p>Datenarm (z. B. VIN maskiert), aber geeignet für schnelle Checks &amp; Reports.</p>
>>>>>>> origin/main

      <h2>Wo ändere ich Cookies?</h2>
      <p>
        Unter <a href="#/cookies">Cookie-Einstellungen</a>.
      </p>
<<<<<<< HEAD

      <h2>Wie erreiche ich euch?</h2>
      <p>
        Für allgemeine Fragen: <a href="mailto:lifetimecircle@online.de">lifetimecircle@online.de</a>.
      </p>
=======
>>>>>>> origin/main
    </PublicSiteShell>
  );
}
