C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs\\03\_RIGHTS\_MATRIX.md

\# LifeTimeCircle – Service Heft 4.0 · Rights Matrix (implementierbar, Kurz)



Version: 2026-03 | Last-Update: YYYY-MM-DD



\*\*Kanonische Rollen:\*\* public, user, vip, dealer, moderator, admin  

\*\*Hinweis:\*\* admin = SUPERADMIN (Governance/Approval/Full Export/Audit).  

\*\*Regel:\*\* RBAC serverseitig enforced (deny-by-default) + Scope (own/org/shared/public) + Objektzustand (z.B. Quarantäne).



Legende: ✅ erlaubt · ❌ verboten · 🔒 nur mit Scope/Policy/Step-up



| Fähigkeit | public | user | vip | dealer | moderator | admin |

|---|---:|---:|---:|---:|---:|---:|

| Public-QR Trustscore ansehen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

| Blog/News lesen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

| Blog/News schreiben | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

| Vehicles (eigene) lesen | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |

| Vehicles (org) lesen | ❌ | ❌ | ❌ | 🔒 (OrgMembership approved) | ❌ | ✅ |

| ServiceHeft Entries (eigene) CRUD | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |

| ServiceHeft Entries (org) CRUD | ❌ | ❌ | ❌ | 🔒 (OrgMembership approved) | ❌ | ✅ |

| Evidence/Nachweise Upload (eigene) | ❌ | ✅ 🔒 (Upload Policy) | ✅ 🔒 | ✅ 🔒 | ❌ | ✅ |

| Evidence Inhalte abrufen bei Quarantäne | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Freigabe/Audit) |

| Verification setzen (T1) | ❌ | ✅ (own) | ✅ (own) | ✅ (own/org) | ❌ | ✅ |

| Verification setzen (T2) | ❌ | ❌ | ❌ | ✅ (org) 🔒 | ❌ | ✅ |

| Verification setzen (T3) | ❌ | ❌ | ❌ | ❌ (nur Partnerflow) | ❌ | ✅ |

| Public-QR aktivieren/rotieren (own/org) | ❌ | ❌ (Default) | ✅ | ✅ | ❌ | ✅ |

| Übergabe/Verkauf-QR starten (own/org) | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |

| Export (redacted) | ❌ | ✅ (own) 🔒 | ✅ (own) 🔒 | ✅ (org) 🔒 | ❌ | ✅ |

| Export (full) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 🔒 (Step-up + Audit + TTL + Encryption) |

| AuditLog lesen | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 🔒 |

| VIP-Gewerbe Staff verwalten (max 2) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 🔒 (Approval + Audit) |



\*\*Fixe Hard-Sperre:\*\* moderator hat niemals Zugriff auf Vehicles/Entries/Documents/Verification/Export/Audit. (Siehe `docs/policies/MODERATOR\_POLICY.md`)



