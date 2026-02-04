C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs\99_MASTER_CHECKPOINT.md
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
✅ Auth-Flow DEV: POST /auth/request + POST /auth/verify = 200 (DEV-OTP optional)  
✅ Consent-Module vorhanden + Router gemountet  
✅ Consent-Persistenz bestätigt: POST /consent/accept + GET /consent/status => is_complete=true  
✅ Sale/Transfer API (P0) vorhanden + Router gemountet  
✅ Audit (Sale/Transfer) best-effort: primary audit table oder fallback sale_transfer_audit_events  
✅ Test-Suite grün: `poetry run pytest` / `poetry run pytest -q` = 100% OK

---

## 1) Projekt-Module (Ist-Stand)

### 1.1 Auth (DEV-Flow)
- /auth/request (optional dev_otp bei LTC_DEV_EXPOSE_OTP=1)
- /auth/verify
- /auth/me

### 1.2 Consent (P0)
- Discovery: GET /consent/current (public)
- Status: GET /consent/status (Auth)
- Accept: POST /consent/accept (Auth)

### 1.3 Sale/Transfer (P0)
- Create: POST /sale/transfer/create (Auth, role vip|dealer)
- Redeem: POST /sale/transfer/redeem (Auth, role vip|dealer) → One-time redeem
- Cancel: POST /sale/transfer/cancel (Auth, Initiator)
- Status: GET /sale/transfer/status/{transfer_id} (Auth; Initiator/Redeemer oder admin/superadmin)

---

## 2) Neu / Fixes (Consent P0)

### 2.1 Consent: Komponenten
- app/consent/policy.py
- app/models/consent.py
- app/services/consent_store.py
- app/routers/consent.py
- tests/test_consent_contract.py

### 2.2 Main: Router-Mount
- app/main.py mountet consent_router via include_router

### 2.3 Kompatibilität / Auth-Import-Fix
Problem: app/auth/routes.py erwartete `app.consent_store` Symbole.  
Fix:
- app/consent_store.py (Wrapper v1) stellt erwartete Funktionen bereit.

### 2.4 Guard-Härtung (dict-User vs Objekt-User)
Fix:
- app/routers/consent.py user_id robust aus dict/Objekt ermitteln
- forbid_moderator robust (dict/Objekt)

---

## 3) Neu / Fixes (Sale/Transfer P0)

### 3.1 Komponenten (Sale/Transfer)
- app/routers/sale_transfer.py
- app/services/sale_transfer_store.py
- app/services/sale_transfer_audit.py
- tests/test_sale_transfer_api.py
- scripts/patch_sale_transfer_router.ps1
- scripts/smoke_sale_transfer.ps1

### 3.2 Datenmodell (Runtime-Table)
Tabelle: `sale_transfers` (wird bei Bedarf via SQLAlchemy MetaData angelegt)  
Kerneigenschaften:
- transfer_id (UUID, PK)
- token_hmac (SHA256-HMAC, unique/index)
- vehicle_id (plain, index)
- status: created|redeemed|cancelled|expired
- created_at / expires_at / redeemed_at / cancelled_at / expired_at
- initiator_user_id / initiator_role
- redeemed_by_user_id / redeemed_by_role
- ownership_transferred (bool)

### 3.3 Token-Sicherheit
- Transfer-Token wird nur im Create-Response ausgegeben.
- Persistiert wird ausschließlich `token_hmac` (HMAC(secret, token)).
- vehicle_id wird für Audit-Events als HMAC abgelegt (vehicle_id_hmac).

### 3.4 Audit-Integration (best-effort, Business-Flow darf nicht sterben)
Problem (früher): `audit_events.module_id` NOT NULL → Inserts ohne module_id brechen Flow.  
Fix/Design:
- `write_sale_audit()` versucht zuerst eine vorhandene globale Audit-Tabelle (z.B. `audit_events` / `audit` / `audits`) zu nutzen und befüllt `module_id="sale_transfer"` wenn Spalte existiert.
- Wenn Insert in Primary fehlschlägt: Fallback-Tabelle `sale_transfer_audit_events` wird automatisch erzeugt und genutzt.
- Audit schreibt in eigener TX (`engine.begin()`), damit ein Audit-Fehler nicht den Business-Commit rollbackt.

### 3.5 Redeem-Logik (One-time)
- Redeem nur, wenn status == "created" und nicht expired.
- Zweites Redeem desselben Tokens muss 409 (not redeemable) oder 410 (expired) liefern (Test abgesichert).
- Redeem schreibt status="redeemed" + Redeemer-Felder + ownership_transferred.

### 3.6 Zeit/UTC Handling (SQLite)
- SQLite/SQLAlchemy liefert DateTime häufig tz-naiv zurück.
- Implementiert: konsistente UTC-Naivzeiten im Store (Vergleiche + Persistenz).
- API-Output: Zeiten werden als ISO-String mit "Z" ausgegeben.

---

## 4) Consent Contract (aktuell)

Required Consents:
- terms v1
- privacy v1

Endpoints:
- GET  /consent/current
  - public discovery (keine Auth)
  - liefert required doc_type/doc_version
- GET  /consent/status
  - Auth erforderlich (Bearer)
  - forbid_moderator
  - liefert required + accepted + is_complete
- POST /consent/accept
  - Auth erforderlich (Bearer)
  - forbid_moderator
  - speichert Acceptances in DB (idempotent möglich)
  - danach muss /consent/status is_complete=true liefern, wenn required erfüllt

Wichtig:
- Auth/verify akzeptiert consents als Payload (Contract-Check), Persistenz wird über /consent/accept geprüft/gesetzt.

---

## 5) Sale/Transfer Contract (aktuell)

### 5.1 Create (Auth: vip|dealer)
POST /sale/transfer/create  
Body:
- vehicle_id (string)
- ttl_seconds (optional; valid range enforced)

Response:
- transfer_id
- transfer_token (nur hier!)
- expires_at (ISO Z)
- status="created"

### 5.2 Redeem (Auth: vip|dealer)
POST /sale/transfer/redeem  
Body:
- transfer_token

Response (success):
- transfer_id
- vehicle_id
- status="redeemed"
- ownership_transferred (bool)

Fehler:
- 404 transfer_not_found
- 409 transfer_not_redeemable
- 410 transfer_expired

### 5.3 Cancel (Auth: Initiator)
POST /sale/transfer/cancel  
Body:
- transfer_id

Response:
- ok=true
- transfer_id
- status="cancelled"

### 5.4 Status (Auth: Initiator/Redeemer oder admin/superadmin)
GET /sale/transfer/status/{transfer_id}

Response:
- transfer_id
- vehicle_id
- status
- created_at / expires_at
- is_expired
- redeemed_at / cancelled_at
- redeemed_by_user_id / initiator_user_id
- ownership_transferred

---

## 6) DEV-ENV (lokal)

Minimal:
- LTC_SECRET_KEY (>= 16 Zeichen; empfohlen deutlich länger)

Optional/Dev:
- LTC_DEV_EXPOSE_OTP = "1"   → /auth/request liefert dev_otp (nur lokal)
- LTC_MAILER_MODE    = "null" (kein SMTP Versand; DEV-OTP nutzen)
- LTC_DB_PATH        = ".\data\app.db" (optional; default ist ./data/app.db)

PowerShell:
- Env setzen mit `$env:NAME="value"`.

Hinweis Line-Endings:
- .py → LF
- .ps1 → CRLF (Git-Warnungen vermeiden)

---

## 7) DEV Start & Smoke (Artefakte)

### 7.1 Server Start (Fenster A)
- server\scripts\dev_start_server.ps1
  - setzt ENV
  - räumt Port 8000 frei
  - py_compile fail-fast
  - startet uvicorn --reload

### 7.2 Smoke: Auth + Consent (Fenster B)
- server\scripts\smoke_auth_consent.ps1
  - /auth/request → /auth/verify → /auth/me → /consent/accept → /consent/status

### 7.3 Smoke: Sale/Transfer (Fenster B)
- server\scripts\smoke_sale_transfer.ps1
  - Login VIP + Create Transfer
  - Login Dealer + Redeem Transfer
  - Status Check (optional)

---

## 8) Tests (Source of Truth)

- `server/tests/test_consent_contract.py`
  - Consent discovery + status + accept + completion

- `server/tests/test_sale_transfer_api.py`
  - Happy path create → redeem
  - Zweites redeem muss nicht-success liefern (409/410)
  - Admin kann status lesen
  - RBAC/Forbidden Pfade

---

## 9) Ergebnis: aktueller Stand (04.02.2026)

- Consent P0: Discovery/Accept/Status inkl. Persistenz ist stabil und reproduzierbar.
- Sale/Transfer P0: API + Store + Audit + Tests sind stabil; pytest Suite ist grün.
- Audit: robust (module_id gesetzt, fallback table vorhanden), darf Business-Flow nicht killen.
