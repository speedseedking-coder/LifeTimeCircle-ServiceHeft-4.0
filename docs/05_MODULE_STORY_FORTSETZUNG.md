docs/05_MODULE_STORY_FORTSETZUNG.md
# LifeTimeCircle – ServiceHeft 4.0
# Modulgeschichte (FORTSETZUNG – implementierbare Zuteilung & Gates)
Stand: 2026-01-29

> Fokus: klare Trennung Free vs VIP/Dealer vs Moderator, plus Public-QR. Serverseitig enforced, UI spiegelt nur.

---

## A) Public (ohne Login)
### A1 | Public-QR Mini-Check
**Zweck:** Vertrauenssignal über Dokumentationsqualität (nie technischer Zustand).  
**Output-Regeln:** keine Kennzahlen/Counts/Prozente/Zeiträume; Pflicht-Disclaimer.  
**Daten:** keine Halterdaten, keine Dokument-Downloads.

---

## B) Free Basic (role: user)
### B1 | Service Heft Kern
- Fahrzeug anlegen (VIN/WID), eigenes Profil, Timeline-Einträge
- Dokument-Upload im eigenen Scope
- Versionierung/Änderungshistorie pro Eintrag (MVP)

### B2 | Verifizierung & Consent (Pflicht)
- E-Mail Login + Verifizierung (Code/Magic-Link)
- AGB/Datenschutz Pflicht, Version+Timestamp

**Explizit NICHT in Free:**
- Verkauf/Übergabe-QR, interner Verkauf
- VIP-only Bild-/Dokumenttiefe
- Gewerbe-Staff/Org-Funktionen
- Moderations-/Admin-Funktionen

---

## C) VIP (role: vip)
### C1 | Alles aus Free + erweiterte Nachweis-/Bildtiefe
- Dokument-/Bildansicht „VIP only“ (gemäß Matrix)

### C2 | Verkauf/Übergabe-QR (nur VIP/Dealer)
- Übergabe-QR erzeugen
- Vorgänge im eigenen Scope protokolliert (Audit Pflicht)

### C3 | VIP-Bereich: Checklisten / Ankauf privat (PDF/Papier only)
- Freigabe nur als PDF/Print (nicht als frei editierbare Online-Checklist in Free)
- Hidden by default für Nicht-VIP

---

## D) Dealer (role: dealer, gewerblich)
### D1 | VIP-Niveau + Gewerbe-Erweiterungen (Org/Staff)
- Multi-User/Staff-Model (VIP-Gewerbe: max 2 Staff) nur nach SUPERADMIN-Freigabe

### D2 | Verkauf/Übergabe-QR & Interner Verkauf
- Wie VIP, zusätzlich gewerbliche Abläufe
- Audit & Nachvollziehbarkeit Pflicht

---

## E) Moderator (role: moderator)
### E1 | Blog/News only
- News lesen + erstellen/bearbeiten
- Keine PII, kein Export, kein Audit-Zugriff

---

## F) Admin (role: admin = SUPERADMIN)
### F1 | Governance & Freigaben
- Rollen vergeben/sperren
- Moderatoren akkreditieren
- VIP-Gewerbe Staff-Plätze freigeben
- Audit-Log einsehen (Admin only)

---

## G) Nächste „Hidden“-Module (bereit zum Einhängen, aber deny-by-default)
> Diese Module sind im UI standardmäßig verborgen und werden nur für VIP/Dealer/Admin aktiviert.

- G1 Werkstattannahme „Direktannahme“-Workflow (Check-in, Menge/Positionen, ggf. Spracheingabe)
- G2 Masterclipboard (positionsbasierte Liste, Copy-to-Workorder)
- G3 OBD-Gateway Integration + OBD-Diagnose einzeln
- G4 GPS-Probefahrt gekoppelt an Abfrage/Protokoll
- G5 Rechnungsprüfer (Dokumentprüf-Workflow)
- G6 Reimport-Identitätscheck
- G7 VIN/WID-Validierung (streng, serverseitig)
- G8 Sicherer Lichteinstellungscheck per Foto (Sitzposition/Referenz)
- G9 KI-Agenten/Assistenzautomation (Werkstattannahme, Prozesse, Verkaufsempfehlungen)

**Gate-Regel:** Alles in G* bleibt „OFF“, bis jeweilige Policies + RBAC + Audit + Upload/Privacy sauber fertig sind.
