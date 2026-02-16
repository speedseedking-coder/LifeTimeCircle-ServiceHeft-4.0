[CmdletBinding()]
param(
  [switch]$UpdateReadme,
  [switch]$NoClobber
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  $root = (& git rev-parse --show-toplevel 2>$null).Trim()
  if (-not $root) { throw "STOP: Konnte Repo-Root nicht ermitteln. Bitte im Git-Repo ausführen." }
  return $root
}

function Ensure-Dir([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) {
    New-Item -ItemType Directory -Path $path | Out-Null
  }
}

function Write-Utf8NoBom([string]$path, [string]$content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
}

function Upsert-File([string]$path, [string]$content, [switch]$NoClobber) {
  if (Test-Path -LiteralPath $path) {
    if ($NoClobber) { Write-Host "SKIP (NoClobber): $path"; return }
    Write-Host "UPDATE: $path"
  } else {
    Write-Host "CREATE: $path"
  }
  Write-Utf8NoBom -path $path -content $content
}

function Read-Utf8([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  return Get-Content -LiteralPath $path -Raw -Encoding UTF8
}

function Update-ReadmeLinks([string]$readmePath) {
  $existing = Read-Utf8 $readmePath
  if (-not $existing) { Write-Host "README.md fehlt → SKIP"; return }

  $marker = "<!-- LTC_START_HERE_LINKS -->"
  $block = @"
$marker
- **Start Here**: `docs/07_START_HERE.md`
- **Maintenance/Runbook**: `docs/05_MAINTENANCE_RUNBOOK.md`
<!-- /LTC_START_HERE_LINKS -->
"@

  if ($existing -match [regex]::Escape($marker)) {
    Write-Host "README.md enthält Marker bereits → SKIP"
    return
  }

  $lines = $existing -split "`r?`n", 0
  $idx = -1
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*#\s+\S') { $idx = $i; break }
  }

  if ($idx -ge 0 -and ($idx+1) -lt $lines.Count) {
    $newLines = @()
    $newLines += $lines[0..$idx]
    $newLines += ""
    $newLines += $block.TrimEnd()
    $newLines += ""
    if (($idx+1) -le ($lines.Count-1)) { $newLines += $lines[($idx+1)..($lines.Count-1)] }
    $new = ($newLines -join "`n")
  } else {
    $new = ($block.TrimEnd() + "`n`n" + $existing)
  }

  Write-Host "UPDATE: README.md (Start Here Links eingefügt)"
  Write-Utf8NoBom -path $readmePath -content $new
}

# ---- Main ----
$root = Get-RepoRoot
Set-Location $root

Ensure-Dir (Join-Path $root "docs")
Ensure-Dir (Join-Path $root "tools")

$agentsPath    = Join-Path $root "AGENTS.md"
$startHerePath = Join-Path $root "docs\07_START_HERE.md"
$taskTplPath   = Join-Path $root "docs\08_CODEX_TASK_TEMPLATE.md"
$readmePath    = Join-Path $root "README.md"

$AGENTS_MD = @"
# LifeTimeCircle – Service Heft 4.0 (AGENTS)
**Agent Briefing (Root)**

Dieser Repo nutzt `./docs` als **Source of Truth (SoT)**.
Bevor du irgendetwas änderst: **SoT lesen** und strikt danach arbeiten.

## SoT / Konflikt-Priorität (bindend)
1) `docs/99_MASTER_CHECKPOINT.md`
2) `docs/02_PRODUCT_SPEC_UNIFIED.md`
3) `docs/03_RIGHTS_MATRIX.md`
4) `docs/01_DECISIONS.md`
5) `server/` (Implementierung)
6) Backlog/sonstiges

## Security Defaults (nicht verhandelbar)
- deny-by-default + least privilege
- RBAC serverseitig enforced + object-level checks
- `moderator` ist strikt nur Blog/News; sonst überall 403
- Keine PII/Secrets in Logs/Responses/Exports

Public-QR Pflichttext (exakt, unverändert):
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## Schnellstart (2 Tabs)
Siehe: `docs/07_START_HERE.md`

## Tests / Quality Gate
Repo-Root:
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1`

## Output-Regeln
- Deutsch, maximal konkret, keine Floskeln
- Keine ZIPs
- Wenn Dateien geändert/neu: voller Dateipfad + kompletter Dateiinhalt
- Nicht nachfragen außer zwingend; sonst Defaultannahmen treffen
"@.TrimEnd() + "`n"

$START_HERE_MD = @"
# Start Here – LifeTimeCircle Service Heft 4.0
**Single Entry Point (SoT)**

## 1) Was ist die Wahrheit?
- Master-Status: `docs/99_MASTER_CHECKPOINT.md`
- Produktlogik (bindend): `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Rollen/Rechte (bindend): `docs/03_RIGHTS_MATRIX.md`
- Entscheidungen (bindend): `docs/01_DECISIONS.md`
- Arbeitsregeln: `docs/06_WORK_RULES.md`
- Repo-Struktur: `docs/04_REPO_STRUCTURE.md`
- Wartung/Start/Smoke: `docs/05_MAINTENANCE_RUNBOOK.md`
- Codex-Kontext: `docs/00_CODEX_CONTEXT.md`

## 2) 5-Minuten Start (Frontend + API)
Vollständig & aktuell: `docs/05_MAINTENANCE_RUNBOOK.md`

Kurzfassung (Windows, 2 Tabs):

### TAB A (API)
Repo-Root:
- `cd (git rev-parse --show-toplevel)`
- `cd .\server`
- `$env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"`
- `poetry run uvicorn app.main:app --reload`

### TAB B (WEB)
Repo-Root:
- `cd (git rev-parse --show-toplevel)`
- `cd .\packages\web`
- `npm install` (einmalig)
- `npm run dev`

URLs:
- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:5173`

## 3) IST-Zustandsprüfung (bei jedem Kontextwechsel)
Wenn vorhanden: `tools/ist_check.ps1`
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1`

## 4) Quality Gate (immer vor PR)
Repo-Root:
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1`

Optional Web Build Smoke (Repo-Root):
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_web_toolkit.ps1 -Smoke -Clean`

## 5) „Definition of Done“ (Security)
- deny-by-default eingehalten
- Moderator überall 403 außer Blog/News/Public
- object-level checks auf allen Vehicle/Dokument/Trust Ressourcen
- keine PII/Secrets in Logs/Responses/Exports
- Public-QR Pflichttext exakt und unverändert
"@.TrimEnd() + "`n"

$CODEX_TASK_TEMPLATE = @"
# Codex Task Template (Copy/Paste)
**Regel: 1 Task = 1 PR = grün = dokumentiert**

## SoT lesen (zwingend)
1) `docs/99_MASTER_CHECKPOINT.md`
2) `docs/02_PRODUCT_SPEC_UNIFIED.md`
3) `docs/03_RIGHTS_MATRIX.md`
4) `docs/01_DECISIONS.md`

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
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1`

Optional:
- `pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_web_toolkit.ps1 -Smoke -Clean`

## Output
- 1 PR, squash-merge ready
- PR-Text: Problem / Lösung / Tests / Security Notes
- Docs-Updates, falls Flow/Policy/RBAC betroffen (mindestens Master Checkpoint referenzieren)
"@.TrimEnd() + "`n"

Upsert-File -path $agentsPath    -content $AGENTS_MD          -NoClobber:$NoClobber
Upsert-File -path $startHerePath -content $START_HERE_MD      -NoClobber:$NoClobber
Upsert-File -path $taskTplPath   -content $CODEX_TASK_TEMPLATE -NoClobber:$NoClobber

if ($UpdateReadme) { Update-ReadmeLinks -readmePath $readmePath }
else { Write-Host "README Update: SKIP (run with -UpdateReadme to enable)" }

Write-Host ""
Write-Host "DONE."
Write-Host "Nächste Schritte:"
Write-Host "  git status -sb"
Write-Host "  (optional) pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1"