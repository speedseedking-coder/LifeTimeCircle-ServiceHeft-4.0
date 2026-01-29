# AGENT BRIEF – LifeTimeCircle / Service Heft 4.0

Version: 1.3  
Stand: 2026-01-27  
Owner: Oberadmin (Produkt/Freigabe)  
Kontakt (projektbezogen): lifetimecircle@online.de

---

## 1) Zweck dieses Dokuments
Verbindliche Arbeitsgrundlage für KI-Agenten und Entwickler. Definiert:
- Produkt, Ziele und Scope
- Non-Negotiables
- Quality Gates (DoD)
- Lieferformate (copy-paste sicher, vollständig)

Siehe auch: `POLICY_INDEX.md`

---

## 2) Produkt & Branding (verbindlich)
- Brand/Hauptbegriff: **LifeTimeCircle** (exakt so schreiben)
- Produkt/Modul: **Service Heft 4.0**
- Legacy-/Altnamen sind obsolet (keine neuen Pfade/Variablen/Seiten unter alten Namen)

---

## 3) Leitprinzip (Non-Negotiable)
Kein Demo-Charakter. Produktionsreif:
- robuste Fehlerbehandlung
- Audit/Logging nachvollziehbar
- Datenschutz/PII minimiert
- testbar (Akzeptanzkriterien erfüllt)

---

## 4) Auth & Zutritt (Non-Negotiables)

### 4.1 E-Mail Login + Verifizierung
- E-Mail Login mit zwingender Verifizierung (Code/Link).
- Verify ist:
  - One-Time
  - TTL-begrenzt
  - rate-limited
  - anti-enumeration (Client darf nicht erkennen, ob E-Mail existiert)

Verbindlich: `AUTH_SECURITY_DEFAULTS.md`

### 4.2 Zustimmung AGB & Datenschutz
- Account-Aktivierung nur mit bestätigten AGB + Datenschutz (serverseitig: Version + Timestamp).

### 4.3 Crypto/Secrets
- Keine Secrets im Repo oder im Client persistent speichern.
- Keine unsalted SHA256 Hashes für PII.
- Pseudonymisierung in Logs/Audit/Exports via HMAC (Secret-Key).

Verbindlich: `CRYPTO_STANDARDS.md` und `PII_POLICY.md`

---

## 5) Rollen & Zugriff (Non-Negotiables)

### 5.1 VIP/Händler Exklusiv-Funktionen
Nur für **VIP** und **DEALER (gewerblich)**:
- Fahrzeugverkauf / interner Verkauf
- Übergabe-QR / Übergabe-Code

### 5.2 VIP-Gewerbe Mitarbeiterplätze
- Max. 2 Mitarbeiterplätze (VIP_BIZ_STAFF).
- Freigabe nur durch **SUPERADMIN/Oberadmin**.

### 5.3 Moderatorenrechte
- MODERATOR: nur News/Blog.
- Keine Halterdaten/PII-A, keine Exporte, kein Audit.

Verbindlich: `ROLES_AND_PERMISSIONS.md` + `MODERATOR_POLICY.md`

---

## 6) Public-QR Mini-Check (Trust-Ampel) – Non-Negotiables
- 4 Stufen: Rot/Orange/Gelb/Grün
- Bewertet ausschließlich Dokumentations-/Nachweisqualität (nicht Zustand)
- Public Contract: keine Rohmetriken/Counts/Percentages im Public-Response
- Unfall:
  - Grün nur bei Abschluss + Belegen
  - `unknown` → niemals Grün

Verbindlich: `TRUSTSCORE_SPEC.md`

---

## 7) Uploads (Bilder/Dokumente)
- Uploads sind niemals öffentlich per Default.
- Allowlist Dateitypen, Größenlimits, Quarantäne/Scan bzw. Approval-Fallback.
- MODERATOR: keine Upload-Einsicht.

Verbindlich: `UPLOAD_SECURITY_POLICY.md`

---

## 8) Qualitätsstandard (Quality Gates / DoD)

### 8.1 Funktional
- Akzeptanzkriterien/Tests erfüllt: `ACCEPTANCE_TESTS.md` (muss existieren)
- Keine Regression
- Buttons/Navigation korrekt, leere Zustände behandelt

### 8.2 Sicherheit & Datenschutz
- UI + API enforce (nicht nur UI)
- keine Secrets/PII in Logs
- Inputs validiert
- Auth/Verify rate-limited + anti-enumeration
- Export redacted by default

### 8.3 Lieferformat
- Änderungen in kleinen, fortlaufenden Code-Blöcken (copy-paste sicher)
- Neue Datei: immer vollständig
- Änderungen: Dateiname + kompletter Ersatzinhalt, wenn angefordert

---

## 9) Explizite Don’ts
- Keine Zustandsbewertung im Public-QR (OBD/Defekt/TÜV/Diagnose verboten).
- Keine Hidden Admin Backdoors ohne Rollenmodell & Audit.
- Keine unsalted SHA Hashes für PII.
- Keine “E-Mail existiert/nicht existiert” Signale in Auth-Responses.

---
