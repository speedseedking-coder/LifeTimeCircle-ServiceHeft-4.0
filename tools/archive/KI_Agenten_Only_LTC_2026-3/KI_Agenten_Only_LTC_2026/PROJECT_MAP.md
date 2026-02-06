# PROJECT MAP – LifeTimeCircle / Service Heft 4.0

Version: 1.3  
Stand: 2026-01-27

---

## 1) Zielbild Architektur (kurz)
- Frontend (static): Landing/Hub/Module/Pages + Client-Logik
- Backend (server): Auth/Verify, Rollen, Datenzugriffe, Audits, Public-QR API (falls serverseitig)
- Docs (dieser Ordner): verbindliche Regeln/Policies/Specs
- Tools (tools): Start-/Build-/Prüfroutinen

---

## 2) Canonical Dokumente (Source of Truth)
Dieses Paket ist vollständig, wenn folgende Dateien vorhanden sind:
- `POLICY_INDEX.md`
- `AGENT_BRIEF.md`
- `PROJECT_MAP.md`
- `ROLES_AND_PERMISSIONS.md`
- `TRUSTSCORE_SPEC.md`
- `ACCEPTANCE_TESTS.md`

Policies:
- `PII_POLICY.md`
- `AUTH_SECURITY_DEFAULTS.md`
- `ADMIN_SECURITY_BASELINE.md`
- `CRYPTO_STANDARDS.md`
- `DATA_CLASSIFICATION.md`
- `DATA_RETENTION.md`
- `AUDIT_SCOPE_AND_ENUMS.md`
- `EXPORT_POLICY.md`
- `UPLOAD_SECURITY_POLICY.md`
- `T3_PARTNER_DATAFLOW.md`
- `MODERATOR_POLICY.md`
- `NEWSLETTER_CONSENT_POLICY.md`

---

## 3) Ordner-/Repo-Integration (Hinweis)
Wenn diese Dateien in ein Projekt integriert werden:
- entweder in einen zentralen `/docs` Ordner legen
- oder als “Security/Compliance Pack” im Root führen

Wichtig:
- Referenzen innerhalb der Docs müssen zur realen Struktur passen.
- Keine zweite, parallele Altversion an anderer Stelle (sonst “welches gilt?”).

---

## 4) Konfiguration
- Projektkontakt: `lifetimecircle@online.de`
- Frontend-Konfig ohne Secrets (z. B. app.config.json)
- Backend-Konfig via `.env` (kein Secret im Repo)

---

## 5) Datenverträge
### 5.1 Module Registry
- `modules.registry.json`
- `id` stabil, URL-safe, eindeutig
- `path` relativ zur static-root

### 5.2 Trustscore
- Public Contract darf keine Rohmetriken im Public-Response liefern
- Debug/Intern nur ADMIN/SUPERADMIN (RBAC)

Verbindlich: `TRUSTSCORE_SPEC.md`

---

## 6) Security/PII/Audit/Export/Uploads (Verlinkung)
- PII/Logs/Audit/Export: `PII_POLICY.md`, `EXPORT_POLICY.md`, `AUDIT_SCOPE_AND_ENUMS.md`
- Crypto: `CRYPTO_STANDARDS.md`
- Uploads: `UPLOAD_SECURITY_POLICY.md`
- Auth Anti-Enumeration: `AUTH_SECURITY_DEFAULTS.md`

---

## 7) Testpunkte (Quick Checklist)
- Auth (Verify TTL/One-time, Rate-Limits, Anti-Enumeration)
- AGB/Datenschutz Gate serverseitig
- Rollen-Gating (VIP/Dealer, VIP_BIZ Slots, Moderator)
- Public-QR: Ampel korrekt, Disclaimer Pflicht, keine metrics im Public
- Logs: Allowlist, keine Secrets/PII
- Uploads: Allowlist/Quarantäne/Scan bzw. Approval-Fallback/RBAC

Verbindlich: `ACCEPTANCE_TESTS.md`

---
