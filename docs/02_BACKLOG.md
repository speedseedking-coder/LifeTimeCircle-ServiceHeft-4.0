# LifeTimeCircle – Service Heft 4.0
**Product Backlog (Epics / Stories / Tasks)**  
Stand: 2026-01-29

Legende:
- **Prio:** P0 (kritisch) / P1 / P2
- **Status:** Idea / Planned / In Progress / Blocked / Done

Definition of Done (kurz):
- Feature ist rollenbasiert abgesichert (RBAC) + UI spiegelt Rechte korrekt.
- Fehler-/Edge-Cases geprüft (mind. Happy Path + 2 Negativfälle).
- Minimaler Audit-Log, wo es sicherheitsrelevant ist (Rollen, Übergaben, Verifizierung).
- Public-QR zeigt **keine Metriken/Counts/Percentages/Zeiträume** und enthält **Disclaimer**.

## EPIC-01 | Fundament: Projektstruktur & Branding
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] A1: Neuer Root-Pfad/Repo-Struktur für „LifeTimeCircle - ServiceHeft 4.0“ festlegen (Alt: Digitale-Fahrzeugzukunft obsolet)
- [ ] A2: Branding-Texte vereinheitlichen (LifeTimeCircle / Service Heft 4.0) über UI/Docs
- [ ] A3: Kontakt-E-Mail in Footer/Impressum/Contact integrieren: lifetimecircle@online.de

**Akzeptanz:**
- Alle Seiten/Module zeigen korrektes Naming, keine „2.0“-Reste.

## EPIC-02 | Auth: Login + Verifizierung + Consent
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] B1: Registrierung/Login per E-Mail (Basis)
- [ ] B2: Verifizierung (Code **oder** Magic-Link) implementieren
- [ ] B3: Pflicht-Checkboxen: AGB + Datenschutz (ohne Zustimmung kein Account)
- [ ] B4: Passwort-Reset / Account-Recovery (minimal, aber produktionsfähig)
- [ ] B5: Session/Token-Handling + Logout
- [ ] B6: Anti-Enumeration + Rate-Limits + TTL für Codes/Links

**Akzeptanz:**
- Ohne bestätigte AGB/Datenschutz keine Registrierung.
- Konto ohne Verifizierung hat keinen produktiven Zugriff.

## EPIC-03 | Rollen & Rechte (RBAC)
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] C1: Rollenmodell: public/user/vip/dealer/moderator/admin
- [ ] C2: Rechte-Matrix technisch abbilden (serverseitige Policy; deny-by-default)
- [ ] C3: Sonderregel: Verkauf/Übergabe-QR nur VIP+Dealer
- [ ] C4: VIP-Gewerbe: 2 Mitarbeiterplätze + Admin-Freigabe-Workflow
- [ ] C5: Moderator: nur News/Blog; Halterdaten strikt begrenzen
- [ ] C6: SUPERADMIN-Claim für Hochrisiko-Operationen (Full Export, Freigaben)

**Akzeptanz:**
- Rechte sind technisch erzwungen (API), UI spiegelt Rechte.

## EPIC-04 | Admin-Bereich (Minimal)
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] D1: Admin Dashboard (Userliste, Rollen setzen)
- [ ] D2: Einladungs-/Akkreditierungsflow für Moderatoren
- [ ] D3: Freigabe-Flow für VIP-Gewerbe Mitarbeiterplätze (2 Plätze)
- [ ] D4: Audit-Log (wer hat welche Rolle wann gesetzt)
- [ ] D5: Sperren/Entsperren (minimal, aber sicher)

**Akzeptanz:**
- Admin kann alle „Freischaltungen“ ohne Handarbeit im Code erledigen.

## EPIC-05 | Service Heft 4.0 Kern: Fahrzeug & Einträge
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] E1: Fahrzeug anlegen/suchen (VIN/WID; Felddefinitionen festlegen)
- [ ] E2: Fahrzeugprofil-Ansicht (Basisdaten, Timeline)
- [ ] E3: Eintragsarten: Service/Wartung/Reparatur/Umbau/Unfall/Prüfung
- [ ] E4: Dokumente/Nachweise (Upload, Metadaten, Sichtbarkeit)
- [ ] E5: Verifizierungsstufen T1/T2/T3 definieren & speichern
- [ ] E6: Änderungs-/Versionshistorie pro Eintrag (mind. wer/was/wann)
- [ ] E7: Soft-Delete Strategie (Einträge/Dokumente) + Restore (Admin)

**Akzeptanz:**
- Einträge sind strukturiert, nachvollziehbar und versioniert.

## EPIC-06 | Public-QR Mini-Check (Trust Ampel)
**Prio:** P1 | **Status:** Planned

### Stories / Tasks
- [ ] F1: Public-View via QR-Link (anonyme Ansicht)
- [ ] F2: Trust-Level Ampel (Rot/Orange/Gelb/Grün) berechnen
- [ ] F3: Kriterien implementieren:
  - Historie vorhanden
  - Verifizierungsgrad T1/T2/T3
  - Aktualität/Regelmäßigkeit
  - Unfalltrust: Grün nur bei Abschluss + Belegen
- [ ] F4: „Disclaimer“: bewertet Dokumentationsqualität, **nicht** technischen Zustand
- [ ] F5: Public Response ohne Metriken/Counts/Percentages/Zeiträume (nur Indikator-Codes)

**Akzeptanz:**
- Public sieht klar: „Dokumentations-Trust“ + Begründungsindikatoren + Disclaimer.

## EPIC-07 | Blogbase (Admin) + Newsletter
**Prio:** P1 | **Status:** Planned

### Stories / Tasks
- [ ] G1: Blogbase aktivierbar auf Frontpage (Admin schreibt)
- [ ] G2: Newsletter-Listenverwaltung (Opt-in/Opt-out)
- [ ] G3: Versand-Workflow (z. B. Admin erstellt Post → optional Newsletter)
- [ ] G4: Moderator UI: nur Blog/News verwalten

**Akzeptanz:**
- Admin kann News posten und optional als Newsletter versenden.

## EPIC-08 | Security/Privacy Baseline (Logs/Audit/Export)
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] H1: Audit-Events für sicherheitsrelevante Aktionen (Rollen, Verifizierung, Übergabe/Verkauf, Exports)
- [ ] H2: Pseudonymisierung via HMAC (keine Klartext-PII in Logs/Audit)
- [ ] H3: Log-Sanitizer: Secrets/PII-Klassen blocken (deny-by-default)
- [ ] H4: Export: Default **redacted** (Standard)
- [ ] H5: Full Export: nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung
- [ ] H6: Upload/Download: Zugriff via RBAC, niemals „public files“

**Akzeptanz:**
- Audit/Logs sind PII-sicher; Exports regelkonform.

## EPIC-09 | Uploads: Allowlist + Limits + Quarantine-by-default
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] I1: Upload-Allowlist (PDF/JPG/PNG) + Größenlimits + Anzahllimits
- [ ] I2: Quarantine-by-default + Scan/Approval Flag (Admin oder automatisiert)
- [ ] I3: Metadaten (Typ, Datum, Quelle, T-Level) + Sichtbarkeitsregeln
- [ ] I4: Secure Storage Pfadmodell (kein guessable public path)

**Akzeptanz:**
- Uploads sind standardmäßig quarantined und nicht öffentlich.

## EPIC-10 | Export/Import (redacted & full)
**Prio:** P1 | **Status:** Planned

### Stories / Tasks
- [ ] J1: Redacted Export (PDF/JSON) für User/VIP/Dealer (ohne Klartext-PII)
- [ ] J2: Full Export nur SUPERADMIN (Audit + TTL/Limit + Verschlüsselung)
- [ ] J3: Export-Audit-Übersicht (Admin)
- [ ] J4: Import (minimal) mit Identitäts-/Integritätscheck + Audit

**Akzeptanz:**
- Export/Import ist regelkonform und auditierbar.

## EPIC-11 | Observability (minimal, produktionsfähig)
**Prio:** P1 | **Status:** Planned

### Stories / Tasks
- [ ] K1: Health-Checks (API/DB/Storage)
- [ ] K2: Request-ID/Korrelation (ohne PII)
- [ ] K3: Security Alerts (Rate-Limit Triggers, verdächtige Login-Versuche)

**Akzeptanz:**
- Betrieb ist nachvollziehbar ohne PII-Leak.

## EPIC-12 | Tech-Stack & Deployment-Entscheidung
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] L1: Tech-Stack festlegen (Frontend/Backend/DB/Hosting)
- [ ] L2: Environments (dev/stage/prod) + Secrets-Management + Migrations
- [ ] L3: CI Minimal (Lint/Build/Test)

**Akzeptanz:**
- Stack ist entschieden und reproduzierbar deploybar.
