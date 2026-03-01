# Security: Production Secrets & Rotation

Stand: **2026-03-01** (Europe/Berlin)

**Owner:** Security-Lead
**Deadline:** Bis **2026-03-03**
**Docs zum Lesen:** `docs/16_SECRETS_MANAGEMENT.md`, `docs/14_DEPLOYMENT_GUIDE.md`

## Ziel

Sichere, dokumentierte und überprüfbare Secrets für das reale Go-Live-Modell:

- `LTC_SECRET_KEY`
- `LTC_DATABASE_URL`
- `LTC_DB_PATH`
- TLS-Zertifikat / Private Key

Kein Pflichtziel für diesen Go-Live:

- App-Code auf `boto3` umbauen
- neue Cloud-IAM-Integration
- neue GitHub-Deploy-Pipeline

## Checkliste

### 1. Secret-Erzeugung

- [ ] `LTC_SECRET_KEY` mit mindestens 32 Zeichen erzeugt
- [ ] Werte nicht in Tickets, Chats oder Markdown-Dateien abgelegt
- [ ] Verantwortliche Person und Erstellungsdatum dokumentiert

Empfohlen:

```bash
openssl rand -hex 32
```

### 2. Sichere Ablage

- [ ] Passwortmanager oder gleichwertige geschützte Ablage gewählt
- [ ] Produktions-Env-Datei nur mit restriktiven Dateirechten
- [ ] Zugriff auf Host und Env-Datei dokumentiert

### 3. Produktionswerte festziehen

- [ ] `LTC_ENV=prod`
- [ ] `LTC_SECRET_KEY=<redacted>`
- [ ] `LTC_DATABASE_URL=sqlite+pysqlite:////var/lib/lifetimecircle/data/app.db`
- [ ] `LTC_DB_PATH=/var/lib/lifetimecircle/data/app.db`

### 4. Verifikation

- [ ] API startet mit gesetzten Werten
- [ ] `/api/health` ist erreichbar
- [ ] Security bestätigt, dass keine Dev-Secrets produktiv genutzt werden

## Prüfschritte

### Rechte der Env-Datei

```bash
ls -l /etc/lifetimecircle/api.env
```

Erwartung:

- kein world-readable
- nur Admins oder definierter Service-Account mit Zugriff

### Startprüfung

```bash
systemctl restart lifetimecircle-api
systemctl status lifetimecircle-api --no-pager
curl -fsS https://app.lifetimecircle.de/api/health
```

## Rotation

### Vor dem Go-Live festlegen

- [ ] Wer darf rotieren?
- [ ] Wer darf freigeben?
- [ ] Wie wird der API-Restart durchgeführt?
- [ ] Wer wird im Incident informiert?

### Standardprozess

1. neues Secret erzeugen
2. Env-Datei aktualisieren
3. API neu starten
4. Health-Check fahren
5. Incident- oder Wartungsprotokoll ergänzen

## Notfallprozess

Wenn `LTC_SECRET_KEY` oder Host-Zugang kompromittiert ist:

1. Secret sofort ersetzen
2. API sofort neu starten
3. Zugriffsrechte prüfen
4. Incident eröffnen
5. Root Cause dokumentieren

## Deliverables bis 2026-03-03 EOD

- [ ] Secret-Ablagemodell dokumentiert
- [ ] Verantwortlichkeiten dokumentiert
- [ ] Produktions-Env geprüft
- [ ] Rotationsprozess dokumentiert
- [ ] Notfallkontakt ergänzt
