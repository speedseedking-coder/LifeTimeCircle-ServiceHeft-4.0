# Deployment Guide – LifeTimeCircle Service Heft 4.0

Stand: **2026-03-01** (Europe/Berlin)

## Zweck
Dieses Dokument beschreibt, wie der Release Candidate `rc-2026-03-01` in eine produktive Umgebung deployt wird. Es ersetzt keine detaillierte Infrastruktur-Architektur, sondern enthält die grundlegenden Schritte und Entscheidungspunkte.

---

## 1) Deployment-Architektur (Entscheidung erforderlich)

Folgende Optionen müssen geklärt werden:

| Frage | Optionen | Status |
|-------|----------|--------|
| **Hosting-Plattform** | Heroku, AWS EC2, GCP Cloud Run, On-Premise, anderes | ⚠️ TBD |
| **API-Server** | FastAPI/Uvicorn direkt, Docker, Managed Service | ⚠️ TBD |
| **Frontend** | Static CDN, Vercel, Netlify, same-host | ⚠️ TBD |
| **Datenbank** | PostgreSQL managed (RDS, Cloud SQL), local, SQLite | ⚠️ TBD |
| **TLS/Domain** | Let's Encrypt, wildcard cert, automatisch erneuerbar? | ⚠️ TBD |

---

## 2) Voraussetzungen vor Deployment

### 2.1 Code & Release
- [ ] RC-Tag `rc-2026-03-01` ist gepusht
- [ ] Alle Gates sind grün (lokale Verifikation)
- [ ] CHANGELOG.md und Release-Notes aktuell

### 2.2 Infrastruktur
- [ ] Ziel-Domain festgelegt (z. B. `app.lifetimecircle.de` oder ähnlich)
- [ ] Produktionsumgebung benannt (z. B. `prod`, `production`)
- [ ] DNS-Einträge vorbereitet/bereit zum Schalten

### 2.3 Konfiguration
- [ ] Produktiver `LTC_SECRET_KEY` generiert (mind. 32 Zeichen, kryptographisch stark)
- [ ] weitere Secrets dokumentiert (siehe Abschnitt 3)
- [ ] Umgebungsvariablen für Prod konfiguriert

### 2.4 Datenbank
- [ ] Produktive DB-Instance vorbereitet
- [ ] Backup-Routine aktiviert
- [ ] Restore-Test durchgeführt
- [ ] Datenbankzugriff für API-Service konfiguriert

### 2.5 Monitoring & Logging
- [ ] Monitoring für API-Verfügbarkeit geplant (z. B. Uptime Robot, DataDog, New Relic)
- [ ] Error-/Crash-Reporting eingerichtet (z. B. Sentry)
- [ ] Logging konfiguriert (zentral, ohne PII-Leaks)

---

## 3) Secrets Management

### Neue Secrets für Prod erforderlich:

1. **LTC_SECRET_KEY** (Pflicht)
   - Länge: mind. 32 Zeichen
   - Zeichen: alphanumerisch + spezial, z. B. Ausgabe von `openssl rand -hex 32`
   - Speicherung: Secrets-Manager (GitHub Secrets, AWS Secrets Manager, Vault, etc.)
   - Rotation: Plan festlegen (z. B. quartalsweise)

2. **Database Password** (optional, abhängig von Setup)
   - Wenn separate Datenbank: Strong password
   - Speicherung: Secrets Manager, nicht im Code

3. **TLS/Certificate** (optional, abhängig von Setup)
   - Let's Encrypt automatisiert oder manuell?
   - Auto-Renewal konfigurieren

### Secrets NICHT im Code/Repo speichern:
- ✅ Github Actions: `${{ secrets.LTC_SECRET_KEY }}`
- ✅ Environment Variables (Server-Umgebung)
- ✅ Secrets Manager (AWS/GCP/Azure/Vault)
- ❌ `.env` Datei (außer lokal mit `.gitignore`)
- ❌ Hardcoded in Python/TypeScript

---

## 4) Deployment-Schritte (generisch)

### Phase 1: Code Preparation
```bash
# 1. Code auf Prod vorbereiten (vom Tag auschecken)
git clone <repo>
cd LifeTimeCircle-ServiceHeft-4.0
git checkout rc-2026-03-01

# 2. Dependencies installieren
cd server
poetry install --no-dev
cd ../packages/web
npm ci
npm run build
```

### Phase 2: Environment Setup
```bash
# 1. Secrets setzen (in Prod-Umgebung)
export LTC_SECRET_KEY="<generated-strong-secret>"
export DATABASE_URL="<prod-db-connection>"

# 2. Runtime-Verzeichnisse
mkdir -p /var/lib/lifetimecircle/{data,storage}
chmod -R 755 /var/lib/lifetimecircle
```

### Phase 3: Services Starten
```bash
# Backend (FastAPI/Uvicorn)
cd server
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend (statische Files via Web-Server, z. B. nginx oder einfach static host)
# Beispiel nginx config: siehe Anhang
```

### Phase 4: Health Check
```bash
# API Health
curl -X GET https://app.lifetimecircle.de/api/health

# Frontend
curl -X GET https://app.lifetimecircle.de/
```

---

## 5) Smoke Tests nach Deployment

Nach erfolgreichem Deploy diese Flows manuell oder per E2E-Test verifizieren:

1. [ ] Public Entry-Seite antwortet (→ `/`)
2. [ ] Auth-Flow starten (→ `/auth`)
3. [ ] Public QR-Route funktioniert (→ `/public/qr/:vehicle_id`)
4. [ ] Admin kann sich mit Step-up einloggen (→ `/admin`)
5. [ ] API-Health-Endpoint antwortet (→ `/api/health`)

Siehe auch `docs/98_WEB_E2E_SMOKE.md` für erweiterte Szenarien.

---

## 6) Rollback Plan

Bei kritischen Fehlern nach Deployment:

1. DNS auf alte Prod-Version zurückstellen (falls alte Version noch läuft)
2. oder: In die vorherige Container/Build-Version zurückkehren
3. oder: Database-Backup zurückspielen (falls nötig)

**Dokumentieren:**
- Wie lange ein Rollback dauert (RTO – Recovery Time Objective)
- Wie viel Datenverlust akzeptabel ist (RPO – Recovery Point Objective)
- Wer entscheidet Rollback und wie wird kommuniziert?

---

## 7) Monitoring & Alerting

Mindestens folgende Metriken überwachen:

| Metrik | Alert-Schwelle | Kanal |
|--------|-----------------|--------|
| **API Response Time** | > 5s | Slack/Email |
| **API Status Codes 5xx** | > 1% | Slack/Email |
| **Disk Space** | < 10% frei | Slack/Email |
| **Memory Usage** | > 80% | Slack/Email |
| **Database Connections** | > 90% pool | Slack/Email |
| **Frontend Load Time** | > 3s | Monitoring System |

---

## 8) Post-Deployment Betreuung

- **Hour 1:** Intensives Monitoring, ansprechbar sein
- **Hour 12:** Prüfe Logs auf Fehler, verifiziere Nightly-Backups
- **Tag 1–7:** Tägliche Checks, Feedback von Nutzern sammeln
- **Woche 2+:** Leichte Monitoring-Reduktion, aber Alerting aktiv

---

## 9) Anhänge

### nginx-Config Beispiel (statische Web + Reverse-Proxy)
```nginx
server {
    listen 443 ssl http2;
    server_name app.lifetimecircle.de;

    ssl_certificate /etc/letsencrypt/live/app.lifetimecircle.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.lifetimecircle.de/privkey.pem;

    # Frontend (static files)
    location / {
        root /var/www/lifetimecircle/web/dist;
        try_files $uri /index.html;
    }

    # API Proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Logging ohne PII
    access_log /var/log/nginx/app.access.log combined buffer=32k flush=5s;
}
```

### Referenzen
- `docs/12_RELEASE_CANDIDATE_2026-03-01.md`
- `docs/13_GO_LIVE_CHECKLIST.md`
- `docs/05_MAINTENANCE_RUNBOOK.md`
- `.github/workflows/ci.yml` (CI-Automatisierung als Referenz)
