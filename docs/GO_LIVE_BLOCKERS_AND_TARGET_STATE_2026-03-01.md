# Go-Live Blocker, RBAC-Pruefung und realistisches Zielbild

Stand: **2026-03-01** (Europe/Berlin)
Bezug: RC `rc-2026-03-01`, Branch `wip/add-web-modules-2026-03-01-0900`

## 1) Executive Summary

Der lokale Workspace ist technisch verifiziert:

- `git diff --check` clean
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1` gruen
- `poetry run pytest -q` gruen
- `npm run build` gruen
- `npm run e2e` war laut Session-Log gruen

Trotzdem ist der geplante Go-Live am **2026-03-06 10:00 CET** nur unter einer engen Bedingung realistisch:

- **Realistisch:** Single-node / single-environment Production auf Basis der aktuellen SQLite-/File-Storage-Architektur, mit sauberem Hardening und ohne Architekturwechsel.
- **Nicht realistisch bis 2026-03-06:** Cloud-native Zielarchitektur aus den neuen Ops-Docs mit RDS PostgreSQL, containerisiertem Deploy, Secrets-Manager-Integration im App-Code, Multi-Instance-Betrieb und vollstaendiger SRE-Automation.

Der groesste operative Fehler waere, die vorhandene Softwarebasis als bereits PostgreSQL-/ECS-/Secrets-Manager-ready zu behandeln. Das ist sie Stand **2026-03-01** nicht.

## 2) Harte Go-Live-Blocker

### Blocker A: Persistenzmodell und Zielarchitektur passen nicht zusammen

Die aktuellen Go-Live-Dokumente planen PostgreSQL/RDS, waehrend der produktive Code an mehreren kritischen Stellen explizit auf SQLite und Dateipfade gebaut ist.

Betroffene Dateien, die vor einem PostgreSQL-/RDS-Go-Live geaendert werden muessen:

- `server/app/auth/storage.py`
- `server/app/auth/settings.py`
- `server/app/auth/service.py`
- `server/app/admin/routes.py`
- `server/app/services/documents_store.py`
- `server/app/consent_store.py`
- `server/app/services/sale_transfer_store.py`
- `server/app/core/config.py`

Begruendung:

- `sqlite3.connect(...)`, `PRAGMA ...`, `sqlite_master` und WAL werden direkt verwendet.
- Auth und Admin laufen nicht ueber die zentrale SQLAlchemy-Engine.
- Dokument-Metadaten liegen in separater Datei `server/data/documents.sqlite`.
- Upload-Dateien liegen lokal unter `server/storage`.
- Consent/Auth verwenden `LTC_DB_PATH`, waehrend das generische Settings-Modell `LTC_DATABASE_URL` nutzt.

Konsequenz:

- Ein Wechsel auf RDS PostgreSQL vor dem 6. Maerz 2026 ist ein Architekturprojekt, kein reines Deploy-Thema.

### Blocker B: Unsichere Header-Fallbacks umgehen die zentrale Actor-Policy

Die zentrale Actor-Dependency ist korrekt auf `LTC_ALLOW_DEV_HEADERS` begrenzt:

- `server/app/auth/actor.py`

Es gibt aber produktionskritische Router, die das Muster umgehen und direkte Header akzeptieren:

- `server/app/routers/documents.py`
- `server/app/routers/export_vehicle.py`

Begruendung:

- `documents.py` akzeptiert `X-LTC-ROLE` und `X-LTC-UID` ohne ENV-Gate.
- `export_vehicle.py` akzeptiert `X-LTC-ROLE` und `X-LTC-UID` ohne ENV-Gate.

Konsequenz:

- Vor Freigabe fuer Production muessen diese Fallbacks entfernt oder strikt an dieselbe DEV/TEST-Gate-Logik gebunden werden wie `app.auth.actor.require_actor`.
- Andernfalls haengt der Schutz davon ab, dass kein Upstream diese Header weiterreicht.

### Blocker C: Produktionsartefakte in Docs referenziert, aber im Repo nicht vorhanden

Die Go-Live-Dokumente setzen Artefakte voraus, die Stand **2026-03-01** nicht existieren.

Fehlende Dateien:

- `.github/workflows/deploy-prod.yml`
- `tools/deploy_prod.sh`
- `server/Dockerfile`
- `packages/web/Dockerfile`

Dokumente mit Annahmen dazu:

- `docs/MASTER_GOLIVE_COORDINATION.md`
- `docs/14_DEPLOYMENT_GUIDE.md`
- `docs/TASK_DEVOPS_INFRASTRUCTURE.md`
- `docs/TASK_SECURITY_SECRETS.md`
- `docs/TASK_RELEASE_MANAGER_GOLIVE.md`

Konsequenz:

- Das aktuelle Repo enthaelt keinen fertigen produktiven Deployment-Pfad fuer die in den Docs beschriebene Zielarchitektur.

### Blocker D: Konfigurationsmodell ist nicht vereinheitlicht

Aktuell existieren parallel:

- `LTC_SECRET_KEY`
- `LTC_DB_PATH`
- `LTC_DATABASE_URL`
- `DATABASE_URL` in Docs

Betroffene Dateien, die vor Production vereinheitlicht werden muessen:

- `server/app/core/config.py`
- `server/app/auth/settings.py`
- `docs/14_DEPLOYMENT_GUIDE.md`
- `docs/16_SECRETS_MANAGEMENT.md`
- `docs/TASK_SECURITY_SECRETS.md`
- `docs/TASK_DEVOPS_INFRASTRUCTURE.md`

Konsequenz:

- Hohes Risiko fuer Fehlstarts, falsche Runtime-Konfiguration und inkonsistente Deploy-Skripte.

## 3) Sofort zu fixende Security-/RBAC-Befunde

### Befund 1: `documents.py` akzeptiert devartige Actor-Header ohne Gate

Datei:

- `server/app/routers/documents.py`

Problem:

- Router implementiert eigene `require_actor(...)`-Logik.
- Diese akzeptiert `X-LTC-ROLE` und `X-LTC-UID` sofort.
- Kein Bezug zu `LTC_ALLOW_DEV_HEADERS`.

Einstufung:

- **Sofort-Fix vor Production**

Empfohlene Aenderung:

- Router auf `from app.auth.actor import require_actor` umstellen.
- Keine eigene Header-Logik mehr im Router.

### Befund 2: `export_vehicle.py` akzeptiert Actor-Header ohne Gate

Datei:

- `server/app/routers/export_vehicle.py`

Problem:

- Fallback akzeptiert `X-LTC-ROLE` und `X-LTC-UID` direkt.
- Export-Pfade sind sensitiv und duerfen nicht auf Client-Header vertrauen.

Einstufung:

- **Sofort-Fix vor Production**

Empfohlene Aenderung:

- Gemeinsame zentrale Actor-Dependency nutzen.
- Header-Fallback nur wenn `LTC_ALLOW_DEV_HEADERS=1` und nur fuer Dev/Test.

### Befund 3: Rollen- und Consent-Pfade nutzen mehrere historische Kompatibilitaetslayer

Dateien:

- `server/app/auth/routes.py`
- `server/app/consent_store.py`
- `server/app/routers/vehicles.py`

Problem:

- Historische Compat-Layer und alternative Call-Patterns erschweren die eindeutige Sicherheitsbewertung.
- Es ist funktional noch vertretbar, aber fuer Production-Haertung zu komplex.

Einstufung:

- **Kein Day-0-Stopper**, aber vor dem naechsten Architekturzyklus vereinfachen.

### Befund 4: Root-Verzeichnis ausserhalb des Repos enthaelt mutmassliche Secret-Dateien

Pfade ausserhalb des Repos:

- `C:\Users\stefa\Projekte\secret.txt`
- `C:\Users\stefa\Projekte\token.txt`

Einstufung:

- **Operatives Sicherheitsrisiko**

Hinweis:

- Nicht Teil des Git-Repos, aber fuer den echten Go-Live-Haushalt problematisch.

## 4) Exakte Dateien, die vor dem 2026-03-06 Go-Live geaendert werden muessen

### Muss geaendert werden fuer sicheren Single-node-Production-Go-Live

- `server/app/routers/documents.py`
- `server/app/routers/export_vehicle.py`
- `docs/MASTER_GOLIVE_COORDINATION.md`
- `docs/14_DEPLOYMENT_GUIDE.md`
- `docs/15_MONITORING_INCIDENT_RESPONSE.md`
- `docs/16_SECRETS_MANAGEMENT.md`
- `docs/TASK_DEVOPS_INFRASTRUCTURE.md`
- `docs/TASK_SECURITY_SECRETS.md`
- `docs/TASK_SRE_MONITORING.md`
- `docs/TASK_RELEASE_MANAGER_GOLIVE.md`
- `docs/CODEX_HANDOVER_2026-03-01.md`

Warum:

- Code: Header-Fallbacks absichern.
- Docs: Produktionszielbild, Deploy-Pfade, Error-Rate-Schwellen, Staging-Soak-Time und Konfigurationsnamen vereinheitlichen.

### Muss zusaetzlich geaendert werden, falls unbedingt PostgreSQL/RDS bis 2026-03-06 erzwungen wird

- `server/app/auth/storage.py`
- `server/app/auth/settings.py`
- `server/app/auth/service.py`
- `server/app/admin/routes.py`
- `server/app/services/documents_store.py`
- `server/app/consent_store.py`
- `server/app/services/sale_transfer_store.py`
- `server/app/core/config.py`
- `server/pyproject.toml`

Warum:

- SQLite-spezifische Pfade und APIs muessen ersetzt oder vereinheitlicht werden.
- Zusatzaengig benoetigte Bibliotheken fuer den neuen Betriebsstack muessen eingebracht werden.

## 5) Realistisches Produktionszielbild auf Basis des Ist-Codes

### Realistisch bis 2026-03-06

Ein **Single-VM / Single-Node Deployment** mit:

- Web-Build aus `packages/web/dist`
- Reverse Proxy via nginx oder vergleichbar
- Backend via `poetry run uvicorn app.main:app`
- SQLite-Dateien lokal auf persistenter Disk
- `server/storage` lokal auf persistenter Disk
- `LTC_SECRET_KEY` als geschuetzte Runtime-Variable
- `LTC_ENV=prod`
- Debug/OpenAPI in prod deaktiviert
- Basis-Monitoring auf HTTP Healthcheck, Disk, Prozess, TLS, Error-Logs
- Manuelle, dokumentierte Rollback-Prozedur

Dieses Zielbild ist kompatibel mit:

- `docs/07_PRODUCTION_BASELINE.md`
- `docs/04_REPO_STRUCTURE.md`
- dem realen Code in `server/app/core/config.py`
- dem realen Auth-/Storage-Modell

### Nicht realistisch bis 2026-03-06 ohne zusaetzliche Implementierung

- Multi-instance API hinter Load Balancer
- RDS PostgreSQL als produktiver Primarspeicher fuer alle Flows
- Objekt-Storage-/Bucket-basiertes Dokumentensystem
- produktive Secrets-Manager-Integration im App-Code
- vollstaendige Container-/Registry-/ECS- oder Kubernetes-Pipeline
- neue APM-/Sentry-/New Relic-Integrationen direkt im Anwendungscode
- vollautomatisierte SRE-Pager-/On-Call- und Status-Page-Kette

## 6) Dokumentenkonsistenz: Was konkret korrigiert werden muss

### Vereinheitlichen auf ein einziges Production-Narrativ

Entscheidung bis spaetestens **Montag, 2026-03-02**:

1. **Short-path Go-Live:** Single-node, SQLite, lokales persistent Storage, minimaler Ops-Stack.
2. **Architecture-change Go-Live:** verschieben, wenn PostgreSQL/RDS/Container/Secrets-Manager wirklich Pflicht sind.

### Danach in den Docs angleichen

Zu vereinheitlichen:

- Staging-Soak-Time: entweder `24h+` oder `48h`, nicht beides
- Error-Rate-Ziele: SLO, Warning, Rollback-Trigger sauber trennen
- Konfigurationsnamen: `LTC_SECRET_KEY`, `LTC_DB_PATH` oder `LTC_DATABASE_URL`, aber konsistent dokumentieren
- Startkommando: `poetry run uvicorn app.main:app ...`
- Deploy-Artefakte nur nennen, wenn sie im Repo existieren

## 7) Konkrete Empfehlung fuer den 6. Maerz 2026

Wenn das Ziel **puenktlicher Go-Live am 2026-03-06** ist, dann ist die pragmatische Linie:

1. Security-Fixes an den Header-Fallbacks sofort umsetzen.
2. Go-Live-Dokumentation auf das real existente Single-node-Zielbild korrigieren.
3. Production auf persistenter Einzelumgebung mit SQLite und lokalem Storage fahren.
4. PostgreSQL/Container/Secrets-Manager als nachgelagerte Architekturphase planen.

Wenn dagegen **RDS/PostgreSQL/Container/Secrets-Manager** zwingend vorgeschrieben sind, dann sollte der Go-Live-Termin **2026-03-06** neu bewertet werden. Auf Basis des aktuellen Codes ist das kein verantwortbarer "nur noch Ops"-Rest.
