C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs\policies\POLICY_INDEX.md
# LifeTimeCircle – ServiceHeft 4.0
## Policy Index (verbindlich)

Stand: 2026-01-29  
Kontakt: lifetimecircle@online.de

Zweck: Navigation und Verbindlichkeitsrahmen für alle Policies.  
Grundsatz: **deny-by-default** + **least privilege**. **RBAC wird serverseitig enforced**.

---

## 0) Kanonische Referenzen
- Docs Index: `docs/00_INDEX.md`
- Project Brief: `docs/00_PROJECT_BRIEF.md`
- Decisions Log: `docs/01_DECISIONS.md`
- Backlog: `docs/02_BACKLOG.md`
- RBAC Matrix: `docs/03_RIGHTS_MATRIX.md`
- Modul-Katalog: `docs/04_MODULE_CATALOG.md`
- Modul-Spec-Schema: `docs/05_MODULE_SPEC_SCHEMA.md`
- Terms/Glossar: `docs/06_TERMS_GLOSSARY.md`
- Context Pack: `docs/07_CONTEXT_PACK.md`
- Project Map: `docs/policies/PROJECT_MAP.md`

---

## 1) Auth / Consent / Zugang
- `docs/policies/AUTH_SECURITY_DEFAULTS.md`
- `docs/policies/NEWSLETTER_CONSENT_POLICY.md`

---

## 2) Rollen & Berechtigungen (RBAC)
- `docs/policies/ROLES_AND_PERMISSIONS.md`
- `docs/03_RIGHTS_MATRIX.md`

Sonderregeln (Reminder):
- Übergabe/Verkauf-QR & interner Verkauf: nur VIP/Dealer.
- VIP-Gewerbe: max. 2 Mitarbeiterplätze; Freigabe nur SUPERADMIN.
- Moderator: nur Blog/News; keine PII; kein Export; kein Audit.

---

## 3) Public-QR / Trustscore
- `docs/policies/TRUSTSCORE_SPEC.md`

Public-Ausgabe (Reminder):
- nur Dokumentationsqualität, nie technischer Zustand
- keine Metrics/Counts/Percentages/Zeiträume
- Pflicht-Disclaimer

---

## 4) Datenschutz / Datenklassen / Aufbewahrung
- `docs/policies/DATA_CLASSIFICATION.md`
- `docs/policies/PII_POLICY.md`
- `docs/policies/DATA_RETENTION.md`

---

## 5) Uploads
- `docs/policies/UPLOAD_SECURITY_POLICY.md`

---

## 6) Exporte
- `docs/policies/EXPORT_POLICY.md`

---

## 7) Audit / Logging / Events
- `docs/policies/AUDIT_SCOPE_AND_ENUMS.md`

---

## 8) Crypto / Security Baselines
- `docs/policies/CRYPTO_STANDARDS.md`
- `docs/policies/ADMIN_SECURITY_BASELINE.md`

---

## 9) Moderator
- `docs/policies/MODERATOR_POLICY.md`

---

## 10) Acceptance / Tests / DoD
- `docs/policies/ACCEPTANCE_TESTS.md`

---

## 11) T3 / Partner Datenflüsse
- `docs/policies/T3_PARTNER_DATAFLOW.md`

---

## 12) KI-Agenten
- `docs/policies/AGENT_BRIEF.md`

---

## 13) Modul-Repos (verbindliche Regel)
- Modul-Repos dürfen keine eigenen abweichenden Policies definieren.
- Modul-Repos müssen `CONTEXT_PACK.md` (Copy aus Core) enthalten.
- Modul-Spezifikation im Modul-Repo muss das Schema aus `docs/05_MODULE_SPEC_SCHEMA.md` erfüllen.
