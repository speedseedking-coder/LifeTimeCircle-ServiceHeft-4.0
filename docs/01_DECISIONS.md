# LifeTimeCircle – Service Heft 4.0
**Decisions Log (verbindliche Entscheidungen)**  
Stand: 2026-02-01

> Regel: Nur Dinge, die wirklich entschieden sind, kommen hier rein.  
> Alles andere gehört in Backlog/Offen.

## D-001 | Projektname/Überbegriff
**Datum:** 2026-01-27  
**Entscheidung:** Projekt/Überbegriff lautet künftig: **„LifeTimeCircle - ServiceHeft 4.0“**.  
**Hinweis:** Alter Projektname/Pfad „Digitale-Fahrzeugzukunft“ ist obsolet; neuer Root-Pfad wird neu angelegt/definiert.

## D-002 | Produkt-Titel
**Datum:** 2026-01-27  
**Entscheidung:** Produkt-Titel: **„Service Heft 4.0“** (statt Service Heft 2.0/ServiceF 2.0).

## D-003 | Branding / Schreibweise
**Datum:** 2026-01-27  
**Entscheidung:** Hauptbegriff/Branding: **„LifeTimeCircle“** (zusammengeschrieben, Life/Time/Circle jeweils groß).

## D-004 | Anmeldung / Verifizierung
**Datum:** 2026-01-27  
**Entscheidung:** Anmeldung via **E-Mail-Login** und **Verifizierung** (OTP oder Magic-Link) wird umgesetzt.

## D-005 | AGB & Datenschutz Pflicht
**Datum:** 2026-01-27  
**Entscheidung:** Anmeldung nur möglich, wenn **AGB** und **Datenschutzrichtlinien** bestätigt wurden.

## D-006 | Produktionsreife (keine Demo)
**Datum:** 2026-01-27  
**Entscheidung:** Oberste Prämisse: **benutzerfertig/produktionsreif** umsetzen, kein Demo-Charakter.

## D-007 | Verkauf/Übergabe-QR & interner Verkauf eingeschränkt
**Datum:** 2026-01-27  
**Entscheidung:** Fahrzeugverkauf (Übergabe-QR/Code) und interner Verkauf sind **nur** für **VIP-Nutzer** und **Händler (gewerblich / DEALER)** verfügbar.

## D-008 | Public-QR Mini-Check: Ampelsystem & Bedeutung
**Datum:** 2026-01-30  
**Entscheidung:** Public-QR Mini-Check nutzt 4-stufige Ampel **Rot/Orange/Gelb/Grün** und bewertet **nur** Dokumentations-/Nachweisqualität, **nicht** den technischen Zustand.  
**Zusatzregeln:** Public Response enthält **keine Metrics/Counts/Percentages/Zeiträume**; Disclaimer ist Pflicht (exakt, ohne Abwandlung):
> „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## D-009 | Public-QR Mini-Check: Kriterien (high-level)
**Datum:** 2026-01-27  
**Entscheidung:** Kriterien für Trust-Level:
- Historie vorhanden
- Verifizierungsgrad (T3/T2/T1)
- Aktualität/Regelmäßigkeit (ohne Metriken)
- Unfalltrust: Für **Grün** bei Unfall nur bei **Abschluss + Belegen**

## D-010 | VIP-Gewerbe Mitarbeiterplätze (Staff-Limit + Freigabe-Gate)
**Datum:** 2026-01-30  
**Entscheidung:** VIP-Gewerbe: **max. 2 Staff**; Freigabe/Aktivierung nur durch **SUPERADMIN** (serverseitig enforced).  
**Hinweis:** Normale Admin-Endpunkte dürfen **kein** SUPERADMIN-Provisioning durchführen (out-of-band Bootstrap/Seed/Deployment).

## D-011 | Moderatoren: Akkreditierung & Zugriff (strikt)
**Datum:** 2026-01-30  
**Entscheidung:** Moderator: Zugriff **nur** auf Blog/News.  
**Explizit verboten:** Vehicles/Entries/Documents/Verification, **kein Export**, **kein Audit-Read**, **keine PII/Halterdaten**.

## D-012 | Landingpage Layout-Standard (Login-Panel)
**Datum:** 2026-01-30  
**Entscheidung:** Landingpage: Hauptseite mit Erklärtext, obere Headerbar mit Modulen/Tools, Login-Panel (E-Mail-Login + OTP/Magic-Link) links/rechts anordbar. Standard: **links**.

## D-013 | Blogbase + Newsletter
**Datum:** 2026-01-27  
**Entscheidung:** Frontpage hat aktivierbare **Blogbase** (Admin-News) und **Newsletter** zur wechselseitigen Kommunikation.

## D-014 | Projekt-Kontakt-E-Mail
**Datum:** 2026-01-27  
**Entscheidung:** Kontakt-E-Mail: **lifetimecircle@online.de**

## D-015 | Exports: Redacted Default + Full Export Gate
**Datum:** 2026-01-30  
**Entscheidung:** Exports sind standardmäßig **redacted** (keine Klartext-PII, keine Secrets; Pseudonyme via HMAC).  
**Full Export:** nur **SUPERADMIN** mit **one-time Grant-Token**, **TTL/Limit**, **Audit ohne PII/Secrets** und **verschlüsselter Response**; Tokens werden niemals im Klartext geloggt.
