// File: C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\docs\policies\MODERATOR_POLICY.md

# MODERATOR_POLICY – Blog/News-only, Null-PII, Null-Export, Null-Audit

**Stand:** 2026-01-28 (Europe/Berlin)

---

## 1) Zweck
Moderator unterstützt Content (Blog/News). Moderator ist **kein** Support-Agent und **kein** Admin.

---

## 2) Erlaubt (MUST)
- Blog/News:
  - erstellen
  - bearbeiten (optional nur eigene Beiträge; Default: eigene)
  - publish/unpublish je Policy (Default: publish requires admin)
- Medien im Blog: nur freigegebene Assets ohne PII

---

## 3) Verboten (hard)
- Zugriff auf Vehicles/Entries/Documents/Verification
- Zugriff auf Audit
- Export-Funktionen
- Sichtbarkeit von PII (E-Mail, Name, Adresse etc.)
- Rollenvergabe / Staff-Freigaben / Admin Ops

---

## 4) Enforcement (MUST)
- Backend: RBAC denies für alle nicht-Content Endpoints.
- UI: Moderator-Menü zeigt nur Blog/News.

---

## 5) Audit (MUST)
- Moderator-Akkreditierung/Entzug ist auditpflichtig.
- BlogPost create/update/publish actions auditieren (ohne PII).
