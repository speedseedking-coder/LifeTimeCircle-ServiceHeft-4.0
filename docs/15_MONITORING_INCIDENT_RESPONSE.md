# Monitoring & Incident Response – LifeTimeCircle Service Heft 4.0

Stand: **2026-03-01** (Europe/Berlin)

## Zweck
Dieses Dokument definiert, wie wir die Anwendung in der Produktion überwachen und auf Fehler reagieren.

---

## 1) Monitoring Strategie

### 1.1 Überwachte Komponenten

| Komponente | Metriken | Tool | Alert-Level |
|------------|----------|------|-------------|
| **API (FastAPI)** | Response time, Error rate (5xx), Request rate | New Relic / DataDog / Prometheus | 🔴 Kritisch |
| **Frontend (React/Web)** | Page load time, JS errors, API fetch failures | Sentry / LogRocket / Honeycomb | 🟡 Warnung |
| **Datenbank** | Connection count, Query time, Disk usage | Native DB monitoring | 🔴 Kritisch |
| **Infrastruktur** | CPU, Memory, Disk, Network I/O | CloudWatch / Stackdriver / Prometheus | 🟡 Warnung |
| **TLS/SSL** | Certificate expiry | Monitoring tool | 🔴 Kritisch (7 Tage vorher alert) |

### 1.2 SLO (Service Level Objectives)

Ziel: Definieren, was „healthy" ist.

| Metrik | Ziel |
|--------|------|
| **Availability** | 99.0% (max 7.2h Downtime/Monat) |
| **Latency (p50)** | < 200ms |
| **Latency (p99)** | < 2000ms |
| **Error Rate** | < 0.1% |

---

## 2) Alert-Regeln

### 🔴 Kritische Alerts (sofort handeln)

```
1. API Error Rate > 1% für > 5 Min
   → Handeln: Server-Logs prüfen, ggf. Incident öffnen
   
2. API Response Time p99 > 5s für > 5 Min
   → Handeln: Datenbank/Load überprüfen, Traffic-Spikes?
   
3. Database Connections > 90% Pool
   → Handeln: Connections auslisten, evtl. Rollback
   
4. Disk Space < 5% verfügbar
   → Handeln: Backup-Logs löschen oder Rollback
   
5. TLS Certificate expires in < 7 Tage
   → Handeln: Erneuerung triggern oder manuell renew
```

### 🟡 Warnungen (beobachten, ggf. handeln)

```
6. Memory Usage > 85% für > 10 Min
   → Handeln: Prozesse überprüfen, OOM-Killer wird aktiv
   
7. Page Load Time > 3s (Frontend)
   → Handeln: Caching überprüfen, ggf. Static Files optimieren
   
8. 4xx Error Rate > 1% (z. B. viele 404/403)
   → Handeln: API-Verträge überprüfen, ggf. Client-Bug
```

---

## 3) Incident Response Runbook

### 3.1 Erste Schritte (jedes Incident)

```
1. Alert empfangen / Nutzer-Report
   → Zeitstempel dokumentieren
   
2. Nagios/PagerDuty / Slack abgleichen
   → Welche Komponente ist down?
   → Ist es ein echtes Problem oder False Positive?
   
3. Entscheiden: Handeln oder nur monitoren?
   → Wenn User-impactend: Sofort handeln
   → Wenn System-nur: Erstmal logs sammeln
```

### 3.2 Incident-Kategorien

#### Kategorie A: API Down / 5xx Storm
```
Erkennungszeichen: Error Rate > 5% oder API antwortet gar nicht
Verantwortlicher: Backend-Team

Erste Aktionen:
1. curl -X GET https://app.lifetimecircle.de/api/health
2. SSH in Prod-Server: top, ps aux | grep uvicorn
3. Server-Logs: tail -f /var/log/lifetimecircle/api.log
4. Datenbank-Verbindungen: SELECT COUNT(*) FROM pg_stat_activity;

Falls API läuft aber Fehler:
- Logs nach Exception suchen
- Ggf. Secrets/Config überprüfen
- Ggf. Datenbank-Verbindung testen

Fallback: Rollback zu rc-2026-03-01 (oder letzte stabile)
siehe Abschnitt 4
```

#### Kategorie B: Datenbank Performance
```
Erkennungszeichen: Query time > 5s, Connections > 90%
Verantwortlicher: DBA / Infrastructure-Team

Erste Aktionen:
1. SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;
2. Langsame Queries identifizieren
3. VACUUM ANALYZE falls nötig
4. Ggf. Connection Pool kurz erhöhen: max_connections

Fallback: Read-Replica upgraden oder Read-only Modus
```

#### Kategorie C: Frontend Fehler / Weiße Seite
```
Erkennungszeichen: Page load > 3s, JS Fehler in Sentry
Verantwortlicher: Frontend-Team

Erste Aktionen:
1. Browser-DevTools öffnen: Network-Tab, Console
2. CDN/Static Host-Status überprüfen
3. Sentry-Fehler analysieren (Stack Traces)
4. Ggf. Browser-Cache leeren

Fallback: Frontend zu alter Version rollback
```

#### Kategorie D: Sicherheits-Incident
```
Erkennungszeichen: Unerwartete Auth-Fehler, Login-Spam, Exploit-Versuche
Verantwortlicher: Security-Team + Backend

Erste Aktionen:
1. Logs auf verdächtige IPs/Patterns überprüfen
2. ggf. IP-Blocking aktivieren
3. LTC_SECRET_KEY ggf. rotieren (wenn kompromittiert)
4. Audit-Logs überprüfen

Notfall-Kontakt: Inform...@example.com oder Slack #security
```

### 3.3 Notification & Eskalation

```
Level 1 (Alert)
→ System sendet Slack/Email

Level 2 (Im Incident)
→ Automatisches Paging: auf-Ruf bei On-call
→ Slack #incidents Kanal
→ Timeline dokumentieren

Level 3 (Kritischer Fehler, > 1h)
→ Manager/Lead informieren
→ Kunden ggf. proaktiv informieren
→ Post-Mortem ansetzen
```

---

## 4) Rollback Procedure

### 4.1 Schneller Rollback (< 5 Min)

**Szenario:** Neuer Code ist buggy, sofort zurück zur letzten stabilen Version.

```bash
# 1. Alte Version vorbereiten (sollte parallel bereit sein)
git checkout rc-2026-02-28  # oder letzte stabile

# 2. Infrastructure umschalten
# Option A: Docker-Image zurück
docker service update --image registry.example.com/lifetimecircle:rc-2026-02-28 api

# Option B: Git-Deploy (einfach)
git pull
./deploy.sh rc-2026-02-28

# 3. Health-Check
curl -X GET https://app.lifetimecircle.de/api/health
# → Expect: 200 OK

# 4. Smoke-Test
cd packages/web
npm run e2e -- --grep "public contact"
```

### 4.2 Datenbank-Rollback (falls nötig)

```sql
-- Erst: Backup der neuen DB machen
pg_dump -U admin prod_db > /backups/prod_db_2026-03-01_backup.sql

-- Restore von letztem Snapshot
-- (Abhängig von deinem Backup-Tool)
# AWS RDS: Restore to Point-in-Time
# GCP: Restore snapshot
# On-Premise: restore_from_backup.sh

-- Nach Restore:
SELECT pg_database.datname, 
       pg_size_pretty(pg_database_size(pg_database.datname)) 
FROM pg_database;
```

### 4.3 Post-Rollback

```
1. Verify: Alle Gates sind grün
   npm run build
   npm run e2e
   
2. Analyze: Was ist schiefgelaufen?
   git log --oneline HEAD..rc-2026-03-01 (shows what we rolled back)
   grep ERROR /var/log/lifetimecircle/api.log > incident_log_2026-03-01.txt
   
3. Fix & Test lokal
   → PR mit Fix erstellen
   → Code Review + lokale Tests
   → Neues Release vorbereiten
   
4. Redeploy: Vorsichtig & mit Monitoring
```

---

## 5) Logging & Log Retention

### 5.1 Was wird geloggt?

```
API (Server)
├─ Request: Method, Path, Status, Response-Time
├─ Error: Exception Type, Message, Stack Trace
├─ Auth: User-ID (ohne Passwort/Token), Login-Versuch Status
└─ Audit: Admin-Aktionen (wer, was, wann)

Frontend (JavaScript)
├─ Console Errors (uncaught exceptions)
├─ API Errors (failed fetch)
├─ User Actions (page views, button clicks) – OPTIONAL
└─ Performance (page load time, FCP, LCP)

Infrastruktur
├─ System: CPU, Memory, Disk usage
├─ Network: Request rate, Latency
└─ TLS: Certificate info, renewal status
```

### 5.2 Log Retention Policy

```
Logs älter als 90 Tage → Archive zu S3/GCS
Logs älter als 1 Jahr → Löschen (oder rechtliche Anforderung prüfen)

Sensitive Logs (z. B. Full Tokens, PII):
→ Nicht speichern oder anonymisieren
→ Audit-Logs separat mit höherem Zugriffslevel
```

### 5.3 Log Aggregation (optional, aber empfohlen)

Zentrales Logging mit:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- oder Datadog
- oder New Relic APM

Vorteile:
- Unified Search über alle Logs
- Alerting on Log Patterns
- Trends erkennen

---

## 6) Notfall-Kontakte

```
On-Call Schedule (TBD):
- Backend Lead: <name>, <phone>, <Slack>
- Frontend Lead: <name>, <phone>, <Slack>
- Infrastructure: <name>, <phone>, <Slack>
- Manager: <name>, <phone>, <Slack>

Eskalation:
- Level 1: Automatischer Paging (On-Call)
- Level 2: Manager (> 30 Min ungelöst)
- Level 3: Director (> 1h ungelöst oder kritisch)

Status-Page / Incident-Kommunikation:
- Public: https://status.lifetimecircle.de
- Internal: Slack #incidents
- Customers: Email (optional)
```

---

## 7) Post-Incident Review

Nach jedem Incident > 15 Minuten:

```
1. Zeitlinie dokumentieren (was passierte wann?)
2. Root-Cause analysieren
3. Action Items ableiten (wie verhindern wir das nächste Mal?)
4. Post-Mortem Meeting (24-48h später)
5. Lessons Learned dokumentieren
```

### Post-Mortem Template

```
Incident: [Kurzbeschreibung]
Zeit: [Start – Ende]
Impact: [#  Nutzer, wie lange, Geschäfts-Effekt]

Timeline:
- HH:MM: Alert
- HH:MM: Investigation started
- HH:MM: Root cause identified
- HH:MM: Fix deployed
- HH:MM: Verified

Root Cause: [Was ist tatsächlich passiert?]

Action Items:
- [ ] Monitorung verbessern (wer, wann)
- [ ] Code-Review strenger (wer, wann)
- [ ] Documentation aktualisieren (wer, wann)
```

---

## 8) Referenzen

- `docs/05_MAINTENANCE_RUNBOOK.md` (lokal)
- `docs/14_DEPLOYMENT_GUIDE.md` (infrastruktur)
- `.github/workflows/ci.yml` (CI als reference)
- Monitoring Tool Doku (je nach Plattform)
