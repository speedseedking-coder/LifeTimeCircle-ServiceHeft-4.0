# Monitoring & Incident Response – LifeTimeCircle Service Heft 4.0

Stand: **2026-03-01** (Europe/Berlin)

## Zweck

Dieses Dokument beschreibt Monitoring und Incident Response für das **tatsächliche Go-Live-Setup**:

- ein einzelner Host
- nginx vor FastAPI/Uvicorn
- SQLite-Dateien auf persistentem Storage
- Upload-Dateien auf persistentem Storage

## Monitoring-Strategie

### Pflicht-Komponenten

| Komponente | Was überwachen | Mindest-Tooling |
|-----------|----------------|-----------------|
| **API** | `/api/health`, 5xx, Latenz | externer Health-Check + Logs |
| **Host** | CPU, RAM, Disk | Host-Monitoring oder einfache Systemchecks |
| **SQLite / Storage** | Dateiexistenz, Disk-Füllstand, Dateisystem-Fehler | Host-Monitoring |
| **TLS** | Zertifikatsablauf | TLS-Ablaufwarnung |
| **Frontend** | Startseite lädt, Kernflow erreichbar | synthetischer Browser- oder HTTP-Check |

### SLOs

| Metrik | Ziel |
|--------|------|
| **Availability** | 99.0% |
| **Latency p99** | < 2000ms |
| **Error Rate** | < 0.5% |

99.0% Availability entsprechen rund **7.2 Stunden** Ausfall pro Monat.

## Alert-Regeln

### Kritisch

1. `/api/health` fällt 3 Checks in Folge aus
2. 5xx-Rate > 1% für 15 Minuten
3. Disk frei < 10%
4. API-Prozess beendet oder restartet wiederholt
5. TLS-Zertifikat läuft in weniger als 14 Tagen ab

### Warnung

1. p99-Latenz > 2s für 10 Minuten
2. Memory > 85% für 10 Minuten
3. Disk frei < 15%
4. ungewöhnlicher Anstieg von 4xx-Fehlern

## Incident-Ablauf

### Sofortmaßnahmen

1. Zeitpunkt und Symptom notieren
2. Externen Health-Check prüfen
3. API-Prozessstatus prüfen
4. aktuelle Logs prüfen
5. entscheiden: fixen oder rollbacken

### Standard-Kommandos

```bash
curl -fsS https://app.lifetimecircle.de/api/health
systemctl status lifetimecircle-api --no-pager
journalctl -u lifetimecircle-api -n 200 --no-pager
df -h /var/lib/lifetimecircle
```

## Incident-Kategorien

### A. API down oder 5xx-Sturm

```bash
curl -fsS https://app.lifetimecircle.de/api/health
systemctl restart lifetimecircle-api
journalctl -u lifetimecircle-api -n 200 --no-pager
```

Prüfen:

- `LTC_SECRET_KEY` gesetzt?
- API startet mit `app.main:app`?
- Reverse Proxy leitet `/api/` korrekt auf `/` um?

### B. Datenbank- oder Dateisystemproblem

```bash
sqlite3 /var/lib/lifetimecircle/data/app.db "PRAGMA integrity_check;"
sqlite3 /var/lib/lifetimecircle/data/documents.sqlite "PRAGMA integrity_check;"
ls -lah /var/lib/lifetimecircle/data
ls -lah /var/lib/lifetimecircle/storage
df -h /var/lib/lifetimecircle
```

Prüfen:

- Dateisystem voll?
- Symlink von `server/data` und `server/storage` intakt?
- SQLite-Dateien beschädigt oder gesperrt?

### C. Frontend lädt nicht

```bash
curl -I https://app.lifetimecircle.de/
ls -lah /var/www/lifetimecircle/web/dist
nginx -t
systemctl reload nginx
```

### D. Security-Incident

- auffällige Header- oder Auth-Muster prüfen
- Logs auf ungewöhnliche IPs oder Pfade prüfen
- `LTC_SECRET_KEY` rotieren, falls kompromittiert
- Release Manager und Security-Verantwortliche sofort informieren

## Rollback

Rollback ist erforderlich, wenn:

- 5xx-Rate > 1% für 15 Minuten bleibt
- Kernflow nicht funktioniert und nicht in 15 Minuten behoben werden kann
- Datenintegrität gefährdet ist

### Ablauf

```bash
cd /opt/lifetimecircle/app
git checkout <letzter_stabiler_tag>

cd packages/web
npm ci
npm run build
rsync -a --delete dist/ /var/www/lifetimecircle/web/dist/

cd ../../server
poetry install
systemctl restart lifetimecircle-api
curl -fsS https://app.lifetimecircle.de/api/health
```

Wenn SQLite-Dateien betroffen sind:

1. aktuelle Dateien sichern
2. Host- oder Dateisystem-Backup zurückspielen
3. Integritätscheck erneut fahren

## Kommunikationspflicht

Vor dem Go-Live müssen ergänzt sein:

- Incident-Kanal
- Status-Kanal
- Primär-On-Call
- Backup-On-Call
- Rollback-Entscheider

Platzhalter in diesem Dokument sind bis dahin zu ersetzen.
