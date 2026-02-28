# LifeTimeCircle - Service Heft 4.0

**Product Backlog (aktualisierter Snapshot)**

Stand: 2026-02-28

Hinweis:
- Dieser Backlog spiegelt den Ist-Stand aus `docs/99_MASTER_CHECKPOINT.md` plus den Arbeitsstand auf Branch `feat/web-final-trust-folder-flow`.
- Source of Truth bleibt: `99_MASTER_CHECKPOINT.md` -> `02_PRODUCT_SPEC_UNIFIED.md` -> `03_RIGHTS_MATRIX.md` -> `01_DECISIONS.md`.

Legende:
- **Prio:** P0 (kritisch) / P1 / P2
- **Status:** Planned / In Progress / Done

Definition of Done (kurz):
- Serverseitiges RBAC (deny-by-default) ist enforced, UI spiegelt Rechte.
- Empty States, Navigation und Fehlerpfade sind sauber.
- Keine Secrets oder Klartext-PII in Logs, Exports oder Public-Flows.
- Public-QR nutzt die Pflicht-Disclaimer-Copy exakt.

## Snapshot: zuletzt erledigt

- [x] CI-/Qualitaetsgate gehaertet: `.github/workflows/ci.yml`, OpenAPI-Audit, RBAC-Audit, `tools/test_all.ps1`
- [x] Web App-Shell mit Guarding fuer `401 -> #/auth`, `consent_required -> #/consent`, `403 -> Forbidden`
- [x] Vehicles im Web auf echte API verdrahtet (`/vehicles`, `/vehicles/{id}`)
- [x] Documents im Web auf echte API verdrahtet (Upload, Lookup, Download-Link, Admin-Quarantaene)
- [x] Trust Folders Backend in main verfuegbar; Web-Flow auf diesem Branch verdrahtet
- [x] `handleUnauthorized` raeumt `ltc_auth_token_v1` mit auf
- [x] Playwright Mini-E2E deckt jetzt auch Admin-/Export-Step-up-Flows ab
- [x] Admin-Web fuer Rollen, Moderator, VIP-Business-Freigaben und Full-Export-Step-up an bestehende APIs verdrahtet
- [x] T1/T2/T3 jetzt fachlich aus Entries abgeleitet; Public-QR und Vehicle Detail zeigen echte Trust-Summary statt Platzhalter

## EPIC-01 | Fundament: Projektstruktur und Branding

**Prio:** P0 | **Status:** In Progress

- [x] A1: Repo-Struktur fuer docs/server/packages etabliert
- [x] A2: Branding auf "LifeTimeCircle / Service Heft 4.0" vereinheitlicht
- [ ] A3: Kontakt- und Rechtstexte final gegen letzte Produktfassung pruefen

## EPIC-02 | Auth: Login, Verifizierung, Consent

**Prio:** P0 | **Status:** In Progress

- [x] B1: E-Mail Login / Register Basis serverseitig vorhanden
- [x] B2: Challenge-Flow (OTP), TTL, Rate-Limits und Anti-Enumeration vorhanden
- [x] B3: Consent-Pflicht mit Version und Timestamp serverseitig vorhanden
- [x] B4: Session / Token Handling inkl. Logout-Endpunkt vorhanden
- [x] B5: Web `AuthPage` und `ConsentPage` auf echte Flows verdrahtet
- [x] B6: Auth-/Consent-Contract bereinigen, damit Login-Flow und nachgelagerter Consent-Schritt ohne Doppelung zusammenpassen

## EPIC-03 | Rollen und Rechte (RBAC)

**Prio:** P0 | **Status:** In Progress

- [x] C1: Rollenmodell `public/user/vip/dealer/moderator/admin/superadmin`
- [x] C2: Rechte-Matrix serverseitig deny-by-default implementiert
- [x] C3: Moderator strikt auf Blog/News begrenzt; Produkt- und Public-Sonderpfade gesperrt
- [x] C4: Clientseitige Navigation fuer geschuetzte Bereiche an SoT angepasst
- [x] C5: Trust-Folders im Web nur fuer `vip|dealer|admin|superadmin`
- [ ] C6: Restliche Admin-/Staff-Sonderfaelle gegen aktuelle Rights-Matrix vollstaendig nachziehen

## EPIC-04 | Admin (Minimal)

**Prio:** P0 | **Status:** Done

- [x] D1: Grundlagen fuer Rollen-/Moderator-Administration serverseitig vorhanden
- [x] D2: Admin-Oberflaechen fuer Rollen setzen, Moderator-Akkreditierung und Staff-Freigaben finalisieren
- [x] D3: Export-Full nur SUPERADMIN mit Step-Up und UI-Flow abschliessen

## EPIC-05 | Service Heft Kern

**Prio:** P0 | **Status:** In Progress

- [x] E1: Fahrzeuge anlegen, listen und Details abrufen
- [x] E2: Fahrzeugprofil und Timeline fachlich vervollstaendigen
- [x] E3: Eintraege inkl. Versionierung breit in UI und API abschliessen
- [x] E4: Dokumente/Nachweise mit Upload, Lookup und Review-Flow verdrahtet
- [x] E5: T1/T2/T3 fachlich und im UI komplett abbilden
- [x] E6: Trust Folders CRUD-light und Add-on-Gate vorhanden; Web-Flow auf Branch verdrahtet

## EPIC-06 | Public-QR Mini-Check

**Prio:** P1 | **Status:** In Progress

- [x] F1: Public View via QR-Link vorhanden
- [x] F2: Disclaimer-Pflichttext exakt abgesichert
- [ ] F3: Trust-Ampel-/Reason-Code-Abbildung weiter haerten und final gegen SoT konsolidieren

## EPIC-07 | Blogbase und Newsletter

**Prio:** P1 | **Status:** Planned

- [x] G1: Public Blog/News-Routen vorhanden
- [ ] G2: Redaktionelle Admin-/Moderator-Flows fertigstellen
- [ ] G3: Newsletter Opt-in/Opt-out fachlich und technisch umsetzen

## EPIC-08 | Security und Privacy Baseline

**Prio:** P0 | **Status:** Done

- [x] H1: Audit-/Redaction-Baseline vorhanden
- [x] H2: HMAC-Pseudonyme und No-PII-Grundsaetze verankert
- [x] H3: Export standardmaessig redacted
- [x] H4: Full-Export mit kompletter UI-/Step-Up-Strecke fertigziehen

## EPIC-09 | Uploads: Allowlist, Limits, Quarantine-by-default

**Prio:** P0 | **Status:** Done

- [x] I1: Allowlist (PDF/JPG/PNG) plus serverseitige Limits
- [x] I2: Quarantine-by-default und Scan-/Approval-Flow
- [x] I3: RBAC auf Dokumentzugriff und Admin-Review

## EPIC-10 | Web Qualitaetsgates und Regression-Schutz

**Prio:** P0 | **Status:** Done

- [x] J1: `tools/test_all.ps1` als deterministischer Sammel-Runner
- [x] J2: CI mit Build, Backend-Tests, OpenAPI-Audit und RBAC-Audit
- [x] J3: Playwright Mini-E2E fuer App-Gates, Public-QR, Vehicles, Documents und Trust Folders
- [x] J4: Weitere E2E-Coverage fuer Auth-, Consent- und spaetere Admin-Flows ausbauen

## Naechste sinnvolle Arbeitsbloeke

- [ ] N1: PR #254 reviewen und mergen
- [x] N2: Auth-/Consent-Contract zwischen `/auth/verify` und `/consent/*` vereinheitlichen
- [x] N3: Fahrzeugprofil, Timeline und Entry-Versionierung weiterziehen
- [x] N4: Admin-Oberflaechen fuer Rollen, Moderator und Export-Freigaben bauen
