# DATA RETENTION – LifeTimeCircle / Service Heft 4.0

Version: 1.1  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 1) Aufbewahrung (verbindliche Defaults)
### 1.1 App-Logs (nicht Audit)
- Retention: 14 Tage
- Rotation: täglich
- PII: nur maskiert/gehäshte Daten (keine PII-A, keine Secrets)

### 1.2 Audit-Logs
- Retention: 365 Tage
- PII-A: verboten
- Zugriff: role/scope enforced

### 1.3 Verify Artefakte
- TTL: 15 Minuten
- Speicherung: gehashed
- Löschung: sofort nach Erfolg oder TTL-Ablauf

### 1.4 Uploads
- Raw Uploads: niemals öffentlich
- Derivate/Redaction bevorzugt für Anzeige/Sharing

---

## 2) Löschung / Erasure
- Hard delete wo möglich, sonst Pseudonymisierung + Zugriff entziehen
- Audit: data_deleted oder data_anonymized

---

## 3) Backups
- Backup Retention: 30 Tage
- Verschlüsselung: Pflicht (AEAD gemäß `CRYPTO_STANDARDS.md`)
- Restore-Test: monatlich, Ergebnis dokumentieren

---

## 4) Incident Ausnahme
- Nur SUPERADMIN
- reason_code: SUSPICIOUS_ACTIVITY
- max Verlängerung: 30 Tage

---
