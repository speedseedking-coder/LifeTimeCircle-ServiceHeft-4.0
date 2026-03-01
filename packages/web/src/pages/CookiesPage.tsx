import { type CSSProperties } from "react";
import CookieSettingsCard from "../components/CookieSettingsCard";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function CookiesPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Cookie-Einstellungen" appStyle={props.appStyle}>
      <CookieSettingsCard />
      <h2>Was wird gespeichert?</h2>
      <p>Technisch notwendige Zustände (z. B. Flow-/Session-Status) und deine Cookie-Auswahl. Marketing/Tracking ist deaktiviert.</p>
    </PublicSiteShell>
  );
}
