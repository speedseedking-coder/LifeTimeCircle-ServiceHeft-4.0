# docs/99_MASTER_CHECKPOINT.md
# 99_MASTER_CHECKPOINT — LifeTimeCircle / Service Heft 4.0

Stand: 2026-01-31 (Europe/Berlin)  
Brand: LifeTimeCircle — Modul: Service Heft 4.0  
Ziel: produktionsreif (keine Demo), stabiler MVP → danach Ausbau  
Source of Truth: `.\docs\` (keine Altpfade/Altversionen)

---

## 0) Update-Marker (Pflicht-Check bei Doku-Änderungen)

Wenn du **eine** dieser Dateien änderst:
- `docs/01_DECISIONS.md`
- `docs/03_RIGHTS_MATRIX.md`
- `docs/04_REPO_STRUCTURE.md`

…dann MUSS dieser Checkpoint prüfen/mitziehen, ob die folgenden FIX-Punkte weiterhin korrekt abgebildet sind:

### 0.1 RBAC-/Business-Gating Marker (FIX)
- Verkauf/Übergabe-QR & interner Verkauf: **nur VIP & DEALER**
- VIP-Gewerbe: **max. 2 Staff**, Freigabe **nur SUPERADMIN**
- moderator: **nur Blog/News**, **kein Export**, **kein Audit-Read**, **keine PII**
- superadmin Provisioning: **out-of-band** (nicht über normale Admin-Endpunkte)

### 0.2 Export Marker (FIX)
- Export default **redacted**
- Full Export nur **SUPERADMIN** + **Audit** + **TTL/Limit** + **Verschlüsselung**
- Token/Secrets niemals in Logs (auch nicht masked im Debug)

### 0.3 Public-QR Marker (FIX)
- bewertet ausschließlich Dokumentations-/Nachweisqualität, nie technischen Zustand
- Public Response: keine Metrics/Counts/Percentages/Zeiträume
- Pflicht-Disclaimer (exakt, ohne Abwandlung):
  „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

### 0.4 Repo-/Nachweis Marker (FIX)
- `docs/04_REPO_STRUCTURE.md` existiert und ist aktuell (nicht löschen)
- ZIP/Git: NICHT rein: `server\data\app.db`, `storage\*` Inhalte, venv/caches/logs/build
- docs sind SoT: keine Altpfade/Altversionen parallel

### 0.5 Lizenzkontrolle Marker (NEU, FIX)
- Default deny, wenn Lizenz fehlt/ungültig/abgelaufen/gesperrt
- Lizenzdaten/Keys niemals im Klartext loggen
- Artefakte vorhanden/geplant:
  - `docs/legal/*`
  - `scripts/legal_check.ps1`
  - `tools/license_asset_audit.py`

---

## 1) Projekt-Identität (FIX)
- Brand: LifeTimeCircle, Modul: Service Heft 4.0
- Ziel: produktionsreifer, stabiler MVP → danach Ausbau
- Design-Regel: Look nicht „wild“ ändern, Fokus auf Module/Komponenten & Aktualität
- Docs sind SoT: alles Relevante muss in `.\docs\` stehen

---

## 2) Nicht verhandelbare Leitplanken (FIX)

### 2.1 Security/Privacy (serverseitig, zwingend)
- deny-by-default + least privilege
- RBAC serverseitig enforced (UI ist nie Sicherheitsinstanz)
- keine Secrets in Logs, keine Klartext-PII in Logs/Audit/Exports
- Pseudonymisierung via HMAC (kein unsalted SHA)
- Tokens/Codes/Links niemals im Klartext loggen

### 2.2 Uploads (FIX)
- Allowlist + Limits
- Quarantine by default
- Freigabe nach Scan/Admin-Approval
- keine öffentlichen Uploads

### 2.3 Exports (FIX)
- redacted default
- Full Export nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung
- Token/Secrets niemals in Logs

### 2.4 Public-QR (öffentlich) (FIX)
- bewertet ausschließlich Dokumentations-/Nachweisqualität, nie technischen Zustand
- Public Response: keine Metrics/Counts/Percentages/Zeiträume
- Pflicht-Disclaimer (exakt, ohne Abwandlung):
  „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

### 2.5 Business-Gating (FIX)
- Verkauf/Übergabe-QR & interner Verkauf: nur VIP & DEALER
- VIP-Gewerbe: max. 2 Staff, Freigabe nur SUPERADMIN

---

## 3) Rollenmodell (RBAC) (FIX)
Rollen: public, user, vip, dealer, moderator, admin, superadmin

Sonderregeln:
- moderator: **nur Blog/News**; **kein Export**, **kein Audit-Read**, **keine PII**, keine Vehicles/Entries/Documents/Verification
- superadmin Provisioning: out-of-band (nicht über normale Admin-Endpunkte)

Hinweis (praktisch notwendig):
- Auth/Session-Endpunkte bleiben nutzbar, damit Moderator sich anmelden/abmelden kann.
- Alles außerhalb Blog/News ist für Moderator serverseitig zu sperren.

---

## 4) Auth & Consent (FIX)
- E-Mail Login + Verifizierung (OTP/Magic-Link)
- One-time + TTL + Rate-Limits + Anti-Enumeration
- Consent-Gate Pflicht (AGB + Datenschutz)
- Speicherung: Version + Timestamp (auditierbar)

---

## 5) Lizenzkontrolle / Legal (NEU, FIX)
Ziel: Lizenzprüfung als zusätzliche Policy-Schicht (RBAC bleibt Pflicht).

Regeln:
- Default deny, wenn Lizenz fehlt/ungültig/abgelaufen/gesperrt
- Lizenzdaten/Keys niemals im Klartext loggen

Artefakte:
- `docs/legal/*`
- `scripts/legal_check.ps1`
- `tools/license_asset_audit.py`

Offen:
- Feature → Tier/Flag Mapping
- Wer darf Lizenz setzen/ändern (vermutlich SUPERADMIN)
- Testfälle (allowed/denied) + Logging-No-Leak Checks

---

## 6) MVP-Scope (Produktkern)

MVP-Kern:
- Service Heft 4.0: Profil (VIN/WID + QR/ID), Timeline/Einträge, Dokumente/Uploads
- Trust-Level je Eintrag/Quelle (T1/T2/T3)
- Public-QR Mini-Check: Ampel Rot/Orange/Gelb/Grün (ohne Metrics, mit Disclaimer)
- Frontpage/Hub + Login
- Blog/News (Admin erstellt; Moderator verwaltet strikt Blog/News)
- Admin-Minimum (Governance):
  - Userliste redacted
  - Rolle setzen
  - Moderatoren akkreditieren
  - VIP-Gewerbe-2-Staff-Freigabe (SUPERADMIN)
  - Audit (ohne PII)

Zusatzmodule (später, VIP/Dealer):
- Verkauf/Übergabe-QR, interner Verkauf
- Gewerbe: Direktannahme, MasterClipboard, OBD/GPS, etc.

---

## 7) Trustscore / T-Level (Status)
- Ampel bewertet nur Dokumentation/Verifizierungsgrad, nicht Technik
- Kriterien high-level (ohne Metriken): Historie, T-Level, Aktualität/Regelmäßigkeit, Unfalltrust
- Unfallregel: „Grün trotz Unfall“ nur bei Abschluss + Belegen

P0-Entscheidungen offen:
- Definition T1/T2/T3 (Belegarten/Prüfer/Regeln)
- Ampel-Mindestbedingungen je Stufe (deterministisch, ohne Metrics)
- Definition „Unfall abgeschlossen“ + Pflichtbelege

---

## 8) Repo/Setup (IST)
Repo: `.\LifeTimeCircle-ServiceHeft-4.0`  
Top-Level: `docs/ server/ static/ storage/ tools/ scripts/`

ZIP-Regel:
- NICHT rein: `server\data\app.db`, venv, caches, Logs, Build-Artefakte

DEV:
- env vars: `LTC_SECRET_KEY`, `LTC_DB_PATH`, `LTC_DEV_EXPOSE_OTP`
- Start: uvicorn via poetry
- Tests: `poetry run pytest`

---

## 9) Backend IST-Stand (FastAPI/Poetry/SQLite)

### 9.1 Core (IST)
- Auth Request/Verify ok (DEV OTP optional)
- Sessions/Token-Check ok
- Audit vorhanden (ohne Klartext-PII)
- RBAC-Guards integriert (401/403 sauber)
- UTC/tz-aware Timestamps gepatcht
- Smoke ok: logout funktioniert, Export-Missing-Tables = 404 statt 500

### 9.2 P1 Moderator: strikt nur Blog/News (IST, FIX)
Ziel: Moderator darf serverseitig **ausschließlich Blog/News** (plus notwendige Auth/Session).  
Umsetzung: deny-by-default für Moderator per `forbid_moderator`-Dependency an allen Nicht-Allow-Routen.

Nachweis/Ankerpunkte (Code):
- `server/app/guards.py`: `forbid_moderator` (403: `role_not_allowed`)
- `server/app/main.py`:
  - `/health` ist deny und trägt `dependencies=[Depends(forbid_moderator)]`
  - Admin-Router wird eingebunden; Admin-Users sind deny für Moderator
- deny Router-Level Guards:
  - `server/app/routers/export.py`
  - `server/app/routers/export_vehicle.py`
  - `server/app/routers/export_servicebook.py`
  - `server/app/routers/export_masterclipboard.py`
  - `server/app/routers/masterclipboard.py`
- Admin-Users Guard (deny für Moderator):
  - `server/app/admin/routes.py` (Router-/Include-Level Dependency für Users-Bereich)

Tests:
- RBAC Test für Moderator-Allowlist/deny-by-default vorhanden und grün (`poetry run pytest`).

---

## 10) Exports (P0)
- Missing Tables werden als 404 gemeldet (kein 500):
  - `vehicle_table_missing`
  - `servicebook_table_missing`

Vehicle Export (Referenz):
- GET `/export/vehicle/{id}`: redacted default, scope enforced
- POST `/export/vehicle/{id}/grant`: superadmin, one-time Token + TTL/Limit
- GET `/export/vehicle/{id}/full`: superadmin + X-Export-Token, Response encrypted

---

## 11) Backlog-Reihenfolge (Epics)
EPIC-02 Auth/Consent  
EPIC-03 RBAC  
EPIC-04 Admin-Minimum  
