import { type CSSProperties } from "react";
import { PublicSiteShell } from "../components/layout/PublicSiteShell";

export default function JobsPage(props: { appStyle?: CSSProperties }): JSX.Element {
  return (
    <PublicSiteShell title="Jobs" appStyle={props.appStyle}>
      <p>Wir suchen Menschen, die Security-First, Datenhygiene und saubere Produktlogik ernst nehmen.</p>
      <h2>Profile</h2>
      <ul>
        <li>Frontend (React/TypeScript, Komponenten, Accessibility)</li>
        <li>Backend (FastAPI, RBAC/Object-Checks, Tests)</li>
        <li>Security/Compliance (PII-Policy, Redaction, Audit-Trails)</li>
      </ul>
      <h2>Bewerbung</h2>
      <p>
        Neutraler Dev-Kontakt: <code>jobs@lifetimecircle.example</code>
      </p>
    </PublicSiteShell>
  );
}
