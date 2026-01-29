# LifeTimeCircle – Service Heft 4.0
**Rechte-Matrix (RBAC) – Entwurf (arbeitsfähig)**  
Stand: 2026-01-29

> Hinweis: Diese Matrix macht die bisherigen Entscheidungen „implementierbar“.  
> Wenn später Details angepasst werden, bitte auch **Backlog EPIC-03** aktualisieren.

Legende:
- ✅ erlaubt
- 🔒 nur eingeschränkt / nur eigener Scope / nur berechtigt (grant)
- ❌ nicht erlaubt

## Rollen
- public
- user
- vip
- dealer (gewerblich)
- moderator
- admin

## Funktionsbereiche

### 1) Public-QR Mini-Check (anonyme Ansicht)
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| QR-Link öffnen / Trust-Ampel sehen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Details zur Trust-Berechnung (Indicators, keine Halterdaten) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Technische Zustandsbewertung | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 2) Service Heft – Fahrzeug & Einträge
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Fahrzeug anlegen | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Eigenes Fahrzeugprofil ansehen | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Fremde Fahrzeuge ansehen (voll) | ❌ | ❌ | 🔒 (wenn berechtigt) | 🔒 (wenn berechtigt) | ❌ | ✅ |
| Einträge erstellen/bearbeiten (eigene Fahrzeuge) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Einträge löschen | ❌ | 🔒 (nur eigener, optional soft-delete) | ✅ | ✅ | ❌ | ✅ |
| Dokumente hochladen (Rechnung/Prüfbericht etc.) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |

### 3) Bilder/Dokumente – Sichtbarkeit (Tiefe)
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Dokument-Metadaten (Titel/Datum/Typ) sehen | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Dokument-Inhalt ansehen/downloaden | ❌ | 🔒 (eigen) | 🔒 (berechtigt) | 🔒 (berechtigt) | ❌ | ✅ |
| Bildansicht „VIP only“ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |

### 4) Verkauf/Übergabe-QR & interner Verkauf
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Übergabe-QR erzeugen | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Interner Verkauf starten/abwickeln | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Audit/Protokoll einsehen | ❌ | ❌ | 🔒 (eigene Vorgänge) | 🔒 (eigene Vorgänge) | ❌ | ✅ |

### 5) Blogbase / News
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| News lesen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| News erstellen/bearbeiten | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| News löschen | ❌ | ❌ | ❌ | ❌ | 🔒 (nur eigene Posts, optional) | ✅ |

### 6) Newsletter
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Opt-in / Opt-out (Abo verwalten) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Versand auslösen | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### 7) Admin / Governance
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Rollen vergeben / User sperren | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Moderatoren akkreditieren | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| VIP-Gewerbe: 2 Mitarbeiterplätze freigeben | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Halterdaten einsehen | ❌ | ❌ | ❌ | 🔒 (wenn berechtigt & notwendig) | ❌ | ✅ |

### 8) Exports (Privacy by default)
| Funktion | public | user | vip | dealer | moderator | admin |
|---|---:|---:|---:|---:|---:|---:|
| Export „redacted“ (Standard) | ❌ | ✅ (eigene) | ✅ (eigene/berechtigt) | ✅ (eigene/berechtigt) | ❌ | ✅ |
| Export „full“ (nur SUPERADMIN-Claim) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
