import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function ImpressumPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Impressum" appStyle={props.appStyle}>
      <p>Betreiberangaben sind je Deployment zu konfigurieren. Keine realen Namen/Adressen in Quelltext/Mockups.</p>
      <h2>Kontakt</h2>
      <p>
        Neutral: <code>support@lifetimecircle.example</code>
      </p>
    </PublicSiteShell>
  );
}
