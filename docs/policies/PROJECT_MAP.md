./docs/policies/PROJECT_MAP.md
# LifeTimeCircle – ServiceHeft 4.0
## Project Map (Architektur- & Repo-Landkarte)

Stand: 2026-01-29  
Kontakt: lifetimecircle@online.de

Zweck: Gesamtbild über das Projekt: Core-Repo (Source of Truth) + Modul-Repos + Integrationslinien.  
Regel: Begriffe/Policies sind kanonisch im Core-Repo. Modul-Repos kopieren `docs/07_CONTEXT_PACK.md` unverändert.

---

## 1) Core-Repo (Source of Truth)
**Root:**  
`<REPO-ROOT>/`

### Verantwortlich für
- ServiceHeft 4.0 Kern (Fahrzeugprofil, Timeline, Nachweise)
- Public-QR Mini-Check (Trustscore Public View)
- Blog/Newsletter (Admin/Moderator)
- Auth/Consent/RBAC (grundsätzlich)
- Kanonische Doku (`docs/`)

### Kanonische Docs
- Modulsteuerung: `docs/04_MODULE_CATALOG.md`, `docs/05_MODULE_SPEC_SCHEMA.md`
- Terms: `docs/06_TERMS_GLOSSARY.md`
- Context Pack: `docs/07_CONTEXT_PACK.md`
- Policies: `docs/policies/*` (Index: `docs/policies/POLICY_INDEX.md`)
- RBAC Matrix: `docs/03_RIGHTS_MATRIX.md`

---

## 2) Modul-Repos (separat, implementieren Workflows/Tools)
### 2.1 MasterClipboard (VIP Gewerbe)
**Pfad:**  
`C:\Users\stefa\Projekte\LifeTimeCircle-Modules\masterclipboard\`

**Pflichtdateien im Modul-Repo:**
- `CONTEXT_PACK.md` (Copy aus Core; unverändert)
- `MODULE_SPEC.md`
- `API_CONTRACT.md`

**Fachlicher Scope:**
- Direktannahme-/Annahme-Session pro Fahrzeug
- Sprachaufnahme → Transkript → Vorschläge (Keywords/Buzzwords) → Triage:
  - Mängelliste (akzeptiert)
  - Mangel prüfen (zu prüfen)
  - abgelehnt (verworfen)
- Monitor-/Tafelansicht (intern)

**Identitäten:**
- Fahrzeug: QR-Fahrzeug-ID
- Actor: Mitarbeiter-ID

**Privacy:**
- keine Public-Ansicht
- keine Klartext-PII im Log
- VIN/WID nicht loggen

---

## 3) Integrationslinien (Core ↔ Modul)
### 3.1 Gemeinsame Identitäten
- QR-Fahrzeug-ID (primär)
- VIN/WID (sekundär, restriktiv)
- Mitarbeiter-ID (Prozess-Actor)

### 3.2 Gemeinsame Regeln
- RBAC serverseitig enforced (deny-by-default)
- Audit/Enums: `docs/policies/AUDIT_SCOPE_AND_ENUMS.md`
- Upload/Export: `docs/policies/UPLOAD_SECURITY_POLICY.md`, `docs/policies/EXPORT_POLICY.md`

### 3.3 Datenfluss (Minimal)
- MasterClipboard erzeugt Annahme-Session + strukturierte Mängelliste/Prüfliste
- Core speichert optional einen ServiceHeft-Eintrag „Annahme/Prüfung“ (rollenbasiert)
- Core schreibt Audit-Events (ohne PII)

---

## 4) Governance
- Module werden kanonisch im `docs/04_MODULE_CATALOG.md` geführt.
- Änderungen an Regeln/Terms nur im Core-Repo (`docs/…`, `docs/policies/…`) + Decision Log.
