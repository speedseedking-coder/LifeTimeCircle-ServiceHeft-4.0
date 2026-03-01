# Codex-Übergabe: LifeTimeCircle Service Heft 4.0 – Operational Readiness

Stand: **2026-03-01 18:30 CET** (Europe/Berlin)

## Situation in 30 Sekunden

`rc-2026-03-01` ist technisch verifiziert. Zusätzlich wurden am 2026-03-01 zwei Dinge nachgezogen:

1. **sofortige Security-Härtung** für sensible Header-Fallbacks
2. **operative Korrektur** der Go-Live-Dokumente auf das realistisch deploybare Zielbild

Das freigegebene Zielbild für den geplanten Go-Live am **2026-03-06 10:00 CET** ist:

- Single-Node Production
- SQLite
- persistenter lokaler Storage
- Frontend statisch hinter Reverse Proxy

## Was neu wichtig ist

### Security

Diese Routen akzeptieren keine unkontrollierten `X-LTC-*`-Header mehr:

- `server/app/routers/documents.py`
- `server/app/routers/export_vehicle.py`

Regressionstest vorhanden:

- `server/tests/test_sensitive_routes_dev_header_gate.py`

### Operations

Die Go-Live-Dokumente wurden auf das reale Repo-Bild korrigiert:

- kein Pflichtpfad über RDS/PostgreSQL
- kein Pflichtpfad über Docker/ECS
- keine Pflicht für `boto3`-Secrets-Integration
- Staging-Minimum jetzt **24h stabil**, nicht 48h

## Wo stehen wir?

| Bereich | Status | Einordnung |
|--------|--------|------------|
| Code / RC | ✅ | verifiziert |
| Backend-Tests | ✅ | grün |
| Web-Build / E2E | ✅ | grün laut Session-Log |
| Security-Hotfix | ✅ | umgesetzt |
| Go-Live-Doku | ✅ | auf Single-Node-Zielbild korrigiert |
| Infrastruktur-Ausführung | 🔵 | offen |
| Secrets-Setup | 🔵 | offen |
| Monitoring / On-Call | 🔵 | offen |
| Business-Freigaben | 🔵 | offen |

## Lies diese Dokumente zuerst

1. `docs/MASTER_GOLIVE_COORDINATION.md`
2. `docs/14_DEPLOYMENT_GUIDE.md`
3. `docs/16_SECRETS_MANAGEMENT.md`
4. `docs/15_MONITORING_INCIDENT_RESPONSE.md`
5. das zu deiner Rolle passende `docs/TASK_*.md`

Ergänzend:

- `docs/GO_LIVE_BLOCKERS_AND_TARGET_STATE_2026-03-01.md`
- `docs/SESSION_LOGBUCH_2026-03-01.md`
- `docs/99_MASTER_CHECKPOINT.md`

## Kritischer Pfad

Bis **2026-03-03 EOD**:

- Host, Domain, TLS und persistente Pfade stehen
- `LTC_SECRET_KEY` ist gesetzt
- Staging läuft im gleichen Betriebsmodell wie Production

Bis **2026-03-04 EOD**:

- Staging mindestens 24h stabil
- Monitoring aktiv
- Rollback geklärt

Wenn diese Punkte offen bleiben, ist **2026-03-06** nicht belastbar.

## Für neue Bearbeiter

Wenn du DevOps machst:

- `docs/TASK_DEVOPS_INFRASTRUCTURE.md`

Wenn du Security machst:

- `docs/TASK_SECURITY_SECRETS.md`

Wenn du SRE machst:

- `docs/TASK_SRE_MONITORING.md`

Wenn du Release koordinierst:

- `docs/TASK_RELEASE_MANAGER_GOLIVE.md`

## Offene Risiken

- Kontakte, Alarmkanäle und Rufnummern sind in Teilen noch Platzhalter
- Production ist bis jetzt organisatorisch vorbereitet, aber noch nicht ausgeführt
- Ein später Architekturwechsel auf Postgres/Container ist ein separates Projekt, kein Day-0-Thema
