# AUTH SECURITY DEFAULTS – LifeTimeCircle / Service Heft 4.0

Version: 1.1  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 1) Verify / Magic-Link Defaults (verbindlich)
- Verify TTL: 15 Minuten
- One-Time Use: nach Erfolg sofort ungültig
- Max. Versuche pro Verify-Code: 5 (danach invalid)
- Resend Cooldown pro E-Mail: 60 Sekunden
- Speicherung: Verify-Token/Code nur gehashed (siehe `CRYPTO_STANDARDS.md`)

---

## 2) Rate-Limits (serverseitig, Pflicht)
### 2.1 Pro IP
- `/auth/request`: 10 / 15 Minuten
- `/auth/verify`:  20 / 15 Minuten

### 2.2 Pro E-Mail
- `/auth/request`: 5 / 15 Minuten
- `/auth/request` pro Tag: 20 / 24h

### 2.3 Temporärer Lockout
- 10 fehlgeschlagene Verifies in 30 Minuten → 30 Minuten Sperre (E-Mail)
- Sperre erzeugt Audit: `rate_limited` oder `suspicious_activity_flagged`

---

## 3) Session-Defaults
- Access Session TTL: 8 Stunden
- Idle Timeout: 30 Minuten
- Re-Auth Pflicht für kritische Aktionen (Export, Rollen/Freigaben, Übergabe-QR)

---

## 4) Logging (Auth)
- Keine Auth/Verify Bodies loggen
- Keine Tokens/Codes/Links loggen
- E-Mail nur maskiert (UI) oder gehashed (Logs)

---

## 5) Anti-Enumeration (Non-Negotiable)
- `/auth/request` Antwort ist immer identisch (Status/Body), unabhängig davon ob E-Mail existiert.
- Beispieltext: “Wenn die E-Mail gültig ist, senden wir einen Code/Link.”
- Keine “user_not_found” Signale in Response/Timing/Headers.

---
