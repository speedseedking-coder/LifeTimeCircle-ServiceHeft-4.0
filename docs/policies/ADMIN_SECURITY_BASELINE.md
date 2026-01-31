# ADMIN SECURITY BASELINE – LifeTimeCircle / Service Heft 4.0

Version: 1.0  
Stand: 2026-01-27  
Owner: SUPERADMIN (Oberadmin)  
Kontakt: lifetimecircle@online.de

---

## 0) Zweck
Mindestanforderungen für ADMIN/SUPERADMIN-Zugänge (Panel, APIs, kritische Aktionen).  
Ziel: Produktionsreife, Missbrauchsschutz, Nachvollziehbarkeit (Audit).

---

## 1) Pflicht: 2FA / Strong Authentication
- ADMIN und SUPERADMIN: 2FA mandatory
- Zulässige 2FA-Methoden:
  - TOTP (Authenticator-App) bevorzugt
  - Backup-Codes (Einmalnutzung) als Fallback
- Kein dauerhaftes E-Mail-only für Admin-Panel (außer Break-glass)

---

## 2) Re-Auth (Step-Up) für kritische Aktionen
Re-Auth Pflicht bei:
- Rollen vergeben/entziehen
- VIP_BIZ Staff Slots freigeben/ablehnen
- Export generieren / Full Export genehmigen
- Übergabe-QR erstellen/widerrufen: **nur VIP/DEALER** (kein Admin-Write)
- Policy/Incident Overrides

Re-Auth Fenster: 10 Minuten oder bis Logout (was zuerst eintritt)

---

## 3) Admin Session Policy
- Max Session: 4 Stunden
- Idle Timeout: 15 Minuten
- Secure Cookies (HttpOnly, Secure, SameSite=strict wo möglich)
- Session rotation nach Login/Re-Auth
- CSRF Schutz für Cookie-basierte Admin-Aktionen

---

## 4) Break-glass (Notfallzugriff)
- Break-glass Account standardmäßig deaktiviert
- Secrets offline gespeichert, rotierend (max 90 Tage oder nach Nutzung)
- Nach Nutzung: Deaktivierung + Security Review + ggf. Admin-Credential-Rotation
- Audit Pflicht:
  - `break_glass_used`
  - `admin_security_review_required`

---

## 5) Monitoring (Minimal)
Alarm bei:
- vielen `permission_denied`
- wiederholten `rate_limited` / Lockouts
- ungewöhnlicher Exportaktivität
- Break-glass Nutzung

---

## 6) Acceptance Tests (DoD)
- ADMIN/SUPERADMIN Login ohne 2FA nicht möglich
- Kritische Aktionen triggern Re-Auth + Audit
- Idle Timeout/Max Session greifen
- Break-glass erzeugt Audit + Review Flag

---
