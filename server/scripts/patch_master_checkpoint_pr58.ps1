# server/scripts/patch_master_checkpoint_pr58.ps1
<#
Idempotent Patch (PR #58):
- docs/99_MASTER_CHECKPOINT.md: stellt PR #58 Einträge unter "## Aktueller Stand (main)" sicher
- ergänzt fehlende Zeilen (keine Duplikate), Reihenfolge stabil
- setzt (falls vorhanden) Stand-Zeile auf 2026-02-06
- UTF-8 ohne BOM

RUN (Repo-Root):
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\patch_master_checkpoint_pr58.ps1
#>

[CmdletBinding()]
param(
  [string] $RepoRoot = $null
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-RepoRoot([string]$StartDir) {
  $resolved = (Resolve-Path -LiteralPath $StartDir).Path
  $di = [System.IO.DirectoryInfo]::new($resolved)
  while ($di -ne $null) {
    if (Test-Path -LiteralPath (Join-Path $di.FullName '.git') -PathType Container) { return $di.FullName }
    if ((Test-Path -LiteralPath (Join-Path $di.FullName 'server') -PathType Container) -and
        (Test-Path -LiteralPath (Join-Path $di.FullName 'docs') -PathType Container)) { return $di.FullName }
    $di = $di.Parent
  }
  return $null
}

$repoRoot =
  if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
    (Resolve-Path -LiteralPath $RepoRoot).Path
  } else {
    Find-RepoRoot (Get-Location).Path
  }

if (-not $repoRoot) { throw 'Repo root not found. cd into repo root or pass -RepoRoot.' }

$doc = Join-Path $repoRoot 'docs/99_MASTER_CHECKPOINT.md'
if (-not (Test-Path -LiteralPath $doc -PathType Leaf)) { throw "Missing file: $doc" }

$src = Get-Content -LiteralPath $doc -Raw

# Newline-Style + Trailing-Newline beibehalten
$nl = if ($src -match "`r`n") { "`r`n" } else { "`n" }
$hasTrailingNl = $src.EndsWith("`n")

$lines = $src -split "\r?\n", 0

# Stand-Zeile setzen (falls vorhanden)
for ($i = 0; $i -lt $lines.Length; $i++) {
  if ($lines[$i] -match '^\s*Stand:\s*\*\*.*\*\*\s*$') {
    $lines[$i] = 'Stand: **2026-02-06**'
    break
  }
}

$marker = '## Aktueller Stand (main)'
$idxMarker = -1
for ($i = 0; $i -lt $lines.Length; $i++) {
  if ($lines[$i] -eq $marker) { $idxMarker = $i; break }
}
if ($idxMarker -lt 0) { throw "Marker not found: $marker" }

$want = @(
  '✅ PR #58 gemerged: `chore(web): silence npm cache clean --force warning (stderr redirect)`'
  '✅ Web Smoke Toolkit: `server/scripts/ltc_web_toolkit.ps1` silenced `npm cache clean --force` via `2>$null`'
  '✅ Script: `server/scripts/patch_ltc_web_toolkit_silence_npm_cache_warn.ps1` (idempotent)'
  '✅ Script: `server/scripts/patch_master_checkpoint_pr58.ps1` (idempotent)'
)

# Presence-Check (exakt, TrimEnd tolerant)
$norm = @()
foreach ($l in $lines) { $norm += $l.TrimEnd() }

$toInsert = @()
foreach ($w in $want) {
  if (-not ($norm -contains $w)) { $toInsert += $w }
}

# Insert-Position: direkt unter Marker (hinter evtl. Leerzeile)
$idxInsert = $idxMarker + 1
if ($idxInsert -lt $lines.Length -and $lines[$idxInsert] -eq '') { $idxInsert++ }

$changed = $false
if ($toInsert.Count -gt 0) { $changed = $true }

if (-not $changed) {
  $outCheck = ($lines -join $nl)
  if ($hasTrailingNl) { $outCheck += $nl }
  if ($outCheck -ne $src) { $changed = $true }
}

if (-not $changed) {
  Write-Host 'OK: no changes needed.'
  return
}

if ($toInsert.Count -gt 0) {
  $before = if ($idxInsert -gt 0) { $lines[0..($idxInsert-1)] } else { @() }
  $after  = if ($idxInsert -lt $lines.Length) { $lines[$idxInsert..($lines.Length-1)] } else { @() }
  $lines = @($before + $toInsert + $after)
}

$out = ($lines -join $nl)
if ($hasTrailingNl) { $out += $nl }

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($doc, $out, $utf8NoBom)

Write-Host 'OK: Master Checkpoint ensured for PR #58.'
