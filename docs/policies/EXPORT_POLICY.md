// File: ./docs/policies/EXPORT_POLICY.md

# EXPORT_POLICY – Datenexport (redacted default, Full Export nur admin)

**Stand:** 2026-01-28 (Europe/Berlin)  
**Prinzip:** Data Minimization, Redaction by default, Auditpflicht

---

## 1) Export-Typen
### 1.1 Redacted Export (Default)
- Enthält keine Klartext-PII.
- Dokumentinhalte optional (Policy-gated), standardmäßig: nur Metadaten + Verweise.
- Für user/vip/dealer: nur own/org scope.

### 1.2 Full Export (hoch sensibel)
- Nur admin.
- Step-up Auth erforderlich.
- Verschlüsselt ausliefern (AES-256-GCM oder KMS envelope).
- TTL/Limit pro Export-Job.

---

## 2) Formate (SHOULD)
- JSON (strukturierter Export)
- PDF Summary (optional, später)
- ZIP ist **nicht** Standard-Output dieser Spezifikation (keine ZIPs als Projekt-Deliverable).

---

## 3) Redaction Regeln (MUST)
- Entferne/ersetze:
  - E-Mail, Name, Adresse, Telefonnummer
  - IPs, Device IDs
- Erlaubt:
  - user_id/vehicle_id (interne IDs)
  - email_hmac (optional, für Referenzen)
- Audit bleibt stets redacted.

Siehe PII_POLICY.md

---

## 4) Export Jobs (MUST)
- Export wird als Job erstellt:
  - requested_by, scope, export_type, created_at, expires_at
- Storage:
  - verschlüsselt
  - signed download URL kurzlebig oder Proxy download
- Löschen:
  - nach Ablauf `expires_at` hard delete

---

## 5) Zugriff (MUST)
- Redacted export:
  - user/vip: own
  - dealer: org
  - admin: any
- Full export:
  - nur admin + step-up + audit

---

## 6) Audit (MUST)
- EXPORT_* Events schreiben
- Denied/Blocked ebenfalls auditieren
Siehe AUDIT_SCOPE_AND_ENUMS.md

