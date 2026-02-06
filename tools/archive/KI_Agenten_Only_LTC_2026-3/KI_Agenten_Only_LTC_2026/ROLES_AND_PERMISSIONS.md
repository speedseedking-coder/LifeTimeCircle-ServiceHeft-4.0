# ROLES & PERMISSIONS – LifeTimeCircle / Service Heft 4.0

Version: 1.3  
Stand: 2026-01-27

Ziel: klares, auditierbares Berechtigungsmodell (UI + API identisch).  
Prinzip: Least Privilege + Server is source of truth.

---

## 1) Rollenübersicht
- PUBLIC (Gast)
- USER (Standard)
- VIP (Privat)
- DEALER (Händler/Gewerblich)
- VIP_BIZ_ADMIN (VIP-Gewerbe Admin)
- VIP_BIZ_STAFF (VIP-Gewerbe Mitarbeiter; max 2, freigabepflichtig)
- MODERATOR (Blog/News)
- ADMIN
- SUPERADMIN (Oberadmin)

---

## 2) Datenklassen
- PII-A (hoch): Halterdaten/Identität/Bewegungsprofile
- PII-B (mittel): indirekte Identifikatoren (VIN/Kennzeichen), maskierte E-Mail, Hashes
- NON-PII: ohne Personenbezug
- SECRETS (S0): Verify/Session/API-Keys (niemals loggen/exportieren)

Verbindlich:
- `PII_POLICY.md`
- `DATA_CLASSIFICATION.md`
- `CRYPTO_STANDARDS.md`

---

## 3) Permission Matrix
Legende: ✅ erlaubt | ❌ nicht erlaubt | ⚠️ eingeschränkt (Scope+Redaction)

| Fähigkeit / Bereich | PUBLIC | USER | VIP | DEALER | VIP_BIZ_ADMIN | VIP_BIZ_STAFF | MODERATOR | ADMIN | SUPERADMIN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Landing/Info | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Public-QR Trust-Ampel | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Account erstellen (mit AGB/DS) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Login + Verify | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Service Heft Einträge ansehen (Scope) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ | ⚠️ |
| Service Heft Einträge ändern (Scope) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ | ⚠️ |
| Bilddoku ansehen (VIP-Gate) | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ | ⚠️ |
| Uploads (Bilder/Dokumente) | ❌ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ | ⚠️ |
| Fahrzeugverkauf / interner Verkauf | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Übergabe-QR / Übergabe-Code | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| VIP_BIZ Staff Slot anfragen/anlegen | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ✅ |
| VIP_BIZ Staff Slot freigeben | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| News/Blog lesen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| News/Blog schreiben/veröffentlichen | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ⚠️ | ✅ |
| Rollen zuweisen | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| Policies/Trust-Regeln ändern | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Audit-Log einsehen | ❌ | ❌ | ❌ | ❌ | ⚠️ | ⚠️ | ❌ | ✅ | ✅ |
| Exporte erzeugen | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ |

---

## 4) Notes
### 4.1 “⚠️ eingeschränkt”
- nur Org/Ownership Scope
- Feld-Redaction (keine PII-A; PII-B maskiert/hashed)
- reason_code ist ENUM (kein Freitext)

Verbindlich: `AUDIT_SCOPE_AND_ENUMS.md`

### 4.2 Uploads
Uploads sind nur erlaubt gemäß:
- `UPLOAD_SECURITY_POLICY.md`

---

## 5) Durchsetzung (Pflicht)
- UI-Gating ist nie ausreichend; API prüft Rolle + Ownership/Scope.
- Fehler: 401/403/404 ohne Leaks.
- Sensitive Events auditiert (Auth, Rollen, Freigaben, Verkauf/Übergabe, Export, Upload).

Verbindlich: `ACCEPTANCE_TESTS.md`

---
