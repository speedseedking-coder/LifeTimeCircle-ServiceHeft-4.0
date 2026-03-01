# Deployment Guide – LifeTimeCircle Service Heft 4.0

Stand: **2026-03-01** (Europe/Berlin)

## Zweck

Dieses Dokument beschreibt den **realisierbaren** Produktionspfad für `rc-2026-03-01`. Stand heute ist der belastbare Pfad:

- ein einzelner Linux-Host oder eine VM
- nginx oder vergleichbarer Reverse Proxy
- FastAPI/Uvicorn direkt aus dem Repo
- SQLite auf persistentem Datenträger
- Frontend als statischer Build

## Zielarchitektur für den Go-Live

| Baustein | Vorgabe am 2026-03-06 |
|---------|------------------------|
| **Host** | 1 VM / 1 Server |
| **Backend** | `poetry run uvicorn app.main:app` |
| **Frontend** | `packages/web/dist` hinter nginx |
| **DB** | SQLite |
| **Datei-Storage** | persistente lokale Verzeichnisse |
| **TLS** | Let's Encrypt oder vorhandenes Zertifikat |

Nicht Teil des Pflichtpfads für den Go-Live:

- RDS/PostgreSQL
- ECS/Kubernetes
- Docker-basierte Deployments
- App-seitige `boto3`-Secrets-Integration

## Voraussetzungen

### Code

- `rc-2026-03-01` ist verfügbar
- Backend-Tests und Web-Build sind grün
- keine offenen P0-Fehler

### Host

- Domain zeigt auf den Zielhost
- Port 443 erreichbar
- ausreichend Disk für `data` und `storage`
- regelmäßige Host-Backups oder Dateisystem-Snapshots konfiguriert

### Pflicht-Konfiguration

- `LTC_SECRET_KEY=<32+ Zeichen>`
- `LTC_ENV=prod`
- `LTC_DATABASE_URL=sqlite+pysqlite:////var/lib/lifetimecircle/data/app.db`
- `LTC_DB_PATH=/var/lib/lifetimecircle/data/app.db`

## Verzeichnislayout

Empfohlene Aufteilung:

```text
/opt/lifetimecircle/app                    # Repo-Checkout
/var/lib/lifetimecircle/data               # persistente SQLite-Dateien
/var/lib/lifetimecircle/storage            # persistente Upload-Dateien
/var/www/lifetimecircle/web/dist           # statische Web-Dateien
/etc/lifetimecircle/api.env                # geschützte Env-Datei
```

Wichtig: Der aktuelle Code erwartet `server/data` und `server/storage`. Deshalb vor dem ersten Start:

```bash
mkdir -p /var/lib/lifetimecircle/data /var/lib/lifetimecircle/storage
rm -rf /opt/lifetimecircle/app/server/data
rm -rf /opt/lifetimecircle/app/server/storage
ln -s /var/lib/lifetimecircle/data /opt/lifetimecircle/app/server/data
ln -s /var/lib/lifetimecircle/storage /opt/lifetimecircle/app/server/storage
```

## Deployment-Schritte

### 1. Checkout und Build

```bash
git clone <repo-url> /opt/lifetimecircle/app
cd /opt/lifetimecircle/app
git checkout rc-2026-03-01

cd server
poetry install

cd ../packages/web
npm ci
npm run build
```

### 2. Env-Datei anlegen

```bash
cat >/etc/lifetimecircle/api.env <<'EOF'
LTC_ENV=prod
LTC_SECRET_KEY=<REDACTED_32_PLUS_CHARS>
LTC_DATABASE_URL=sqlite+pysqlite:////var/lib/lifetimecircle/data/app.db
LTC_DB_PATH=/var/lib/lifetimecircle/data/app.db
EOF

chmod 600 /etc/lifetimecircle/api.env
```

### 3. Backend per systemd starten

```ini
[Unit]
Description=LifeTimeCircle API
After=network.target

[Service]
WorkingDirectory=/opt/lifetimecircle/app/server
EnvironmentFile=/etc/lifetimecircle/api.env
ExecStart=/usr/bin/env poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4. Frontend ausliefern

```bash
mkdir -p /var/www/lifetimecircle/web
rsync -a --delete /opt/lifetimecircle/app/packages/web/dist/ /var/www/lifetimecircle/web/dist/
```

### 5. nginx konfigurieren

```nginx
server {
    listen 443 ssl http2;
    server_name app.lifetimecircle.de;

    ssl_certificate /etc/letsencrypt/live/app.lifetimecircle.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.lifetimecircle.de/privkey.pem;

    location / {
        root /var/www/lifetimecircle/web/dist;
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Verifikation

### Technisch

```bash
systemctl restart lifetimecircle-api
systemctl status lifetimecircle-api --no-pager
curl -fsS http://127.0.0.1:8000/health
curl -fsS https://app.lifetimecircle.de/api/health
```

### Smoke-Tests

- Public Startseite lädt
- Auth-Startseite lädt
- Public-QR-Route lädt
- Admin-Login startet
- Dokument-Upload-Pfad schreibt Dateien auf persistenten Storage

## Rollback

Wenn der Deploy fehlschlägt:

1. `git checkout <letzter_stabiler_tag>`
2. Frontend erneut bauen und nach `/var/www/lifetimecircle/web/dist/` synchronisieren
3. `systemctl restart lifetimecircle-api`
4. `curl https://app.lifetimecircle.de/api/health`

Nur wenn Daten beschädigt sind:

1. Host-Snapshot oder Dateisystem-Backup zurückspielen
2. Integrität von `/var/lib/lifetimecircle/data/app.db` und `/var/lib/lifetimecircle/data/documents.sqlite` prüfen

## Mindest-Monitoring

- Health-Check alle 1 Minute
- 5xx-Rate alarmieren ab > 1% für 15 Minuten
- Disk-Warnung ab < 15% frei
- Disk-kritisch ab < 10% frei
- TLS-Ablaufwarnung 14 Tage vorher

## Referenzen

- `docs/MASTER_GOLIVE_COORDINATION.md`
- `docs/15_MONITORING_INCIDENT_RESPONSE.md`
- `docs/16_SECRETS_MANAGEMENT.md`
