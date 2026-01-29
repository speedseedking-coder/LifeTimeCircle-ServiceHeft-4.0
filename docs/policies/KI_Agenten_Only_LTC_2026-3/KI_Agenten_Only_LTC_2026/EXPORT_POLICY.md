# EXPORT POLICY – LifeTimeCircle / Service Heft 4.0

Version: 1.1  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 1) Default: Redacted Export (immer)
- PII-A: entfernen
- PII-B: maskieren/hashten
- Export-Metadaten:
  - generated_at, generated_by_role, scope, redacted=true

---

## 2) Redaction Matrix (Minimum)
### 2.1 Immer entfernen (PII-A)
- Haltername, Adresse, Telefon, Ausweis-/ID-Daten
- unredacted Rohdokumente/Bilder
- Standort-/Bewegungsprofile als Zeitreihe

### 2.2 Immer maskieren/hashten (PII-B)
- E-Mail → Hash (Export), UI ggf. maskiert
- VIN → vin_hash oder letzte 4
- Kennzeichen → plate_hash oder letzte 2
- IP → ip_hash (nie Klartext)

Hashing gemäß `CRYPTO_STANDARDS.md`.

---

## 3) Full Export (Ausnahme, nur SUPERADMIN)
Nur wenn zwingend erforderlich:
- reason_code: EXPORT_FULL_APPROVED_SUPERADMIN
- verschlüsselt (AEAD) gemäß `CRYPTO_STANDARDS.md`
- TTL: 24h
- Download-Limit: 3
- Jeder Download auditiert: export_downloaded

---

## 4) Rollenregeln
- MODERATOR: keine Exporte
- USER: nur eigene Daten, redacted
- VIP/DEALER/VIP_BIZ: scope-basiert, redacted
- ADMIN: operativ, redacted
- SUPERADMIN: Ausnahmeprozess möglich

---
