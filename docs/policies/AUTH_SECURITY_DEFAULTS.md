// File: ./docs/policies/AUTH_SECURITY_DEFAULTS.md

# AUTH_SECURITY_DEFAULTS – Login, Sessions, Anti-Abuse (passwordless)

**Stand:** 2026-01-28 (Europe/Berlin)  
**Scope:** Auth, Verification, Sessions, Consent-Enforcement

---

## 1) Grundprinzipien
- Passwordless: **OTP oder Magic-Link** (E-Mail verifiziert).
- **Anti-Enumeration**: Responses dürfen nie verraten, ob eine E-Mail existiert.
- **Rate-Limits**: pro IP, pro E-Mail-HMAC, pro Device-Fingerprint (falls vorhanden).
- **No Secrets in Logs**: keine Codes, keine Magic-Links, keine Tokens.

---

## 2) E-Mail Normalisierung (MUST)
- Trim, lowercase, Unicode-Normalisierung (NFKC).
- Persistiert: `email_normalized` (geschützt) und `email_hmac` (für Logs/Rate-Limits).
- `email_hmac = HMAC-SHA256(app_secret, email_normalized)` (siehe CRYPTO_STANDARDS.md).

---

## 3) Verification Challenge (OTP / Magic-Link)
### 3.1 Storage (MUST)
- Speichere **nur** Hashes:
  - OTP: `otp_hash = HMAC-SHA256(secret, otp + challenge_id)`
  - Magic-Link: `token_hash = HMAC-SHA256(secret, raw_token)`
- Speichere metadata: purpose(login|signup|step_up), created_at, expires_at, attempts, locked_until.

### 3.2 TTL Defaults (SHOULD)
- OTP gültig: 10 Minuten
- Magic-Link gültig: 30 Minuten
- Challenge hard-expire: 60 Minuten

### 3.3 Attempt Limits (SHOULD)
- OTP: max 5 Fehlversuche pro Challenge → lock bis expiry
- Magic-Link: single-use; bei reuse sofort invalid

### 3.4 Anti-Enumeration Response (MUST)
- „Wenn diese E-Mail existiert, wurde eine Nachricht gesendet.“ (immer gleich)
- Gleiche Latenz-Klasse (jitter optional), gleicher Statuscode.

---

## 4) Rate Limits (SHOULD, produktiver Startwert)
- Request Verification:
  - pro IP: 10/min
  - pro email_hmac: 3/10min
- Verify Code/Link:
  - pro IP: 20/min
  - pro challenge: 10/min
- Global: WAF/Edge-Rate-Limit zusätzlich empfohlen.

---

## 5) Session Security
### 5.1 Session Token (MUST)
- HttpOnly, Secure, SameSite=Lax (oder Strict, wenn kompatibel).
- Rotierbare Refresh-Logik (optional) oder kurzlebige Sessions.

### 5.2 Session TTL (SHOULD)
- Access Session: 8 Stunden
- Inaktivitäts-Timeout: 30 Minuten (rolling)
- Admin Step-up: 15 Minuten (siehe ADMIN_SECURITY_BASELINE.md)

### 5.3 Device Binding (MAY)
- optionales Device-Fingerprint Hashing (nur HMAC), nicht als Klartext.

---

## 6) Consent Enforcement (MUST)
- Ohne akzeptierte AGB + Datenschutz: kein produktiver Zugriff.
- Bei jedem Login prüfen:
  - latest required doc_version je doc_type
  - ConsentRecord existiert und accepted_at gesetzt
- ConsentRecord enthält:
  - user_id, doc_type, doc_version, accepted_at, source(ui|api), evidence_hash(optional)

---

## 7) Security Events (Audit)
Audit schreiben bei:
- role changes / org approvals
- consent accepted
- public share enable/rotate
- export full/redacted requested
- verification T-level gesetzt
Siehe AUDIT_SCOPE_AND_ENUMS.md
