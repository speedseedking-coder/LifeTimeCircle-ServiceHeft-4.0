# Web E2E Smoke - Stand 2026-03-01

## Ziel

Schneller Überblick, was die Playwright-Mini-Suite im aktuellen Web-Workspace bereits absichert und welche manuellen Smokes bei Bedarf zusätzlich sinnvoll sind.

## Automatisierte Suite

Ausführen:

```powershell
cd C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\packages\web
npm run e2e
```

Die Suite prüft derzeit:

1. Public Routes: Contact, Entry, Blog, News, Public QR.
2. App Gate: Redirects bei fehlendem Token, Consent-Gates und Forbidden-Fälle.
3. Auth/Consent: OTP-Request, Verify, Redirect, Feldsemantik und Fokusführung.
4. Vehicles: Listen- und Detailflow, Revisionen, Formularsemantik.
5. Documents: Upload, Lookup, Admin-Quarantäne-Sichtbarkeit, Formularsemantik.
6. Trust Folders: Liste, Detail, Fokusführung und Rollen-Gates.
7. Admin: Rollenwechsel, Step-up, VIP-Business, Export-Grant.
8. Responsive Layouts: `375px`, `640px`, `768px`, `1920px`.

## Manuelle Zusatz-Smokes

Nur nötig, wenn du Änderungen außerhalb der vorhandenen Playwright-Abdeckung gemacht hast.

1. `#/auth`
   - Fokus startet im E-Mail-Feld.
   - Nach erfolgreichem Code-Request springt Fokus auf das OTP-Feld.

2. `#/consent`
   - Erster offener Consent ist fokussiert.
   - Speichern ohne beide Haken blockiert sauber.

3. `#/trust-folders?...`
   - Eingabefeld für neuen Folder ist direkt fokussiert.
   - `Tab`-Reihenfolge bleibt logisch.

4. `#/trust-folders/{id}?...`
   - Rename-Feld ist fokussiert.
   - Delete-Button ist per Tastatur erreichbar und sauber beschriftet.

5. `#/documents`
   - Upload- und Lookup-Formular bleiben ohne horizontales Overflow nutzbar.

## Erwartete Fehlerbilder

- `401`: Actor fehlt oder Session abgelaufen -> Redirect nach `#/auth?...`
- `403` mit `consent_required` -> Redirect nach `#/consent?...`
- `403` sonst -> Forbidden-UI
- `403` mit `admin_step_up_required` -> Step-up zuerst anfordern

## Hinweis zu Proxy-Logs

Während `npm run e2e` können Vite-Proxy-Logs gegen `127.0.0.1:8000` auftauchen. Das ist nur dann relevant, wenn die Tests selbst fehlschlagen. Maßgeblich ist der Exitcode der Playwright-Suite.
