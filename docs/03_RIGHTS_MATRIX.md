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
- `moderator`: **strikt nur Blog/News** (kein Zugriff auf Servicebook/Exports/Documents/PII)

---

## 2. Globale Regeln
- **deny-by-default**: jede Route muss explizit gated sein
- **Actor required**: ohne Actor → **401**
- **Moderator hard-block**: überall außer Blog/News → **403**
- **Exports**: nur redacted für Nicht-Admins; Dokument-Refs nur `APPROVED`
- **Uploads**: Quarantine-by-default; `APPROVED` nur nach Scan `CLEAN`

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