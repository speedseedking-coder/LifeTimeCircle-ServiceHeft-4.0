import React from "react";
import { Link } from "react-router-dom";

export default function VehiclesPage(): JSX.Element {
  const demoVehicles = [
    { id: "demo-1", title: "Demo Fahrzeug 1" },
    { id: "demo-2", title: "Demo Fahrzeug 2" },
  ];

  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>Vehicles</h1>
      <p>Scaffold-Seite: Liste der Fahrzeuge (Owner-scoped, object-level checks serverseitig).</p>

      <section style={{ marginTop: 16 }}>
        <h2>Beispiel-Liste (nur UI)</h2>
        <ul>
          {demoVehicles.map((v) => (
            <li key={v.id}>
              <Link to={`/vehicles/${encodeURIComponent(v.id)}`}>{v.title}</Link>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Navigation</h2>
        <ul>
          <li><Link to="/documents">Zu Documents</Link></li>
          <li><Link to="/auth">Zu Auth</Link></li>
          <li><Link to="/consent">Zu Consent</Link></li>
        </ul>
      </section>
    </main>
  );
}
