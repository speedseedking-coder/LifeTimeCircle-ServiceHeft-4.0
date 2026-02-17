# Web E2E Smoke (Wireframe) — Stand 2026-02-17

## Voraussetzungen
- API läuft lokal (server) mit LTC_SECRET_KEY (>=16)
- Web läuft lokal (packages/web)
- Hinweis: Moderator ist außerhalb Blog/News strikt 403 (erwartet).

## Klickpfad (Happy Path)
1) /consent
   - Zustimmen → Redirect /vehicles
2) /vehicles
   - Liste lädt (empty ok)
   - Fahrzeug öffnen → /vehicles/{id}
3) /vehicles/{id}
   - Details sichtbar (VIN nur masked, falls angezeigt)
4) /documents
   - Upload (multipart) → Status erscheint in Liste
5) /public/qr
   - Pflichttext exakt vorhanden:
     „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## Fehlerfälle (erwartet)
- 401: Actor fehlt → UI zeigt “Bitte anmelden”
- 403 + code=consent_required → Redirect nach /consent
- 403 (sonst) → “Keine Berechtigung”
