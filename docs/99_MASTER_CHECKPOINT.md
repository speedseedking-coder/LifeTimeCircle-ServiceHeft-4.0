cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0"

@'
# 99_MASTER_CHECKPOINT

Stand: 2026-02-01
Brand: LifeTimeCircle — Modul: Service Heft 4.0

## 1) Projekt-Identität (FIX)
- Brand: LifeTimeCircle, Modul: Service Heft 4.0
- Ziel: produktionsreifer, stabiler MVP → danach Ausbau
- Design-Regel: Look nicht „wild“ ändern, Fokus auf Module/Komponenten & Aktualität
- Source of Truth: .\docs\ (keine Altpfade/Altversionen)

## 2) Nicht verhandelbare Leitplanken (FIX)
### Security/Privacy (serverseitig, zwingend)
- deny-by-default + least privilege
- RBAC serverseitig enforced (UI ist nie Sicherheitsinstanz)
- keine Secrets in Logs, keine Klartext-PII in Logs/Audit/Exports
- Pseudonymisierung via HMAC (kein unsalted SHA)

### Uploads (FIX)
- Allowlist + Limits + Quarantine by default
- Freigabe nach Scan/Admin-Approval
- keine öffentlichen Uploads

### Exports (FIX)
- redacted default
- Full Export nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung
- Token/Secrets niemals in Logs

### Public-QR (öffentlich) (FIX)
- bewertet ausschließlich Dokumentations-/Nachweisqualität, nie technischen Zustand
- Public Response: keine Metrics/Counts/Percentages/Zeiträume
- Pflicht-Disclaimer (exakt):
  „Trust-Ampel bewertet ausschließlich Dokumentations- und Nachweisqualität …“

### Business-Gating (FIX)
- Verkauf/Übergabe-QR & interner Verkauf: nur VIP & DEALER
- VIP-Gewerbe: max. 2 Staff, Freigabe nur SUPERADMIN

## 3) Rollenmodell (RBAC) (FIX)
Rollen: public, user, vip, dealer, moderator, admin, superadmin

Sonderregeln:
- moderator: nur Blog/News, keine PII, kein Export, kein Audit-Read
- superadmin Provisioning: out-of-band (nicht über normale Admin-Endpunkte)

## 4) Auth & Consent (FIX)
- E-Mail Login + Verifizierung (OTP/Magic-link)
- One-time + TTL + Rate-Limits + Anti-Enumeration
- Consent-Gate Pflicht (AGB + Datenschutz)
- Speicherung Version + Timestamp (auditierbar)
- Tokens/Codes/Links niemals im Klartext loggen

## 5) MVP-Scope (Produktkern)
MVP-Kern:
- Service Heft 4.0: Profil (VIN/WID + QR/ID), Timeline/Einträge, Dokumente/Uploads
- Trust-Level je Eintrag/Quelle (T1/T2/T3)
- Public-QR Mini-Check: Ampel Rot/Orange/Gelb/Grün (ohne Metrics, mit Disclaimer)
- Frontpage/Hub + Login
- Blog/News (Admin erstellt; Moderator verwaltet strikt Blog/News)
- Admin-Minimum (Governance): Userliste redacted, Rolle setzen, Moderatoren akkreditieren,
  VIP-Gewerbe-2-Staff-Freigabe (SUPERADMIN), Audit (ohne PII)

Zusatzmodule (später, VIP/Dealer):
- Verkauf/Übergabe-QR, interner Verkauf
- Gewerbe: Direktannahme, MasterClipboard, OBD/GPS, etc.

## 6) Trustscore / T-Level (Status)
- Ampel bewertet nur Dokumentation/Verifizierungsgrad, nicht Technik
- Kriterien high-level (ohne Metriken): Historie, T-Level, Aktualität/Regelmäßigkeit, Unfalltrust
- Unfallregel: „Grün trotz Unfall“ nur bei Abschluss + Belegen

Offen/P0-Entscheidung:
- konkrete Definition T1/T2/T3 (deterministisch, ohne Metrics)
- Ampel-Mindestbedingungen je Stufe
- Definition „Unfall abgeschlossen“ + Pflichtbelege

## 7) Repo/Setup (IST)
Repo: .\LifeTimeCircle-ServiceHeft-4.0
Top-Level: docs/ server/ static/ storage/ tools/ scripts/

ZIP-Regel:
- NICHT rein: server\data\app.db, venv, caches, Logs, Build-Artefakte

Start/Tests (DEV):
- env vars: LTC_SECRET_KEY, LTC_DB_PATH, LTC_DEV_EXPOSE_OTP
- Start: uvicorn via poetry
- Tests: poetry run pytest

## 8) Backend IST-Stand (FastAPI/Poetry/SQLite)
- Auth Request/Verify ok (DEV OTP optional)
- Sessions/Token-Check ok
- Audit vorhanden (ohne Klartext-PII)
- RBAC-Guards integriert (401/403 sauber)
- UTC/tz-aware Timestamps gepatcht
- Pytest grün

## 9) Exports (P0)
- Ziel: Policy-konform
- Missing Tables werden als 404 gemeldet (kein 500)

Vehicle Export:
- GET /export/vehicle/{id}: redacted default, scope enforced
- POST /export/vehicle/{id}/grant: superadmin, one-time Token + TTL/Limit
- GET /export/vehicle/{id}/full: superadmin + X-Export-Token, Response encrypted

## 10) Offene Entscheidungen (MUSS vor „final“)
- T1/T2/T3 Belegarten/Prüfer/Regeln
- Ampel-Mindestbedingungen (ohne Metrics, aber deterministisch)
- Definition „Unfall abgeschlossen“ + Pflichtbelege
- Übergabe-/Verkaufsflow (inkl. Käufer ohne Account)
- Newsletter-Workflow (Send-only vs Reply/Feedback + Moderation)

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

## 12) DoD Gate vor Abgabe (MUSS)
- Navigation/Buttons/Empty States ok
- RBAC serverseitig, keine UI-only Security
- Public-QR: ohne Metrics + Disclaimer exakt
- Logs/Audit/Export konform (keine PII/Secrets, HMAC)
- Upload-Quarantäne & Allowlist aktiv
- Keine Pfad-/Altversion-Konflikte (Docs SoT = .\docs)
'@ | Set-Content -Encoding UTF8 .\docs\99_MASTER_CHECKPOINT.md
