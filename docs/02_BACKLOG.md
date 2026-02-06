\# LifeTimeCircle – Service Heft 4.0

\*\*Product Backlog (Epics / Stories / Tasks)\*\*  

Stand: 2026-01-29



Legende:

\- \*\*Prio:\*\* P0 (kritisch) / P1 / P2

\- \*\*Status:\*\* Idea / Planned / In Progress / Blocked / Done



Definition of Done (kurz):

\- Serverseitiges RBAC (deny-by-default) ist enforced, UI spiegelt Rechte.

\- Empty States/Navigation/Buttons sauber.

\- Keine Secrets/Klartext-PII in Logs/Exports (HMAC-Pseudonyme).

\- Public-QR: keine Metrics/Counts/Percentages/Zeiträume, Disclaimer Pflicht-Copy.



\## EPIC-01 | Fundament: Projektstruktur \& Branding

\*\*Prio:\*\* P0 | \*\*Status:\*\* Planned

\- \[ ] A1: Repo-Struktur finalisieren (docs/server/static/packages)

\- \[ ] A2: Branding-Texte vereinheitlichen (LifeTimeCircle / Service Heft 4.0)

\- \[ ] A3: Kontakt-E-Mail überall: lifetimecircle@online.de



\## EPIC-02 | Auth: Login + Verifizierung + Consent

\*\*Prio:\*\* P0 | \*\*Status:\*\* Planned

\- \[ ] B1: E-Mail Login/Register Basis

\- \[ ] B2: Challenge (OTP/Magic-Link) mit TTL, Rate-Limits, Anti-Enumeration

\- \[ ] B3: Consent-Pflicht (AGB/Datenschutz) mit Version+Timestamp

\- \[ ] B4: Session/Token Handling + Logout

\- \[ ] B5: Audit Events für Auth/Consent



\## EPIC-03 | Rollen \& Rechte (RBAC)

\*\*Prio:\*\* P0 | \*\*Status:\*\* Planned

\- \[ ] C1: Rollenmodell public/user/vip/dealer/moderator/admin/superadmin

\- \[ ] C2: Rechte-Matrix serverseitig implementieren (Policy Engine)

\- \[ ] C3: Übergabe/Verkauf nur VIP+Dealer

\- \[ ] C4: VIP-Gewerbe Staff-Freigabe (max 2, SUPERADMIN)

\- \[ ] C5: Moderator nur Blog/News; keine PII; kein Export; kein Audit



\## EPIC-04 | Admin (Minimal)

\*\*Prio:\*\* P0 | \*\*Status:\*\* Planned

\- \[ ] D1: Rollen setzen (Audit: role granted/revoked)

\- \[ ] D2: Moderator akkreditieren/revoken

\- \[ ] D3: VIP-Gewerbe Staff approve (SUPERADMIN)

\- \[ ] D4: Export-Full nur SUPERADMIN + Step-Up (falls vorgesehen)



\## EPIC-05 | Service Heft Kern

\*\*Prio:\*\* P0 | \*\*Status:\*\* Planned

\- \[ ] E1: Fahrzeug anlegen/suchen (VIN/WID)

\- \[ ] E2: Fahrzeugprofil + Timeline

\- \[ ] E3: Einträge + Versionierung

\- \[ ] E4: Dokumente/Nachweise (Upload, Metadaten, Sichtbarkeit)

\- \[ ] E5: T1/T2/T3 speichern



\## EPIC-06 | Public-QR Mini-Check

\*\*Prio:\*\* P1 | \*\*Status:\*\* Planned

\- \[ ] F1: Public View via QR-Link

\- \[ ] F2: Trust-Ampel + Indicator-Codes (ohne Metriken)

\- \[ ] F3: Disclaimer Pflicht-Copy



\## EPIC-07 | Blogbase + Newsletter

\*\*Prio:\*\* P1 | \*\*Status:\*\* Planned

\- \[ ] G1: Blogbase (Admin)

\- \[ ] G2: Newsletter Opt-in/Opt-out

\- \[ ] G3: Moderator UI nur Blog/News



\## EPIC-08 | Security/Privacy Baseline (Logs/Audit/Export)

\*\*Prio:\*\* P0 | \*\*Status:\*\* Planned

\- \[ ] H1: Audit-Schema + Redaction-Filter (deny-by-default)

\- \[ ] H2: HMAC Pseudonyme (email\_hmac/ip\_hmac/ua\_hmac), keine Klartext-PII

\- \[ ] H3: Export default redacted

\- \[ ] H4: Full Export nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung



\## EPIC-09 | Uploads: Allowlist + Limits + Quarantine-by-default

\*\*Prio:\*\* P0 | \*\*Status:\*\* Planned

\- \[ ] I1: Allowlist (PDF/JPG/PNG) + Size/Count Limits

\- \[ ] I2: Quarantine-by-default + Scan/Approval

\- \[ ] I3: Zugriff RBAC, keine public files




