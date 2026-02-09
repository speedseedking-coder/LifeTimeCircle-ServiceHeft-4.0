import React from "react";
import { Link, useParams } from "react-router-dom";

export default function VehicleDetailPage(): JSX.Element {
  const params = useParams();
  const vehicleId = params.vehicleId ?? "(unknown)";

  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>Vehicle Detail</h1>
      <p>Scaffold-Seite: Detailansicht zu einem Fahrzeug.</p>

      <section style={{ marginTop: 16 }}>
        <h2>Vehicle ID</h2>
        <code style={{ display: "inline-block", padding: 8, border: "1px solid #ddd", borderRadius: 8 }}>
          {vehicleId}
        </code>
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Navigation</h2>
        <ul>
          <li><Link to="/vehicles">Zurück zur Vehicles-Liste</Link></li>
          <li><Link to="/documents">Zu Documents</Link></li>
        </ul>
      </section>
    </main>
  );
}
