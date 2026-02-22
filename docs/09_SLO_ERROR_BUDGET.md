# LifeTimeCircle – SLO & Error Budget (Entwurf v1)
Stand: 2026-02-22

## Ziel
Definiert erste, messbare Betriebsziele für Availability, Latenz, Error-Rate sowie Wiederanlauf/Recovery (RPO/RTO), vendor-neutral und no-PII-konform.

## SLOs (monatlich)

1) **API Availability (kritische Endpunkte): 99.9%**
- Scope: Auth, Consent-Gate, Vehicles, Upload, Export-Metadaten, Public QR.
- Messung: erfolgreiche Requests / Gesamtrequests je Endpoint-Gruppe.

2) **Latency p95**
- Auth/Consent-Endpunkte: <= 300 ms
- Lese-Endpunkte (Vehicles/Public QR): <= 500 ms
- Schreib-Endpunkte (Upload-Metadaten/Statuswechsel): <= 800 ms

3) **Server Error Rate (5xx): < 0.5%**
- Scope: alle produktiven API-Routen.
- Separat beobachten: 401/403 (Sicherheits-/Policy-indikativ, nicht automatisch SLO-Verstoß).

4) **Export-Job Erfolgsquote: >= 99.0%**
- Scope: asynchrone/synchrone Export-Erstellung inkl. TTL-Handling.
- Fehler: Job fehlgeschlagen oder Artefakt nicht fristgerecht verfügbar.

5) **Public QR Availability: 99.9%**
- Scope: öffentliche QR-Aufrufe (datenarm, no-PII).

## Error Budget (monatlich)
- Bei 99.9% Availability entspricht das 0.1% Downtime.
- Beispielwerte nach Monatslänge:
  - 30 Tage: 43m 12s
  - 31 Tage: 44m 38s
- Praktisch entspricht das ungefähr 43–45 Minuten/Monat.
- Budget-Verbrauch > 50% in der ersten Monatshälfte:
  - Fokus auf Stabilitätsmaßnahmen, Feature-Risiko reduzieren.
- Budget-Verbrauch >= 100%:
  - temporärer Feature-Freeze für riskante Änderungen,
  - nur Security-/Stabilitäts-Fixes bis Rückkehr in Budget.

## RPO/RTO (Entwurf, konkret aber vorläufig)
- **RPO:** <= 15 Minuten für transaktionale Kerndaten.
- **RTO:** <= 60 Minuten bis Wiederherstellung kritischer Kernrouten.
- Gilt für: Auth, Consent, Vehicles, Upload-Metadaten, Export-Metadaten, Public QR Basisfunktion.

## Messpunkte und Korrelation

### Endpoint-/Job-Gruppen
- Auth: Login/Token-Flow, Session-nahe Prüfungen.
- Consent: Consent lesen/setzen, Gate-Wirksamkeit.
- Vehicles/Core: geschützte Kernrouten.
- Upload: Annahme, Quarantäne-Status, Freigabe-Übergänge.
- Export: Erstellung, Bereitstellung, TTL-Löschung.
- Public QR: öffentliche Lesepfade.

### Security Telemetry (D-033, Allowlist, no-PII)
- `request_id`
- `status_code`
- `route_template`
- `role_category`
- `event_type`

### Ops-Metriken / Access-Logs (no-PII)
- `timestamp`
- `method`
- `latency_ms`

Hinweis:
- Diese Ops-Felder sind nicht automatisch Teil der Security Telemetry.
- Aufnahme in Security Telemetry erfordert Allowlist-Review/Decision (deny-by-default).

### Korrelation
- `request_id` ist Primärschlüssel für Request-Korrelation über:
  - API-Access-Log
  - Security-Telemetry
  - Job-Trigger/Job-Result-Log (falls Request-initiiert)
- Keine Korrelation über PII, Tokens oder Rohpayloads.

## Auslöser für operative Maßnahmen
- p95-Latenz 2 Intervalle in Folge über Ziel: Incident-Triage + Last-/DB-Analyse.
- 5xx-Rate über 0.5%: sofortige Ursachenanalyse, Rollback/Hotfix prüfen.
- Wiederkehrende 401/403-Anomalien: RBAC-/Consent-Gates und Missbrauchssignale prüfen.
- TTL-Löschfehler: Export-Auslieferung temporär einschränken bis TTL-Konformität wiederhergestellt ist.

## Bezug zu SoT-Entscheidungen
- D-010 Consent blockierend/versioniert.
- D-016 und D-024 TTL für Exporte/PDFs.
- D-033 no-PII Telemetry + Request-ID + Redaction.