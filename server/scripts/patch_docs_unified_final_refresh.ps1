# server/scripts/patch_docs_unified_final_refresh.ps1
# Idempotent docs refresh: unify product spec + decisions + rights matrix + work rules + repo structure + master checkpoint alignment
# PowerShell 7+ recommended

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Normalize-Newlines([string]$s) {
  if ($null -eq $s) { return "`n" }
  $s = $s -replace "`r`n", "`n"
  $s = $s -replace "`r", "`n"
  if (-not $s.EndsWith("`n")) { $s += "`n" }
  return $s
}

function Write-FileUtf8NoBom([string]$path, [string]$content) {
  $content = Normalize-Newlines $content
  $dir = Split-Path -Parent $path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }

  $existing = $null
  if (Test-Path -LiteralPath $path) {
    try {
      $existing = Get-Content -LiteralPath $path -Raw -ErrorAction Stop
      $existing = Normalize-Newlines $existing
    } catch {
      $existing = $null
    }
  }

  if ($existing -eq $content) {
    Write-Host "OK: $path (no changes needed)."
    return
  }

  [System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))
  Write-Host "UPDATED: $path"
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot
Write-Host "Repo-Root: $RepoRoot"

# ---------------------------
# docs/02_PRODUCT_SPEC_UNIFIED.md
# ---------------------------
$productSpec = @'
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
- Sammlungen
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
- **T3 verifiziert**: Dokument vorhanden
- **T2 unverifiziert**: physisches Serviceheft vorhanden
- **T1 unverifiziert**: physisches Serviceheft nicht vorhanden

Leitlinien:
- Vorhistorie (nahe Baujahr) mit Serviceheft-Fotos zählt stark.
- Datumsführung ist zentral.

---

## 8) Public Mini-Check (QR Scan am Fahrzeug)
- Ampel (4 Stufen): Rot / Orange / Gelb / Grün
- Public sichtbar (datenarm):
  - Fahrzeugklasse, Marke/Modell, Baujahr, Motor/Antrieb grob
  - VIN maskiert: erste 3 + letzte 4
  - Trust-Ampel + 1 Satz je Stufe
  - Unfallstatus-Badge: Unfallfrei / Nicht unfallfrei / Unbekannt
- Pflicht-Disclaimer immer anzeigen (siehe oben).

---

## 9) Trust-Ampel & To-dos (intern)
- Rot: geringe/unsichere Nachweisqualität
- Orange: Warnbereich; „Unbekannt“ deckelt max Orange
- Gelb: solide; To-dos aktiv
- Grün: sehr gute Nachweisqualität

Optional intern:
- Dunkelgrün: Unfallfrei + Top-Nachweise
- Hellgrün: Unfall dokumentiert & abgeschlossen + Top-Nachweise

To-dos:
- VIP: Top 3 priorisiert
- Non-VIP: vollständige Liste

---

## 10) Unfalltrust (nur wenn Unfall relevant)
- Verkaufsstart fragt Unfallstatus: Unfallfrei / Nicht unfallfrei / Unbekannt
- „Unbekannt“ deckelt Trust max **Orange**
- Bei Unfall: Grün nur bei abgeschlossenem Unfalltrust mit Belegen
- Hinweise: Lackdickenmessung / Sprühnebel als mögliche Nachweise

---

## 11) Trust-Ordner: Oldtimer-Trust & Restauration-Trust
Oldtimer-Trust:
- Historische Dokumente, Serviceheft-Fotos, alte Rechnungen, Wertgutachten, Fotolog, Fachbetrieb-Nachweise

Restauration-Trust (Add-on):
- Etappen (Karosserie, Lack, Motor, Fahrwerk, Elektrik, Innenraum, …)
- je Etappe: Datum, durchgeführt von, Dokumente/Belege, Before/After, optional Kosten, Meilensteine

---

## 12) Modul-Eingang (Vorschläge) & Spam-Schutz
Buttons:
- Übernehmen
- Ablehnen (Pflicht-Kommentar; intern gespeichert; später übernehmbar)
- Später prüfen (geparkt; Filter)

Spam-Schutz:
- limitiert nur nicht-essentielle Vorschläge
- essentielle Logs nicht limitiert

---

## 13) Essenzielle Systemlogs (immutable)
- OBD-Log, GPS-Probefahrt-Log: nicht lösch-/korrigierbar; nur Ergänzungen als Doku-Anhang

---

## 14) Verkauf, Transfer, Händler
- Übergabe-QR/Owner Transfer: für alle, 14 Tage gültig, 1× verlängerbar
- Free: „Interesse am Verkauf“ = interne Markierung (nur Admin-Test sichtbar)
- Dealer Suite: Handel/Weiterverkauf intern nur VIP-Händler

---

## 15) PDFs, Zertifikate, Ablauf & Auto-Delete
- QR-PDF unbegrenzt
- Trust-Zertifikat 90 Tage
- Wartungsstand 30 Tage
- Inserat-Export 30 Tage (VIP-only)
Ablauf:
- Datei wird gelöscht, Historie-Eintrag bleibt
- nur neueste Datei; Historie bleibt
- Erneuerung nur nach User-Bestätigung

---

## 16) Benachrichtigungen
- In-App + E-Mail
- Daily Digest + kritisch sofort
- VIP: Ruhezeiten (nur E-Mail) + Reminder 7 Tage vor Ablauf
- Free: keine Ruhezeiten (Digest bleibt)

---

## 17) Admin, Moderatoren, Support
- Admin: Audit/Soft-Delete/Restore; essenzielle Löschungen als Plausi-Check an Superadmin
- Moderator: nur Blog/News (Entwurf → Review → Publish; Publish final Superadmin)
- Support/Feedback: Profiladmin → Admin-Inbox (offen/in Prüfung/gelöst)

---

## 18) Import (XLSX/CSV)
- Vehicles + Entries
- 2-Step: Validierung → Import + Report + Infobutton
- Pflichtspalten: VIN, Datum, Typ, durchgeführt von, Kilometerstand
- Optional: Bemerkung, Kosten, T-Status
- Dubletten: skip + Report

---

## 19) Module, Gating & Sammler-Pack (Packaging)
- Module als Showroom sichtbar; MVP Kernmodule aktiv
- Free: Kern + Dokumente + Transfer + Public + Interesse-Flag
- VIP: Core Pro + Zertifikate; Add-ons einzeln
- VIP-Händler: Dealer Suite + Inserat-Tooling
- Sammler Pack: Empfehlungen, Badges, Checklisten; optional Oldtimer-/Restauration-Add-ons

---

## 20) Add-ons: Grandfathering & Admin-Gate
- Gate/Paywall betrifft nur Neuaktivierung: `addon_first_enabled_at == NULL`
- Bestand bleibt voll nutzbar (auch bei Reaktivierung)
- Admin-Schalter pro Add-on: neu erlauben, neu kostenpflichtig, optional admin-only
'@

# ---------------------------
# docs/01_DECISIONS.md (cleaned, no duplicates)
# ---------------------------
$decisions = @'
# docs/01_DECISIONS.md
# LifeTimeCircle – Service Heft 4.0
**Entscheidungen / SoT (Decisions Log)**  
Stand: **2026-02-06**

> Regel: Wenn etwas nicht explizit erlaubt ist → **deny-by-default**.

---

## D-001: RBAC serverseitig enforced (deny-by-default + least privilege)
**Status:** beschlossen  
**Warum:** Client ist manipulierbar.  
**Konsequenz:** Jede Route ist gated; Tests prüfen Guard-Coverage.

## D-002: Moderator strikt nur Blog/News
**Status:** beschlossen  
**Warum:** least privilege, kein Zugriff auf Fahrzeug-/Dokumentdaten.  
**Konsequenz:** Moderator außerhalb Blog/News überall **403**.

## D-003: Export redacted (Dokumente nur APPROVED)
**Status:** beschlossen  
**Warum:** Datenabfluss minimieren.  
**Konsequenz:** Exports liefern Dokument-Refs nur mit Status **APPROVED**.

## D-004: Uploads Quarantäne-by-default
**Status:** beschlossen  
**Warum:** Uploads sind Angriffspfad.  
**Konsequenz:** Neu-Uploads sind quarantined; Auslieferung erst nach Freigabe.

## D-005: Quarantäne Review Admin-only
**Status:** beschlossen  
**Warum:** Review ist sicherheitskritisch.  
**Konsequenz:** Quarantäne-Liste/Approve/Reject nur `admin/superadmin`.

## D-006: Actor required → 401 (unauth) statt 403
**Status:** beschlossen  
**Warum:** saubere Semantik.  
**Konsequenz:** Ohne Actor: 401. Mit Actor aber verboten: 403.

## D-007: Scan-Status + Approve nur bei CLEAN
**Status:** beschlossen  
**Warum:** Freigabe nur nach Scan.  
**Konsequenz:** Approve nur wenn `scan_status=CLEAN`, sonst 409. INFECTED auto-reject.

## D-008: Sale/Transfer Status nur Initiator oder Redeemer (object-level)
**Status:** beschlossen  
**Warum:** Status darf nicht erratbar sein (ID-Leak).  
**Konsequenz:** `GET /sale/transfer/status/{tid}` nur Initiator|Redeemer; sonst 403.

## D-009: Produkt ist „Unified“ (kein Parallelzweig „2.0“)
**Status:** beschlossen  
**Warum:** Drift verhindern.  
**Konsequenz:** Bindend: `docs/02_PRODUCT_SPEC_UNIFIED.md`.

## D-010: Consent versioniert + zeitgestempelt; Re-Consent blockierend
**Status:** beschlossen  
**Warum:** Rechtssicherheit.  
**Konsequenz:** AGB/DS speichern `version`+`accepted_at`; ohne Re-Consent keine Produkt-Routen.

## D-011: Paywall Fahrzeuge (1 gratis, ab 2 kostenpflichtig) serverseitig
**Status:** beschlossen  
**Warum:** UI-only ist umgehbar.  
**Konsequenz:** Server prüft Entitlements/Plan beim 2. Fahrzeug.

## D-012: Add-on Gate nur bei Erstaktivierung (Grandfathering)
**Status:** beschlossen  
**Warum:** kein Downgrade für Bestand.  
**Konsequenz:** Gate nur wenn `addon_first_enabled_at == NULL`.

## D-013: PII-Workflow blockiert T3; confirmed ohne Bereinigung auto-delete (Default 30d)
**Status:** beschlossen  
**Warum:** DSGVO/PII Risiko minimieren.  
**Konsequenz:** PII suspected/confirmed nur Owner/Admin; T3 blockiert; Admin-Override auditpflichtig; confirmed→Auto-Löschung (Default 30 Tage).

## D-014: Trusted Upload speichert Hash/Checksum
**Status:** beschlossen  
**Warum:** Integritätssignal/Nachweisqualität.  
**Konsequenz:** Hash/Checksum pro Dokument gespeichert.

## D-015: Essenzielle Systemlogs immutable (OBD/GPS)
**Status:** beschlossen  
**Warum:** Nachweiswert entsteht durch Unveränderbarkeit.  
**Konsequenz:** nicht lösch-/editierbar; nur Ergänzungen.

## D-016: PDFs/Zertifikate TTL; Datei weg, Historie bleibt; Erneuerung nur mit User-Bestätigung
**Status:** beschlossen  
**Warum:** Datenabfluss reduzieren.  
**Konsequenz:** Trust 90d, Wartung 30d, Inserat 30d (VIP), QR unbegrenzt; Ablauf löscht Datei, Historie bleibt.

## D-017: E2E Nutzerfluss ist bindend (Landing→Eintritt→Rolle→Signup→Consent→VIN→Einträge)
**Status:** beschlossen  
**Warum:** Fragmentierung verhindern, Onboarding liefert sofort Wert.  
**Konsequenz:** Umsetzung folgt `docs/02_PRODUCT_SPEC_UNIFIED.md`.

## D-018: Gewerbe-Typen Taxonomie für „durchgeführt von“
**Status:** beschlossen  
**Warum:** Vergleichbarkeit/Filterbarkeit.  
**Konsequenz:** feste Kategorien laut Produkt-Spec.

## D-019: Entry Pflichtfelder + Optionalfelder + UX-Hinweis verbindlich
**Status:** beschlossen  
**Warum:** roter Faden + Nachweisqualität.  
**Konsequenz:** Pflicht: Datum/Typ/durchgeführt von/KM; Optional: Bemerkung/Kosten + Hinweis „wertsteigernd“.

## D-020: T1/T2/T3 Definition normiert (physisches Serviceheft)
**Status:** beschlossen  
**Warum:** Nachträge nachvollziehbar einstufen.  
**Konsequenz:** T3=Dokument; T2=phys. Serviceheft vorhanden; T1=kein phys. Serviceheft.

## D-021: Unfallstatus „Unbekannt“ deckelt Trust max Orange; Grün bei Unfall nur nach Abschluss mit Belegen
**Status:** beschlossen  
**Warum:** Unklarheit ist Risiko.  
**Konsequenz:** „Unbekannt“→max Orange; „Nicht unfallfrei“→Grün nur mit abgeschlossenem Unfalltrust.

## D-022: To-dos ab Gelb; VIP Top 3 priorisiert, Non-VIP komplette Liste
**Status:** beschlossen  
**Warum:** Fokus für VIP, Transparenz für alle.  
**Konsequenz:** To-dos ab Gelb; Systemgrund + optionale Owner-Notiz.

## D-023: Notifications: Daily Digest + kritisch sofort; VIP Ruhezeiten nur E-Mail
**Status:** beschlossen  
**Warum:** Relevanz ohne Spam.  
**Konsequenz:** Kritisch sofort (Approvals, essenzielle Löschungen, Abläufe, Unfalltrust nötig, To-dos ab Gelb). VIP: Ruhezeiten E-Mail.

## D-024: Blog/News Workflow: Draft → Review → Publish (final Superadmin)
**Status:** beschlossen  
**Warum:** Qualität/Verantwortung.  
**Konsequenz:** Moderator erstellt Draft; Admin review; Superadmin publish.

## D-025: Import 2-Step (Validate→Run) + Report; Dubletten skip + Report
**Status:** beschlossen  
**Warum:** keine „blind writes“.  
**Konsequenz:** Validate Pflicht; Run erst danach; Report immer; Dubletten transparent skip.
'@

# ---------------------------
# docs/03_RIGHTS_MATRIX.md (align with "Moderator strikt nur Blog/News")
# ---------------------------
$rights = @'
# docs/03_RIGHTS_MATRIX.md
# LifeTimeCircle – Service Heft 4.0
**Rights / RBAC Matrix (SoT)**  
Stand: **2026-02-06** (Europe/Berlin)

> Rollen sind serverseitig enforced. Default: deny-by-default.  
> Zusätzlich gilt object-level (Owner/Business/Scope).  
> Produkt-Spezifikation ist bindend: `docs/02_PRODUCT_SPEC_UNIFIED.md`

---

## 1) Rollen
- `superadmin`: Vollzugriff (System, Admin, Support, Publish)
- `admin`: Admin-Funktionen, Quarantäne-Review, Review
- `dealer`: Business-User (Dealer Suite), kein Admin/Quarantäne
- `vip`: Premium-Enduser, kein Admin/Quarantäne
- `user`: Standard-Enduser
- `moderator`: strikt nur Blog/News (keine Fahrzeuge/Dokumente/Trust/Exports/PII/Audit)

---

## 2) Globale Regeln
- deny-by-default: jede Route explizit gated
- Actor required: ohne Actor → 401
- Keine PII/Secrets in Logs/Responses/Exports

### Moderator (hart)
Moderator ist **nur** erlaubt für:
- `/auth/*`
- `/health`
- `/public/*`
- `/blog/*` (read)
- `/news/*` (read)
- optional später (wenn implementiert): `/cms/blog/*`, `/cms/news/*` (Draft/Edit)

Alles andere: **403**.

### Consent Gate
- Produkt-Routen erfordern die aktuellste akzeptierte Version
- ohne Re-Consent: nur Consent-Flow erlaubt (wenn/sofern freigeschaltet; default: deny)

### Uploads / Quarantäne
- Quarantine-by-default
- Approve nur nach Scan CLEAN

### Exports
- für Nicht-Admins nur redacted
- Dokument-Refs nur APPROVED

---

## 3) Public (ohne Login)
- `/public/*` ist frei
- Public Datenarmut: Klasse, Marke/Modell, Baujahr, Motor/Antrieb grob
- VIN maskiert: erste 3 + letzte 4
- Trust-Ampel + Unfallstatus-Badge
- Pflicht-Disclaimer (exakt):
  - „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## 4) Dokumente (`/documents/*`)
- Upload erlaubt für user/vip/dealer (object-level)
- Read/Download für user/vip/dealer **nur** wenn APPROVED + Scope passt
- Quarantäne-Liste/Approve/Reject/Rescan: nur admin/superadmin
- Moderator: überall 403

PII:
- suspected/confirmed nur Owner/Admin
- solange PII offen: Trust T3 blockiert
- Admin-Override auditpflichtig

---

## 5) Sale/Transfer Status (Security)
- `GET /sale/transfer/status/{tid}`: Role-Gate (vip|dealer) + object-level (Initiator|Redeemer)

---

## 6) Add-ons / Grandfathering
- Gate nur bei Erstaktivierung: `addon_first_enabled_at == NULL`
- Bestandsfahrzeuge bleiben nutzbar (auch bei Reaktivierung)
- Admin-Schalter: neu erlauben, neu kostenpflichtig, optional admin-only
'@

# ---------------------------
# docs/06_WORK_RULES.md
# ---------------------------
$workRules = @'
# docs/06_WORK_RULES.md
# LifeTimeCircle – Service Heft 4.0
**Arbeitsregeln (Chat/Umsetzung) – SoT**  
Stand: **2026-02-06** (Europe/Berlin)

## Sprache / Output
- Deutsch
- maximal konkret
- keine Floskeln
- nicht nachfragen außer zwingend (sonst Defaultannahme)

## Code-Regeln
- Keine ZIPs.
- Wenn Code/Dateien: immer vollständiger Dateipfad + kompletter Dateiinhalt.
- Keine Platzhalter / keine halben Snippets.
- Wenn zu lang: Block 1/n … n/n.

## Source of Truth (SoT)
- ./docs ist SoT (keine Altpfade, keine Parallel-Spezifikationen).
- Immer zuerst: `docs/99_MASTER_CHECKPOINT.md`
- Produkt-Spezifikation (bindend): `docs/02_PRODUCT_SPEC_UNIFIED.md`

## Konflikt-Priorität
1) `docs/99_MASTER_CHECKPOINT.md`
2) `docs/02_PRODUCT_SPEC_UNIFIED.md`
3) `docs/03_RIGHTS_MATRIX.md`
4) `docs/01_DECISIONS.md`
5) `server/`
6) Backlog/sonstiges

## Security Default (nicht verhandelbar)
- deny-by-default + least privilege
- RBAC serverseitig enforced + object-level checks
- Moderator strikt nur Blog/News; sonst überall 403
- Keine PII/Secrets in Logs/Responses/Exports

## Doku-Disziplin
Jede Feature-/Policy-/Flow-Änderung erfordert Update in ./docs:
- `docs/99_MASTER_CHECKPOINT.md`
- `docs/01_DECISIONS.md`
- `docs/03_RIGHTS_MATRIX.md`
- `docs/02_PRODUCT_SPEC_UNIFIED.md`

## Env-Hinweis
- Export/Redaction/HMAC braucht `LTC_SECRET_KEY` (>=16); Tests/DEV setzen ihn explizit.

## Public-QR Pflichttext (exakt, unverändert)
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“
'@

# ---------------------------
# docs/04_REPO_STRUCTURE.md
# ---------------------------
$repoStructure = @'
# docs/04_REPO_STRUCTURE.md
# LifeTimeCircle – Service Heft 4.0
**Repo-Struktur / Source of Truth (SoT)**  
Stand: **2026-02-06**

> ./docs ist Source of Truth.

---

## 1) SoT
- ./docs ist SoT für Architektur, Policy, RBAC, Workflow, Produkt-Spezifikation.
- Keine Altpfade/Altversionen (keine Kopien unter server/ etc.).

## 2) Struktur (Soll)
LifeTimeCircle-ServiceHeft-4.0/
- docs/
  - 01_DECISIONS.md
  - 02_PRODUCT_SPEC_UNIFIED.md
  - 03_RIGHTS_MATRIX.md
  - 04_REPO_STRUCTURE.md
  - 06_WORK_RULES.md
  - 99_MASTER_CHECKPOINT.md
- server/
- packages/
  - web/
- .github/
  - workflows/

## 3) Quick Commands (Repo-Root)
```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0"

git switch main
git pull --ff-only origin main
git status -sb

cd .\server
$env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"
poetry run pytest -q

cd ..
pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_web_toolkit.ps1 -Smoke -Clean