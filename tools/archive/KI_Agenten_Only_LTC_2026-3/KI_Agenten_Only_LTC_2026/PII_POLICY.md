# PII POLICY – LifeTimeCircle / Service Heft 4.0

Version: 1.3  
Stand: 2026-01-27  
Owner: SUPERADMIN (Oberadmin/Haupt-Admin)  
Kontakt: lifetimecircle@online.de

---

## 0) Geltungsbereich (Scope)
Gilt für:
- alle Server-APIs, Worker/Jobs, Web-Frontends, Admin-Tools, Moderations-Tools
- Logs (App/Server/Proxy), Audit-Logs, Monitoring/Tracing, Exporte/Reports
- alle Rollen- und Rechtepfade (PUBLIC bis SUPERADMIN)

---

## 1) Grundprinzipien (Non-Negotiable)
1. Datenschutz > Komfort.
2. Least Privilege.
3. Server-First Enforcement.
4. No Secrets in Logs.
5. Audit Pflicht (PII-minimiert).
6. Export redacted by default; Full Export nur Ausnahmeprozess.

Verwandte Policies:
- `DATA_CLASSIFICATION.md`
- `DATA_RETENTION.md`
- `EXPORT_POLICY.md`
- `AUDIT_SCOPE_AND_ENUMS.md`
- `CRYPTO_STANDARDS.md`
- `UPLOAD_SECURITY_POLICY.md`

---

## 2) Definitionen
### 2.1 PII
PII = Daten, die eine Person direkt/indirekt identifizieren können.

### 2.2 Secrets (S0)
Verify-Code/Link Token, Sessions/JWT, API-Keys.  
Regel: niemals loggen, niemals exportieren, niemals persistent im Client.

---

## 3) Datenklassen (verbindlich)
- PII-A (hoch): Halterdaten, Identität, Bewegungsprofile, unredacted Dokumente mit PII
- PII-B (mittel): indirekte Identifikatoren (VIN/Kennzeichen), maskierte E-Mail, Hashes
- NON-PII: ohne Personenbezug

Grenzfälle: `DATA_CLASSIFICATION.md`

---

## 4) Logging-Policy (Application Logs)
### 4.1 Verboten (immer)
- Tokens/Codes/Links/Sessions/JWT/API-Keys/Reset-Links/Passwort-Hashes
- Auth/Verify Bodies
- vollständige E-Mails, Halterdaten, Adressen, Telefon
- VIN/Kennzeichen im Klartext

### 4.2 Allowlist Logging (Pflicht)
Nur Allowlist-Felder (route, status, trace_id, duration, actor_role, actor_id, ip_hash/ip_prefix, error_code ohne PII).
Kein Header-/Body-Dump.

### 4.3 Exceptions
Keine PII in Exception-Texten; Validierung nur Feldnamen.

---

## 5) Maskierung & Hashing (verbindlich)
- UI: E-Mail nur maskiert (`m***@domain.tld`)
- Logs/Export: Hashes via HMAC-SHA256 (Secret-Key) gemäß `CRYPTO_STANDARDS.md`
- IP: nur ip_hash oder ip_prefix (nie Full-IP)
- VIN/Kennzeichen: vin_hash/plate_hash oder gekürzt; public nie vollständig

Unsalted SHA256 über PII ist untersagt.

---

## 6) Audit (separat vom App-Log)
Pflicht-Events:
- Auth: login_requested, verify_sent, verify_success, verify_failed, rate_limited
- Rollen/Freigaben: role_granted, role_revoked, vip_biz_staff_slot_*
- Verkauf/Übergabe: handover_qr_*, vehicle_transfer_*
- Export: export_requested, export_generated, export_downloaded, export_denied
- Security: permission_denied, suspicious_activity_flagged
- Uploads: upload_received/quarantined/approved/rejected

Schema Pflichtfelder:
- event_id, timestamp, event_type
- actor_role, actor_id
- target_type, target_id
- result, reason_code (ENUM), trace_id

ENUM: `AUDIT_SCOPE_AND_ENUMS.md`

---

## 7) Zugriff
- SUPERADMIN/ADMIN: Audit (PII-minimiert)
- VIP_BIZ_*: nur Scope + Redaction
- MODERATOR/USER/PUBLIC: kein Audit

---

## 8) Export
- Standardexport: redacted (kein PII-A; PII-B maskiert/hashed)
- Full Export: nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung

Details: `EXPORT_POLICY.md`

---

## 9) Retention
Verbindlich: `DATA_RETENTION.md`

---

## 10) Tests
Verbindlich: `ACCEPTANCE_TESTS.md`

---
