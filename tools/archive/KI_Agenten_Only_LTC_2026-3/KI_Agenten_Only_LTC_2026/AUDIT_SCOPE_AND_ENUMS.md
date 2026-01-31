# AUDIT SCOPE & ENUMS – LifeTimeCircle / Service Heft 4.0

Version: 1.0  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 1) Bedeutung von "⚠️ eingeschränkt"
"⚠️" bedeutet: Zugriff nur im eigenen Scope (Org/Ownership) + Feld-Redaction.

### 1.1 Org-/Ownership-Scope
Zugriff ist nur erlaubt, wenn mindestens eins gilt:
- `viewer_org_id == target_org_id`
- `owner_id == viewer_id` (Owner der Ressource)

### 1.2 Feld-Redaction (Pflicht)
Auch im erlaubten Scope:
- keine PII-A Felder
- PII-B nur maskiert/hashed
- IP nur hash
- keine Auth-Secrets/Verify-Daten

---

## 2) reason_code ENUM (Pflicht, kein Freitext)
Regel: `reason_code` ist immer genau 1 Wert aus dieser Liste.

### 2.1 Permission
- `PERM_DENIED_ROLE`
- `PERM_DENIED_SCOPE`
- `PERM_DENIED_OWNERSHIP`

### 2.2 Auth / Security
- `AUTH_RATE_LIMIT_IP`
- `AUTH_RATE_LIMIT_EMAIL`
- `AUTH_LOCKOUT_TEMP`
- `SUSPICIOUS_ACTIVITY`

### 2.3 Export
- `EXPORT_REDACTED_DEFAULT`
- `EXPORT_FULL_APPROVED_SUPERADMIN`
- `EXPORT_DENIED_POLICY`

### 2.4 Business Actions
- `VIP_BIZ_STAFF_SLOT_APPROVED`
- `VIP_BIZ_STAFF_SLOT_DENIED`
- `HANDOVER_ALLOWED_VIP_DEALER_ONLY`
- `HANDOVER_DENIED_NOT_VIP_DEALER`

---
