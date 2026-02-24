// File: ./docs/policies/PII_POLICY.md

# PII_POLICY – Personenbezogene Daten (Erhebung, Verarbeitung, Schutz)

**Stand:** 2026-01-28 (Europe/Berlin)  
**Prinzip:** Datenminimierung, Zweckbindung, least privilege, redaction by default

---

## 1) Was ist PII im Projekt (Definition)
PII umfasst insbesondere:
- E-Mail-Adresse
- Name, Adresse, Telefonnummer
- Zahlungsdaten (falls später)
- Geräte-/Trackingdaten, wenn identifizierend
- Kombinationen, die eine Person identifizierbar machen

**Nicht-PII (typisch):**
- rein technische IDs ohne Personenbezug (random IDs)
- HMAC-Pseudonyme ohne Rückschluss ohne Secret

---

## 2) Verarbeitung (MUST)
- PII wird nur verarbeitet, wenn für Auth, Consent, Support oder legitime Funktionen nötig.
- Speicherung möglichst minimal:
  - Auth: E-Mail notwendig (Account)
  - Logs/Audit: **keine Klartext-PII** (nur HMAC/IDs)

---

## 3) Logging & Audit (MUST)
- Keine Klartext-PII in Logs/Audit.
- E-Mail im Audit nur als `email_hmac`.
- Support-Debug: nur mit expliziten Debug-Flags, ebenfalls ohne Klartext-PII.

---

## 4) Zugriffskontrolle (MUST)
- Moderator: keine PII-Sichtbarkeit.
- User/VIP/Dealer: sehen nur eigene/Org-PII soweit nötig (Standard: E-Mail Konto).
- Admin: PII-Sichtbarkeit nur wenn erforderlich; UI maskiert by default; Reveal nur mit Step-up + Audit.

---

## 5) Pseudonymisierung (MUST)
- PII-Pseudonyme via HMAC-SHA256 (siehe CRYPTO_STANDARDS.md).
- Kein unsalted SHA.
- HMAC keys in Secret Manager/KMS; Rotation nach Standard.

---

## 6) Exports (MUST)
- Standardexport = redacted (keine PII).
- Full Export nur admin + Audit + TTL/Limit + Verschlüsselung.
Siehe EXPORT_POLICY.md

---

## 7) Datenweitergabe (MUST)
- Keine PII an T3-Partner, außer explizit notwendig und vertraglich geregelt (Standard: nein).
Siehe T3_PARTNER_DATAFLOW.md

---

## 8) Testdaten (MUST)
- In Staging/Dev: keine echten PII.
- Seed-Daten synthetisch.
