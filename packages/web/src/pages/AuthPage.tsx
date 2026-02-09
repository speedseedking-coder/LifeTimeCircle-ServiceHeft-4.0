import React from "react";
import { Link } from "react-router-dom";

export default function AuthPage(): JSX.Element {
  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>Auth</h1>
      <p>Scaffold-Seite: Login/Signup wird hier verdrahtet. (Nur UI-Placeholder.)</p>

      <section style={{ marginTop: 16 }}>
        <h2>Navigation</h2>
        <ul>
          <li><Link to="/consent">Weiter zu Consent</Link></li>
          <li><Link to="/vehicles">Zu Vehicles</Link></li>
          <li><Link to="/documents">Zu Documents</Link></li>
        </ul>
      </section>
    </main>
  );
}
