docs/99_MASTER_CHECKPOINT.md
# LifeTimeCircle – Service Heft 4.0 · 99_MASTER_CHECKPOINT

Stand: 04.02.2026 (Europe/Berlin)  
Kontakt: lifetimecircle@online.de

Ziel: produktionsreif (keine Demo)  
Security Default: deny-by-default + least privilege  
RBAC: serverseitig enforced (keine Client-Trusts)  
Source of Truth (Docs): C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs

---

## 0) Quick-Status (grün/gelb/rot)

✅ Server bootet (uvicorn --reload)  
✅ OpenAPI erreichbar: GET /openapi.json = 200  
✅ Auth-Flow DEV: POST /auth/request + POST /auth/verify = 200 (DEV-OTP, wenn aktiviert)  
✅ Consent-Module vorhanden + Router gemountet  
✅ Consent-Persistenz bestätigt: POST /consent/accept + GET /consent/status => is_complete=true  

✅ **Sale/Transfer P0** vorhanden + Router gemountet  
✅ **Sale/Transfer Tests**: `poetry run pytest -q` **grün** (letzter Lauf 04.02.2026)  
✅ Audit für Sale/Transfer: **best-effort**, darf Business-Flow nicht killen

---

## 1) Zwischen-Check: Änderungen seit 01.02.2026

### 1.1 Sale/Transfer P0 (neu)
Ziel: Eigentumsübergabe/Übergabeprozess über Token (VIP/Dealer) mit Audit.

Neu angelegt:
- `server/app/routers/sale_transfer.py`
- `server/app/services/sale_transfer_store.py`
- `server/app/services/sale_transfer_audit.py`
- `server/tests/test_sale_transfer_api.py`
- `server/scripts/patch_sale_transfer_router.ps1`
- `server/scripts/smoke_sale_transfer.ps1`

Git-Referenzen (harte Fakten):
- Commit: `ec47d77` — `P0: Sale/Transfer API (vip/dealer) + audit + tests` (Initial)
- Commit: `2629b67` — `P0: Sale/Transfer stabilisiert + Audit best-effort + Smoke + Master Checkpoint` (Stabilisierung)

Änderungen in `2629b67` (harte Fakten):
- `docs/99_MASTER_CHECKPOINT.md`
- `server/app/services/sale_transfer_store.py`
- `server/app/services/sale_transfer_audit.py`
- `server/scripts/smoke_sale_transfer.ps1`
- `server/.gitignore` (neu)

### 1.2 Wichtige Fixes im Verlauf (Sale/Transfer)
- Audit Insert konnte wegen `audit_events.module_id NOT NULL` crashen → Audit wurde so gebaut, dass `module_id` gesetzt wird (wenn Spalte existiert) und ansonsten auf Fallback ausweicht.
- SQLite DateTimes: naive/aware Vergleich führte zu `TypeError` → Vergleich/Handling so angepasst, dass keine tz-Mismatch-Exceptions mehr entstehen.
- Redeem mehrfach: zweites Redeem darf **nicht** erneut erfolgreich sein → Status/Conflict-Handling korrigiert.
- Intermittent `transfer_not_found`: Persistenz/Lookup/Transaktionsverhalten stabilisiert (Commit/Query-Flow bereinigt).

### 1.3 Repo Hygiene: LF Enforcement (neu)
Neu:
- `.gitattributes` mit `eol=lf` Regeln für `*.md`, `*.py`, `*.ps1`

Git-Referenz (harte Fakten):
- Commit: `18c809f` — `Chore: enforce LF via gitattributes`

---

## 2) Consent P0 (bestehend, reproduzierbar)

### 2.1 Consent: Komponenten (angelegt)
- `app/consent/policy.py`
- `app/models/consent.py`
- `app/services/consent_store.py`
- `app/routers/consent.py`
- `tests/test_consent_contract.py`

### 2.2 Main: Router-Mount
- `app/main.py` importiert und mountet `consent_router` (include_router)

### 2.3 Kompatibilität / Auth-Import-Fix
Problem: ImportError in `app/auth/routes.py` (erwartet `app.consent_store: record_consent, get_consent_status, env_consent_version, env_db_path`)

Lösung:
- Konsolidierung auf `app/services/consent_store.py` + kompatible Imports
- Router `/consent/*` stabil erreichbar

---

## 3) Consent Contract (aktuell)

### 3.1 API
- `POST /consent/accept` → speichert AGB+Datenschutz (Version+Timestamp)
- `GET /consent/status` → `is_complete=true|false` + Version/Zeiten

### 3.2 Erwartung
- Consent ist Pflicht (AGB+Datenschutz)
- Version+Timestamp auditierbar (persistiert)

---

## 4) Sale/Transfer P0 (aktuell)

### 4.1 Zielbild
- VIP erstellt Übergabe-Token (Transfer)
- Dealer löst Token ein (Redeem)
- RBAC enforced (VIP/Dealer, nicht Admin-only)
- Audit best-effort: Fehler im Audit dürfen Business-Flow nicht killen

### 4.2 Verhalten (Kurz)
- Create: erzeugt Token + Persistenz
- Redeem:
  - valid/created → redeem ok
  - bereits eingelöst / anderer Status → 409/410 (kein 200)
  - expiry sauber geprüft (keine tz-naive/aware Exceptions)

---

## 5) DEV-ENV (lokal)

Minimal:
- `LTC_SECRET_KEY` (>= 16 Zeichen; empfohlen >= 32)

Optional/Dev:
- `LTC_DEV_EXPOSE_OTP = "1"` → `/auth/request` liefert dev_otp (nur lokal)
- `LTC_MAILER_MODE    = "null"` (kein SMTP Versand; DEV-OTP nutzen)
- `LTC_DB_PATH        = ".\data\app.db"` (optional; default ist `./data/app.db`)

Typische Stolperfallen:
- Poetry muss im `server`-Ordner laufen (sonst: "pyproject.toml nicht gefunden").
- Env setzen in PowerShell immer mit `$env:NAME="value"`.

---

## 6) DEV Start & Smoke

### 6.1 Server Start (Fenster A)
Script:
- `server\scripts\dev_start_server.ps1`

Start:
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev_start_server.ps1`

Erwartung:
- "Application startup complete."
- Requests werden als 200 geloggt (bei Erfolg)

### 6.2 Smoke: Auth + Consent (Fenster B)
Script:
- `server\scripts\smoke_auth_consent.ps1`

Ziel:
- Auth: request → verify → me
- Consent: accept → status (`is_complete=true`)

Start:
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke_auth_consent.ps1`

### 6.3 Smoke: Sale/Transfer (Fenster B)
Script:
- `server\scripts\smoke_sale_transfer.ps1` (Stand: Commit `2629b67`)

Ziel:
- Login VIP → create transfer
- Login Dealer → redeem transfer
- optional: status read / cancel cases

---

## 7) Tests / Qualität

Letzter Status:
- `poetry run pytest -q` → ✅ grün (04.02.2026)

Abgedeckt:
- Consent Contract Test
- Sale/Transfer API: happy path + negative cases (u.a. Admin kann Status lesen)

---

## 8) Aktueller Git-Status (harte Fakten)

- Branch: `main`
- Status: up to date mit `origin/main`
- Working Tree: clean

Commits seit letztem Stand (harte Fakten):
- `2629b67` — `P0: Sale/Transfer stabilisiert + Audit best-effort + Smoke + Master Checkpoint`
- `18c809f` — `Chore: enforce LF via gitattributes`

---

## 9) Ergebnis: aktueller Stand

Consent (Discovery + Persistenz) ist funktional und reproduzierbar.  
Sale/Transfer P0 ist implementiert inkl. RBAC + Audit (best-effort) und Test-Suite ist grün.
