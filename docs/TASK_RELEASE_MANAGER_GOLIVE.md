# Release Manager: Go-Live Orchestration & Stakeholder Freigaben

Stand: **2026-03-01** (Europe/Berlin)

**Owner:** Release Manager / Project Lead
**Deadline:** Bis **2026-03-05**
**Docs zum Lesen:** `docs/MASTER_GOLIVE_COORDINATION.md`, `docs/13_GO_LIVE_CHECKLIST.md`

## Ziel

Den Go-Live am **2026-03-06 10:00 CET** koordinieren, basierend auf dem jetzt freigegebenen Betriebsmodell:

- Single-Node
- SQLite
- persistenter lokaler Storage
- kein Architektur-Umbau in letzter Minute

## Checkliste

### 1. Stakeholder und Freigaben

- [ ] Business-Freigabe eingeholt
- [ ] Produkt-Freigabe eingeholt
- [ ] Security-Freigabe eingeholt
- [ ] DevOps-Freigabe eingeholt
- [ ] SRE-Freigabe eingeholt
- [ ] Support informiert

### 2. Operative Go/No-Go-Kriterien

- [ ] `rc-2026-03-01` bleibt freigegebener Stand
- [ ] Staging läuft mindestens **24 Stunden** stabil
- [ ] zentrale Gates grün
- [ ] Monitoring aktiv
- [ ] Rollback-Verantwortung benannt
- [ ] Incident-Kanal und Status-Kanal benannt

### 3. Kommunikation

- [ ] Go-Live-Timeline verteilt
- [ ] Support-Briefing durchgeführt
- [ ] kundenseitige Kommunikation vorbereitet, falls nötig
- [ ] Eskalationsliste mit echten Namen und Rufnummern gefüllt

## Freigabevorlage

```markdown
# Go-Live Approval – LifeTimeCircle

Datum: 2026-03-05
Release: rc-2026-03-01
Deploy-Zielbild: Single-Node + SQLite + persistenter lokaler Storage

- [ ] Product
- [ ] Security
- [ ] DevOps
- [ ] SRE
- [ ] Support

Go / No-Go: ______________________
Entscheider: _____________________
Zeitpunkt: _______________________
```

## T-Plan

### T-24h: 2026-03-05 10:00 CET

- Staging seit 24h stabil?
- Kontakte vollständig?
- On-Call bestätigt?
- Go/No-Go-Termin bestätigt?

### T-1h: 2026-03-06 09:00 CET

- letzter Statuscall
- offene Risiken benennen
- finale Freigabe dokumentieren

### T-0: 2026-03-06 10:00 CET

- Deploy starten lassen
- Statusführung übernehmen
- Zwischenstände dokumentieren

### T+24h

- Support-Lage auswerten
- Incident-Lage auswerten
- Retrospektive ansetzen

## Eskalation

Vor dem Go-Live müssen ersetzt sein:

- `[Status-Kanal]`
- `[Incident-Kanal]`
- `[Primär-On-Call]`
- `[Backup-On-Call]`
- `[Rollback-Entscheider]`

Mit Platzhaltern ist kein belastbarer Go-Live möglich.
