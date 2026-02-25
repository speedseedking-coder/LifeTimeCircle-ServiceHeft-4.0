# LifeTimeCircle – Threat Model v1 (Phase 1 / Week 1–2)
Stand: 2026-02-22

## Scope
In Scope:
- Auth
- Upload
- Export
- Public QR

Nicht in Scope:
- Vendor-spezifische Infrastrukturdetails
- Tiefgehende kryptografische Re-Designs

## Datenflüsse (vereinfacht)

### 1) Auth
1. Client -> Auth-Endpoint (Credentials/Token-Flow)
2. Server validiert Auth + Rollen
3. Server setzt Sicherheitskontext (Rolle, Consent-Status)
4. Request geht auf geschützte Route

### 2) Upload
1. Client lädt Datei-Metadaten/Datei hoch
2. Server legt Upload in Quarantäne (`PENDING/QUARANTINED`)
3. Scan/Review-Flow
4. Nur `APPROVED` darf in nachgelagerte Flows (z. B. Export)

### 3) Export
1. Berechtigter Client triggert Export
2. Server prüft RBAC + Objektbezug + Datenfreigaben
3. Export-Artefakt wird temporär bereitgestellt
4. TTL-Job löscht Datei, Historie bleibt

### 4) Public QR
1. Öffentlicher Aufruf über QR-Token
2. Server liefert nur freigegebene, datenarme Ansicht
3. Keine PII-Ausgabe, keine privilegierten Datenpfade

## Angriffsflächen
- Auth-Endpunkte (Token-Diebstahl, Replay)
- Geschützte Routen mit objektbezogenen IDs (ID-Guessing/Enumeration)
- Upload-Pipeline (Malware, Polyglot-Dateien, Missbrauch von Dateitypen)
- Export-Pipeline (Datenabfluss, TTL-Umgehung)
- Public-Endpunkte (Token-Enumeration, Scraping)
- Logging/Telemetry (PII/Secret-Leaks)

## Top-Risiken und Mitigations (max. 10)

1) **Token Theft**
- Eintritt: kompromittierter Client/Leak in Logs.
- Impact: unautorisierter Zugriff.
- Mitigation: keine Token in Logs, kurze TTL, serverseitige Prüfung jeder Anfrage, no-PII Telemetrie.
- Evidence: SoT Decision D-033.
- Tests: `server/tests/test_security_telemetry.py`.

2) **Replay-Angriffe auf wiederholbare Requests**
- Eintritt: abgefangene Requests werden erneut gesendet.
- Impact: doppelte Aktionen/unerlaubte Wiederholung.
- Mitigation: Request-ID/Korrelation, idempotente Endpunkte wo nötig, strikte Auth-Prüfung.
- Evidence: SoT Decision D-033 + Request-ID-Komponenten im Checkpoint.
- Tests: TBD (spezifischer Replay-Testfall).

3) **ID Guessing / Object Enumeration**
- Eintritt: erratbare IDs/Tokens in URL.
- Impact: Fremddatenzugriff.
- Mitigation: object-level checks zusätzlich zum Role-Gate; deny-by-default bei Unsicherheit.
- Evidence: SoT Decision D-008.
- Tests: vorhanden laut Checkpoint/Regression-Pack; Detailpfade siehe dokumentierte RBAC-Tests im Master Checkpoint.

4) **Moderator-Rechteausweitung**
- Eintritt: Fehlkonfiguration in Routern/Dependencies.
- Impact: Zugriff auf nicht erlaubte Kernrouten.
- Mitigation: Moderator strikt nur Blog/News, sonst 403.
- Evidence: SoT Decision D-002.
- Tests: laut Master Checkpoint dokumentierte RBAC-Regressionstests.

5) **Upload Abuse (Malware/unerlaubte Inhalte)**
- Eintritt: manipulierte Datei-Uploads.
- Impact: Schadcode, Datenkompromittierung.
- Mitigation: Quarantäne-by-default, Scan-Status, Freigabe nur CLEAN durch Admin.
- Evidence: SoT Decisions D-004..D-007.
- Tests: `server/tests/test_documents_quarantine_rbac.py`.

6) **Export Leakage**
- Eintritt: überbreite Exportinhalte oder unzureichende Redaction.
- Impact: PII-Abfluss.
- Mitigation: Export nur redacted/approved, least privilege, keine PII in Artefakten außerhalb Scope.
- Evidence: SoT Decisions D-003, D-016, D-024.
- Tests: `server/tests/test_exports.py`, `server/tests/test_export_vehicle.py`, `server/tests/test_export_servicebook.py`, `server/tests/test_export_masterclipboard.py`.

7) **TTL-Bypass bei Exports/PDFs**
- Eintritt: Artefakte bleiben länger verfügbar als erlaubt.
- Impact: verlängerte Exposition sensibler Daten.
- Mitigation: verbindliche TTL, Löschjob, Historie ohne Dateiinhalt.
- Evidence: SoT Decisions D-016, D-024.
- Tests: Export-Tests vorhanden; TTL-spezifische End-to-End-Checks ggf. ergänzen.

8) **Public Endpoint Enumeration (QR/Public Site)**
- Eintritt: automatisiertes Durchprobieren von Tokens/Pfaden.
- Impact: ungewollte Einsicht in öffentliche Daten.
- Mitigation: datenarme Responses, keine PII, harte Trennung zu geschützten Routen, Monitoring auf 401/403; Rate-Limiting falls eingeführt.
- Evidence: Moderator-/Public-Gates im Master Checkpoint.
- Tests: laut Master Checkpoint dokumentierte Moderator-Block-Tests.

9) **Consent-Bypass**
- Eintritt: Aufruf produktiver Kernrouten ohne gültigen Consent.
- Impact: Rechts-/Compliance-Risiko.
- Mitigation: versionierter Consent serverseitig blockierend enforced.
- Evidence: SoT Decision D-010.
- Tests: laut Master Checkpoint dokumentierte Consent-Gate-Regressionen.

10) **PII/Secret-Leaks in Telemetry/Logs**
- Eintritt: neue Felder ohne Redaction-Allowlist.
- Impact: Datenschutzvorfall.
- Mitigation: no-PII Allowlist, Redaction Pflicht, deny-by-default für neue Telemetry-Felder.
- Evidence: SoT Decision D-033.
- Tests: `server/tests/test_security_telemetry.py`.

## Testbare Kontrollpunkte (kurz)
- 401 für unauthenticated, 403 für forbidden bleibt stabil.
- Moderator auf Nicht-Blog/News immer 403.
- Upload ohne CLEAN niemals approve/exportfähig.
- Export-Datei nach TTL nicht mehr abrufbar; Historie bleibt.
- Public QR liefert keine PII-Felder.
- Logs/Telemetry enthalten request_id, status, route_template, role_category, event_type – keine PII/Secrets.