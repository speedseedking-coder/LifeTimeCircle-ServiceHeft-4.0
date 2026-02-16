export default function ConsentPage(): JSX.Element {
  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>Consent</h1>
      <p>
        Scaffold-Seite: AGB/Datenschutz anzeigen + akzeptieren (versioniert). Ohne gültigen Consent sollen
        Produkt-Routen blockiert werden (serverseitig).
      </p>

      <section style={{ marginTop: 16 }}>
        <h2>Aktionen (Scaffold)</h2>
        <button type="button" disabled style={{ padding: "10px 14px" }}>
          Akzeptieren (kommt später)
        </button>
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Navigation</h2>
        <ul>
          <li><a href="/auth">Zurück zu Auth</a></li>
          <li><a href="/vehicles">Weiter zu Vehicles</a></li>
        </ul>
      </section>
    </main>
  );
}
