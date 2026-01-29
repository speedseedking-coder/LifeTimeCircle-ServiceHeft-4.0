# LifeTimeCircle – Service Heft 4.0
**Product Backlog (Epics / Stories / Tasks)**  
Stand: 2026-01-27

Legende:
- **Prio:** P0 (kritisch) / P1 / P2
- **Status:** Idea / Planned / In Progress / Blocked / Done

Definition of Done (kurz):
- Feature ist rollenbasiert abgesichert (RBAC) + UI spiegelt Rechte korrekt.
- Fehler-/Edge-Cases geprüft (mind. Happy Path + 2 Negativfälle).
- Minimaler Audit-Log, wo es sicherheitsrelevant ist (Rollen, Übergaben, Verifizierung).

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

**Akzeptanz:**
- Ohne bestätigte AGB/Datenschutz keine Registrierung.
- Konto ohne Verifizierung hat keinen produktiven Zugriff.

## EPIC-03 | Rollen & Rechte (RBAC)
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] C1: Rollenmodell: public/user/vip/dealer/moderator/admin
- [ ] C2: Rechte-Matrix (wer sieht was: Fahrzeuge, Einträge, Dokumente, Blog)
- [ ] C3: Sonderregel: Verkauf/Übergabe-QR nur VIP+Dealer
- [ ] C4: VIP-Gewerbe: 2 Mitarbeiterplätze + Admin-Freigabe-Workflow
- [ ] C5: Moderator: nur News/Blog; Halterdaten strikt begrenzen

**Akzeptanz:**
- Rechte sind technisch erzwungen (API + UI).

## EPIC-04 | Admin-Bereich (Minimal)
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] D1: Admin Dashboard (Userliste, Rollen setzen)
- [ ] D2: Einladungs-/Akkreditierungsflow für Moderatoren
- [ ] D3: Freigabe-Flow für VIP-Gewerbe Mitarbeiterplätze
- [ ] D4: Audit-Log (wer hat welche Rolle wann gesetzt)

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
- [ ] E6: Änderungs-/Versionshistorie pro Eintrag

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

**Akzeptanz:**
- Public sieht klar: „Dokumentations-Trust“ + Begründungsindikatoren.

## EPIC-07 | Blogbase (Admin) + Newsletter
**Prio:** P1 | **Status:** Planned

### Stories / Tasks
- [ ] G1: Blogbase aktivierbar auf Frontpage (Admin schreibt)
- [ ] G2: Newsletter-Listenverwaltung (Opt-in/Opt-out)
- [ ] G3: Versand-Workflow (z. B. Admin erstellt Post → optional Newsletter)
- [ ] G4: Moderator UI: nur Blog/News verwalten (falls gewünscht)

**Akzeptanz:**
- Admin kann News posten und optional als Newsletter versenden.

## EPIC-08 | Landingpage & Navigation (UX-Standard)
**Prio:** P1 | **Status:** Planned

### Stories / Tasks
- [ ] H1: Landingpage: Erklärtext + Headerbar mit Modulen/Tools
- [ ] H2: Login-Panel links/rechts konfigurierbar (Default links)
- [ ] H3: Modul-Hub (Kacheln) stabil, keine „verschwindenden“ Inhalte

**Akzeptanz:**
- Mobile + Desktop sauber, Navigation vollständig, Buttons funktionieren.

## EPIC-09 | Verkauf/Übergabe-QR (VIP/Dealer only)
**Prio:** P2 | **Status:** Planned

### Stories / Tasks
- [ ] I1: Übergabe-QR/Code-Flow (VIP/Dealer)
- [ ] I2: Interner Verkauf (VIP/Dealer)
- [ ] I3: Protokoll/Audit für Übergaben

**Akzeptanz:**
- Feature ist nicht sichtbar/nutzbar für normale User.

## EPIC-10 | Qualität, Betrieb, Produktion
**Prio:** P0 | **Status:** Planned

### Stories / Tasks
- [ ] J1: Logging/Monitoring-Basis
- [ ] J2: Security-Basics (Rate limits, Passwortregeln, CSRF/CORS je Stack)
- [ ] J3: Datenschutz-Mechanik (Datenexport/Löschkonzept – minimal)
- [ ] J4: Backup/Restore-Strategie (MVP-fähig)

**Akzeptanz:**
- Minimaler Production-Standard erfüllt (kein „Demo“-Betrieb).
