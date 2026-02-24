// packages/web/src/pages/AuthPage.tsx
export default function AuthPage(): JSX.Element {
  return (
    <main style={{ padding: 12 }}>
      <h1>Auth</h1>
      <p>Scaffold-Seite: Login/Signup wird hier verdrahtet. (Nur UI-Placeholder.)</p>

      <section style={{ marginTop: 16 }}>
        <h2>Navigation (Hash)</h2>
        <ul>
          <li>
            <a href="#/consent">Weiter zu Consent</a>
          </li>
          <li>
            <a href="#/vehicles">Zu Vehicles</a>
          </li>
          <li>
            <a href="#/documents">Zu Documents</a>
          </li>
        </ul>
      </section>
    </main>
  );
}