# docs/02_PRODUCT_SPEC_UNIFIED.md
# LifeTimeCircle – Service Heft (Unified)
**Produkt-Spezifikation (bindend) – Nutzerfluss, Kernlogik, Trust, Gating**  
Stand: **2026-02-06** (Europe/Berlin)

> Ab jetzt existiert nur noch **LifeTimeCircle · Service Heft (Unified)**.  
> „2.0“ ist **kein Parallelzweig** mehr, sondern die ursprüngliche Vision, die in 4.0 fertig professionalisiert wird.

---

## 0) Leitplanken (nicht verhandelbar)
- Ziel: **produktionsreif** (keine Demo).
- Security: **deny-by-default + least privilege**, RBAC **serverseitig enforced**, zusätzlich **object-level checks**.
- Trust-Ampel bewertet ausschließlich **Dokumentations- und Nachweisqualität** (kein technischer Zustand).

---

## 1) Marke, Ziel, Prämisse
- Branding: **LifeTimeCircle** (zusammengeschrieben; L/T/C groß).
- Modul: **Service Heft 4.0** (läuft unter LifeTimeCircle).
- Zweck: Lebenszyklus dokumentieren, Nachweise/Vertrauen aufbauen, Werterhalt unterstützen.

Pflicht-Disclaimer (Public-QR, exakt):
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## 2) User-Flow (End-to-End) – von „Seite öffnen“ bis Fahrzeugakte

### 2.1 Frontpage (vor Login)
- Erklärungstext: Nutzen, Werterhalt, Lebenszyklus (neutral, nicht technisch bewertend).
- Zentraler CTA: **„Eintritt“**
- Legal/Info-Reihe (Footer/Leiste): **FAQ, AGB, Cookies, Jobs, Datenschutz, Kooperationen**
- Optional:
  - News/Blogbase (Content-Workflow, Moderator/Admin)
  - Newsletter Opt-in

Top-Header-Navigation (Hauptbereich, sobald im Web aktiv):
- Dashboard
- Fahrzeuge
- Module
- Profiladmin
- E-Rolle
- Anmeldung

### 2.2 Eintritt → Rollenwahl (Privat/Gewerblich)
- Auswahl: **Privat** oder **Gewerblich**
- Gewerblich-Typen (Taxonomie für „durchgeführt von“):
  - Fachwerkstatt
  - Händler
  - Autohaus
  - Reifenservice
  - Tuning-Fachbetrieb
  - Sonstiges
  - Gesetzliches: TÜV / Gutachten / Wertgutachten
  - Eigenleistung

### 2.3 Registrierung / Login
Registrierung:
- E-Mail + Passwort
- Verifizierung per **E-Mail-Code**
- Pflicht: **AGB + Datenschutz** bestätigen (Speicherung: Version + Zeitstempel)
- Re-Consent: bei neuer Version **blockierend** (nur Consent-Flow möglich, kein Produktzugriff)

Nach Verifizierung:
- erste **VIN** erfassen → direkt ins Onboarding (Ereigniseinträge), damit der „Stammbaum“ startet.

Login:
- E-Mail + Passwort (weitere Faktoren später optional)

---

## 3) Fahrzeuge, Sammlungen, Flotten (Organisation)

### 3.1 Fahrzeugklassen
- Hypercar
- Sport
- Luxus
- Alltag
- Nutzfahrzeug

### 3.2 Collections / Flotte
- Sammlungen (z.B. „Collection A“)
- Flotten
- Oldtimer/Liebhaber
- Militaria-Sammlung

### 3.3 Paywall-Regel (MVP, serverseitig)
- **1 Fahrzeug gratis**
- ab **2. Fahrzeug kostenpflichtig**
- Enforcement serverseitig (keine reine UI-Sperre)

### 3.4 Nachtrag (historische Einträge)
- Nachtrag alter Serviceeinträge (z.B. physisches Serviceheft) ist möglich.
- Nachträge erhalten einen Trust-Status (T1/T2/T3, siehe Trust).

---

## 4) Fahrzeugakte (Kernprodukt) – Haupttabs
Tabs/Module (MVP-UI-Struktur):
- Fahrzeug
- Fahrzeugakte
- Eintragung (Timeline)
- Archiv
- Rechnung
- Dokumentation
- Galerie
- Modul-Ereignisse (inkl. Systemlogs)

---

## 5) Timeline / Einträge (Ereignisse)

### 5.1 Pflichtfelder (MVP, serverseitig enforced)
- Datum
- Kategorie/Typ
- „Durchgeführt von“ (Gewerbe-Typ / Gesetzliches / Eigenleistung)
- Kilometerstand (Pflicht)

### 5.2 Optionalfelder (immer mit Hinweis „wertsteigernd“)
- Bemerkung
- Kostenbetrag

UI-Regel (immer bei Optionalfeldern):
- Hinweis: **„Datenpflege = bessere Trust-Stufe & Verkaufswert“**

### 5.3 To-dos
- To-dos aktiv ab **Gelb** (Trust-Ampel).
- Begründung je To-do:
  - Systemgrund (automatisch)
  - Owner-Notiz (optional)

---

## 6) Dokumente / Upload, Kamera, PII (Datenschutz, produktionshart)

## 6.x Trust-Evidence (harte Quelle)
Trust darf nur auf serverseitig deterministischen Evidence-Regeln aufsetzen:

Ein Dokument zählt als „valid evidence“ genau dann, wenn:
- approval_status = APPROVED
- scan_status = CLEAN
- pii_status = OK
- nicht gelöscht (deleted_at = NULL)

Upload ist immer Quarantäne-by-default:
- approval_status = QUARANTINED
- scan_status = PENDING

Approve ist nur erlaubt, wenn CLEAN + PII_OK.
INFECTED führt automatisch zu REJECTED.

PII-Regel (blockierend für T3):
- pii_status in (SUSPECTED, CONFIRMED) => Sichtbarkeit nur Owner/Admin
- solange PII offen: kein T3 möglich (Trust darf nicht grün werden durch solche Dokumente)
- MVP-Bereinigung erfolgt via Neu-Upload (Replace), nicht via Toggle/Editor.

### 6.1 Upload (MVP)
- Uploadquellen:
  - Foto aufnehmen (Kamera)
  - Datei hochladen
- Dateitypen MVP:
  - Bilder
  - PDF
  - kein Video

### 6.2 Trusted Upload (Integritätssignal)
- Pro Dokument wird ein Hash/Checksum gespeichert (Integrität/Manipulationssignal).

### 6.3 PII-Workflow (final)
Status je Dokument:
- OK
- PII vermutet
- PII bestätigt

Regeln:
- PII vermutet: Dokument bleibt gespeichert, aber nur Owner/Admin sichtbar bis bereinigt.
- Bereinigung: aktuell Neu-Upload (später optional Editor: Schwärzen/Crop).
- Solange PII offen (vermutet/bestätigt): Eintrag kann nicht **T3** werden.
- Admin-Override ist möglich (mit Audit).
- PII bestätigt und nicht bereinigt: Auto-Löschung nach X Tagen (Default: 30).

---

## 7) Verifizierung & Trust-Level (T1/T2/T3) – Nachträge

Nachträge erhalten Status:
- **T3 verifiziert**: Dokument vorhanden
- **T2 unverifiziert**: physisches Serviceheft vorhanden
- **T1 unverifiziert**: physisches Serviceheft nicht vorhanden

Leitlinien:
- Vorhistorie (nahe Baujahr) mit Serviceheft-Bildern zählt stark für Trust.
- Datumsführung ist zentral für den „roten Faden“ im Lebenslauf.

---

## 8) Public Mini-Check (QR Scan am Fahrzeug)

### 8.1 Ampel (4 Stufen)
- Rot / Orange / Gelb / Grün
- Zeigt Nachweisqualität, keine technische Bewertung.

### 8.2 Public sichtbar (datenarm)
- Fahrzeugklasse
- Marke/Modell
- Baujahr
- Motor/Antrieb (grob)
- VIN maskiert: erste 3 + letzte 4
- Public-QR v1 nutzt deterministische Reason-Codes (ohne Metriken/Zahlen/Zeitraeume im Hint).
- Mapping v1: `block -> Rot`, `cap -> Orange`, `warn -> Gelb`, keine Reasons -> Gruen.
- Public-Hint wird deterministisch aus Top-Reason (kleinste Prioritaet) abgeleitet; Gruen nutzt Fallback-Hint ohne Ziffern.
- Trust-Ampel + 1 Satz je Stufe
- Unfallstatus-Badge:
  - Unfallfrei
  - Nicht unfallfrei
  - Unbekannt

Regeln:
- J/K Details bleiben verborgen; keine sensiblen Daten.
- Pflicht-Disclaimer immer anzeigen (siehe oben).

---

## 9) Trust-Ampel & To-dos (intern)

### 9.1 Ampel-Logik (Kernregeln)
- Rot: geringe/unsichere Nachweisqualität.
- Orange: Warnbereich v.a. bei Unsicherheit/Unfallkontext (inkl. Deckelung bei „Unbekannt“).
- Gelb: solide Datenlage, Verbesserung möglich (To-dos aktiv).
- Grün: sehr gute Nachweisqualität.

Optionale Feinstufen (intern):
- Dunkelgrün: Unfallfrei + Top-Nachweise
- Hellgrün: Unfall dokumentiert & abgeschlossen + Top-Nachweise

Fehlende Nachweise ziehen aktiv nach unten (nicht nur „Grün sperren“).

### 9.2 To-dos (Priorisierung)
- VIP: Top 3 priorisiert
- Non-VIP: vollständige Liste

---

## 10) Unfalltrust (nur wenn Unfall relevant)

Regeln:
- Unfalltrust beeinflusst Scoring nur, wenn Unfallstatus relevant ist.
- Verkaufsstart fragt Unfallstatus ab: Unfallfrei / Nicht unfallfrei / Unbekannt.
- „Unbekannt“ deckelt Trust max. **Orange**.
- Bei Unfall: Grün nur bei abgeschlossenem Unfalltrust mit Belegen.

Hinweise (Nachweise):
- Bei Unfallfrei: Lackdickenmessung / Sprühnebel können als Nachweise dienen.

---

## 11) Trust-Ordner: Oldtimer-Trust & Restauration-Trust

### 11.1 Oldtimer-Trust
Ziel: Vertrauensaufbau für Oldtimer/Liebhaber trotz oft fehlender digitaler Historie.

Nachweise:
- historische Dokumente
- Serviceheft-Fotos
- alte Rechnungen
- Wertgutachten
- Fotolog
- Fachbetrieb-Nachweise

### 11.2 Restauration-Trust (Add-on, ausbaufähig)
Strukturierte Etappen:
- Karosserie, Lack, Motor, Fahrwerk, Elektrik, Innenraum, …

Pro Etappe:
- Datum
- durchgeführt von
- Dokumente/Belege
- Galerie Before/After
- optional Kosten
- Meilensteine

Ziel: Restauration als belegbare Storyline, ohne technische Bewertung.

---

## 12) Modul-Eingang (Vorschläge) & Spam-Schutz

Buttons:
- Übernehmen
- Ablehnen (Pflicht-Kommentar; intern gespeichert; später übernehmbar durch Owner + Flottenadmin)
- Später prüfen (geparkt; Filter im Eingang)

Spam-Schutz:
- pro Modul pro Fahrzeug limitiert nur nicht-essenzielle Vorschläge
- essenzielle Logs werden nicht limitiert (siehe Systemlogs)

---

## 13) Essenzielle Systemlogs (immutable)
- OBD-Log
- GPS-Probefahrt-Log

Regel:
- nicht lösch-/korrigierbar
- Fehlerbehebung nur als Doku-Anhang / Ergänzung

---

## 14) Verkauf, Transfer, Händler (klar getrennt)

### 14.1 Übergabe-QR / Owner Transfer (für alle)
- 14 Tage gültig
- 1× verlängerbar

### 14.2 Free: „Interesse am Verkauf“
- Button existiert als interne Markierung
- sichtbar nur für Admin/Owner-Kontext (nur du siehst es als Admin-Test)

### 14.3 Dealer Suite (VIP-Händler)
- Handel/Weiterverkauf intern: nur VIP-Händler / Dealer Suite
- Dealer-Inserat-Tooling (VIP-Händler)

---

## 15) PDFs, Zertifikate, Ablauf & Auto-Delete

PDF-Typen + TTL:
- QR-PDF: unbegrenzt
- Trust-Zertifikat: 90 Tage
- Wartungsstand: 30 Tage
- Inserat-Export: 30 Tage (VIP-only)

Ablage:
- Dokumentation → Zertifikate/Exports

Ablauf-Regel:
- Nach Ablauf: PDF-Datei wird gelöscht
- Serviceheft-Eintrag bleibt bestehen
- Versionierung: ersetzt (nur neueste Datei), Historie bleibt
- Erneuerung: Zertifikate erneuerbar mit Bestätigung des Users

---

## 16) Benachrichtigungen
Kanäle:
- In-App + E-Mail

Logik:
- Daily Digest
- kritisch sofort

Kritisch sofort (MVP):
- Dokument-Approval / Quarantäne-Entscheide
- essenzielle Löschungen / Plausi-Checks
- VIP-Ablauf (Zertifikate/Exports)
- Unfalltrust nötig
- To-dos ab Gelb

Ruhezeiten:
- nur VIP einstellbar (nur E-Mail)
- Free: keine Ruhezeiten (Digest bleibt)

VIP-Reminder:
- 7 Tage vor Ablauf

---

## 17) Admin, Mitarbeiter, Audit, Löschungen

Admin:
- Audit / Soft-Delete / Restore
- essenzielle Löschungen: Plausi-Check an Superadmin (du)

Löschen (UX/Regel):
- Dropdown Grund (MVP: optional erweiterbar)
- Pflicht-Kommentar

VIP-Gewerbe:
- 2 Mitarbeiter-Seats möglich (Hauptadmin/Superadmin freigeben)
- Eingriffmodus konfigurierbar (Policy via Admin)

Moderator:
- akkreditiert (Invite + Freischaltung)
- nur Blog/News (keine Halter-/Fahrzeugdaten)
- Content-Workflow: Entwurf → Review → Publish
- Publish final: Superadmin (du)

Support/Feedback:
- Profiladmin → Admin-Inbox (Status: offen / in Prüfung / gelöst)

---

## 18) Import (XLSX/CSV) – Gewerbe-ready
- Import Vehicles + Entries
- 2-Step: Validierung → Import
- Report + Infobutton/Gebrauchsanweisung

Entry Pflichtspalten:
- VIN
- Datum
- Typ
- durchgeführt von
- Kilometerstand

Optional:
- Bemerkung
- Kosten
- T-Status

Dubletten:
- skip + Report (transparent)

---

## 19) Module, Gating & Sammler-Pack (Packaging)
- Viele Module sichtbar als Showroom; MVP Kernmodule aktiv.
- Free: schlank (Kern + Dokumente + Transfer + Public + internes Interesse-Flag).
- VIP: Core Pro + Zertifikate; Toolbox-Add-ons einzeln zubuchbar.
- VIP-Händler (Dealer Suite): interner Handel, Kommunikation, Dealer-Inserat-Tooling.
- Sammler Pack:
  - Pflege/Standzeit-Empfehlungen
  - Galerie/Collection-Badges
  - Checklisten
  - optional Oldtimer-/Restauration-Add-ons

---

## 20) Add-ons: Grandfathering & Admin-Gate (Oldtimer-/Restauration-Trust)

Ziel:
- Neue Aktivierungen später kostenpflichtig/admin-gesteuert, ohne Bestandsfahrzeuge zu sperren.

Definition „neu“:
- Ein Fahrzeug gilt für ein Add-on als NEU, wenn `addon_first_enabled_at` **NULL** ist (Add-on war nie aktiv).
- Nur dann darf Gate/Paywall greifen.

Bestand (Grandfathered):
- Wenn `addon_first_enabled_at` nicht NULL:
  - volle Nutzbarkeit bleibt erhalten, auch bei Re-Aktivierung.

Admin-Schalter pro Add-on:
- Neu-Aktivierung erlaubt: ja/nein
- Neu-Aktivierung kostenpflichtig: ja/nein
- optional: Neu-Aktivierung nur durch Admin
---

## Export – Vehicle P0 (redacted + grant + full encrypted)

Ziel: Datenabfluss minimieren, aber Proof/Verifizierung ermöglichen.

- GET /export/vehicle/{id} liefert **redacted**: data._redacted=true, vin_hmac vorhanden, **kein** VIN/owner_email im Response.
- POST /export/vehicle/{id}/grant erzeugt einen **zeitlich begrenzten** Export-Token (persistiert, unique).
- GET /export/vehicle/{id}/full liefert nur mit Header X-Export-Token:
  - 400 wenn Header fehlt
  - TTL enforced (expires_at)
  - One-time enforced (used=true)
  - decrypted payload enthält payload.vehicle.vin (+ data.vehicle für P0-Kompat)

Security: RBAC serverseitig + Object-Level Owner/Admin, Moderator überall 403, no-PII Logs/Telemetry.
