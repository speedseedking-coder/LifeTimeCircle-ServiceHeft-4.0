# Day-2 Paket — Monitoring · Backups · Incident-Basics · UX-Polish

## Scope & Prinzipien
- Ziel: „Day-2 Operations“ minimal absichern: Beobachtbarkeit, Backup/Restore-Disziplin, Incident-Handling, UX-Polish.
- Keine neuen Produktfeatures, nur Betriebs- und Qualitätsnacharbeit.
- Security Default ist non-negotiable: **deny-by-default + least privilege**, RBAC **serverseitig** inkl. object-level checks.
- **Moderator** ist strikt auf **Blog/News** beschränkt; außerhalb davon **403**.
- **Keine PII/Secrets/Tokens** in Logs, Exports, Docs, Tickets, Screenshots.
- Wenn ein Fakt nicht in SoT steht: als **TBD** markieren, nicht raten.
- Trust ist keine Technikbewertung:
  „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## Monitoring (Minimum Viable Observability)
### Kernsignale (Minimum)
- **API Fehlerquote (5xx)**: Anstieg = Incident-Kandidat.
- **Latenz p95**: /auth, /vehicles, /documents, /trust (TBD: genaue Routen je nach Router-Set).
- **Auth/Actor Failures (401)**: Spike = Auth/Actor/Config-Problem.
- **403-Spikes** differenzieren:
  - 403 wegen **consent_required**
  - 403 wegen **entitlement_required**
  - 403 wegen **RBAC/object-level**
- **Uploads Pipeline**: QUARANTINED/PENDING zu CLEAN/APPROVED Durchlauf (Stau = Problem).
- **DB/Lock Errors** (insb. Windows/SQLite lokal): Auftreten tracken.

### Logging-Leitplanken (PII-safe)
- Keine Tokens, keine Secrets, keine unmaskierte VIN/Kennzeichen, keine E-Mail/Personendaten.
- Log-Events lieber mit: request_id, route, status_code, actor_role (ohne Identität), object_id (nicht-personenbezogen).

### Health/Readiness (minimal)
- `/health` muss OK liefern.
- (TBD) falls separates readiness exists: dort DB/Queue/Storage Checks.

---

## Backups & Restore (minimal)
### Was sichern
- Primäre Datenbank (TBD: DB-Typ/Ort in Produktion).
- (TBD) Object Storage für Uploads (falls extern): Backup-Strategie/Versioning klären.

### Frequenz & Retention
- TBD (SoT definiert keine konkreten Zeiten): Vorschlag erst nach Owner-Entscheid.

### Restore-Drill (monatlich, minimal)
- Ziel: „Restore ist machbar“ (nicht „perfekt“).
- Schritte:
  1) Backup auswählen (Datum/Version notieren)
  2) Restore in isolierter Umgebung
  3) Smoke: `/health` OK + minimaler Read auf Kernrouten (TBD: welche genau)
- Success-Kriterien:
  - API startet
  - Kernreads funktionieren
  - Keine PII-Leaks in Logs

---

## Incident-Basics (minimal)
### Severity
- **S0 (Security/Critical):** Verdacht auf Datenabfluss/PII/Secrets, Auth-Bypass, Privilege Escalation.
- **S1 (Major):** API down, 5xx dauerhaft hoch, Upload-Pipeline blockiert, Consent/Entitlement bricht flächig.
- **S2 (Minor):** Degradierte Performance, einzelne Features gestört, UI-Polish-Probleme.

### First 15 Minutes Checklist
1) **Containment:** Feature/Route isolieren, Rollback prüfen, risky changes stoppen.
2) **Evidence:** Logs (PII-safe), Statuscodes, Zeitfenster, betroffene Routen.
3) **Comms:** Kurzstatus intern; extern nur nach Freigabe (TBD: Kanal/Template).
4) **Owner:** Incident Commander benennen, Rollen zuweisen.
5) **Fix/Workaround:** kleinster stabiler Schritt (z. B. rollback, disable noncritical path).

### Rollen (keine Personen)
- Incident Commander (IC)
- Ops/Platform
- Backend
- Web
- Comms/Stakeholder-Update
- Security Reviewer (bei S0)

### Postmortem (Template)
- Was ist passiert?
- Impact (wer/was betroffen)?
- Root Cause (technisch + prozessual)
- Fix (kurzfristig) + Prevention (langfristig)
- Follow-ups (Owner + Deadline)

---

## UX-Polish (A11y + Skeletons)
### A11y Minimum
- Tastaturbedienung: alle primären Aktionen erreichbar (Tab/Shift+Tab/Enter/Esc).
- Fokus sichtbar (nicht entfernt), sinnvoller Fokus-Order.
- Kontrast prüfen (mind. für Kerntexte/Buttons).
- Form-Labels/ARIA für Inputs, Fehlermeldungen eindeutig und screenreader-tauglich.
- Error-Mapping (401/403/404/409) konsistent und verständlich.

### Skeletons (Loading States)
- Skeletons dort, wo Listen/Details geladen werden:
  - Vehicles Übersicht
  - Entries Timeline
  - Documents Liste/Upload Bereich
  - Trust Panel
- Regeln:
  - Skeleton folgt dem Layout (verhindert Layout-Shift).
  - Keine „Fake-Content“-Lügen: klar als Loading erkennbar.
  - Kurz warten? → Spinner ok; länger → Skeleton.

---

## Task-Backlog (Day-2)
> Format: ID · Prio · Bereich · Beschreibung · DoD · Verify · Owner

### P0
DAY2-001 · P0 · Monitoring · Request-ID & Statuscode Standard  
- DoD: Logging enthält request_id + route + status_code (PII-safe); keine Tokens/PII.  
- Verify: Stichprobe Logs; keine Tokens/PII sichtbar.  
- Owner: Backend/Ops

DAY2-002 · P0 · Monitoring · 5xx/Latency Baseline definieren  
- DoD: Baseline/Schwellen dokumentiert (oder als TBD markiert).  
- Verify: Doc-Review.  
- Owner: Ops

DAY2-003 · P0 · Incident · S0–S2 + First-15-Min fixieren  
- DoD: Severity + Checkliste bestätigt; Rollen ohne Personen.  
- Verify: Doc-Review.  
- Owner: Ops/Docs

DAY2-004 · P0 · Backups · Backup/Restore Verantwortlichkeit klären  
- DoD: Owner-Rolle festgelegt; DB/Storage als konkret oder TBD.  
- Verify: Doc-Review.  
- Owner: Ops

DAY2-005 · P0 · UX/A11y · Fokus sichtbar + Keyboard-Navigation kritische Flows  
- DoD: Eintritt/Auth/Consent/Vehicles/Upload/Trust keyboard-nutzbar.  
- Verify: Manuell Tab/Enter/Esc; Fokus sichtbar.  
- Owner: Web

DAY2-006 · P0 · UX/Skeletons · Skeletons für Vehicles + Trust  
- DoD: Skeleton bei Load; kein Layout-Shift; Error-State separat.  
- Verify: Network Throttle + visuelle Prüfung.  
- Owner: Web

### P1
DAY2-007 · P1 · Monitoring · 401 vs 403 Ursachen trennen  
- DoD: 401/403(consent)/403(entitlement)/403(rbac/object) getrennt dokumentiert.  
- Verify: Doc-Review (Tooling TBD).  
- Owner: Ops/Backend

DAY2-008 · P1 · Monitoring · Upload-Pipeline Statusmetriken  
- DoD: Aggregierte Counts für QUARANTINED/PENDING/CLEAN/INFECTED/APPROVED/REJECTED (PII-safe).  
- Verify: Admin-Flow + Auswertung (Tooling TBD).  
- Owner: Backend/Ops

DAY2-009 · P1 · Backups · Monatlicher Restore-Drill Plan  
- DoD: Ablauf + Success Criteria dokumentiert; Termin/Owner TBD oder gesetzt.  
- Verify: Doc-Review.  
- Owner: Ops

DAY2-010 · P1 · Incident · Postmortem Template operational  
- DoD: Template vorhanden; Ablageort TBD oder konkret.  
- Verify: Doc-Review.  
- Owner: Ops/Docs

DAY2-011 · P1 · UX/A11y · Kontrast + Labels/ARIA in Formularen  
- DoD: Inputs/Errors klar; Labels/ARIA vorhanden.  
- Verify: Manuell + Screenreader Smoke (Tooling TBD).  
- Owner: Web

DAY2-012 · P1 · UX/Skeletons · Skeletons für Entries + Documents  
- DoD: Entries/Documents Loading ohne Jitter; Empty-States korrekt.  
- Verify: Network Throttle + visuelle Prüfung.  
- Owner: Web

### P2
DAY2-013 · P2 · Monitoring · Log-Retention Policy  
- DoD: Retention dokumentiert; PII-safe bestätigt.  
- Verify: Doc-Review.  
- Owner: Ops

DAY2-014 · P2 · Incident · Comms Template (intern/extern)  
- DoD: 2 kurze Templates; keine PII; Freigabeprozess TBD.  
- Verify: Doc-Review.  
- Owner: Ops/Comms

DAY2-015 · P2 · UX · Konsistentes Empty-State Copy  
- DoD: Empty-States konsistent, kurz, handlungsleitend.  
- Verify: UI Review.  
- Owner: Web

DAY2-016 · P2 · Docs · Verlinkung im MASTER  
- DoD: docs/99_MASTER_CHECKPOINT.md verlinkt docs/11_DAY2_PACKAGE.md.  
- Verify: rg "11_DAY2_PACKAGE" docs/99_MASTER_CHECKPOINT.md.  
- Owner: Docs
