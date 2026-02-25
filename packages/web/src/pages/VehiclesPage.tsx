// packages/web/src/pages/VehiclesPage.tsx
export default function VehiclesPage(): JSX.Element {
  const demoVehicles = [
    { id: "demo-1", title: "Demo Fahrzeug 1" },
    { id: "demo-2", title: "Demo Fahrzeug 2" },
  ];

  return (
    <main style={{ padding: 12 }}>
      <h1>Vehicles</h1>
      <p>Scaffold-Seite: Liste der Fahrzeuge (Owner-scoped, object-level checks serverseitig).</p>

      <section style={{ marginTop: 16 }}>
        <h2>Beispiel-Liste (nur UI)</h2>
        <ul>
          {demoVehicles.map((v) => (
            <li key={v.id}>
              <a href={`#/vehicles/${encodeURIComponent(v.id)}`}>{v.title}</a>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Navigation (Hash)</h2>
        <ul>
          <li>
            <a href="#/documents">Zu Documents</a>
          </li>
          <li>
            <a href="#/auth">Zu Auth</a>
          </li>
          <li>
            <a href="#/consent">Zu Consent</a>
          </li>
        </ul>
      </section>
    </main>
  );
}