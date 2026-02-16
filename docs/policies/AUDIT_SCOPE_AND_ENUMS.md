// File: ./docs/policies/AUDIT_SCOPE_AND_ENUMS.md

# AUDIT_SCOPE_AND_ENUMS – Audit Events, Felder, Redaction

**Stand:** 2026-01-28 (Europe/Berlin)  
**Ziel:** Nachvollziehbarkeit sicherheitsrelevanter Vorgänge ohne PII/Secrets in Logs.

---

## 1) Audit Pflichtfelder (MUST)
Ein AuditEvent MUST enthalten:
- `event_id` (UUID)
- `created_at` (UTC ISO)
- `actor_type` (user|system)
- `actor_id` (intern)
- `actor_role` (public|user|vip|dealer|moderator|admin) – Snapshot
- `action` (enum)
- `target_type` (enum)
- `target_id` (intern, optional)
- `scope` (own|org|shared|public)
- `result` (success|denied|error)
- `request_id` / `correlation_id`
- `redacted_metadata` (JSON, no PII, no secrets)

**MUST NOT:** OTPs, Magic-Links, Access Tokens, Refresh Tokens, Dokumentinhalte, Klartext-PII.

---

## 2) Redaction Regeln (MUST)
- PII nur als:
  - `email_hmac`
  - `user_ref` (interne ID)
- IP-Adressen:
  - in Audit optional, wenn nötig, dann gekürzt/hashed (HMAC) und nur bei Security Events.
- Dokumente:
  - nur `document_id` + `doc_type` + `quarantine_status` (keine Titel/Dateinamen im Audit, außer redacted)

---

## 3) Action Enums (verbindlich)
### Auth / Consent
- AUTH_CHALLENGE_CREATED
- AUTH_CHALLENGE_VERIFIED
- AUTH_CHALLENGE_FAILED
- SESSION_CREATED
- SESSION_REVOKED
- CONSENT_ACCEPTED
- CONSENT_REQUIRED_BLOCK

### RBAC / Governance
- ROLE_GRANTED
- ROLE_REVOKED
- ORG_CREATED
- ORG_MEMBERSHIP_REQUESTED
- ORG_MEMBERSHIP_APPROVED
- ORG_MEMBERSHIP_REVOKED
- MODERATOR_ACCREDITED
- MODERATOR_REVOKED

### Vehicle / Entries
- VEHICLE_CREATED
- VEHICLE_UPDATED
- VEHICLE_DELETED
- ENTRY_CREATED
- ENTRY_UPDATED
- ENTRY_VERSION_CREATED
- ENTRY_DELETED

### Documents / Upload
- UPLOAD_RECEIVED
- UPLOAD_QUARANTINED
- UPLOAD_SCANNED_CLEAN
- UPLOAD_SCANNED_SUSPICIOUS
- UPLOAD_APPROVED
- UPLOAD_REJECTED
- DOCUMENT_VISIBILITY_CHANGED

### Verification
- VERIFICATION_SET_T1
- VERIFICATION_SET_T2
- VERIFICATION_SET_T3
- VERIFICATION_REVOKED
- T3_PARTNER_ACCREDITED
- T3_PARTNER_REVOKED

### Public / Transfer / Sale
- PUBLIC_SHARE_ENABLED
- PUBLIC_SHARE_DISABLED
- PUBLIC_SHARE_ROTATED
- HANDOVER_TOKEN_CREATED
- HANDOVER_COMPLETED
- HANDOVER_EXPIRED

### Export
- EXPORT_REDACTED_REQUESTED
- EXPORT_REDACTED_READY
- EXPORT_FULL_REQUESTED
- EXPORT_FULL_READY
- EXPORT_DENIED

### Admin Ops
- ADMIN_STEP_UP_SUCCESS
- ADMIN_STEP_UP_FAILED
- CONFIG_CHANGED
- RETENTION_OVERRIDE_SET

---

## 4) Target Types (enum)
- USER
- ORG
- ORG_MEMBERSHIP
- VEHICLE
- ENTRY
- ENTRY_VERSION
- DOCUMENT
- VERIFICATION
- PUBLIC_SHARE
- HANDOVER
- EXPORT_JOB
- BLOG_POST
- NEWSLETTER_SUBSCRIPTION
- SYSTEM_CONFIG

---

## 5) Denied/Blocked Auditing (MUST)
Auch denied MUST auditieren, aber ohne zusätzliche sensitive Metadaten:
- action (attempted)
- actor
- endpoint/resource
- reason_code (enum), z. B. RBAC_DENY, CONSENT_MISSING, QUARANTINE_BLOCK, RATE_LIMIT

---

## 6) Audit Zugriff (MUST)
- Nur admin darf Audit einsehen/filtern/exportieren.
- Moderator hat keinen Zugriff.
- Export aus Audit folgt EXPORT_POLICY.md
