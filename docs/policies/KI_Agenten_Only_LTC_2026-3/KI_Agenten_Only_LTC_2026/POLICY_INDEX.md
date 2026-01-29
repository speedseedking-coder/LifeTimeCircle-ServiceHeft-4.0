
# POLICY_INDEX – LifeTimeCircle / Service Heft 4.0

Version: 1.2  
Stand: 2026-01-27  
Owner: Oberadmin (Produkt/Freigabe)  
Kontakt (projektbezogen): lifetimecircle@online.de

---

## 0) Zweck
Zentrales Inhaltsverzeichnis aller verbindlichen Regeln/Policies.
Dieses Dokument ist „Source of Truth“, welche Regeln für Produktion gelten und in welcher Reihenfolge neue Entwickler/KI-Agenten sie lesen müssen.

---

## 1) Canonical Rule (wichtig)
Dieses Regelwerk gilt als **canonical**, wenn alle Dateien **in derselben Ebene** (dieser Ordner) liegen.
Duplikate/Altversionen in anderen Pfaden sind **nicht gültig** und müssen entfernt oder eindeutig als „ARCHIVE/OBSOLETE“ markiert werden.

---

## 2) Pflicht-Lesereihenfolge (Onboarding)
1. `AGENT_BRIEF.md` – Non-Negotiables, Quality Gates, Lieferformate
2. `PROJECT_MAP.md` – Architektur, Ordner, Einstiegspunkte
3. `ROLES_AND_PERMISSIONS.md` – Rollenmodell & serverseitige Durchsetzung
4. `TRUSTSCORE_SPEC.md` – Public-QR Trust-Ampel (nur Nachweisqualität, kein Metrics-Leak)
5. `PII_POLICY.md` – PII/Secrets/Logs/Audit/Export Grundregeln
6. `ACCEPTANCE_TESTS.md` – Definition of Done (Tests/Abnahme)

---

## 3) Policies (verbindlich, Production)

### 3.1 Security & Auth
- `AUTH_SECURITY_DEFAULTS.md`  
  Verify TTL, Rate-Limits, Lockout, Sessions, Anti-Enumeration.
- `ADMIN_SECURITY_BASELINE.md`  
  2FA, Re-Auth, Admin-Sessions, Break-glass, Monitoring.
- `CRYPTO_STANDARDS.md`  
  Crypto-Standards (HMAC statt unsalted SHA, AEAD, Token-Hashing, Signaturen).

### 3.2 Datenschutz / Daten
- `PII_POLICY.md`  
  PII/Secrets Regeln (Logging, Audit, Export).
- `DATA_CLASSIFICATION.md`  
  Einstufung “Grenzfälle” (VIN/Kennzeichen/QR-ID/Standort/Dokumente).
- `DATA_RETENTION.md`  
  Aufbewahrung + Löschung + Backups/Restore.

### 3.3 Audit / Scope / Export
- `AUDIT_SCOPE_AND_ENUMS.md`  
  “⚠️ eingeschränkt” + Reason-Code ENUM (kein Freitext/keine PII).
- `EXPORT_POLICY.md`  
  Redaction-Matrix + Full-Export Ausnahmeprozess (Verschlüsselung gemäß CRYPTO).

### 3.4 Uploads (Bilder/Dokumente)
- `UPLOAD_SECURITY_POLICY.md`  
  Allowlist, Quarantäne/Scan (oder Approval-Fallback), RBAC, Redaction, Logging/Audit.

### 3.5 Partnerprozesse / Trust
- `T3_PARTNER_DATAFLOW.md`  
  Minimaler Datenfluss + Signaturregeln für T3.

### 3.6 Kommunikation / Moderation
- `MODERATOR_POLICY.md`  
  Moderator: strikt Blog/News, keine PII, kein Audit/Export.
- `NEWSLETTER_CONSENT_POLICY.md`  
  Separater Newsletter-Opt-In, Unsubscribe, Audit.

---

## 4) Dateinamen-Konvention
- Standard: GROSSBUCHSTABEN + UNTERSTRICH (z. B. `ROLES_AND_PERMISSIONS.md`).
- Keine neuen Dokumente mit Bindestrich/Case-Mix.

---

## 5) Change Control
- Änderungen an Policies nur via PR/Review-Prozess.
- PR muss relevante Abnahme-Tests in `ACCEPTANCE_TESTS.md` ergänzen/anpassen.
- Reviewer: ADMIN/SUPERADMIN je nach Bereich.

---
