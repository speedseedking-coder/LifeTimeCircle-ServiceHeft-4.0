# SRE: Monitoring & On-Call-Rota Setup

Stand: **2026-03-01** (Europe/Berlin)

**Owner:** SRE-Lead / Ops-Lead
**Deadline:** Bis **2026-03-05**
**Docs zum Lesen:** `docs/15_MONITORING_INCIDENT_RESPONSE.md`

## Ziel

Monitoring und Incident-Bereitschaft für das reale Single-Node-Setup aufbauen. Was vor dem Go-Live zählt:

- Verfügbarkeit sehen
- Ausfälle schnell erkennen
- Rollback sauber entscheiden
- Rufbereitschaft benennen

Nicht erforderlich vor dem Go-Live:

- APM-Agenten in den Code einbauen
- Sentry/New Relic SDK integrieren
- PagerDuty erzwingen, wenn ein einfacheres Rufmodell ausreicht

## Checkliste

### 1. Monitoring aktivieren

- [ ] externer Health-Check für `https://<domain>/api/health`
- [ ] Host-Monitoring für CPU, RAM und Disk
- [ ] TLS-Ablaufwarnung
- [ ] Zugriff auf API-Logs und nginx-Logs

### 2. Alert-Schwellen festziehen

- [ ] API down: 3 Fehlchecks in Folge
- [ ] 5xx > 1% für 15 Minuten
- [ ] p99 > 2s für 10 Minuten
- [ ] Disk < 15% frei Warnung
- [ ] Disk < 10% frei kritisch

### 3. On-Call und Kommunikation

- [ ] Primär-On-Call benannt
- [ ] Backup-On-Call benannt
- [ ] Incident-Kanal festgelegt
- [ ] Status-Kanal festgelegt
- [ ] Rollback-Entscheider dokumentiert

### 4. Runbooks validieren

- [ ] API down
- [ ] Disk voll
- [ ] SQLite beschädigt oder gesperrt
- [ ] Frontend nicht erreichbar
- [ ] Secret-Rotation nach Incident

## Minimale Tool-Empfehlung

Für diesen Go-Live reicht eine Kombination aus:

- UptimeRobot, Better Stack oder Uptime Kuma für Health-Checks
- `systemd` + `journalctl` für API-Logs
- nginx-Access-/Error-Logs
- Host-Monitoring des Providers oder einfache Node-Checks

Wenn bereits vorhanden, kann natürlich ein größeres Tooling verwendet werden. Es ist aber kein Muss.

## Verifikation

### Laufende Checks

```bash
curl -fsS https://app.lifetimecircle.de/api/health
systemctl status lifetimecircle-api --no-pager
journalctl -u lifetimecircle-api -n 100 --no-pager
df -h /var/lib/lifetimecircle
```

### Vor dem Go-Live

- [ ] Test-Alarm ausgelöst und empfangen
- [ ] On-Call-Erreichbarkeit getestet
- [ ] Runbook für Rollback durchgesprochen
- [ ] Staging mindestens 24h beobachtet

## Deliverables bis 2026-03-05 EOD

- [ ] Monitoring-URLs dokumentiert
- [ ] Alarmkanäle dokumentiert
- [ ] Primär- und Backup-On-Call dokumentiert
- [ ] Runbook-Links dokumentiert
- [ ] Go-Live-Watchplan für T-0 bis T+24h dokumentiert
