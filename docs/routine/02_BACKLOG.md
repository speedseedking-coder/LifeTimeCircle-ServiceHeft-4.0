\# Dateiname: docs/routine/02\_BACKLOG.md

\# LifeTimeCircle – Service Heft 4.0 · Backlog (priorisiert)

Version: 2026-03 | Last-Update: YYYY-MM-DD



\## EPIC A — Docs/Grundlagen

\- A1: Docs-Struktur final (00\_INDEX, routine, policies)  

&nbsp; AC: Alle Links in `docs/00\_INDEX.md` funktionieren, keine doppelten Wahrheiten.

\- A2: Rollenliste final + Benennung  

&nbsp; AC: Rollen/Scopes in `policies/ROLES\_AND\_PERMISSIONS.md` sind konsistent.



\## EPIC B — Auth \& Consent (Pflicht)

\- B1: Auth Request (E-Mail)  

&nbsp; AC: Response ist anti-enumeration; Rate-Limits aktiv; OTP gespeichert (TTL).

\- B2: Auth Verify (OTP/Link)  

&nbsp; AC: One-time; TTL enforced; Audit-Event; Session/JWT ausgestellt.

\- B3: Consent Gate  

&nbsp; AC: Ohne AGB+DS kein Zugriff; Consent Version+Timestamp gespeichert.



\## EPIC C — RBAC \& Audit (Pflicht)

\- C1: RBAC Middleware/Dependency  

&nbsp; AC: deny-by-default; Rollen/Scopes serverseitig enforced; Tests vorhanden.

\- C2: AuditLog Basis  

&nbsp; AC: Login/Verify/Consent/RoleChange/Transfer/Export werden als Events protokolliert.



\## EPIC D — Service Heft Core

\- D1: Vehicle Entity + QR-ID  

&nbsp; AC: Fahrzeug anlegen; QR-Token generiert; Zugriff nur berechtigt.

\- D2: ServiceEntry + Evidence (T1/T2/T3)  

&nbsp; AC: Einträge + Nachweise verknüpfbar; Verifizierungsgrad speicherbar; kein Public-Leak.

\- D3: VIP-Bilder (optional im MVP)  

&nbsp; AC: Nicht-VIP sieht keine Bildansicht/Downloads.



\## EPIC E — Public-QR Trustscore (Pflicht)

\- E1: Trustscore Engine (intern)  

&nbsp; AC: Ampel Rot/Orange/Gelb/Grün aus Kriterien; Unfalltrust Regel umgesetzt.

\- E2: Public-Endpoint/View  

&nbsp; AC: Keine Metrics/Counts/Percentages/Zeiträume; Disclaimer Pflicht; keine PII.



\## EPIC F — VIP/Dealer Transfer

\- F1: Übergabe-QR / Transfer Flow  

&nbsp; AC: Nur VIP/DEALER; Audit Pflicht; Tokens TTL; Replays verhindert.

\- F2: Dealer Staff (max 2)  

&nbsp; AC: Provisionierung nur SUPERADMIN; Limit enforced; Audit Pflicht.



\## EPIC G — Blog/News + Newsletter

\- G1: Blog/News CRUD  

&nbsp; AC: Admin write; Moderator write nur Blog/News; keine PII/Exports.

\- G2: Newsletter Dispatch (Queue/Log)  

&nbsp; AC: Admin kann “Dispatch” auslösen; Log/Audit; später SMTP.



\## EPIC H — Uploads/Exports/Hardening

\- H1: Upload Pipeline  

&nbsp; AC: Allowlist + Quarantine; Scan/Approval; niemals public.

\- H2: Export Policy  

&nbsp; AC: Redacted default; Full export nur SUPERADMIN + Audit + TTL/Limit + Encryption.

\- H3: Security Baseline  

&nbsp; AC: Secrets nie im Log; HMAC Pseudonymisierung; Rate-Limits; Tests/Checkliste.



