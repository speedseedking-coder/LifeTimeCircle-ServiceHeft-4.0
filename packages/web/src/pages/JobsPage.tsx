import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function JobsPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Jobs" appStyle={props.appStyle}>
      <p>Wir suchen Menschen, die Security-First, Datenhygiene und belastbare Produktlogik ernst nehmen.</p>
      <h2>Profile</h2>
      <ul>
        <li>Frontend: React, TypeScript, Accessibility, belastbare Formular- und State-Flows.</li>
        <li>Backend: FastAPI, RBAC, object-level checks, Tests und stabile API-Verträge.</li>
        <li>Security und Compliance: PII-Regeln, Redaction, Audit-Trails und sichere Standardpfade.</li>
      </ul>
      <h2>Worauf wir achten</h2>
      <p>Kurze Wege, klare Entscheidungen, keine Marketing-Abkürzungen bei Rollen, Daten und Sicherheitsversprechen.</p>
      <h2>Bewerbung</h2>
      <p>
        Schreib an <a href="mailto:lifetimecircle@online.de">lifetimecircle@online.de</a> mit kurzem Profil und Arbeitsbeispielen.
      </p>
    </PublicSiteShell>
  );
}
