# docs/01_DECISIONS.md
# LifeTimeCircle – Service Heft 4.0
**Entscheidungen / SoT (Decisions Log)**  
Stand: 2026-02-06

> Ziel: Kurze, nachvollziehbare Entscheidungen (warum / was / Konsequenzen).  
> Regel: Wenn etwas nicht explizit erlaubt ist → **deny-by-default**.

---

## D-001: RBAC serverseitig enforced (deny-by-default + least privilege)
**Status:** beschlossen  
**Warum:** Client kann manipuliert werden; Rechte müssen im Backend sicher sein.  
**Konsequenz:** Alle Router haben Dependencies/Gates; Tests prüfen Guard-Coverage.

---

## D-002: Moderator strikt nur Blog/News
**Status:** beschlossen  
**Warum:** Minimierung von Datenzugriff, keine PII, keine Exports.  
**Konsequenz:** Moderator bekommt überall sonst **403** via Router-Dependency `forbid_moderator`.

---

## D-003: Export redacted (PII minimieren, Dokumente nur approved)
**Status:** beschlossen  
**Warum:** Exports sind riskant (Datenabfluss).  
**Konsequenz:** Redaction-Store filtert Dokument-Refs nur auf `APPROVED`.

---

## D-004: Uploads Quarantäne-by-default
**Status:** beschlossen  
**Warum:** Uploads sind Angriffspfad (Malware, PII, ungewollte Inhalte).  
**Konsequenz:** Neu hochgeladene Dokumente sind `PENDING/QUARANTINED`; Auslieferung/Export nur bei `APPROVED`.

---

## D-005: Admin-Only Quarantäne Review (Approve/Reject/List)
**Status:** beschlossen  
**Warum:** Review ist sicherheitskritisch; least privilege.  
**Konsequenz:** Nur `admin/superadmin` dürfen Quarantäne-Liste sehen und Approve/Reject ausführen.

---

## D-006: Actor required liefert 401 (unauth) statt 403
**Status:** beschlossen  
**Warum:** Semantik sauber: unauth → 401, auth-but-forbidden → 403.  
**Konsequenz:** `require_actor` wirft 401, nicht 403.

---

## D-007: Upload-Scan Hook + Approve nur bei CLEAN
**Status:** beschlossen  
**Warum:** Quarantäne ohne Scan ist zu schwach; Freigabe nur nach Scan.  
**Konsequenz:** `scan_status` Feld + `approve` nur wenn `CLEAN`, sonst 409; Admin-Rescan Endpoint; INFECTED auto-reject.

---

## D-008: Sale/Transfer Status nur für Initiator oder Redeemer (object-level RBAC)
**Status:** beschlossen  
**Warum:** `tid` ist erratbar/teilbar; Status darf nicht für beliebige `vip|dealer` lesbar sein (ID-Leak via `initiator_user_id` / `redeemed_by_user_id`).  
**Konsequenz:** `GET /sale/transfer/status/{tid}` zusätzlich zum Role-Gate (`vip|dealer`) nur wenn Actor **Initiator** oder **Redeemer** ist; sonst **403**. Tests müssen das explizit abdecken.

---

## D-009: Actor Source of Truth (serverseitig, DEV-Headers gated)
**Status:** beschlossen  
**Warum:** Client/Headers sind manipulierbar; Actor/Claims müssen serverseitig konsistent und vertrauenswürdig bestimmt werden.  
**Konsequenz:** Zentraler Actor-Resolver ist **serverseitige SoT**; DEV/Test-Header-Override ist **hart gated** (nur DEV/Test), in Produktion deaktiviert/ignoriert.

---

## D-010: VIP Business Staff-Limit + SUPERADMIN Gate
**Status:** beschlossen  
**Warum:** Staff-Accounts sind ein Rechte-/Angriffsvektor; least privilege und Kosten-/Missbrauchsschutz.  
**Konsequenz:** VIP-Gewerbe ist auf **max. 2 Staff-Accounts** limitiert; Freigabe/Erhöhung/Änderung der Staff-Zuordnung ist **nur `superadmin`** erlaubt. Tests müssen das Limit und das Gate abdecken.