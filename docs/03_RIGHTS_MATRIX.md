# docs/03_RIGHTS_MATRIX.md
# LifeTimeCircle – Service Heft 4.0
**Rights / RBAC Matrix (SoT)**  
Stand: 2026-02-05

> Rollen sind serverseitig enforced. Default: deny-by-default.
> Wenn etwas nicht explizit erlaubt ist → **verboten**.

---

## 1. Rollen
- `superadmin`: Vollzugriff (System, Admin, Support, Debug)
- `admin`: Admin-Funktionen, Quarantäne-Review, Exports, Management
- `dealer`: Business-User (Händler), begrenzte Datenzugriffe, keine Admin/Quarantäne
- `vip`: Premium-Enduser, erweiterte Einsichten (aber kein Admin/Quarantäne)
- `user`: Standard-Enduser
- `moderator`: **strikt nur Blog/News** (kein Zugriff auf Servicebook/Exports/Documents/PII, kein Audit)

---

## 2. Globale Regeln
- **deny-by-default**: jede Route muss explizit gated sein
- **Actor required**: ohne Actor → **401**
- **Moderator hard-block**: überall außer Blog/News → **403**
- **Exports**: nur redacted für Nicht-Admins; Dokument-Refs nur `APPROVED`
- **Uploads**: Quarantine-by-default; `APPROVED` nur nach Scan `CLEAN`
- **Keine Secrets/PII** im Klartext in Logs/Audit/Exports

---

## 2b. Enforcement (Tests)
- `server/tests/test_moderator_block_coverage_runtime.py`:
  - iteriert über **alle registrierten Routes** (Runtime-Scan)
  - Allowlist (ohne 403): `/auth/*`, `/health`, `/public/*`, `/blog/*`, `/news/*`
  - außerhalb der Allowlist muss `moderator` **403** bekommen
  - Blog/News-Test ist bewusst **skipped**, solange `/blog|/news` Routes noch nicht existieren

---

## 3. Dokumente / Uploads (`/documents/*`)

### 3a: Zugriff auf approved Dokumente
| Route | superadmin | admin | dealer | vip | user | moderator |
|------|-----------:|------:|------:|----:|----:|----------:|
| `POST /documents/upload` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ 403 |
| `GET /documents/{id}` | ✅ | ✅ | ✅ (nur wenn APPROVED+scope) | ✅ (nur wenn APPROVED+scope) | ✅ (nur wenn APPROVED+scope) | ❌ 403 |
| `GET /documents/{id}/download` | ✅ | ✅ | ✅ (nur wenn APPROVED+scope) | ✅ (nur wenn APPROVED+scope) | ✅ (nur wenn APPROVED+scope) | ❌ 403 |

### 3b: Quarantäne-Workflow (Admin only)
| Route | superadmin | admin | dealer | vip | user | moderator |
|------|-----------:|------:|------:|----:|----:|----------:|
| `GET /documents/admin/quarantine` | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| `POST /documents/{id}/approve` | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| `POST /documents/{id}/reject` | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| `POST /documents/{id}/scan` | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |

**Approve-Gate:** Approve ist nur erlaubt bei `scan_status=CLEAN`, sonst **409 not_scanned_clean**.

---

## 4. Servicebook (`/servicebook/*`)
| Route (repräsentativ) | superadmin | admin | dealer | vip | user | moderator |
|------|-----------:|------:|------:|----:|----:|----------:|
| `GET /servicebook/{id}/entries` | ✅ | ✅ | ✅ (scoped) | ✅ (scoped) | ✅ (scoped) | ❌ 403 |
| `POST /servicebook/{id}/inspection-events` | ✅ | ✅ | ✅ (scoped) | ✅ (scoped) | ✅ (scoped) | ❌ 403 |
| `POST /servicebook/{id}/cases/{case_id}/remediation` | ✅ | ✅ | ✅ (scoped) | ✅ (scoped) | ✅ (scoped) | ❌ 403 |

---

## 5. Export (`/export/*`)
| Route (repräsentativ) | superadmin | admin | dealer | vip | user | moderator |
|------|-----------:|------:|------:|----:|----:|----------:|
| Grant Full Export Token | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| Redacted Export | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ 403 |

**Dokument-Refs im Export:** nur `APPROVED`.

---

## 6. Verkauf / Übergabe (Sale/Transfer, inkl. interner Verkauf)
> Business-Regel (RBAC): **nur `vip` und `dealer`** dürfen Verkauf/Übergabe-Prozesse auslösen/abwickeln.

| Aktion (repräsentativ) | superadmin | admin | dealer | vip | user | moderator |
|------|-----------:|------:|------:|----:|----:|----------:|
| Verkauf/Übergabe initiieren | ❌ 403 | ❌ 403 | ✅ | ✅ | ❌ 403 | ❌ 403 |
| Verkauf/Übergabe annehmen/bestätigen | ❌ 403 | ❌ 403 | ✅ | ✅ | ❌ 403 | ❌ 403 |
| Interner Verkauf (Händler-intern) | ❌ 403 | ❌ 403 | ✅ | ✅ | ❌ 403 | ❌ 403 |

### 6b. Status lesen ist object-level gated (ID-Leak verhindern)
`GET /sale/transfer/status/{tid}`

- Role-Gate: **nur `vip|dealer`** (alle anderen **403**)
- Zusätzlich: **nur Initiator oder Redeemer** darf den Status lesen (sonst **403**), weil sonst `tid`-Enumeration zu ID-Leaks führen kann (`initiator_user_id`, `redeemed_by_user_id`).

---

## 7. VIP-Gewerbe (Staff-Limit & Freigabe)
- VIP-Gewerbe darf **max. 2 Staff-Accounts** haben.
- **Freigabe/Erhöhung/Änderung** der Staff-Zuordnung ist **nur `superadmin`** erlaubt.