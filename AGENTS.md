# LifeTimeCircle – Service Heft 4.0 (AGENTS)
**Agent Briefing (Root)**

Dieser Repo nutzt ./docs als **Source of Truth (SoT)**.
Bevor du irgendetwas änderst: **SoT lesen** und strikt danach arbeiten.

## SoT / Konflikt-Priorität (bindend)
1) docs/99_MASTER_CHECKPOINT.md
2) docs/02_PRODUCT_SPEC_UNIFIED.md
3) docs/03_RIGHTS_MATRIX.md
4) docs/01_DECISIONS.md
5) server/ (Implementierung)
6) Backlog/sonstiges

## Security Defaults (nicht verhandelbar)
- deny-by-default + least privilege
- RBAC serverseitig enforced + object-level checks
- moderator ist strikt nur Blog/News; sonst überall 403
- Keine PII/Secrets in Logs/Responses/Exports

Public-QR Pflichttext (exakt, unverändert):
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## Schnellstart (2 Tabs)
Siehe: docs/07_START_HERE.md

## Tests / Quality Gate
Repo-Root:
- pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1

## Output-Regeln
- Deutsch, maximal konkret, keine Floskeln
- Keine ZIPs
- Wenn Dateien geändert/neu: voller Dateipfad + kompletter Dateiinhalt
- Nicht nachfragen außer zwingend; sonst Defaultannahmen treffen
