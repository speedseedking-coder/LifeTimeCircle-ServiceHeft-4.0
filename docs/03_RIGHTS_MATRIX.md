# LifeTimeCircle – Service Heft 4.0
**Rechte-Matrix (RBAC) – Entwurf (arbeitsfähig)**  
Stand: 2026-01-29

Legende:
- ✅ erlaubt
- 🔒 nur eingeschränkt / nur eigener Scope / nur berechtigt (grant)
- ❌ nicht erlaubt

## Rollen
- public
- user
- vip
- dealer
- moderator
- admin (SUPERADMIN-Claim für Hochrisiko)

### 1) Public-QR Mini-Check
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| QR-Link öffnen / Trust-Ampel sehen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Indicators (keine Halterdaten, keine Metriken) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 2) Service Heft – Fahrzeuge/Einträge
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Fahrzeug anlegen | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Eigenes Fahrzeug lesen | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Fremde Fahrzeuge lesen (voll) | ❌ | ❌ | 🔒 | 🔒 | ❌ | ✅ |
| Einträge erstellen/bearbeiten (own) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |

### 3) Verkauf/Übergabe
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Übergabe-QR erzeugen | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Interner Verkauf | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |

### 4) Blog/News
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Lesen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Schreiben | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

### 5) Exports
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Export redacted (Standard) | ❌ | ✅ (own) | ✅ (own/grant) | ✅ (own/grant) | ❌ | ✅ |
| Export full (nur SUPERADMIN) | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 (SUPERADMIN) |
