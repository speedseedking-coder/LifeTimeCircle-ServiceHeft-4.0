C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs\99_MASTER_CHECKPOINT.md
# LifeTimeCircle – Service Heft 4.0 · 99_MASTER_CHECKPOINT

Stand: 01.02.2026 (Europe/Berlin)
Kontakt: lifetimecircle@online.de

Ziel: produktionsreif (keine Demo)
Security Default: deny-by-default + least privilege
RBAC: serverseitig enforced (keine Client-Trusts)
Source of Truth (Docs): C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs

---

## 0) Quick-Status (grün/gelb/rot)

✅ Server bootet (uvicorn --reload)  
✅ OpenAPI erreichbar: GET /openapi.json = 200  
✅ Auth-Flow DEV: POST /auth/request + POST /auth/verify = 200 (mit DEV-OTP, wenn aktiviert)  
✅ Consent-Module vorhanden + Router gemountet  
✅ Consent-Persistenz bestätigt: POST /consent/accept + GET /consent/status => is_complete=true  

### DoD Consent (reproduzierbar)

- Server neu gestartet (dev_start_server.ps1)
- Smoke #1: /auth/request + /auth/verify + /auth/me + /consent/accept + /consent/status → OK
- Server neu gestartet
- Smoke #2: /consent/status zeigt accepted: terms v1 + privacy v1; is_complete=true

---

## 1) Neu / Fixes (Consent P0)

### 1.1 Consent: neue Komponenten (angelegt)
- app/consent/policy.py
- app/models/consent.py
- app/services/consent_store.py
- app/routers/consent.py
- tests/test_consent_contract.py

### 1.2 Main: Router-Mount
- app/main.py importiert und mountet consent_router (include_router)

### 1.3 Kompatibilität / Auth-Import-Fix
Problem: ImportError in app/auth/routes.py (erwartet app.consent_store: record_consent, get_consent_status, env_consent_version, env_db_path)

Fix: compat wrapper
- app/consent_store.py (Wrapper v1) stellt die erwarteten Funktionen bereit.

### 1.4 Guard-Härtung (dict-User vs Objekt-User)
Problem: Consent-Endpoints liefen in "NoneType/dict has no attribute id" weil get_current_user teils dict liefert.

Fix:
- app/routers/consent.py angepasst: user_id robust aus dict/Objekt ermitteln
- forbid_moderator robust (dict/Objekt)

---

## 2) Consent Contract (aktuell)

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

## 3) DEV-ENV (lokal)

Minimal:
- LTC_SECRET_KEY (>= 32 Zeichen, sonst RuntimeError)
Optional/Dev:
- LTC_DEV_EXPOSE_OTP = "1"   → /auth/request liefert dev_otp (nur lokal)
- LTC_MAILER_MODE    = "null" (kein SMTP Versand; DEV-OTP nutzen)
- LTC_DB_PATH        = ".\data\app.db" (optional; default ist ./data/app.db)

Typische Stolperfallen:
- Poetry muss im server-Ordner laufen (sonst: "pyproject.toml nicht gefunden").
- Env setzen in PowerShell immer mit `$env:NAME="value"` (nicht als plain text).

---

## 4) DEV Start & Smoke

### 4.1 Server Start (Fenster A)
Empfohlenes Script:
- server\scripts\dev_start_server.ps1

Inhalt/Verhalten:
- setzt ENV (SECRET_KEY, DEV_EXPOSE_OTP, MAILER_MODE)
- räumt Port 8000 frei
- py_compile app/main.py (fail-fast)
- startet uvicorn --reload

Start:
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev_start_server.ps1

Erwartung (Log):
- "Application startup complete."
- Requests werden als 200 geloggt

### 4.2 Smoke: Auth + Consent (Fenster B)
Script:
- server\scripts\smoke_auth_consent.ps1

Ziel:
- Auth: request → verify → me
- Consent: accept → status (is_complete=true)

Start:
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke_auth_consent.ps1

Erwartung:
- AUTH ME zeigt user_id + role
- CONSENT STATUS zeigt accepted (terms+privacy) und is_complete=true

---

## 5) Aktuelle Artefakte (Scripts)

Neu/Ergänzt:
- server\scripts\dev_start_server.ps1
- server\scripts\smoke_auth_consent.ps1

Vorhanden (Auszug):
- patch_consent_p0_add_files_and_mount.ps1
- patch_consent_router_user_dict_fix.ps1
- patch_consent_store_wrapper_v1.ps1
- patch_mount_consent_router.ps1
- smoke_http.ps1
- auth_test.ps1

---

## 6) Nächste Schritte (konkret)

P0 Stabilität:
1) Smoke-Script so halten, dass es immer:
   - /auth/request → /auth/verify → /auth/me → /consent/accept → /consent/status
2) Persistenz-Check:
   - Server restart → Smoke erneut → muss wieder is_complete=true liefern

P1 Policy/Prod:
3) Sicherstellen: LTC_DEV_EXPOSE_OTP default OFF (Prod)
4) Mailer-Mode für Prod (SMTP) sauber konfigurieren (separat, später)

---

## 7) Ergebnis: aktueller Stand

Consent-Discovery + Consent-Persistenz + Auth-Flow (DEV) sind funktional.
Server läuft stabil mit den aktuellen Patches; Consent ist über Status verifizierbar (is_complete=true nach accept).
