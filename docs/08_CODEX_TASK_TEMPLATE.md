# Codex Task Template (Copy/Paste)
**Regel: 1 Task = 1 PR = grün = dokumentiert**

## SoT lesen (zwingend)
1) docs/99_MASTER_CHECKPOINT.md
2) docs/02_PRODUCT_SPEC_UNIFIED.md
3) docs/03_RIGHTS_MATRIX.md
4) docs/01_DECISIONS.md

## Ziel
- (1 Satz, messbar)

## Scope (anfassen)
- Datei/Ordnerliste

## Nicht-Ziele (nicht anfassen)
- Explizite Liste

## Akzeptanzkriterien
- [ ] ...
- [ ] ...
- [ ] ...

## Security/RBAC Pflichten
- deny-by-default + least privilege
- RBAC serverseitig enforced + object-level checks
- Moderator nur Blog/News; sonst 403
- Keine PII/Secrets in Logs/Responses/Exports

## Commands (müssen grün sein)
Repo-Root:
- pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1

Optional:
- pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_web_toolkit.ps1 -Smoke -Clean

## Output
- 1 PR, squash-merge ready
- PR-Text: Problem / Lösung / Tests / Security Notes
- Docs-Updates, falls Flow/Policy/RBAC betroffen (mindestens Master Checkpoint referenzieren)
