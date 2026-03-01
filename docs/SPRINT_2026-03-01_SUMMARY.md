# 2026-03-01 Release Hardening Sprint – Summary

Stand: **2026-03-01 18:50 CET** (Europe/Berlin)

---

## Ziel

Den technisch verifizierten Release Candidate `rc-2026-03-01` in einen belastbar dokumentierten Go-Live-Kandidaten ueberfuehren, ohne den Ist-Code architektonisch falsch darzustellen.

---

## Abgeschlossene Arbeit

### 1. Release- und Nachweisbasis

Commit: `464e766`

- `CHANGELOG.md` aktualisiert
- `RECENT_FILES.txt` erzeugt
- `COMMIT_LIST.txt` erzeugt
- Git-Tag `rc-2026-03-01` erstellt

### 2. Operations-Dokumentation aufgebaut

Commit: `713ac00`

- `docs/00_OPERATIONS_OVERVIEW.md` als operativen Einstiegspunkt angelegt
- `docs/14_DEPLOYMENT_GUIDE.md` fuer den realen Deployment-Pfad angelegt
- `docs/15_MONITORING_INCIDENT_RESPONSE.md` fuer Monitoring und Incident-Handling angelegt
- `docs/16_SECRETS_MANAGEMENT.md` fuer Secrets, Rotation und Notfaelle angelegt

### 3. Sprint-Zusammenfassung erstellt

Commit: `cab3d4c`

- `docs/SPRINT_2026-03-01_SUMMARY.md` erstmals erzeugt

### 4. Rollenspezifische Aufgabenlisten erstellt

Commit: `7166da5`

- `docs/TASK_DEVOPS_INFRASTRUCTURE.md`
- `docs/TASK_SECURITY_SECRETS.md`
- `docs/TASK_SRE_MONITORING.md`
- `docs/TASK_RELEASE_MANAGER_GOLIVE.md`

### 5. Master-Koordination erstellt

Commit: `0b79f69`

- `docs/MASTER_GOLIVE_COORDINATION.md`

### 6. Spaete Korrekturen fuer Realitaetsabgleich und Security

Lokaler Workspace-Stand am Abend des 2026-03-01:

- `docs/GO_LIVE_BLOCKERS_AND_TARGET_STATE_2026-03-01.md` dokumentiert, dass PostgreSQL/RDS, Containerisierung und App-seitige Secret-Manager-Integration kein Day-0-Pflichtpfad sind.
- `docs/CODEX_HANDOVER_2026-03-01.md` fasst den operativen Zielzustand fuer neue Bearbeiter zusammen.
- `server/app/routers/documents.py` nutzt die zentrale Actor-Policy statt unkontrollierter Legacy-Header.
- `server/app/routers/export_vehicle.py` akzeptiert Legacy-Header nur noch hinter dem expliziten Dev-Gate.
- `server/tests/test_sensitive_routes_dev_header_gate.py` deckt diese Regression ab.

---

## Verbindliches Zielbild fuer den Go-Live

Fuer den geplanten Go-Live am **Donnerstag, 2026-03-06, 10:00 CET** gilt als freigegebenes Day-0-Modell:

- Single-Node Production
- Backend via `poetry run uvicorn app.main:app`
- Frontend als statischer Build hinter Reverse Proxy
- SQLite auf persistentem Datentraeger
- persistente lokale Verzeichnisse fuer `server/data` und `server/storage`

Nicht Teil des verbindlichen Day-0-Modells:

- RDS oder PostgreSQL als Pflicht
- Docker, ECS oder Kubernetes als Pflicht
- Multi-Instance-Betrieb
- App-seitige Integration eines Secret Managers

Wenn eines dieser erweiterten Zielbilder gefordert wird, ist das ein separates Architekturprojekt und kein reiner Betriebsrest.

---

## Was jetzt belastbar vorliegt

- Release Candidate `rc-2026-03-01` ist technisch verifiziert.
- Kernpfade fuer Web und Backend sind ueber Build, E2E und Tests abgesichert.
- Go-Live-Dokumentation ist auf den realistischen Single-Node-Pfad korrigiert.
- Rollenbezogene Arbeitslisten fuer DevOps, Security, SRE und Release Management liegen vor.
- Die Security-Haertung fuer sensible Header-Fallbacks ist umgesetzt und getestet.

---

## Offene Arbeit vor echtem Go-Live

### Operativ offen

- Host oder VM bereitstellen
- Domain, TLS und Redirect-Regeln einrichten
- persistente Pfade fuer Daten und Storage anbinden
- `LTC_SECRET_KEY` produktiv setzen
- Staging im gleichen Betriebsmodell wie Production aufsetzen
- Monitoring, Alarmierung und On-Call aktivieren
- Rollback und Backup/Restore pruefen
- organisatorische und rechtliche Freigaben einholen

### Nicht mehr als offen formulierbar

Diese Punkte duerfen nicht mehr so dargestellt werden, als waeren sie bereits vorbereitet oder Pflicht fuer den 2026-03-06-Go-Live:

- VPC-/Cloud-Architekturentscheidungen als Muss
- RDS/PostgreSQL-Migration als Muss
- Docker-/ECS-/Kubernetes-Deployment als Muss
- produktive Secret-Manager-Integration im App-Code als Muss

---

## Verifikation

In der Sprint-Session verifiziert:

- `git diff --check`
- `npm run build`
- `npm run e2e`
- `poetry run pytest -q`

Fuer die spaeten Security-Korrekturen zusaetzlich verifiziert:

- `poetry run pytest -q .\tests\test_sensitive_routes_dev_header_gate.py`

Hinweis:

- Der fruehe RC-Stand war clean.
- Der aktuelle Workspace ist nach den spaeten Korrekturen bewusst nicht clean, solange die lokalen Aenderungen noch nicht committet sind.

---

## Relevante Dokumente

Zuerst lesen:

1. `docs/99_MASTER_CHECKPOINT.md`
2. `docs/CODEX_HANDOVER_2026-03-01.md`
3. `docs/MASTER_GOLIVE_COORDINATION.md`
4. `docs/14_DEPLOYMENT_GUIDE.md`
5. `docs/15_MONITORING_INCIDENT_RESPONSE.md`
6. `docs/16_SECRETS_MANAGEMENT.md`

Nach Rolle:

- DevOps: `docs/TASK_DEVOPS_INFRASTRUCTURE.md`
- Security: `docs/TASK_SECURITY_SECRETS.md`
- SRE: `docs/TASK_SRE_MONITORING.md`
- Release: `docs/TASK_RELEASE_MANAGER_GOLIVE.md`

Ergaenzend:

- `docs/GO_LIVE_BLOCKERS_AND_TARGET_STATE_2026-03-01.md`
- `docs/12_RELEASE_CANDIDATE_2026-03-01.md`
- `docs/13_GO_LIVE_CHECKLIST.md`

---

## Fazit

Der Sprint hat den Release Candidate nicht in eine neue Zielarchitektur ueberfuehrt, sondern die reale Betriebsfaehigkeit sauber beschrieben.

Stand **2026-03-01 18:50 CET** ist die belastbare Linie:

- Code verifiziert
- Security-Hotfix fuer sensible Header-Fallbacks umgesetzt
- Go-Live-Doku konsistent auf Single-Node + SQLite + persistenten lokalen Storage gezogen
- operative Ausfuehrung und Freigaben weiterhin offen

Die naechste Phase ist deshalb nicht "Architektur entwerfen", sondern das dokumentierte Day-0-Modell wirklich ausfuehren oder den Go-Live-Termin bei abweichendem Zielbild neu bewerten.
