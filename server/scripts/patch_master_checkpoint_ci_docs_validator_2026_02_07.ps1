# server/scripts/patch_master_checkpoint_ci_docs_validator_2026_02_07.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $start = $PSScriptRoot
  if ([string]::IsNullOrWhiteSpace($start)) { $start = (Get-Location).Path }
  $current = (Resolve-Path -LiteralPath $start).Path
  while ($true) {
    if (Test-Path -LiteralPath (Join-Path $current ".git")) { return $current }
    if (Test-Path -LiteralPath (Join-Path $current "docs/99_MASTER_CHECKPOINT.md")) { return $current }
    $p = [System.IO.Directory]::GetParent($current)
    if ($null -eq $p) { break }
    $current = $p.FullName
  }
  throw "Repo root not found."
}

function Read-Text([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing file: $path" }
  return Get-Content -LiteralPath $path -Raw -Encoding UTF8
}

function Write-Text([string]$path, [string]$text, [string]$nl) {
  if (-not $text.EndsWith($nl)) { $text += $nl }
  Set-Content -LiteralPath $path -Value $text -Encoding UTF8
}

$repo = Resolve-RepoRoot
$fp   = Join-Path $repo "docs/99_MASTER_CHECKPOINT.md"

$raw  = Read-Text $fp
$nl   = ($raw -match "`r`n") ? "`r`n" : "`n"
$lines = $raw -split "\r?\n", -1

$today = "2026-02-07"
$changed = $false

# 1) Stand: **YYYY-MM-DD** (Suffix wie " (Europe/Berlin)" bleibt erhalten)
$standIdx = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*Stand:\s*\*\*(\d{4}-\d{2}-\d{2})\*\*(.*)$') {
    $standIdx = $i
    $suffix = $Matches[2]
    $newLine = "Stand: **$today**$suffix"
    if ($lines[$i] -ne $newLine) { $lines[$i] = $newLine; $changed = $true }
    break
  }
}

if ($standIdx -lt 0) {
  # fallback insert after first header line
  $insertAt = 1
  if ($lines.Count -lt 1) { $insertAt = 0 }
  $before = @()
  if ($insertAt -gt 0 -and $lines.Count -ge $insertAt) { $before = @($lines[0..($insertAt-1)]) }
  $after = @()
  if ($insertAt -lt $lines.Count) { $after = @($lines[$insertAt..($lines.Count-1)]) }
  $lines = @($before + @("Stand: **$today**") + $after)
  $changed = $true
}

# 2) Header finden
$hdr = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*##\s+Aktueller Stand\s*\(main\)\s*$') { $hdr = $i; break }
}
if ($hdr -lt 0) { throw "Header not found: '## Aktueller Stand (main)'" }

# 3) Entry (nur einmal)
$needle = "PR #65 gemerged"
$already = (($lines -join "`n") -match [regex]::Escape($needle))

if (-not $already) {
  $entry = @(
    '✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`',
    '✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf',
    '✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)',
    '✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)'
  )

  $insertAt = $hdr + 1
  while ($insertAt -lt $lines.Count -and $lines[$insertAt] -eq '') { $insertAt++ }

  $before = @()
  if ($insertAt -gt 0) { $before = @($lines[0..($insertAt-1)]) }
  $after = @()
  if ($insertAt -lt $lines.Count) { $after = @($lines[$insertAt..($lines.Count-1)]) }

  $lines = @($before + $entry + $after)
  $changed = $true
}

$newRaw = ($lines -join $nl)
if (-not $changed -or $newRaw -eq $raw) {
  Write-Host "OK: no changes needed."
  exit 0
}

Write-Text $fp $newRaw $nl
Write-Host "OK: master checkpoint updated."
Write-Host "File: $fp"
