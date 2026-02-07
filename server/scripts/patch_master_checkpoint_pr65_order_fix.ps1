# server/scripts/patch_master_checkpoint_pr65_order_fix.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $start = $PSScriptRoot
  if ([string]::IsNullOrWhiteSpace($start)) { $start = (Get-Location).Path }
  $current = (Resolve-Path -LiteralPath $start).Path
  while ($true) {
    if (Test-Path -LiteralPath (Join-Path $current ".git")) { return $current }
    $p = [System.IO.DirectoryInfo]::new($current).Parent
    if ($null -eq $p) { break }
    $current = $p.FullName
  }
  throw "Repo root not found."
}

$repo = Resolve-RepoRoot
$fp   = Join-Path $repo "docs/99_MASTER_CHECKPOINT.md"
if (-not (Test-Path -LiteralPath $fp)) { throw "Missing file: $fp" }

$raw = Get-Content -LiteralPath $fp -Raw -Encoding UTF8

# Normalize line endings for processing (LF)
$txt = ($raw -replace "`r`n","`n") -replace "`r","`n"

# Normalize title line (dash/sonderzeichen kill)
$txt = [regex]::Replace($txt, '(?m)^\#\s+LifeTimeCircle.*$', '# LifeTimeCircle – Service Heft 4.0')

# Normalize "Aktueller Stand" header line
$txt = [regex]::Replace($txt, '(?m)^\#\#\s+Aktueller\s+Stand.*$', '## Aktueller Stand (main)')

# Canonical PR#65 block (exact lines)
$blockLines = @(
  '✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`'
  '✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf'
  '✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)'
  '✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)'
)
$blockText = ($blockLines -join "`n") + "`n"

# 1) Remove PR#65 block anywhere (PR line + next up to 3 ✅ lines)
$txt = [regex]::Replace(
  $txt,
  '(?m)^\s*✅\s*PR\s*#65\b.*\n(?:^\s*✅.*\n){0,3}',
  ''
)

# 2) Find Aktueller Stand header (after normalization)
$hdrMatch = [regex]::Match($txt, '(?m)^##\s+Aktueller\s+Stand\s+\(main\)\s*$')
if (-not $hdrMatch.Success) {
  Write-Host "DEBUG: header not found. First 80 lines:" -ForegroundColor Yellow
  ($txt -split "`n" | Select-Object -First 80) | ForEach-Object { Write-Host $_ }
  throw "Header not found: '## Aktueller Stand (main)' in $fp"
}

# 3) If PR#65 already directly under header: stop; else insert under header
$already = [regex]::IsMatch($txt, '(?ms)^##\s+Aktueller\s+Stand\s+\(main\)\s*\n\s*✅\s*PR\s*#65\b')
if ($already) {
  Write-Host "OK: PR#65 already under Aktueller Stand."
} else {
  $insertPos = $hdrMatch.Index + $hdrMatch.Length
  $txt = $txt.Insert($insertPos, "`n$blockText")
  Write-Host "OK: inserted PR#65 block under Aktueller Stand."
}

if (-not $txt.EndsWith("`n")) { $txt += "`n" }

$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($fp, $txt, $enc)
Write-Host "Wrote: $fp"
