# LifeTimeCircle – Service Heft 4.0
**Rechte-Matrix (RBAC) – implementierbar (SoT)**  
Stand: 2026-02-04

> Zweck: Diese Matrix ist die **serverseitig** umzusetzende Rechtebasis (deny-by-default + least privilege).
> Grundregel: Wenn etwas hier nicht explizit erlaubt ist → **verweigern**.

Legende:
- ✅ erlaubt
- 🔒 nur eingeschränkt / nur eigener Scope / nur wenn berechtigt
- ❌ nicht erlaubt

## Rollen
- public
- user
- vip
- dealer (gewerblich)
- moderator
- admin
- superadmin

## Grundregeln (FIX)
- **Scope**: `user/vip/dealer` arbeiten grundsätzlich im **eigenen** Fahrzeug-/Account-Scope; „fremd“ nur wenn **explizit berechtigt**.
- **moderator**: strikt **nur Blog/News**; keine Vehicles/Entries/Documents/Verification; **kein Export**, **kein Audit-Read**, **keine PII**.
- **superadmin**: High-Risk-Gates (z.B. Full-Exports, VIP-Gewerbe-Staff-Freigaben). Provisioning **out-of-band** (nicht über normale Admin-Rollen-Setter).

## Funktionsbereiche

### 1) Public-QR Mini-Check (anonyme Ansicht)
| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| QR-Link öffnen / Trust-Ampel sehen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Details zur Trust-Berechnung (Indicators, **keine Halterdaten**) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Technische Zustandsbewertung | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 2) Service Heft – Fahrzeug & Einträge
| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fahrzeug anlegen | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Eigenes Fahrzeugprofil ansehen | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Fremde Fahrzeuge ansehen (voll) | ❌ | ❌ | 🔒 (wenn berechtigt) | 🔒 (wenn berechtigt) | ❌ | ✅ | ✅ |
| Einträge erstellen/bearbeiten (eigene Fahrzeuge) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Einträge löschen | ❌ | 🔒 (nur eigener, optional soft-delete) | ✅ | ✅ | ❌ | ✅ | ✅ |
| Dokumente hochladen (Rechnung/Prüfbericht etc.) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

### 3) Bilder/Dokumente – Sichtbarkeit (Tiefe)
> FIX: **Quarantine-by-default**. Dokument-Inhalte sind für `user/vip/dealer` erst bei Status **APPROVED** abrufbar.
> Admin/Superadmin dürfen Inhalte in Quarantäne **nur zum Review** sehen (siehe 3b).

| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dokument-Metadaten (Titel/Datum/Typ) sehen (eigener Scope) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Dokument-Inhalt ansehen/downloaden (**nur APPROVED**, eigener Scope) | ❌ | 🔒 | ✅ | ✅ | ❌ | ✅ | ✅ |
| Bildansicht „VIP only“ (**nur APPROVED**) | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |

### 3b) Dokumente – Quarantäne Workflow (P0 Uploads)
| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Quarantäne-Liste sehen (`PENDING/QUARANTINED`) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Dokument in Quarantäne inhaltlich prüfen (Review-Download/Preview) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Dokument freigeben (`APPROVE`) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Dokument ablehnen (`REJECT`) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Öffentlicher Zugriff auf Uploads (StaticFiles o.ä.) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 4) Verkauf/Übergabe-QR & interner Verkauf (Business-Gating)
| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Übergabe-QR erzeugen | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Interner Verkauf starten/abwickeln | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Audit/Protokoll einsehen | ❌ | ❌ | 🔒 (eigene Vorgänge) | 🔒 (eigene Vorgänge) | ❌ | ✅ | ✅ |

### 5) Blogbase / News
| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| News lesen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| News erstellen/bearbeiten | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| News löschen | ❌ | ❌ | ❌ | ❌ | 🔒 (nur eigene Posts, optional) | ✅ | ✅ |

### 6) Newsletter
| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Opt-in / Opt-out (Abo verwalten) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Versand auslösen | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

### 7) Admin / Governance
| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rollen vergeben / User sperren (ohne SUPERADMIN-Setzen) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Moderatoren akkreditieren | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| VIP-Gewerbe: 2 Mitarbeiterplätze freigeben | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Halterdaten einsehen | ❌ | ❌ | ❌ | 🔒 (wenn berechtigt & notwendig) | ❌ | ✅ | ✅ |
| Audit lesen (ohne PII/Secrets) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| SUPERADMIN-Provisioning (Bootstrap/out-of-band) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### 8) Exports (Security/Privacy)
| Funktion | public | user | vip | dealer | moderator | admin | superadmin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Redacted Export (Default) | ❌ | 🔒 (eigener Scope) | 🔒 (eigener Scope) | 🔒 (berechtigt) | ❌ | ✅ | ✅ |
| Full Export: Grant (one-time Token, TTL/Limit) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Full Export: Abruf (X-Export-Token, Response verschlüsselt) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
