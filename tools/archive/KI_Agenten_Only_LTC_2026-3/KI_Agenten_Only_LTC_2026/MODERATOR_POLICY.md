# MODERATOR POLICY – LifeTimeCircle / Service Heft 4.0

Version: 1.0  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 1) Grundregel (Non-Negotiable)
MODERATOR erhält niemals PII-A und niemals Auth-Daten/Secrets.

---

## 2) Erlaubt
- News/Blog erstellen, bearbeiten, veröffentlichen
- Moderation von Blog-Kommentaren (falls vorhanden)
- Einsicht in aggregierte Kennzahlen ohne Personen-/Halterbezug (optional)

---

## 3) Verboten
- Halterdaten (PII-A), Adressen, Telefon, Ausweise
- vollständige E-Mails anderer Nutzer
- Zugriff auf Fahrzeug-Owner-Beziehungen
- Exporte/Reports mit Nutzerbezug
- Zugriff auf Audit-Log (optional: nur Blog-Events ohne Identifiers)

---

## 4) Umsetzung (Pflicht)
- Backend: harte RBAC/Scope Checks (kein UI-only Gating)
- Logs: kein PII, kein Freitext mit PII, Allowlist Logging
- Fehlercodes: 403/404 ohne Leaks

---
