# LifeTimeCircle – Service Heft 4.0
**Decisions Log (verbindliche Entscheidungen)**  
Stand: 2026-01-29

> Regel: Nur Dinge, die wirklich entschieden sind, kommen hier rein.  
> Alles andere gehört in Backlog/Offen.

## D-001 | Projektname/Überbegriff
**Datum:** 2026-01-27  
**Entscheidung:** Projekt/Überbegriff lautet künftig: **„LifeTimeCircle - ServiceHeft 4.0“**.

## D-002 | Produkt-Titel
**Datum:** 2026-01-27  
**Entscheidung:** Produkt-Titel: **„Service Heft 4.0“**.

## D-003 | Branding / Schreibweise
**Datum:** 2026-01-27  
**Entscheidung:** Brand: **„LifeTimeCircle“** (zusammengeschrieben).

## D-004 | Anmeldung / Verifizierung
**Datum:** 2026-01-27  
**Entscheidung:** Anmeldung via **E-Mail-Login** und **Verifizierung** (Code/Link).

## D-005 | AGB & Datenschutz Pflicht
**Datum:** 2026-01-27  
**Entscheidung:** Anmeldung nur mit bestätigten **AGB** und **Datenschutz** (Version + Timestamp speichern).

## D-006 | Produktionsreife (keine Demo)
**Datum:** 2026-01-27  
**Entscheidung:** Umsetzung **produktionsreif**, kein Demo-Charakter.

## D-007 | Verkauf/Übergabe-QR & interner Verkauf eingeschränkt
**Datum:** 2026-01-27  
**Entscheidung:** Übergabe/Verkauf nur **VIP** und **Dealer**.

## D-008 | Public-QR Mini-Check: Ampelsystem & Bedeutung
**Datum:** 2026-01-27  
**Entscheidung:** Ampel **Rot/Orange/Gelb/Grün** bewertet **nur** Dokumentations-/Nachweisqualität (nie technischen Zustand).  
**Pflicht-Disclaimer (Public, exakte Copy):**  
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## D-009 | Public-QR Mini-Check: Kriterien
**Datum:** 2026-01-27  
**Entscheidung:** Kriterien:
- Historie vorhanden
- Verifizierungsgrad (T1/T2/T3)
- Aktualität/Regelmäßigkeit
- Unfalltrust: **Grün** bei Unfall nur bei **Abschluss + Belegen**

## D-010 | VIP-Gewerbe Mitarbeiterplätze
**Datum:** 2026-01-27  
**Entscheidung:** VIP-Gewerbe: max **2** Staff. Freigabe nur **SUPERADMIN**.

## D-011 | Moderatoren: Zugriff
**Datum:** 2026-01-27  
**Entscheidung:** MODERATOR nur Blog/News; keine PII; kein Export; kein Audit.

## D-012 | Landingpage Layout-Standard
**Datum:** 2026-01-25  
**Entscheidung:** Login-Panel Default **links**.

## D-013 | Blogbase + Newsletter
**Datum:** 2026-01-27  
**Entscheidung:** Blogbase (Admin-News) + Newsletter.

## D-014 | Projekt-Kontakt-E-Mail
**Datum:** 2026-01-27  
**Entscheidung:** Kontakt: **lifetimecircle@online.de**

## D-015 | Security Baseline: deny-by-default + least privilege + serverseitiges RBAC
**Datum:** 2026-01-29  
**Entscheidung:** Standard ist **deny-by-default** und **least privilege**. Rechte werden **serverseitig** erzwungen.

## D-016 | Logs/Audit/PII: keine Secrets/keine Klartext-PII, Pseudonymisierung via HMAC
**Datum:** 2026-01-29  
**Entscheidung:** In Logs/Audit/Exports keine Secrets, keine Klartext-PII. Pseudonymisierung via **HMAC** (kein unsalted SHA).

## D-017 | Export-Regel: Standard redacted, Full Export nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung
**Datum:** 2026-01-29  
**Entscheidung:** Export default **redacted**. Full Export nur **SUPERADMIN** + **Audit** + **TTL/Limit** + **Verschlüsselung**.
