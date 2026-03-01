# DevOps: Infrastruktur-Architektur – Aktionsplan

Stand: **2026-03-01** (Europe/Berlin)

**Owner:** DevOps-Lead / Infrastructure-Lead  
**Deadline:** Bis **2026-03-03**  
**Docs zum Lesen:** `docs/00_OPERATIONS_OVERVIEW.md`, `docs/14_DEPLOYMENT_GUIDE.md`

## Ziel für den 2026-03-06

Baue eine **Single-Node-Produktionsumgebung**, die exakt zum Ist-Code passt:

- ein Host
- nginx oder vergleichbarer Reverse Proxy
- `uvicorn app.main:app`
- SQLite auf persistentem Datenträger
- `server/data` und `server/storage` persistent angebunden

Nicht als Pflicht behandeln:

- Docker
- ECS/Kubernetes
- PostgreSQL/RDS
- neue CI/CD-Pipeline

## Checkliste

### 1. Host und Netz

- [ ] Zielhost bereitgestellt
- [ ] SSH-/Admin-Zugang geprüft
- [ ] Domain zeigt auf Host
- [ ] Port 443 erreichbar
- [ ] TLS-Zertifikat aktiv oder beantragt

### 2. Persistenz

- [ ] `/var/lib/lifetimecircle/data` angelegt
- [ ] `/var/lib/lifetimecircle/storage` angelegt
- [ ] `server/data` auf persistentes `data` verlinkt
- [ ] `server/storage` auf persistentes `storage` verlinkt
- [ ] Schreibtest und Neustart-Test durchgeführt

### 3. Runtime

- [ ] Repo auf Zielhost ausgecheckt
- [ ] `rc-2026-03-01` aktiviert
- [ ] `poetry install` in `server/` erfolgreich
- [ ] `npm ci && npm run build` in `packages/web/` erfolgreich
- [ ] `systemd`-Service für API angelegt
- [ ] Reverse Proxy konfiguriert

### 4. Staging und Production

- [ ] Staging nutzt dasselbe Betriebsmodell wie Production
- [ ] `/api/health` extern erfolgreich
- [ ] `/health` intern erfolgreich
- [ ] Frontend-Startseite erfolgreich

### 5. Backups

- [ ] Backup oder Snapshot für `/var/lib/lifetimecircle` definiert
- [ ] Restore-Probe dokumentiert

## Minimaler Deploy-Ablauf

```bash
cd /opt/lifetimecircle/app
git checkout rc-2026-03-01

cd server
poetry install

cd ../packages/web
npm ci
npm run build
rsync -a --delete dist/ /var/www/lifetimecircle/web/dist/

systemctl restart lifetimecircle-api
systemctl reload nginx

curl -fsS https://app.lifetimecircle.de/api/health
```

## Deliverables bis 2026-03-03 EOD

- [ ] Hostname / IP / Domain dokumentiert
- [ ] Pfadmodell dokumentiert
- [ ] systemd-Unit dokumentiert
- [ ] Reverse-Proxy-Konfiguration dokumentiert
- [ ] Backup-Mechanismus dokumentiert
- [ ] Staging-URL an Security, SRE und Release kommuniziert

## Wenn mehr Architektur gewünscht ist

Falls Product oder Management auf PostgreSQL, Container oder Secret-Manager-Integration besteht:

- als **separates Architekturprojekt** aufnehmen
- nicht in diesen Go-Live pressen
- Go-Live-Termin neu verhandeln
