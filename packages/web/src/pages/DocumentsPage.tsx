// packages/web/src/pages/DocumentsPage.tsx
export default function DocumentsPage(): JSX.Element {
  return (
    <main style={{ padding: 12 }}>
      <h1>Documents</h1>
      <p>Scaffold-Seite: Upload/Download/Status (Quarantäne-by-default; Review folgt serverseitig).</p>

      <section style={{ marginTop: 16 }}>
        <h2>Aktionen (Scaffold)</h2>
        <button type="button" disabled style={{ padding: "10px 14px" }}>
          Upload (kommt später)
        </button>
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Navigation (Hash)</h2>
        <ul>
          <li>
            <a href="#/vehicles">Zu Vehicles</a>
          </li>
          <li>
            <a href="#/auth">Zu Auth</a>
          </li>
        </ul>
      </section>
    </main>
  );
}
