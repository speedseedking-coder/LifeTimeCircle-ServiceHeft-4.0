# Go-Live Checkliste

Stand: **2026-03-01** (Europe/Berlin)

Zweck: Diese Checkliste trennt den verifizierten Release-Candidate vom echten Live-Betrieb. Sie beschreibt keine Feature-Arbeit, sondern die offenen Betriebsentscheidungen vor einem öffentlichen Rollout.

## 1) Zielbild
Vor Go-Live muss klar sein:

- welche Domain produktiv verwendet wird
- wo API und Web betrieben werden
- wer Freigaben erteilt
- wie Monitoring, Backups und Incident-Reaktion laufen

## 2) Infrastruktur
- Ziel-Domain und Subdomains festgelegt
- TLS-Zertifikate und Redirect-Regeln eingerichtet
- Produktionsumgebung für API und Web benannt
- Trennung von Dev-, Test- und Produktivumgebungen dokumentiert

## 3) Secrets und Konfiguration
- `LTC_SECRET_KEY` produktiv gesetzt, stark genug und nicht aus Dev übernommen
- weitere produktive Secrets dokumentiert und nicht im Repo gespeichert
- Rotation und Notfallwechsel für Secrets festgelegt
- produktive Export-, Auth- und Consent-Konfiguration geprüft

## 4) Daten und Betrieb
- produktive Datenbank angebunden
- Backup- und Restore-Test dokumentiert
- Logging ohne PII-Leaks geprüft
- Aufbewahrung und Zugriff auf Exporte organisatorisch geklärt

## 5) Monitoring und Incident
- Verfügbarkeit von API und Web wird überwacht
- Fehlerkanal für Build-, Smoke- und Laufzeitfehler ist festgelegt
- Incident-Verantwortliche und Eskalationsweg sind benannt
- Rollback-Pfad für fehlerhafte Deploys ist dokumentiert

## 6) Produktfreigabe
- rechtliche und organisatorische Freigaben für öffentlichen Rollout liegen vor
- Public-QR Disclaimer und datenarme Public-Copy wurden final abgenommen
- Moderator-, Admin- und Export-Gates wurden vor Freigabe noch einmal verifiziert

## 7) Technische Abschlussprüfung
Unmittelbar vor Go-Live erneut ausführen:

- `git diff --check`
- `npm run build`
- `npm run e2e`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1`

## 8) Referenzen
- `docs/12_RELEASE_CANDIDATE_2026-03-01.md`
- `docs/05_MAINTENANCE_RUNBOOK.md`
- `docs/99_MASTER_CHECKPOINT.md`
