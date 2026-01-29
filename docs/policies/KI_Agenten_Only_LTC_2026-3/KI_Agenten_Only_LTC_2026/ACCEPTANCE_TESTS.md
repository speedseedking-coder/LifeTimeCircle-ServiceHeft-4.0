# ACCEPTANCE TESTS – LifeTimeCircle / Service Heft 4.0

Version: 1.2  
Stand: 2026-01-27  
Owner: Oberadmin (Produkt/Freigabe)

---

## 0) Zweck
Definition of Done. Ein Feature ist erst fertig, wenn relevante Tests (UI + API) erfüllt sind.

---

## 1) Branding / Legacy
### AT-BR-01
Kein neuer Legacy-Name in Code/Pfaden/UI/Docs. Branding exakt: “LifeTimeCircle”, “Service Heft 4.0”.

---

## 2) Auth: Verify + AGB/Datenschutz + Anti-Enumeration
### AT-AUTH-01 Verify One-Time + TTL
Code/Link nach Nutzung ungültig; nach TTL ungültig.

### AT-AUTH-02 Rate-Limits
IP + E-Mail Limits greifen; server antwortet deterministisch; Audit `rate_limited`.

### AT-AUTH-03 AGB/DS Pflicht
Aktivierung ohne Zustimmung serverseitig blockiert; Zustimmung gespeichert (Version + Timestamp).

### AT-AUTH-04 Keine Secrets in Logs
Logs enthalten niemals Verify-Code/Link, Tokens, Sessions/JWT, Reset-Links, API-Keys.

### AT-AUTH-05 Anti-Enumeration
`/auth/request` Response ist identisch (Status/Body) unabhängig davon, ob E-Mail existiert.

---

## 3) Rollen / VIP-Gating / Moderator
### AT-ROLE-01 Verkauf/Übergabe nur VIP/DEALER
USER sieht nicht und kann nicht ausführen (UI+API). VIP/DEALER kann (Scope/Ownership).

### AT-ROLE-02 VIP_BIZ Staff Slots
Max 2 Staff Slots; Freigabe nur SUPERADMIN; Audit-Events entstehen.

### AT-ROLE-03 Moderator ohne PII
MODERATOR: Blog/News ok; keine Halterdaten/PII-A; keine Exporte; kein Audit.

---

## 4) Public-QR Trustscore
### AT-TRUST-01 Disclaimer Pflicht
Klartext: bewertet nur Nachweisqualität, nicht technischen Zustand.

### AT-TRUST-02 Unfall-Grün-Bremse
Bei accident=true ist Grün nur bei closed=true + evidence>=min, sonst max Gelb.

### AT-TRUST-03 Unknown nie Grün
accident=unknown → max Gelb.

### AT-TRUST-04 Keine Zustandsbewertung
Kein OBD/Defekt/TÜV/Diagnose-Wording in Public-QR.

### AT-TRUST-05 Kein Metrics-Leak
Public Response enthält niemals Rohmetriken/Counts/Percentages/Zeiträume (`metrics` existiert nicht public).

---

## 5) Crypto / Hashing
### AT-CRYPTO-01 Keine unsalted SHA für PII
E-Mail/IP/VIN/Kennzeichen Hashes sind HMAC-basiert (Secret-Key), nicht plain SHA256.

### AT-CRYPTO-02 Token Speicherung gehashed
Verify/Magic-Link Tokens liegen serverseitig nur gehashed, nie im Klartext.

---

## 6) Logging / Audit / Export
### AT-LOG-01 Allowlist Logging
Keine Body/Header Dumps; nur erlaubte Felder.

### AT-AUDIT-01 Pflicht-Events existieren
Auth/Role/Freigaben/Verkauf-Übergabe/Export/PermissionDenied erzeugen Audit.

### AT-EXPORT-01 Standardexport redacted
Keine PII-A; PII-B maskiert/hashed; `redacted=true`.

### AT-EXPORT-02 Full Export nur Ausnahme
Nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung.

---

## 7) Uploads
### AT-UPLOAD-01 Allowlist & Limits
Nur erlaubte Dateitypen; Größenlimits greifen.

### AT-UPLOAD-02 Quarantäne Pflicht
Jeder Upload startet in QUARANTINED und wird nicht sofort ausgeliefert.

### AT-UPLOAD-03 Scan oder Approval-Fallback
- Wenn Scanner aktiv: Statuswechsel erst nach Scan (AVAILABLE/REJECTED).
- Wenn Scanner nicht aktiv: Statuswechsel erst nach Admin-Freigabe.

### AT-UPLOAD-04 RBAC
Nur Owner/Scope darf zugreifen; MODERATOR darf keine Uploads einsehen.

---
