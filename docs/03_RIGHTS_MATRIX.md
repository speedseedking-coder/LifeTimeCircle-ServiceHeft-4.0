# docs/03_RIGHTS_MATRIX.md
# LifeTimeCircle – Service Heft 4.0
**Rights / RBAC Matrix (SoT)**  
Stand: **2026-02-06** (Europe/Berlin)

> Rollen sind serverseitig enforced. Default: deny-by-default.  
> Wenn etwas nicht explizit erlaubt ist → verboten.  
> Zusätzlich gilt bei allen objektbezogenen Ressourcen: object-level checks (Owner/Business-Zugehörigkeit/Scopes).  
> Produkt-Spezifikation ist bindend: `docs/02_PRODUCT_SPEC_UNIFIED.md`

---

## 1) Rollen
- `superadmin`: Vollzugriff (System, Admin, Support, Debug, Publish)
- `admin`: Admin-Funktionen, Quarantäne-Review, Exports, Management, Review
- `dealer`: Business-User (Händler / Dealer Suite), begrenzte Datenzugriffe, kein Admin/Quarantäne
- `vip`: Premium-Enduser (privat oder gewerblich), erweiterte Einsichten (aber kein Admin/Quarantäne)
- `user`: Standard-Enduser
- `moderator`: strikt nur Blog/News (kein Zugriff auf Fahrzeuge/Dokumente/Trust/Exporte/PII/Audit)

---

## 2) Globale Regeln (Systemweit)
- deny-by-default: jede Route muss explizit gated sein
- Actor required: ohne Actor → 401
- Moderator hard-block: überall außer Blog/News → 403
- Consent Gate (AGB/Datenschutz):
  - Produkt-Routen erfordern die aktuellste akzeptierte Version
  - ohne Re-Consent: nur Consent-Flow erlaubt (Produkt-Routen blockiert)
- PII:
  - niemals öffentlich
  - PII suspected/confirmed nur Owner/Admin
  - solange PII offen: Trust T3 blockiert
- Uploads:
  - Quarantine-by-default
  - Approve nur nach Scan CLEAN
- Exports:
  - für Nicht-Admins nur redacted
  - Dokument-Refs nur APPROVED
- Keine PII/Secrets in Logs/Responses/Exports

---

## 3) Enforcement (Tests)
- Runtime-Scan (Moderator):
  - iteriert über alle registrierten Routes
  - Allowlist (ohne 403): `/auth/*`, `/health`, `/blog/*`, `/news/*`
  - außerhalb der Allowlist muss `moderator` 403 bekommen

---

## 4) Public (ohne Login)

### 4.1 Public Site / Public QR Mini-Check
| Route-Group | superadmin | admin | dealer | vip | user | moderator | public |
|---|---:|---:|---:|---:|---:|---:|---:|
| `/public/*` (Site/QR) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ (403) | ✅ |
Public Daten-Regeln (bindend):
- datenarm: Klasse, Marke/Modell, Baujahr, Motor/Antrieb grob
- VIN maskiert: erste 3 + letzte 4
- Trust-Ampel + Unfallstatus-Badge
- Pflicht-Disclaimer (exakt):
  - „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

### 4.2 Public Content Read (Blog/News)
| Route-Group | superadmin | admin | dealer | vip | user | moderator | public |
|---|---:|---:|---:|---:|---:|---:|---:|
| `/blog/*` (read) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/news/*` (read) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 5) Auth / Consent

### 5.1 Auth
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/auth/*` (register/login/verify) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 5.2 Consent (AGB/Datenschutz)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/consent/*` (read/accept/re-consent) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Regel:
- ohne gültigen Consent (neueste Version akzeptiert) → Produkt-Routen blockiert; Consent-Flow bleibt möglich.

---

## 6) Profil / Entitlements (UI: Profiladmin / E-Rolle)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/profile/*` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ 403 |
| `/entitlements/*` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ 403 |

Hinweis:
- Moderator bleibt auf Blog/News beschränkt; Profilzugriffe sind hier nur für akkreditierte Self-Profile-Ansichten gedacht.

---

## 7) Vehicles / Flotten / Sammlungen

### 7.1 Vehicles (Owner-Objekte, object-level)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/vehicles/*` | ✅ | ✅ | ✅ (eigene Business/Flotte) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

Regeln:
- object-level: nur Owner oder Business-Zugehörige sehen/ändern
- Paywall: 1 Fahrzeug gratis, ab 2 serverseitig gated (Plan/Entitlement)

### 7.2 Collections/Fleets
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/collections/*` | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

---

## 8) Vehicle Record / Entries / Galerie / Archiv / Rechnungen

### 8.1 Entries (Timeline)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/vehicles/{id}/entries/*` | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

Pflichtfelder (MVP) sind serverseitig enforced:
- Datum, Typ, durchgeführt von, Kilometerstand

### 8.2 Galerie
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/vehicles/{id}/gallery/*` | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

### 8.3 Archiv/Rechnungen
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/vehicles/{id}/archive/*` | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |
| `/vehicles/{id}/invoices/*` | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

---

## 9) Dokumente / Uploads (`/documents/*`)

### 9.1 Upload / Read / Download (approved, object-level)
| Route | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `POST /documents/upload` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ 403 |
| `GET /documents/{id}` | ✅ | ✅ | ✅ (APPROVED+scope+object-level) | ✅ (APPROVED+scope+object-level) | ✅ (APPROVED+scope+object-level) | ❌ 403 |
| `GET /documents/{id}/download` | ✅ | ✅ | ✅ (APPROVED+scope+object-level) | ✅ (APPROVED+scope+object-level) | ✅ (APPROVED+scope+object-level) | ❌ 403 |

### 9.2 Quarantäne / Review (Admin-only)
| Route | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `GET /documents/admin/quarantine` | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| `POST /documents/{id}/approve` | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| `POST /documents/{id}/reject` | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| `POST /documents/{id}/rescan` | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |

PII-Regeln (bindend):
- PII suspected/confirmed: Sichtbarkeit nur Owner/Admin
- solange PII offen: Trust T3 blockiert
- Admin-Override nur mit Audit

---

## 10) Trust (intern) + Trust-Ordner (Add-ons)

### 10.1 Trust intern (vehicle-scoped)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/trust/*` | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

### 10.2 Trust-Ordner (Unfall/Oldtimer/Restauration)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/trust/folders/*` | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

Grandfathering/Add-on Gate:
- Gate nur bei Erstaktivierung (`addon_first_enabled_at == null`)
- Bestandsfahrzeuge bleiben nutzbar, auch bei Re-Aktivierung
- Admin-Schalter pro Add-on: neu erlauben, neu kostenpflichtig, optional admin-only

---

## 11) Moduleingang / Vorschläge / Systemlogs
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/modules/*` (suggestions, vehicle-scoped) | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |
| `/systemlogs/*` (OBD/GPS, immutable) | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

Immutable Logs:
- OBD/GPS Logs nicht lösch-/editierbar (nur Ergänzungen)

---

## 12) Verkauf & Übergabe

### 12.1 Übergabe-QR (Owner Transfer)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/transfer/*` | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |

Regel:
- Laufzeit 14 Tage + 1 Verlängerung

### 12.2 Dealer Suite / Weiterverkauf
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/dealer/*` | ✅ | ✅ | ✅ | ✅ (nur wenn Dealer Suite aktiv) | ❌ 403 | ❌ 403 |

### 12.3 Sale Transfer Status (Security Fix)
| Route | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `GET /sale/transfer/status/{tid}` | ✅ | ✅ | ✅ (Initiator|Redeemer) | ✅ (Initiator|Redeemer) | ❌ 403 | ❌ 403 |

---

## 13) PDFs / Zertifikate / Exports

| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/pdf/qr/*` (QR-PDF) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ 403 |
| `/pdf/trust/*` (Trust-Zertifikat) | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |
| `/pdf/maintenance/*` (Wartungsstand) | ✅ | ✅ | ✅ (eigene) | ✅ (eigene) | ✅ (eigene) | ❌ 403 |
| `/export/ad/*` (Inserat-Export) | ✅ | ✅ | ✅ (eigene Business) | ✅ | ❌ 403 | ❌ 403 |

TTL-Regeln:
- Trust-Zertifikat 90 Tage
- Wartungsstand 30 Tage
- Inserat-Export 30 Tage (VIP-only)
- Datei läuft ab/gelöscht, Historie-Eintrag bleibt

---

## 14) Notifications
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/notifications/*` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ 403 |

VIP:
- Ruhezeiten (nur E-Mail)
- Reminder 7 Tage vor Ablauf

Free:
- keine Ruhezeiten (Digest bleibt)

---

## 15) Admin / Support / Moderation

### 15.1 Support/Feedback
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/support/feedback` (create) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/support/admin/*` (inbox) | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |

### 15.2 Blog/News Authoring (Moderator erlaubt, aber strikt Content-only)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/cms/blog/*` (draft/edit) | ✅ | ✅ (review) | ❌ 403 | ❌ 403 | ❌ 403 | ✅ |
| `/cms/news/*` (draft/edit) | ✅ | ✅ (review) | ❌ 403 | ❌ 403 | ❌ 403 | ✅ |
| `/cms/publish/*` (publish final) | ✅ | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |

Regel:
- Workflow: Entwurf → Review → Publish
- Publish final: Superadmin

---

## 16) Import (Gewerbe-ready)
| Route-Group | superadmin | admin | dealer | vip | user | moderator |
|---|---:|---:|---:|---:|---:|---:|
| `/import/*` (csv/xlsx, validate, run, report) | ✅ | ✅ | ✅ | ✅ (nur Gewerbe-Context) | ❌ 403 | ❌ 403 |

Regel:
- 2-Step Validierung ist verpflichtend (validate → run)
- Report ist verpflichtend (Erfolg/Fehler/Mapping)
- Dubletten: skip + Report

Zusatzregel „Trust-Evidence“:
- Nicht-Admins dürfen Dokumente nur downloaden, wenn sie „valid evidence“ sind:
  APPROVED + CLEAN + PII_OK (und object-level Zugriff).

PII-Sichtbarkeit:
- pii_status != OK => nur Owner/Admin sichtbar.


## Export / PDFs

| Endpoint | guest | vip | dealer | moderator | admin | superadmin |
|-----------|--------|-----|--------|------------|--------|-------------|
| POST /export/vehicle/{vehicle_id}/grant | ❌ | Owner | Owner | ❌ | ✅ | ✅ |
| GET /export/vehicle/{vehicle_id}/full | ❌ | Owner* | Owner* | ❌ | ✅ | ✅ |

\* GET /export/vehicle/{vehicle_id}/full requires Header X-Export-Token; Token ist **one-time** (used=true) und **TTL**-gebunden (expires_at).