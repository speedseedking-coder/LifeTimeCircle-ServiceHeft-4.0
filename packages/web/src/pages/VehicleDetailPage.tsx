function getVehicleIdFromPath(pathname: string): string {
  const parts = pathname.split("/").filter(Boolean);
  const i = parts.indexOf("vehicles");
  if (i >= 0 && parts[i + 1]) return decodeURIComponent(parts[i + 1]);
  return "(unknown)";
}

export default function VehicleDetailPage(): JSX.Element {
  const vehicleId = getVehicleIdFromPath(window.location.pathname);

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
          <li><a href="/vehicles">Zurück zur Vehicles-Liste</a></li>
          <li><a href="/documents">Zu Documents</a></li>
        </ul>
      </section>
    </main>
  );
}
