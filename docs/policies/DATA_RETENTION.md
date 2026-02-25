// File: ./docs/policies/DATA_RETENTION.md

# DATA_RETENTION – Aufbewahrung, Löschung, Legal Hold

**Stand:** 2026-01-28 (Europe/Berlin)  
**Prinzip:** so kurz wie möglich, so lang wie nötig (Zweck + Recht)

---

## 1) Grundregeln
- Retention ist pro Datentyp definiert.
- Löschung = hard delete oder irreversible Anonymisierung (abhängig von Datentyp).
- Legal Hold kann Löschungen blockieren (admin-only, auditpflichtig).

---

## 2) Retention Defaults (SHOULD – produktiver Start)
### Auth / Security
- EmailVerificationChallenge: 30 Tage (ohne Secrets, nur Hashes/Metadaten)
- Sessions: 30 Tage (revoked sessions max 30 Tage zur Abuse-Analyse)
- Rate-limit counters: 7 Tage (aggregiert, ohne PII)

### Consent
- ConsentRecord: solange Account aktiv + 10 Jahre Nachlauf (Rechtsnachweis)

### Domain Daten
- Vehicle/Entry/EntryVersion: solange Account/Org aktiv oder bis User/Owner löscht (mit Warnung: Historie geht verloren)
- Documents:
  - Quarantäne-rejected: 30 Tage, dann hard delete
  - Freigegeben: solange Entry/Vehicle existiert oder Owner löscht

### Public / Transfer
- PublicShare Token history (hash only): 180 Tage
- HandoverTransfer: 2 Jahre (audit/reklamation)

### Audit
- AuditEvents: 7 Jahre (Sicherheits-/Compliance-Nachweis)

### Blog/Newsletter
- BlogPosts: dauerhaft, bis Admin löscht
- NewsletterSubscription: solange Subscription + 2 Jahre Nachlauf

---

## 3) Löschkonzept (MUST)
- User-Initiierte Löschung:
  - Account löschen: PII entfernen/anonymisieren, Domain Inhalte optional (Policy-Entscheidung), Audit bleibt (redacted).
- Dokument-Löschung:
  - Lösche Storage + DB-Metadaten; Audit bleibt.

---

## 4) Legal Hold (MUST)
- Nur admin darf Legal Hold setzen/entfernen.
- Jede Änderung auditpflichtig.
- Legal Hold blockiert:
  - Audit purge
  - Export purge
  - ggf. Domain Delete, falls Streitfall markiert

---

## 5) Backups (SHOULD)
- Backups verschlüsselt.
- Backup Retention getrennt dokumentieren; Restore darf Löschungen nicht dauerhaft reaktivieren (tombstones empfohlen).
