// File: C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs\policies\AGENT_BRIEF.md

# AGENT_BRIEF – LifeTimeCircle / Service Heft 4.0 (produktiver Standard)

**Stand:** 2026-01-28 (Europe/Berlin)  
**Kontakt:** lifetimecircle@online.de  
**Source of Truth:** C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs\policies

---

## 1) Ziel
Service Heft 4.0 ist ein digitales, verifizierbares Service-/Historienheft für Fahrzeuge mit Nachweisen, Verifizierungsstufen (T1/T2/T3) und optionalem **Public-QR Mini-Check**.

**Nicht-Ziel:** technische Zustandsbewertung (weder intern noch öffentlich als Aussage).

---

## 2) Hard Constraints (nicht verhandelbar)
### 2.1 Produktiv / Sicherheit
- deny-by-default + least privilege.
- RBAC **serverseitig enforced** (UI ist nie Sicherheit).
- Keine Secrets in Logs.
- Keine Klartext-PII in Logs/Exports.
- Pseudonymisierung via **HMAC** (kein unsalted SHA).

### 2.2 Public-QR
- Public-QR bewertet **nur Nachweis-/Dokumentationsqualität**.
- Public Output zeigt **keine** Zahlen/Counts/Prozente/Zeiträume.
- Public Output hat **pflichtigen Disclaimer**.

### 2.3 Rollen / Governance
- Verkauf/Übergabe-QR & interner Verkauf: **nur vip/dealer/admin**.
- VIP-Gewerbe: max 2 Staff; Freigabe **nur admin**.
- moderator: nur Blog/News; keine PII; kein Export; kein Audit.

### 2.4 Upload/Export
- Upload: Allowlist, Limits, Quarantäne by default, Freigabe nach Scan oder Admin-Approval.
- Export: standardmäßig redacted; Full Export nur admin + Audit + TTL/Limit + Verschlüsselung.

---

## 3) Verbindliche Policies (zu lesen vor Implementierung)
- ROLES_AND_PERMISSIONS.md
- AUTH_SECURITY_DEFAULTS.md
- ADMIN_SECURITY_BASELINE.md
- AUDIT_SCOPE_AND_ENUMS.md
- PII_POLICY.md
- DATA_CLASSIFICATION.md
- DATA_RETENTION.md
- CRYPTO_STANDARDS.md
- UPLOAD_SECURITY_POLICY.md
- EXPORT_POLICY.md
- TRUSTSCORE_SPEC.md
- NEWSLETTER_CONSENT_POLICY.md
- MODERATOR_POLICY.md
- T3_PARTNER_DATAFLOW.md
- ACCEPTANCE_TESTS.md

---

## 4) Definition of Done (Feature-Abnahme)
Ein Feature gilt nur als „Done“, wenn:
- Navigation/Buttons korrekt; Empty States sauber.
- Serverseitige RBAC-Checks vorhanden + getestet.
- Public-QR ohne Metrics + Disclaimer sichtbar.
- Logs/Audit/Export konform (keine Secrets, keine Klartext-PII).
- Uploads: Quarantäne/Scan/Freigabe umgesetzt.
- Keine Pfadfehler / keine Altpfade / keine Altversionen.

---

## 5) Defaultannahmen (bis eine Decision sie ändert)
- **admin = SUPERADMIN**.
- Verification: T1 = Selbstauskunft, T2 = Beleg vorhanden, T3 = akkreditiert verifiziert.
- E-Mail-Login ist passwordless (OTP/Magic Link) mit Anti-Enumeration & Rate-Limits.
