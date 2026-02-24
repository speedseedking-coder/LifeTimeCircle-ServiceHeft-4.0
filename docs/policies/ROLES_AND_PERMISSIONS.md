// File: ./docs/policies/ROLES_AND_PERMISSIONS.md

# ROLES_AND_PERMISSIONS – RBAC & Scopes (serverseitig, verbindlich)

**Stand:** 2026-01-28 (Europe/Berlin)  
**Prinzip:** deny-by-default, least privilege, serverseitig enforced

---

## 1) Rollen (kanonisch)
- **public**: nur Public-QR read-only + Blog lesen
- **user**: eigenes Serviceheft (own)
- **vip**: wie user + VIP-Funktionen (z. B. Übergabe/Verkauf)
- **dealer**: wie vip + Org-Features (org scope)
- **moderator**: nur Blog/News (write), sonst read-only public-level
- **admin**: SUPERADMIN (voller Zugriff + Governance)

---

## 2) Scopes
- **own**: User-eigene Ressourcen
- **org**: Ressourcen der Organisation (dealer/vip_business)
- **shared**: explizit geteilte Ressourcen (opt-in, revokebar)
- **public**: Public-QR, Blog

**Regel:** Zugriff = Rolle erlaubt Aktion **und** Scope passt **und** Objektzustand erlaubt (z. B. Dokument in Quarantäne).

---

## 3) Kernrechte (Auszug, implementierbar)
### 3.1 Vehicles / Entries
- public: kein Zugriff
- user: CRUD own
- vip: CRUD own (+ Übergabe/Verkauf)
- dealer: CRUD own + CRUD org (via OrgMembership approved)
- moderator: kein Zugriff
- admin: CRUD all

### 3.2 Documents (Uploads)
- public: keine Dokumentansicht, keine Metadaten, keine Inhalte
- user: own; Inhalte abhängig von Visibility (private/shared)
- vip/dealer: own/org; erweiterte Ansicht möglich (VIP-only)
- moderator: kein Zugriff
- admin: all

**Quarantäne:** Inhalte sind für nicht-admin **nie** sichtbar, bis freigegeben.

### 3.3 Verification (T1/T2/T3)
- user/vip: T1 setzen auf own
- dealer: T1/T2 setzen auf org; T3 nur via akkreditierter Partner-Flow
- admin: T1/T2/T3 setzen global + Partner akkreditieren
- public/moderator: kein Zugriff

### 3.4 PublicShare / Public-QR
- Aktivieren/Deaktivieren/Rotieren:
  - vip/dealer/admin/superadmin: erlaubt (nur own/org)
  - user: optional (Default: verboten, außer Decision erlaubt)
  - moderator/public: verboten
- Public-View:
  - alle (inkl. public): read-only

**Public Output Rules:** siehe TRUSTSCORE_SPEC.md

### 3.5 Übergabe/Verkauf (QR)
- vip/dealer/admin/superadmin: erlaubte Nutzung (own/org), Auditpflicht
- user/public/moderator: verboten

### 3.6 Blog/News
- Lesen: alle
- Schreiben: moderator/admin
- Admin: darf alles moderieren, publish/unpublish, löschen (auditpflichtig)

### 3.7 Export
- Redacted Export: user/vip/dealer für own/org möglich (Policy-gated), admin global
- Full Export: nur admin (siehe EXPORT_POLICY.md)

---

## 4) Moderator-Sperrregeln (hard)
- Keine PII Sichtbarkeit
- Kein Export
- Kein Audit
- Kein Zugriff auf Vehicles/Entries/Documents/Verification

Details: MODERATOR_POLICY.md

---

## 5) Implementation Contract (Backend)
Jede Route MUST:
1) Auth prüfen (oder public)
2) Rolle prüfen
3) Scope prüfen
4) Objektzustand prüfen (quarantine, revoked, disabled)
5) AuditEvent schreiben bei sicherheitsrelevanten Aktionen

