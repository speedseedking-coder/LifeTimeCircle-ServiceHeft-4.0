function trustFoldersHref(vehicleId: string): string {
  return `#/trust-folders?vehicle_id=${encodeURIComponent(vehicleId)}&addon_key=restauration`;
}

export default function VehicleDetailPage(props: { vehicleId: string }): JSX.Element {
  const vehicleId = props.vehicleId;

  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>Vehicle Detail</h1>
      <p>Scaffold-Seite: Detailansicht zu einem Fahrzeug mit Einstieg in nachgelagerte Produktbereiche.</p>

      <section style={{ marginTop: 16 }}>
        <h2>Vehicle ID</h2>
        <code style={{ display: "inline-block", padding: 8, border: "1px solid #ddd", borderRadius: 8 }}>
          {vehicleId}
        </code>
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Trust-Modul</h2>
        <p>
          Für dieses Fahrzeug können Trust-Folders add-on-gated und consent-gated geöffnet werden. Der Link übergibt den
          Vehicle-Kontext direkt in die Trust-Folder-Ansicht.
        </p>
        <a href={trustFoldersHref(vehicleId)}>Trust Folders für dieses Vehicle öffnen</a>
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Navigation</h2>
        <ul>
          <li>
            <a href="#/vehicles">Zurück zur Vehicles-Liste</a>
          </li>
          <li>
            <a href="#/documents">Zu Documents</a>
          </li>
          <li>
            <a href={trustFoldersHref(vehicleId)}>Zu Trust Folders</a>
          </li>
        </ul>
      </section>
    </main>
  );
}
