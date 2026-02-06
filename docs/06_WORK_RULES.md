# docs/06_WORK_RULES.md
# LifeTimeCircle – Service Heft 4.0
**Arbeitsregeln (Chat/Umsetzung) – SoT**  
Stand: 2026-02-05

Ziel: maximal konkret, produktionsreif, keine Demos, keine Lücken.

## Sprache / Output
- Deutsch
- maximal konkret
- keine Floskeln
- nicht nachfragen außer zwingend (sonst Defaultannahme)

## Code-Regeln
- Keine ZIPs. Nur Code.
- Code immer: vollständiger Dateipfad + kompletter Dateiinhalt.
- Keine Platzhalter.
- Keine halben Snippets.
- Wenn zu lang: Block 1/n … n/n.

## Security / Policy
- Default: deny-by-default + least privilege
- RBAC serverseitig enforced
- Moderator strikt nur Blog/News (überall sonst 403)
- Keine PII/Secrets in Logs/Responses

## Public-QR Pflichttext (exakt)
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## Git / Workflow
- Feature-Branch
- PR nach main
- CI muss grün sein (inkl. RBAC-Guard-Tests)
- Branch Protection: PR-only, strict up-to-date, required checks, linear history