// File: ./docs/policies/DATA_CLASSIFICATION.md

# DATA_CLASSIFICATION – Datenklassen & Handhabung

**Stand:** 2026-01-28 (Europe/Berlin)

---

## 1) Datenklassen (kanonisch)
### CLASS_PUBLIC
- Inhalte, die öffentlich vorgesehen sind (z. B. Blog, Public-QR Ampel/Disclaimer)
- MUST: keine PII, keine Secrets, keine Metrics/Zeiträume im Public-QR Output

### CLASS_INTERNAL
- Betriebsdaten ohne PII (z. B. Feature Flags, non-sensitive Telemetrie ohne IDs)
- Zugriff: team-intern, least privilege

### CLASS_CONFIDENTIAL
- Nutzerbezogene Inhalte (Service-Einträge, Dokument-Metadaten), interne IDs
- Zugriff: RBAC + Scope; Exports redacted default

### CLASS_RESTRICTED
- PII, Auth-Metadaten, Audit-Daten, Export-Jobs, Admin-Konfiguration
- Zugriff: strikt, Admin nur mit Step-up für sensitive Views
- Logging/Audit ohne Klartext-PII

### CLASS_SECRET
- Kryptoschlüssel, Signing Keys, App Secrets, Token Seeds
- Zugriff: KMS/Secret Manager only; niemals im Code/Repo/Logs

---

## 2) Mapping (Beispiele)
- BlogPost (public) → CLASS_PUBLIC
- Public-QR Output → CLASS_PUBLIC (ohne Metrics)
- User.email → CLASS_RESTRICTED (PII)
- ConsentRecord → CLASS_RESTRICTED
- AuditEvent → CLASS_RESTRICTED (redacted)
- Vehicle/Entry/Document (Inhalte) → CLASS_CONFIDENTIAL
- Storage refs + encryption metadata → CLASS_RESTRICTED
- KMS keys / HMAC secrets → CLASS_SECRET

---

## 3) Handhabungsregeln (MUST)
- CLASS_SECRET: nur KMS; Rotation; Zugriff protokolliert.
- CLASS_RESTRICTED: redaction by default; exfiltration controls; admin step-up.
- CLASS_CONFIDENTIAL: RBAC + scope checks; no public exposure; quarantine gates für Uploads.
- CLASS_PUBLIC: content security (XSS), aber keine Privacy-Risiken.

---

## 4) Datenübertragung (MUST)
- TLS enforced.
- Minimierung: nur benötigte Felder pro API.
- Public endpoints liefern nie CONFIDENTIAL/RESTRICTED.
