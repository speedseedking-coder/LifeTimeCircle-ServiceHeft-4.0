# 99_MASTER_CHECKPOINT — LifeTimeCircle / Service Heft 4.0

Stand: 2026-02-01 (Europe/Berlin)  
Brand: LifeTimeCircle — Modul: Service Heft 4.0  
Ziel: produktionsreif (keine Demo), stabiler MVP → danach Ausbau  
Source of Truth: `.\docs\` (keine Altpfade/Altversionen)

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
- moderator: nur Blog/News, keine PII, kein Export, kein Audit-Read
- superadmin Provisioning: out-of-band (nicht über normale Admin-Endpunkte)

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
- Auth Request/Verify ok (DEV OTP optional)
- Sessions/Token-Check ok
- Audit vorhanden (ohne Klartext-PII)
- RBAC-Guards integriert (401/403 sauber)
- UTC/tz-aware Timestamps gepatcht
- Smoke ok: logout funktioniert, Export-Missing-Tables = 404 statt 500

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
EPIC-10 Betrieb/Qualität/Produktion  
EPIC-05 Service Heft Kern  
EPIC-06 Public-QR Mini-Check  
EPIC-08 Landingpage/Navigation  
EPIC-07 Blog/Newsletter  
EPIC-09 Verkauf/Übergabe  

---

## 12) DoD Gate vor Abgabe (MUSS)
- Navigation/Buttons/Empty States ok
- RBAC serverseitig, keine UI-only Security
- Public-QR: ohne Metrics + Disclaimer exakt
- Logs/Audit/Export konform (keine PII/Secrets, HMAC)
- Upload-Quarantäne & Allowlist aktiv
- Keine Pfad-/Altversion-Konflikte (Docs SoT = `.\docs`)
- Lizenzkontrolle: serverseitig enforced + Tests + keine Leaks

