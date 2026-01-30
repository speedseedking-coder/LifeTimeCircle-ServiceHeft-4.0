# 99_MASTER_CHECKPOINT — LifeTimeCircle / Service Heft 4.0

Datum/Zeit 2026-01-31 00:xx — Checkpoint: export_servicebook + multitable export_store (40/40 tests green)

Headline „Checkpoint …“

Kurzliste: Export Servicebook hinzugefügt, export_store multitable v2, Tests grün (40)





Stand: 2026-01-30 (Europe/Berlin)  
Ziel: produktionsreif (keine Demo), stabiler MVP → danach Ausbau  
Kontakt: lifetimecircle@online.de  
Source of Truth (Docs): `C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs\` (keine Altpfade/Altversionen)

---

## 0) Projektidentität (FIX)

- Brand: **LifeTimeCircle**
- Produkt/Modul: **Service Heft 4.0**
- Design-Regel: Look nicht „wild“ ändern — Fokus auf Module/Komponenten & Aktualität
- Grundsatz: **kein Demo-Modus** (keine Demo-Shortcuts bei Security/Privacy/RBAC)

---

## 1) Nicht verhandelbare Leitplanken (FIX)

### 1.1 Security/Policy (serverseitig)

- **deny-by-default** + **least privilege**
- **RBAC serverseitig enforced** (UI ist nie Sicherheitsinstanz)
- **keine Secrets in Logs**
- **keine Klartext-PII** in Logs/Audit/Exports
- Pseudonymisierung: **HMAC** (kein unsalted SHA)
- Uploads: **Allowlist + Limits + Quarantine by default**, Freigabe nach Scan oder Admin-Approval, **keine öffentlichen Uploads**
- Exports: **redacted default**; **Full Export nur SUPERADMIN** + Audit + TTL/Limit + Verschlüsselung

### 1.2 Public-QR (öffentlich)

- Public-QR bewertet **ausschließlich Nachweis-/Dokumentationsqualität**, **nie technischen Zustand**
- Public Response: **keine Metrics/Counts/Percentages/Zeiträume**
- **Disclaimer ist Pflicht** (Public-UI-Copy, ohne Abwandlung):

  > „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

### 1.3 Business-Gating

- **Verkauf/Übergabe-QR & interner Verkauf**: nur **VIP** & **DEALER** (gewerblich)
- VIP-Gewerbe: **max. 2 Staff**; Freigabe nur **SUPERADMIN**

---

## 2) Rollenmodell (RBAC) (FIX)

Rollen:

- `public`      (nur Public-QR Mini-Check)
- `user`        (eigene Fahrzeuge + eigene Einträge/Dokumente)
- `vip`         (erweiterte Features/Sicht, Transfer/Verkauf möglich)
- `dealer`      (gewerblich; VIP-nah; Transfer/Verkauf; ggf. Multi-User)
- `moderator`   (nur Blog/News; keine PII; kein Export; kein Audit-Read)
- `admin`       (Governance)
- `superadmin`  (High-Risk-Gates)

Sonderregeln:

- VIP-Gewerbe: max. 2 Staff, Freigabe nur SUPERADMIN
- Moderator: strikt Blog/News-only (keine Vehicles/Entries/Documents/Verification; kein Export; kein Audit-Read)
- SUPERADMIN-Provisioning: **nicht** über normale Admin-Role-Setter-Endpoints (out-of-band Bootstrap/Seed/Deployment)

---

## 3) Auth & Consent (Pflicht, FIX)

- Login: E-Mail Login + Verifizierung (OTP oder Magic-Link)
- Verifizierung: **One-time**, **TTL**, **Rate-Limits**, **Anti-Enumeration**
- Consent-Gate: AGB + Datenschutz **Pflicht**
  - Speichern: **Version + Timestamp** (auditierbar)
  - Ohne gültige Zustimmung: **kein produktiver Zugriff**
- Tokens/Codes/Links: **niemals im Klartext loggen**

---

## 4) Produktkern / MVP-Module (Scope)

### 4.1 MVP (Kern)

1) **Service Heft 4.0**
   - Fahrzeugprofil (VIN/WID + Fahrzeug-ID/QR)
   - Timeline/Einträge (Service/Wartung/Reparatur/Umbau/Unfall/Prüfung)
   - Dokumente/Nachweise (Upload + Metadaten + Sichtbarkeit)
   - Trust-Level pro Eintrag/Quelle: **T1/T2/T3** (Definition offen, siehe §5)

2) **Public-QR Mini-Check**
   - Ampel Rot/Orange/Gelb/Grün (nur Dokuqualität, ohne Metrics)
   - Disclaimer (exakt)

3) **Frontpage/Hub**
   - Erklärtext + Headerbar (Module/Tools)
   - „Zutrittsknopf“
   - Login-Panel: Default links (rechts optional)

4) **Blog/News**
   - Admin erstellt/veröffentlicht
   - Moderator: nur Blog/News verwalten (strikt)

5) **Admin-Minimum (Governance)**
   - Userliste (redacted)
   - Rolle setzen
   - Moderatoren akkreditieren
   - VIP-Gewerbe-2-Staff-Freigabe (SUPERADMIN Gate)
   - Audit (ohne PII)

### 4.2 Zusatzmodule (VIP/Dealer; später)

- Verkauf/Übergabe-QR (nur VIP/Dealer)
- Interner Verkauf (nur VIP/Dealer)
- Gewerbe-Module: MasterClipboard, Direktannahme, OBD-Gateway, GPS-Probefahrt (siehe §8)

---

## 5) Trustscore / T-Level (Definitionen & Status)

### 5.1 Ampel (Public-QR)

Stufen: **Rot / Orange / Gelb / Grün**  
Bewertet: **Dokumentation & Verifizierungsgrad**, nicht Technikzustand.

Kriterien (high-level, ohne Metrics):

- Historie vorhanden (Einträge/Belege)
- Verifizierungsgrad: **T3/T2/T1**
- Aktualität/Regelmäßigkeit der Dokumentation
- Unfalltrust: **Grün bei Unfall nur mit Abschluss + Belegen**

Unfallregel:

- „Grün trotz Unfall“ nur, wenn Unfall **abgeschlossen** und **mit Belegen dokumentiert** (Definition „abgeschlossen“ ist offen → Backlog)

### 5.2 T1/T2/T3 (OFFEN → Backlog)

- T3 = höchster Verifizierungsgrad (Beleg/Quelle verifiziert)
- T2 = mittlerer Verifizierungsgrad
- T1 = niedrigster Verifizierungsgrad
- Konkrete Belegarten/Prüfer/Regeln sind **P0-Entscheidung**, bevor Trustscore „hart“ finalisiert wird.

---

## 6) Rechte-Matrix (Kurzfassung, implementierbar)

- Public-QR: alle Rollen dürfen Ampel sehen; **Zustandsbewertung niemand**
- Service Heft: `user/vip/dealer/admin/superadmin` im eigenen Scope; fremd nur „berechtigt“; `moderator` nie
- Dokumente/Bilder: Inhalte nur im Scope; „VIP-only Bildansicht“ nur `vip/dealer/admin/superadmin`
- Blog/News: lesen alle; schreiben `moderator/admin/superadmin`; löschen: moderator ggf. nur eigene Posts, admin/superadmin alles
- Newsletter: Opt-in/out `user/vip/dealer/admin/superadmin`; Versand nur `admin/superadmin`
- Admin/Governance: nur `admin/superadmin` (High-Risk: Full Export + Staff-Freigaben = superadmin)

---

## 7) Roadmap (MVP in 3 Sprints)

Sprint A — Fundament (PFLICHT)

- Auth + Verifizierung + Consent-Gate
- Rollenmodell + serverseitige Guards überall
- Admin-Minimum (Rollen/Governance)

Sprint B — Service Heft Kern

- Vehicle + Entries + Uploads + T-Level Speicherung

Sprint C — Public & Wachstum

- Public-QR Mini-Check (Policy-konform)
- Blog/Newsletter (simpel → ausbauen)
- Moderator-Portal (Blog/News-only)

---

## 8) Modul-Landschaft (Produktstory / Zuteilung)

### 8.1 Free (Basic)

- Autokauf-Co-Pilot (Container/Startpunkt; VIP-Module verborgen)
- Checklisten „Ankauf privat“ nur Papier/PDF
- QR-Fahrzeug-ID (für Fahrzeuganlage notwendig)
- Digitaler Fahrzeugschein (codiert/geschützt; nur eingeloggter User)
- Fahrzeugbewertung ohne KI (Freitext/Sprachbeschreibung; kein echter Fahrzeugwert)
- Frontschadencheck „Front zerschossen“ (Spaß)

### 8.2 VIP Privat/Sammler

- KI-Fahrzeugbewertung (KI-gestützt, Detailabfrage)
- Galerie-Sammler (Hypercars/Sport/Luxus/Oldtimer/Militaria; Doku-Historie)
- Geräusch- & Schwingungsanalyse (Handyaufnahme/Sensorik)

### 8.3 VIP Gewerbe / Dealer

- Direktannahme-Workflow
- **MasterClipboard** (Sprachaufnahme → Triage → Monitor/Tafel)
- GPS-Probefahrt-Nachweis (anonymisiert; Durchführer = Mitarbeiter-ID)
- OBD-Gateway Integration (GPS + OBD gekoppelt)
- OBD-Diagnose einzeln
- Händlernetzwerk/Weiterleitung
- Interner Fahrzeugankauf (nur ServiceHeft 4.0)
- Rechnungsprüfer, Reimport-Identitätscheck, VIN/WID-Validierung
- Lichteinstellungs-Check per Foto
- KI-Agenten (Assistenz/Automation; strikt policy-konform)

### 8.4 MasterClipboard (Funktionskern, FINAL-Beschreibung)

- Zweck: Fahrzeugannahme standardisieren + Triage + Team-Transparenz (Monitor/Tafel)
- Input: Sprachaufnahme (Begutachtung)
- Verarbeitung: Speech-to-Text + Schlüsselwort-/Mängel-Erkennung + Kategorisierung
- Status:
  - Mängelliste (akzeptiert)
  - Mangel prüfen (zu prüfen)
  - abgelehnt (mit Reason)
- Kategorien (Beispiele): Fahrwerk, Motor/Antrieb, Getriebe, Unterboden, Bremsen, Lenkung, Elektrik, Karosserie/Lack, Glas/Beleuchtung, Innenraum, Reifen/Felgen, Klima/Heizung, Diagnose
- Identitäten: Fahrzeug-ID/QR; Durchführer nur via Mitarbeiter-ID (keine Klarnamen)

### 8.5 Modul-Repos (Regel: keine Policy-Drift)

- Core-Policies liegen **nur** im Core-Repo `docs/` und optional `docs/policies/`.
- Modul-Repos (z. B. `C:\Users\stefa\Projekte\LifeTimeCircle-Modules\...`) enthalten:
  - CONTEXT_PACK.md
  - MODULE_SPEC.md
  - API_CONTRACT.md

---

## 9) Repo/Setup (lokal) — IST

- Repo: `C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0`
- Server: `C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server`

Top-Level (bekannt): `docs/ server/ static/ storage/ tools/ scripts/`  
Repo-Struktur: siehe `docs/04_REPO_STRUCTURE.md`

ZIP-Regel (für Uploads/Checkpoints):

- Rein: `docs/ server/ static/ tools/ scripts/ .env.example README* CHANGELOG*`
- Nicht rein: `server\data\app.db`, `.venv`, `__pycache__`, `.pytest_cache`, Logs, Build-Artefakte

---

## 10) Backend IST-Stand (Server — FastAPI/Poetry/SQLite)

Status (Kern):

- Auth E-Mail Challenge (DEV OTP optional) läuft
- Sessions/Token-Check funktioniert
- Audit vorhanden (ohne Klartext-PII)
- RBAC-Guards integriert (401/403 sauber)
- UTC/tz-aware Timestamps gepatcht
- Pytest grün

Wichtige Bereiche/Dateien (Server):

- `app/auth/*` (AuthContext, OTP, Rate-Limit, Auth-Audit, HMAC)
- `app/core/*` (Settings/Config, Security Actor/require_roles)
- `app/routers/*` (FastAPI Router, inkl. MasterClipboard)
- `app/services/*` (Audit Events + Idempotency via SQLAlchemy)
- `scripts/*` (Start/Checks)

Start/Tests (PowerShell):

- Tests:
  - `cd server`
  - `poetry run pytest`
- Start (DEV):
  - `$env:LTC_SECRET_KEY="dev-only-change-me-please-change-me-32chars-XXXX"`
  - `$env:LTC_DB_PATH=".\\data\\app.db"`
  - `$env:LTC_DEV_EXPOSE_OTP="false"`
  - `.\scripts\uvicorn_run.ps1`

Hinweis (Windows):

- ENV gilt pro PowerShell-Fenster (bei neuem Fenster Variablen neu setzen).
- Port 8000 freimachen:
  - `netstat -ano | findstr :8000`
  - `taskkill /PID <PID> /F`

---

## 11) Admin-Rollenverwaltung (P0)

Ziel-Endpoints (admin-only):

- `GET /admin/users` (Liste, redacted; keine PII)
- `POST /admin/users/{user_id}/role` (Role setzen)
- `POST /admin/users/{user_id}/moderator` (Moderator akkreditieren)

Audit: minimal, ohne Klartext-PII.

Typischer Fehler:

- Admin-Tests 404 → Router nicht gemountet (include fehlt in `main.py`)

---

## 12) Exports (P0 umgesetzt)

Ziel (Policy-konform):

- Default: **redacted**
- Full: **nur SUPERADMIN** + **TTL/Limit** + **Verschlüsselung** + **Audit** (ohne Klartext-PII, ohne Tokens)

Implementiert: **Vehicle Export**

- `GET /export/vehicle/{id}`
  - Zugriff: `user/vip/dealer/admin/superadmin` **im Scope** (Owner/Scope enforced)
  - Output: redacted default (**keine Klartext-PII**, keine Secrets; z.B. VIN nur als `vin_hmac`)
- `POST /export/vehicle/{id}/grant`
  - Zugriff: `superadmin`
  - Output: one-time Export-Token + Ablaufzeit (TTL), **Limit enforced**
  - Audit: ohne Klartext-PII/Secrets, **Token wird nie geloggt**
- `GET /export/vehicle/{id}/full`
  - Zugriff: `superadmin`
  - Header: `X-Export-Token`
  - Output: verschlüsselt (`ciphertext`, Fernet / cryptography)

Code-SoT:

- `server/app/routers/export_vehicle.py`
- `server/app/services/export_store.py` (TTL/Limit + one-time token)
- `server/app/services/export_crypto.py` (Encryption + JSON-safe)
- `server/app/services/export_redaction.py` (Redaction/HMAC)
- Tests: `server/tests/test_export_vehicle.py`

RBAC-Hinweis:

- `moderator`: **kein Export**, **kein Audit-Read**


---

## 13) Offene Entscheidungen (Produkt/Regeln) — MUSS vor „final“

- T1/T2/T3 Definition (Belegarten, Prüfer, Regeln)
- Trust-Ampel Logik: Mindestbedingungen je Stufe (ohne Metrics, aber deterministisch)
- Unfall „abgeschlossen“: Definition + Pflichtbelege
- Übergabe-/Verkaufsflow (inkl. Käufer ohne Account)
- Newsletter-Workflow (Send-only vs Feedback/Reply + Moderation)

---

## 14) Backlog (Epics) — Reihenfolge (hart sinnvoll)

- EPIC-02 Auth/Consent
- EPIC-03 RBAC
- EPIC-04 Admin-Minimum
- EPIC-10 Betrieb/Qualität/Produktion
- EPIC-05 Service Heft Kern
- EPIC-06 Public-QR Mini-Check
- EPIC-08 Landingpage/Navigation
- EPIC-07 Blog/Newsletter
- EPIC-09 Verkauf/Übergabe

---

## 15) Definition of Done — Gate vor Abgabe (MUSS)

- Navigation/Buttons/Empty States ok
- RBAC serverseitig (keine UI-only Security)
- Public-QR: ohne Metrics + Disclaimer exakt
- Logs/Audit/Export konform (keine PII/Secrets, HMAC)
- Upload-Quarantine & Allowlist aktiv
- Keine Pfad-/Altversion-Konflikte (Docs SoT = `...\docs`)

---

## 16) Nächste konkrete Aktion (P0) — Plan der Wahrheit

1) **Exports auf weitere Targets erweitern** (vehicles/servicebook/users)  
   - gleiche Mechanik: redacted default, full nur superadmin, one-time grant + TTL + Verschlüsselung, Audit minimal

2) **SUPERADMIN Bootstrap/Provisioning** (out-of-band, auditierbar, ohne PII)  
   - Seed/Script/Deployment-Mechanik definieren & dokumentieren  
   - normaler Admin darf superadmin nicht „einfach setzen“

3) **Cleanup / Konsolidierung**
   - Init-/Altdateien prüfen (z. B. `*_init_.py`), nur behalten wenn genutzt
   - Doku-Index aktuell halten (`99_MASTER_CHECKPOINT.md` als Klammer)

---

## 17) Verworfen / Nur Option (NICHT IST)

- NestJS/Prisma/Postgres/Redis/BullMQ/S3/ClamAV als Stack ist **keine aktuelle IST-Basis** dieses Repos.
  Falls später entschieden: als eigene DECISION + Migrationsplan aufnehmen (und dann erst SoT umstellen).

1) Doku-Update committen (99_MASTER_CHECKPOINT)

Mach minimal in docs/99_MASTER_CHECKPOINT.md diesen Block rein (copy/paste):

Export Vehicle

GET /export/vehicle/{id}: redacted default, keine Klartext-PII, keine Secrets (z.B. vin → vin_hmac)

POST /export/vehicle/{id}/grant: nur SUPERADMIN, one-time Token, TTL/Limit enforced, Audit ohne PII/Secrets, Token wird nicht geloggt

GET /export/vehicle/{id}/full: nur SUPERADMIN, benötigt Header X-Export-Token, Response ist verschlüsselt (ciphertext)

RBAC

moderator: kein Export, kein Audit-Read

Security/Privacy

Logs/Audit: keine Tokens, keine Klartext-PII; Pseudonymisierung via HMAC

---

ENDE 99_MASTER_CHECKPOINT


