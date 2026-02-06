# T3 PARTNER DATAFLOW – LifeTimeCircle / Service Heft 4.0

Version: 1.0  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 1) Prinzip
- Partner erhält nur minimal notwendige Daten
- Standard: keine PII-A
- Jede Partner-Interaktion erzeugt Audit-Event

---

## 2) Erlaubte Daten an Partner (Default)
- vehicle_internal_id oder partner_token
- event_type (z. B. ServiceEntryVerification)
- erforderliche Nachweise in redacted Form (wenn möglich)
- optional: VIN nur gehashed oder letzte 4 Zeichen

Nicht erlaubt:
- Halterdaten
- vollständige E-Mail
- Standort-/Bewegungsprofile
- unredacted Dokumente

---

## 3) Partner Signatur / Proof
- Partner bestätigt Ereignis über:
  - signiertes Payload (partner_key) ODER
  - verifizierten Partner-Account + serverseitige Signierung
- Speicherung:
  - t3_partner_id, t3_signature, verified_at, evidence_ref
- Audit:
  - t3_verification_requested, t3_verification_completed, t3_verification_failed

---

## 4) Zugriff auf T3 Daten
- Public Trustscore darf T3 Level zeigen, aber keine Partner-Details
- Owner/VIP/DEALER sehen Details nach Scope
- MODERATOR: keine T3 Detaildaten

---
