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
$fp   = Join-Path $repo 'docs/99_MASTER_CHECKPOINT.md'

$raw  = Read-Text $fp
$nl   = ($raw -match "`r`n") ? "`r`n" : "`n"
$lines = $raw -split "\r?\n", -1

$today = '2026-02-07'

# 1) Stand: **YYYY-MM-DD** setzen (oder einfügen, falls fehlt)
$standIdx = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*Stand:\s*\*\*\d{4}-\d{2}-\d{2}\*\*\s*$') { $standIdx = $i; break }
}
if ($standIdx -ge 0) {
  $lines[$standIdx] = "Stand: **$today**"
} else {
  # fallback: nach Titelblock einfügen
  $insert = 0
  for ($i=0; $i -lt [Math]::Min($lines.Count, 30); $i++) {
    if ($lines[$i] -match '^\s*#\s+') { $insert = $i + 1 }
  }
  $lines = @($lines[0..$insert] + @("Stand: **$today**") + $lines[($insert+1)..($lines.Count-1)])
}

# 2) Header finden
$hdr = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*##\s+Aktueller Stand\s*\(main\)\s*$') { $hdr = $i; break }
}
if ($hdr -lt 0) { throw "Header not found: '## Aktueller Stand (main)'" }

# 3) Entry (NUR wenn noch nicht vorhanden)
$needle = 'PR #65 gemerged'
$already = (($lines -join "`n") -match [regex]::Escape($needle))

if (-not $already) {
  $entry = @(
    '✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`',
    '✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf',
    '✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)',
    '✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)'
  )

  # direkt nach Header einfügen, aber nach evtl. Leerzeile
  $insertAt = $hdr + 1
  while ($insertAt -lt $lines.Count -and $lines[$insertAt] -eq '') { $insertAt++ }

  $lines = @(
    $lines[0..($insertAt-1)] +
    $entry +
    $lines[$insertAt..($lines.Count-1)]
  )
}

$out = ($lines -join $nl)
Write-Text $fp $out $nl

Write-Host 'OK: master checkpoint updated.'
Write-Host "File: $fp"
