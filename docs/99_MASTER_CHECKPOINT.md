\# 99\_MASTER\_CHECKPOINT — LifeTimeCircle / Service Heft 4.0

Stand: 2026-01-30 (Europe/Berlin)  

Ziel: produktionsreif (keine Demo), stabiler MVP → danach Ausbau  

Kontakt: lifetimecircle@online.de  

Source of Truth (Docs): C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs\\  (keine Altpfade/Altversionen)



---



\## 0) Projektidentität (FIX)

\- Brand: \*\*LifeTimeCircle\*\*

\- Produkt/Modul: \*\*Service Heft 4.0\*\*

\- Design-Regel: Look nicht „wild“ ändern — Fokus auf Module/Komponenten \& Aktualität

\- Grundsatz: \*\*kein Demo-Modus\*\* (keine Demo-Shortcuts bei Security/Privacy/RBAC)



---



\## 1) Nicht verhandelbare Leitplanken (FIX)



\### 1.1 Security/Policy (serverseitig)

\- \*\*deny-by-default\*\* + \*\*least privilege\*\*

\- \*\*RBAC serverseitig enforced\*\* (UI ist nie Sicherheitsinstanz)

\- \*\*keine Secrets in Logs\*\*

\- \*\*keine Klartext-PII\*\* in Logs/Audit/Exports

\- Pseudonymisierung: \*\*HMAC\*\* (kein unsalted SHA)

\- Uploads: \*\*Allowlist + Limits + Quarantine by default\*\*, Freigabe nach Scan oder Admin-Approval, \*\*keine öffentlichen Uploads\*\*

\- Exports: \*\*redacted default\*\*; \*\*Full Export nur SUPERADMIN\*\* + Audit + TTL/Limit + Verschlüsselung



\### 1.2 Public-QR (öffentlich)

\- Public-QR bewertet \*\*ausschließlich Nachweis-/Dokumentationsqualität\*\*, \*\*nie technischen Zustand\*\*

\- Public Response: \*\*keine Metrics/Counts/Percentages/Zeiträume\*\*

\- \*\*Disclaimer ist Pflicht\*\* (Public-UI-Copy, ohne Abwandlung):

&nbsp; > „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“



\### 1.3 Business-Gating

\- \*\*Verkauf/Übergabe-QR \& interner Verkauf\*\*: nur \*\*VIP\*\* \& \*\*DEALER\*\* (gewerblich)

\- VIP-Gewerbe: \*\*max. 2 Staff\*\*; Freigabe nur \*\*SUPERADMIN\*\*



---



\## 2) Rollenmodell (RBAC) (FIX)

Rollen:

\- `public`  (nur Public-QR Mini-Check)

\- `user`    (eigene Fahrzeuge + eigene Einträge/Dokumente)

\- `vip`     (erweiterte Features/Sicht, Transfer/Verkauf möglich)

\- `dealer`  (gewerblich; VIP-nah; Transfer/Verkauf; ggf. Multi-User)

\- `moderator` (nur Blog/News; keine PII; kein Export; kein Audit)

\- `admin` / `superadmin` (Governance; `superadmin` = High-Risk-Gates)



Sonderregeln:

\- VIP-Gewerbe: max. 2 Staff, Freigabe nur SUPERADMIN

\- Moderator: strikt Blog/News-only (keine Vehicles/Entries/Documents/Verification; kein Export; kein Audit-Read)



---



\## 3) Auth \& Consent (Pflicht, FIX)

\- Login: E-Mail Login + Verifizierung (OTP oder Magic-Link)

\- Verifizierung: \*\*One-time\*\*, \*\*TTL\*\*, \*\*Rate-Limits\*\*, \*\*Anti-Enumeration\*\*

\- Consent-Gate: AGB + Datenschutz \*\*Pflicht\*\*

&nbsp; - Speichern: \*\*Version + Timestamp\*\* (auditierbar)

&nbsp; - Ohne gültige Zustimmung: \*\*kein produktiver Zugriff\*\*

\- Tokens/Codes/Links: \*\*niemals im Klartext loggen\*\*



---



\## 4) Produktkern / MVP-Module (Scope)



\### 4.1 MVP (Kern)

1\) \*\*Service Heft 4.0\*\*

&nbsp;  - Fahrzeugprofil (VIN/WID + Fahrzeug-ID/QR)

&nbsp;  - Timeline/Einträge (Service/Wartung/Reparatur/Umbau/Unfall/Prüfung)

&nbsp;  - Dokumente/Nachweise (Upload + Metadaten + Sichtbarkeit)

&nbsp;  - Trust-Level pro Eintrag/Quelle: \*\*T1/T2/T3\*\* (Definition offen, siehe §5)

2\) \*\*Public-QR Mini-Check\*\*

&nbsp;  - Ampel Rot/Orange/Gelb/Grün (nur Dokuqualität, ohne Metrics)

&nbsp;  - Disclaimer (exakt)

3\) \*\*Frontpage/Hub\*\*

&nbsp;  - Erklärtext + Headerbar (Module/Tools)

&nbsp;  - „Zutrittsknopf“

&nbsp;  - Login-Panel: Default links (rechts optional)

4\) \*\*Blog/News\*\*

&nbsp;  - Admin erstellt/veröffentlicht

&nbsp;  - Moderator: nur Blog/News verwalten (strikt)

5\) \*\*Admin-Minimum (Governance)\*\*

&nbsp;  - Userliste (redacted)

&nbsp;  - Rolle setzen

&nbsp;  - Moderatoren akkreditieren

&nbsp;  - VIP-Gewerbe-2-Staff-Freigabe (SUPERADMIN Gate)

&nbsp;  - Audit (ohne PII)



\### 4.2 Zusatzmodule (VIP/Dealer; später)

\- Verkauf/Übergabe-QR (nur VIP/Dealer)

\- Interner Verkauf (nur VIP/Dealer)

\- Gewerbe-Module: MasterClipboard, Direktannahme, OBD-Gateway, GPS-Probefahrt (siehe §8)



---



\## 5) Trustscore / T-Level (Definitionen \& Status)



\### 5.1 Ampel (Public-QR)

Stufen: \*\*Rot / Orange / Gelb / Grün\*\*  

Bewertet: \*\*Dokumentation \& Verifizierungsgrad\*\*, nicht Technikzustand.



Kriterien (high-level, ohne Metrics):

\- Historie vorhanden (Einträge/Belege)

\- Verifizierungsgrad: \*\*T3/T2/T1\*\*

\- Aktualität/Regelmäßigkeit der Dokumentation

\- Unfalltrust: \*\*Grün bei Unfall nur mit Abschluss + Belegen\*\*



Unfallregel:

\- „Grün trotz Unfall“ nur, wenn Unfall \*\*abgeschlossen\*\* und \*\*mit Belegen dokumentiert\*\* (Definition „abgeschlossen“ ist offen → Backlog)



\### 5.2 T1/T2/T3 (OFFEN → Backlog)

\- T3 = höchster Verifizierungsgrad (Beleg/Quelle verifiziert)

\- T2 = mittlerer Verifizierungsgrad

\- T1 = niedrigster Verifizierungsgrad

Konkrete Belegarten/Prüfer/Regeln sind \*\*P0-Entscheidung\*\*, bevor Trustscore „hart“ finalisiert wird.



---



\## 6) Rechte-Matrix (Kurzfassung, implementierbar)

\- Public-QR: alle Rollen dürfen Ampel sehen; \*\*Zustandsbewertung niemand\*\*

\- Service Heft: `user/vip/dealer/admin` im eigenen Scope; fremd nur „berechtigt“; `moderator` nie

\- Dokumente/Bilder: Inhalte nur im Scope; „VIP-only Bildansicht“ nur `vip/dealer/admin`

\- Blog/News: lesen alle; schreiben `moderator/admin`; löschen: moderator ggf. nur eigene Posts, admin alles

\- Newsletter: Opt-in/out `user/vip/dealer/admin`; Versand nur `admin`

\- Admin/Governance: nur `admin/superadmin` (High-Risk: Full Export + Staff-Freigaben = superadmin)



---



\## 7) Roadmap (MVP in 3 Sprints)

Sprint A — Fundament (PFLICHT)

\- Auth + Verifizierung + Consent-Gate

\- Rollenmodell + serverseitige Guards überall

\- Admin-Minimum (Rollen/Governance)

Sprint B — Service Heft Kern

\- Vehicle + Entries + Uploads + T-Level Speicherung

Sprint C — Public \& Wachstum

\- Public-QR Mini-Check (Policy-konform)

\- Blog/Newsletter (simpel → ausbauen)

\- Moderator-Portal (Blog/News-only)



---



\## 8) Modul-Landschaft (Produktstory / Zuteilung)



\### 8.1 Free (Basic)

\- Autokauf-Co-Pilot (Container/Startpunkt; VIP-Module verborgen)

\- Checklisten „Ankauf privat“ nur Papier/PDF

\- QR-Fahrzeug-ID (für Fahrzeuganlage notwendig)

\- Digitaler Fahrzeugschein (codiert/geschützt; nur eingeloggter User)

\- Fahrzeugbewertung ohne KI (Freitext/Sprachbeschreibung; kein echter Fahrzeugwert)

\- Frontschadencheck „Front zerschossen“ (Spaß)



\### 8.2 VIP Privat/Sammler

\- KI-Fahrzeugbewertung (KI-gestützt, Detailabfrage)

\- Galerie-Sammler (Hypercars/Sport/Luxus/Oldtimer/Militaria; Doku-Historie)

\- Geräusch- \& Schwingungsanalyse (Handyaufnahme/Sensorik)



\### 8.3 VIP Gewerbe / Dealer

\- Direktannahme-Workflow

\- \*\*MasterClipboard\*\* (Sprachaufnahme → Triage → Monitor/Tafel)

\- GPS-Probefahrt-Nachweis (anonymisiert; Durchführer = Mitarbeiter-ID)

\- OBD-Gateway Integration (GPS + OBD gekoppelt)

\- OBD-Diagnose einzeln

\- Händlernetzwerk/Weiterleitung

\- Interner Fahrzeugankauf (nur ServiceHeft 4.0)

\- Rechnungsprüfer, Reimport-Identitätscheck, VIN/WID-Validierung

\- Lichteinstellungs-Check per Foto

\- KI-Agenten (Assistenz/Automation; strikt policy-konform)



\### 8.4 MasterClipboard (Funktionskern, FINAL-Beschreibung)

\- Zweck: Fahrzeugannahme standardisieren + Triage + Team-Transparenz (Monitor/Tafel)

\- Input: Sprachaufnahme (Begutachtung)

\- Verarbeitung: Speech-to-Text + Schlüsselwort-/Mängel-Erkennung + Kategorisierung

\- Status:

&nbsp; - Mängelliste (akzeptiert)

&nbsp; - Mangel prüfen (zu prüfen)

&nbsp; - abgelehnt (mit Reason)

\- Kategorien (Beispiele): Fahrwerk, Motor/Antrieb, Getriebe, Unterboden, Bremsen, Lenkung, Elektrik, Karosserie/Lack, Glas/Beleuchtung, Innenraum, Reifen/Felgen, Klima/Heizung, Diagnose

\- Identitäten: Fahrzeug-ID/QR; Durchführer nur via Mitarbeiter-ID (keine Klarnamen)



\### 8.5 Modul-Repos (Regel: keine Policy-Drift)

\- Core-Policies liegen \*\*nur\*\* im Core-Repo `docs/` und `docs/policies/`.

\- Modul-Repos (z. B. `C:\\Users\\stefa\\Projekte\\LifeTimeCircle-Modules\\...`) enthalten:

&nbsp; - CONTEXT\_PACK.md

&nbsp; - MODULE\_SPEC.md

&nbsp; - API\_CONTRACT.md



---



\## 9) Repo/Setup (lokal) — IST

\- Repo: `C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0`

\- Server: `C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\server`

\- Node/Packages: `C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\packages\\lifetimecircle-core`



Top-Level (bekannt): `docs/ server/ static/ storage/ tools/ scripts/`



ZIP-Regel (für Uploads/Checkpoints):

\- Rein: `docs/ server/ static/ tools/ scripts/ .env.example README\* CHANGELOG\*`

\- Nicht rein: `server\\data\\app.db`, `.venv`, `\_\_pycache\_\_`, `.pytest\_cache`, Logs, Build-Artefakte



---



\## 10) Backend IST-Stand (Server — FastAPI/Poetry/SQLite)

Status (zuletzt):

\- Auth E-Mail Challenge (DEV OTP optional) läuft

\- Sessions/Token-Check funktioniert

\- Audit Tail Script zeigt Events ohne PII

\- RBAC-Guard integriert

\- Deprecation-Fixes (FastAPI lifespan, utcnow → timezone-aware) gepatcht

\- Pytest war zwischendurch grün (Snapshots: 5/5 bis 10 passed; danach Admin-Routes/Tests ergänzt)



Wichtige Bereiche/Dateien (Server):

\- `app/auth/\*`

\- `settings.py` (env/secret validation)

\- `crypto.py` (token\_hash / HMAC)

\- `storage.py` (sqlite auth storage)

\- `rbac.py` (get\_current\_user + require\_roles; 401/403 sauber)

\- `deps.py` (Compatibility layer)

\- `app/routers/masterclipboard`

\- `scripts/`

&nbsp; - `uvicorn\_run.ps1` (Start; verlangt LTC\_SECRET\_KEY >= 32)

&nbsp; - `patch\_\*` (Patch-Skripte)

&nbsp; - `audit\_tail.py` (letzte Events, ohne PII)



Run/Tests (PowerShell):

\- Tests:

&nbsp; - `cd server`

&nbsp; - `poetry run pytest`

\- Admin Route-Check:

&nbsp; - `poetry run python -c "from app.main import create\_app; app=create\_app(); print(\[r.path for r in app.routes if getattr(r,'path',None) and r.path.startswith('/admin')])"`

\- Start (DEV):

&nbsp; - `$env:LTC\_SECRET\_KEY="dev-only-change-me-please-change-me-32chars-XXXX"`

&nbsp; - `$env:LTC\_DB\_PATH=".\\\\data\\\\app.db"`

&nbsp; - `$env:LTC\_DEV\_EXPOSE\_OTP="false"`

&nbsp; - `.\\uvicorn\_run.ps1`



Hinweis (Windows):

\- ENV gilt pro PowerShell-Fenster (bei neuem Fenster Variablen neu setzen).

\- Port 8000 freimachen:

&nbsp; - `netstat -ano | findstr :8000`

&nbsp; - `taskkill /PID 20900 /F`  (Beispiel; PID aus netstat nehmen)



---



\## 11) Admin-Rollenverwaltung (P0)

Ziel-Endpoints (admin-only):

\- `GET /admin/users` (Liste, redacted; keine PII)

\- `POST /admin/users/{user\_id}/role` (Role setzen)

Audit: minimal, ohne Klartext-PII



Typischer Fehler:

\- Admin-Tests 404 → Router nicht gemountet (include fehlt in `main.py`)



---



\## 12) Offene Entscheidungen (Produkt/Regeln) — MUSS vor „final“

\- T1/T2/T3 Definition (Belegarten, Prüfer, Regeln)

\- Trust-Ampel Logik: Mindestbedingungen je Stufe (ohne Metrics, aber deterministisch)

\- Unfall „abgeschlossen“: Definition + Pflichtbelege

\- Übergabe-/Verkaufsflow (inkl. Käufer ohne Account)

\- Newsletter-Workflow (Send-only vs Feedback/Reply + Moderation)



---



\## 13) Backlog (Epics) — Reihenfolge (hart sinnvoll)

\- EPIC-02 Auth/Consent

\- EPIC-03 RBAC

\- EPIC-04 Admin-Minimum

\- EPIC-05 Service Heft Kern

\- EPIC-06 Public-QR Mini-Check

\- EPIC-08 Landingpage/Navigation

\- EPIC-07 Blog/Newsletter

\- EPIC-09 Verkauf/Übergabe

\- EPIC-10 Betrieb/Qualität/Produktion



---



\## 14) Definition of Done — Gate vor Abgabe (MUSS)

\- Navigation/Buttons/Empty States ok

\- RBAC serverseitig (keine UI-only Security)

\- Public-QR: ohne Metrics + Disclaimer

\- Logs/Audit/Export konform (keine PII/Secrets, HMAC)

\- Upload-Quarantine \& Allowlist aktiv

\- Keine Pfad-/Altversion-Konflikte (Docs SoT = `...\\docs`)



---



\## 15) Nächste konkrete Aktion (P0) — „Plan der Wahrheit“

1\) Admin-Router sauber in App registrieren (404 Fix) → Tests grün

2\) RBAC-Hardening pro Modul (MasterClipboard: dealer/vip/admin; user/mod/public blocken)

3\) Danach: Cleanup (bak/init-Schrott) + Commit + optional Tag „checkpoint“



---



\## 16) Verworfen / Nur Option (NICHT IST)

\- NestJS/Prisma/Postgres/Redis/BullMQ/S3/ClamAV als Stack ist \*\*keine aktuelle IST-Basis\*\* dieses Repos.

&nbsp; Falls später entschieden: als eigene DECISION + Migrationsplan aufnehmen (und dann erst SoT umstellen).



---

ENDE 99\_MASTER\_CHECKPOINT


---

## 3) Falls du „die alte Master-Version“ überschrieben hast (Git-Rettung)
Wenn die alte Datei **einmal committed** war, bekommst du sie so zurück:

```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0"
git log -- docs\99_MASTER_CHECKPOINT.md
# dann eine Commit-ID nehmen und z.B.:
git checkout <COMMIT_ID> -- docs\99_MASTER_CHECKPOINT.md

## CHECKPOINT – Stand jetzt

### Erledigt (Main)
- Admin: `/admin/users/{user_id}/moderator` hinzugefügt (Komfort-Endpoint).
  - Audit ohne Freitext-Reason (nur `reason_provided`), keine Klartext-PII.
  - Tests vorhanden (Admin erlaubt, User 403, ohne Token 401).
- VIP-Gewerbe: Freigabe nur SUPERADMIN, Staff-Limit serverseitig enforced (max. 2 Staff).
  - Business-Request anlegbar, Approve nur SUPERADMIN, Staff nur nach Approve.
  - Tests vorhanden (Approve-Gate + Staff-Limit).
- Public-QR: `GET /public/qr/{vehicle_id}` minimal, ohne Metriken/Zahlen/Zeiträume, Disclaimer Pflicht.
  - Test stellt Disclaimer + keine Zahlen sicher.

### Status
- Tests grün (pytest).

### Nächster Fokus
- Exporte: Standard redacted; Full Export nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung.


Repo-Struktur: siehe `docs/04_REPO_STRUCTURE.md`

