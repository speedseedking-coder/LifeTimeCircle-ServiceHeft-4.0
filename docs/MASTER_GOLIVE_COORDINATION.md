# Go-Live Execution Plan – Master Coordination (2026-03-01 → 2026-03-06)

Stand: **2026-03-01 18:30 CET** (Europe/Berlin)

## Executive Summary

Der Release Candidate `rc-2026-03-01` ist verifiziert. Für den Go-Live am **Donnerstag, 6. März 2026, 10:00 CET** gilt bis auf Weiteres dieses Zielbild:

- Single-Node Production
- Backend: `poetry run uvicorn app.main:app`
- Frontend: statischer Build hinter nginx oder vergleichbarem Reverse Proxy
- Datenhaltung: SQLite auf persistentem Datenträger
- Dokumente: persistente lokale Verzeichnisse für `server/data` und `server/storage`

Wichtig: Ein Go-Live mit RDS/PostgreSQL, Container-Orchestrierung oder App-seitiger Secret-Manager-Integration ist im aktuellen Repo-Stand nicht als Pflichtpfad abgedeckt. Wer dieses Zielbild verlangt, verschiebt den Go-Live.

## Verbindliches Zielbild für 2026-03-06

### Architektur

- Ein Host oder eine VM für Production
- TLS-Termination und Reverse Proxy vor dem Backend
- Backend läuft aus dem Repo-Checkout im Ordner `server`
- Frontend-Assets aus `packages/web/dist`
- Persistente Pfade:
  - `/var/lib/lifetimecircle/data`
  - `/var/lib/lifetimecircle/storage`

### Erforderliche Konfiguration

- `LTC_SECRET_KEY` ist Pflicht und muss mindestens 32 Zeichen haben
- `LTC_ENV=prod`
- `LTC_DATABASE_URL=sqlite+pysqlite:////var/lib/lifetimecircle/data/app.db`
- `LTC_DB_PATH=/var/lib/lifetimecircle/data/app.db`
- `server/data` und `server/storage` müssen auf persistente Verzeichnisse zeigen, z. B. per Symlink oder Bind-Mount

### Externe Checks

- Health-Check extern über `https://<domain>/api/health`
- Upstream-Health intern über `http://127.0.0.1:8000/health`

## Workstreams

### DevOps

**Deadline:** 2026-03-03 EOD

- Host bereitstellen
- Domain und TLS konfigurieren
- Persistente Pfade anlegen
- Prozesssteuerung für API einrichten, bevorzugt `systemd`
- Staging und Production mit gleichem Betriebsmodell aufsetzen

### Security

**Deadline:** 2026-03-03 EOD

- `LTC_SECRET_KEY` generieren und sicher ablegen
- Zugriffsmodell für Prod-Env-Datei oder Secret Store festlegen
- Berechtigungen für Secrets und Hostzugriff dokumentieren
- Rotations- und Notfallprozess festlegen

### SRE

**Deadline:** 2026-03-05 EOD

- Verfügbarkeit, Error Rate, Disk, Memory und TLS überwachen
- Alarmkanäle und Rufbereitschaft festlegen
- Incident-Runbooks gegen das reale Single-Node-Setup prüfen

### Release Manager

**Deadline:** 2026-03-05 EOD

- Freigaben einsammeln
- Support-Briefing koordinieren
- Go/No-Go moderieren
- T-0 bis T+24h Kommunikationsführung übernehmen

## Abhängigkeiten

| Bereich | Braucht | Liefert |
|--------|---------|---------|
| DevOps | Domain-Entscheidung, Host-Zugang | Staging-/Prod-URL, Betriebsmodell |
| Security | DevOps-Zielhost | Secrets, Zugriffsregeln, Rotationsplan |
| SRE | erreichbare Staging-URL | Monitoring, Alerts, Rufbereitschaft |
| Release | Status aller drei Streams | Go/No-Go, Kommunikation, Eskalation |

## Harte Go-Live-Blocker

Bis **Dienstag, 3. März 2026, EOD** muss erledigt sein:

1. Produktionshost steht und ist per Domain/TLS erreichbar.
2. Persistente Datenpfade sind angebunden und gegen Neustarts verifiziert.
3. `LTC_SECRET_KEY` ist gesetzt und der API-Start in `prod` funktioniert.
4. Staging läuft mit demselben Setup wie Production.

Bis **Mittwoch, 4. März 2026, EOD** muss erledigt sein:

1. Staging läuft mindestens **24 Stunden** ohne kritische Fehler.
2. Smoke-Tests und zentrale Gates sind grün.
3. Monitoring und Alarmierung sind aktiv.

Wenn einer dieser Punkte offen bleibt, ist **2026-03-06** nicht haltbar.

## Go-Live Timeline

### T-24h: Mittwoch, 5. März 2026, 10:00 CET

- Staging seit mindestens 24h stabil
- Rollback auf letzten bekannten Tag getestet
- Support und On-Call bestätigt
- Go/No-Go-Vorlage vorbereitet

### T-1h: Donnerstag, 6. März 2026, 09:00 CET

- Finaler Health-Check Staging und Production-Host
- Secrets-Verfügbarkeit bestätigt
- DNS, TLS und Logging bestätigt
- Freigabe durch Release Manager

### T-0: Donnerstag, 6. März 2026, 10:00 CET

1. `git checkout rc-2026-03-01`
2. Backend-Abhängigkeiten prüfen
3. Frontend neu bauen
4. Backend-Prozess neu starten
5. Reverse Proxy reloaden
6. Smoke-Tests fahren

### T+15min

- `/api/health` grün
- Public Startseite grün
- Kernflow Auth oder Public QR manuell geprüft

### T+24h

- Intensive Beobachtung beenden
- Incident- und Support-Lage auswerten
- Retrospektive terminieren

## Erfolgskriterien

- **Availability:** 99.0% im Monatsmittel, das entspricht ca. **7.2h** Ausfall pro Monat
- **API-Latenz p99:** < 2s
- **Error Rate:** < 0.5%
- **Rollback-Trigger:** > 1% 5xx für 15 Minuten oder ausgefallener Kernflow ohne kurzfristigen Fix

## Eskalation

Tragt vor T-24h verbindlich ein:

- Status-Kanal
- Incident-Kanal
- Primäre Rufnummern
- Entscheidungsbefugte Person für Rollback

Solange diese Angaben fehlen, ist die Dokumentation nur teilweise operativ.

## Nächste Schritte pro Rolle

### DevOps

- `docs/TASK_DEVOPS_INFRASTRUCTURE.md` abarbeiten
- `docs/14_DEPLOYMENT_GUIDE.md` gegen die reale Umgebung durchgehen

### Security

- `docs/TASK_SECURITY_SECRETS.md` abarbeiten
- `docs/16_SECRETS_MANAGEMENT.md` auf das gewählte Ablagemodell festziehen

### SRE

- `docs/TASK_SRE_MONITORING.md` abarbeiten
- `docs/15_MONITORING_INCIDENT_RESPONSE.md` mit echten Kontakten und Alarmkanälen füllen

### Release

- `docs/TASK_RELEASE_MANAGER_GOLIVE.md` abarbeiten
- tägliches Statusformat und Go/No-Go-Protokoll fixieren

**Go-Live Target:** 2026-03-06 10:00 CET  
**Freigegebenes Betriebsmodell:** Single-Node + SQLite + persistenter lokaler Storage
