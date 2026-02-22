# LifeTimeCircle – Production Baseline (Phase 1 / Week 1–2)
Stand: 2026-02-22

## Zweck und Scope
Dieses Dokument definiert den minimalen Betriebs- und Sicherheitsstandard für `dev`, `staging`, `prod`.
Bindend sind deny-by-default, least privilege, serverseitiges RBAC, object-level checks und strikt no-PII in Logs/Responses/Exports/Telemetry.

## Environments

### dev
- Zweck: lokale Entwicklung, reproduzierbare Tests.
- Debug/OpenAPI: erlaubt.
- Daten: synthetisch oder anonymisiert, keine realen personenbezogenen Daten.
- Secrets: lokal gesetzt, niemals committet.

### staging
- Zweck: produktionsnahe Verifikation vor Rollout.
- Debug/OpenAPI: restriktiv, möglichst wie prod.
- Daten: anonymisiert/synthetisch, keine realen Secrets in Testdaten.
- Gates: RBAC/Consent/Export-TTL/Upload-Quarantäne müssen aktiv sein.

### prod
- Zweck: Produktivbetrieb.
- Debug/OpenAPI: deaktiviert.
- Security-Policies vollständig aktiv.
- Logging/Telemetry strikt no-PII mit Redaction.

## Konfigurationsparameter (Beispiele; Namen nur nennen, wenn im Repo real genutzt)

Im Repo nachweisbar genutzte Parameter:
- `LTC_ENV` (z. B. `dev`/`staging`/`prod`, falls im jeweiligen Startprofil gesetzt)
- `LTC_SECRET_KEY` (Mindestlänge >=16, Zielwert >=32)
- `LTC_DB_PATH` (je Umgebung isoliert)
- `LTC_EXPORT_TTL_SECONDS` (TTL-Steuerung für Export-Artefakte)
- `LTC_EXPORT_MAX_USES` (Nutzungsbegrenzung für Export-Artefakte)

Weitere Parameter abstrahiert halten:
- Datenbank-Verbindung (URL/DSN/Pfad je Umgebung isoliert)
- Storage-Pfad/Bucket je Umgebung isoliert

Regeln:
- Keine Secrets in Beispiel-Dateien mit echten Werten.
- Keine Shared-Secrets zwischen `staging` und `prod`.
- Keine Klartext-Secrets in Tickets, Logs, Responses, Exports oder Telemetrie.

## Secrets-Policy
- Secret-Quellen: Secret-Manager oder geschützte Laufzeit-Variablen (nicht im Repo).
- Rotation:
  - turnusmäßig (z. B. 90 Tage) und sofort bei Verdacht auf Leak.
  - dokumentierter Roll-Forward-Prozess ohne Downtime-Zwang.
- Handling:
  - nie loggen, nie in Error-Responses ausgeben.
  - nie in Exporte/Backups ohne Verschlüsselungs- und Zugriffsregel aufnehmen.
  - Zugriff nur nach least-privilege.

## Logging- und Telemetry-Policy (strikt no-PII)
Erlaubte Felder (D-033-konform):
- `status_code`
- `route_template` (keine sensitiven Path-Parameter)
- `request_id`
- `role_category` (z. B. `admin`, `vip`, `moderator`)
- `event_type` (z. B. `auth_unauthorized`, `rbac_forbidden`)

Verbotene Felder/Inhalte:
- Tokens (JWT/Bearer/Refresh), E-Mail, VIN, Namen, Freitext-Payloads, Dokumentinhalte, rohe Headers/Cookies.

Pflichtmaßnahmen:
- Redaction vor Persistenz/Export.
- Request-ID für technische Korrelation in Response/Header und Logs.
- Telemetrie-Erweiterungen nur per Allowlist-Review (deny-by-default).

## Deployment-Minimum (vendor-neutral)
- TLS/HTTPS obligatorisch.
- Healthcheck-Endpoint vorhanden und überwacht.
- DB-Migration/Initialisierung deterministisch vor Traffic-Freigabe.
- Rollout erst nach erfolgreichem RBAC-/Consent-/Upload-/Export-Policy-Check.

## TTL-Hinweis (Exports/PDF)
- TTL ist für Export-/PDF-Artefakte geregelt und wird pro Artefakt-Typ angewandt.
- Historie bleibt erhalten, Datei-Artefakte laufen ab/werden entfernt (siehe D-016, D-024).
- Wenn konkrete TTL-Parameter im Betrieb genutzt werden, müssen sie exakt gemäß Implementierung dokumentiert werden (keine implizite neue Spezifikation in diesem Dokument).

## Bezug auf bindende Entscheidungen
- D-002 Moderator nur Blog/News.
- D-004..D-007 Upload-Quarantäne + Scan/Freigabe-Regeln.
- D-010 Consent versioniert und blockierend.
- D-016/D-024 Export-/PDF-TTL mit Historie.
- D-033 Security-Telemetry nur no-PII, Redaction + Request-ID.