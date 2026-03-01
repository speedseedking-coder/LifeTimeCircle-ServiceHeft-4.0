# Operations & Infrastructure – Overview

Stand: **2026-03-01** (Europe/Berlin)

Dieses Dokument fasst den operativen Ist-Stand für den Go-Live zusammen.

## Freigegebenes Betriebsmodell

Für den geplanten Go-Live am **2026-03-06** ist dieses Modell verbindlich:

- ein Host
- FastAPI/Uvicorn direkt aus dem Repo
- Frontend statisch hinter Reverse Proxy
- SQLite auf persistentem Storage
- Dokumente auf persistentem Storage

Nicht Teil des verbindlichen Day-0-Modells:

- RDS/PostgreSQL
- Docker/ECS/Kubernetes
- neue App-seitige Secret-Manager-Integrationen

## Welche Dokumente wofür gelten

| Dokument | Zweck |
|----------|-------|
| `14_DEPLOYMENT_GUIDE.md` | reale Deploy-Schritte |
| `15_MONITORING_INCIDENT_RESPONSE.md` | Monitoring und Incident-Handling |
| `16_SECRETS_MANAGEMENT.md` | Secrets und Rotation |
| `MASTER_GOLIVE_COORDINATION.md` | Rollen, Fristen, T-Plan |
| `TASK_*.md` | ausführbare Arbeitslisten pro Rolle |

## Weg zu Production

### 1. Vorbereitung

- Host bereitstellen
- Domain und TLS aktivieren
- persistente Pfade anbinden
- Secrets setzen

### 2. Staging

- `rc-2026-03-01` deployen
- Build und Health-Checks verifizieren
- mindestens 24h stabil beobachten

### 3. Go-Live

- Finales Go/No-Go
- Production deployen
- Smoke-Tests fahren
- T+24h intensiv beobachten

## Rollenfokus

### DevOps

- Host, TLS, systemd, Reverse Proxy, Persistenz

### Security

- `LTC_SECRET_KEY`, Env-Datei, Rechte, Rotation

### SRE

- Health-Checks, Log-Zugriff, Alerts, On-Call

### Release

- Freigaben, Kommunikation, Go/No-Go, Eskalation

## Kritische Prüfpunkte

- `LTC_SECRET_KEY` gesetzt
- `LTC_DATABASE_URL` und `LTC_DB_PATH` konsistent
- `server/data` und `server/storage` persistent
- `/api/health` extern grün
- Rollback-Verantwortung benannt

## Offene Pflichtangaben vor Go-Live

Dieses Repo enthält teils noch Platzhalter. Vor dem Go-Live müsst ihr ergänzen:

- echte Kontakte
- Incident-Kanal
- Status-Kanal
- On-Call-Rota
- Rollback-Entscheider
