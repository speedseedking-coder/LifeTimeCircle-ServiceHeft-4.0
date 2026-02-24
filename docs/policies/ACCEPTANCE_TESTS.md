// File: ./docs//policies//ACCEPTANCE/_TESTS.md



\# ACCEPTANCE\_TESTS – DoD-Gates (produktive Abnahme)



\*\*Stand:\*\* 2026-01-28 (Europe/Berlin)  

\*\*Hinweis:\*\* Diese Tests sind verbindlich für Release-Abnahme.



---



\## 1) RBAC serverseitig (MUST)

\### AT-RBAC-01: Moderator kann niemals Fahrzeugdaten sehen

\- Given: User mit Rolle moderator

\- When: ruft Vehicles/Entries/Documents/Verification APIs auf

\- Then: server denies (403) + AuditEvent result=denied (ohne PII)



\### AT-RBAC-02: Public sieht nur Public-QR + Blog

\- Given: unauthenticated user

\- When: ruft geschützte APIs (Vehicle/Entry/Document) auf

\- Then: 401/403 (je Design), keine Datenleaks, keine PII



\### AT-RBAC-03: Dealer org scope nur nach Approval

\- Given: dealer staff status=pending

\- When: ruft org scoped vehicle list auf

\- Then: denied

\- And: nach admin approval → allowed



---



\## 2) Auth Security (MUST)

\### AT-AUTH-01: Anti-Enumeration

\- Given: E-Mail existiert vs existiert nicht

\- When: request verification

\- Then: Response identisch (Statuscode + Message-Klasse), keine Existenz-Leaks



\### AT-AUTH-02: OTP niemals im Log

\- Given: OTP flow

\- When: Systeme schreiben Logs/Audit

\- Then: kein OTP/Magic-Link/Token im Klartext vorhanden



\### AT-AUTH-03: Consent Gate

\- Given: User ohne AGB/DS Consent

\- When: versucht produktive API aufzurufen

\- Then: blocked (CONSENT\_REQUIRED\_BLOCK), Consent UI erzwingt Annahme



---



\## 3) Upload Security (MUST)

\### AT-UP-01: Quarantäne by default

\- Given: user lädt Dokument hoch

\- Then: Document.quarantine\_status=QUARANTINED

\- And: user kann Inhalt nicht abrufen, bevor freigegeben



\### AT-UP-02: Allowlist enforced

\- Given: upload mit nicht erlaubtem Typ

\- Then: rejected, AuditEvent UPLOAD\_REJECTED, kein Storage write



---



\## 4) Export Policy (MUST)

\### AT-EX-01: Redacted export enthält keine PII

\- Given: user exportiert own data

\- Then: Export enthält keine Klartext-E-Mail/Name/Adresse



\### AT-EX-02: Full export nur admin + step-up

\- Given: vip/dealer versucht full export

\- Then: denied + audit

\- Given: admin ohne step-up

\- Then: denied/step-up required

\- Given: admin mit step-up

\- Then: full export erstellt verschlüsselt + TTL + audit



---



\## 5) Audit (MUST)

\### AT-AUD-01: Security Events werden auditiert

\- Given: role grant, org approval, export, public share rotate, verification set

\- Then: AuditEvent vorhanden mit Pflichtfeldern

\- And: redacted\_metadata enthält keine PII/Secrets



---



\## 6) Public-QR (MUST)

\### AT-PUB-01: Public Output ohne Metrics

\- Given: public QR view

\- Then: UI/Response zeigt keine Zahlen/Counts/Prozente/Zeiträume

\- And: Disclaimer sichtbar



\### AT-PUB-02: Token rotation

\- Given: vip/dealer rotiert public token

\- Then: alter Link invalid, neuer Link valid, AuditEvent PUBLIC\_SHARE\_ROTATED



---



\## 7) Admin Baseline (MUST)

\### AT-ADM-01: Step-up required for sensitive admin actions

\- Given: admin ohne step-up

\- When: role grant / full export / partner accreditation

\- Then: step-up required + audit



\### AT-ADM-02: PII masked by default

\- Given: admin UI user list

\- Then: PII ist maskiert; Reveal nur mit step-up + audit



