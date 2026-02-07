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

function TrimNorm([string]$s) {
  if ($null -eq $s) { return "" }
  return (($s -replace '\p{Cf}','') -replace [char]0x00A0,' ').Trim()
}

$repo = Resolve-RepoRoot
$fp   = Join-Path $repo "docs/99_MASTER_CHECKPOINT.md"
if (-not (Test-Path -LiteralPath $fp)) { throw "Missing file: $fp" }

$raw = Get-Content -LiteralPath $fp -Raw -Encoding UTF8

# Normalize line endings for processing (keep LF in output)
$txt = ($raw -replace "`r`n","`n") -replace "`r","`n"

# Normalize main title line (dash/sonderzeichen kill)
$txt = [regex]::Replace($txt, '(?m)^\#\s+LifeTimeCircle.*$', '# LifeTimeCircle – Service Heft 4.0')

# Normalize the Aktueller Stand header line (any variant -> (main))
$txt = [regex]::Replace($txt, '(?m)^\#\#\s+Aktueller\s+Stand.*$', '## Aktueller Stand (main)')

$lines = $txt -split "`n", -1

# Canonical PR#65 block
$block = @(
  '✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`'
  '✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf'
  '✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)'
  '✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)'
)

# Remove any PR#65 block anywhere (contiguous: PR line + next ✅ lines)
$list = New-Object 'System.Collections.Generic.List[string]'
for ($i=0; $i -lt $lines.Length; $i++) {
  $t = TrimNorm $lines[$i]

  if ($t -match '^\s*✅\s*PR\s*#65\b') {
    $skipped = 0
    $j = $i
    while ($j -lt $lines.Length -and $skipped -lt 4) {
      $tj = TrimNorm $lines[$j]
      if ($skipped -eq 0) {
        if ($tj -match '^\s*✅\s*PR\s*#65\b') { $skipped++; $j++; continue }
        break
      } else {
        if ($tj -eq "") { $j++; continue }
        if ($tj -match '^\s*✅\s+') { $skipped++; $j++; continue }
        break
      }
    }
    $i = $j - 1
    continue
  }

  # also remove exact canonical lines (in case they exist elsewhere)
  $isCanonical = $false
  foreach ($b in $block) {
    if ((TrimNorm $b) -eq $t) { $isCanonical = $true; break }
  }
  if ($isCanonical) { continue }

  $list.Add($lines[$i])
}

# Find header index reliably
$hdr = -1
for ($i=0; $i -lt $list.Count; $i++) {
  if ((TrimNorm $list[$i]) -match '(?i)^\#\#\s+Aktueller\s+Stand\b') { $hdr = $i; break }
}
if ($hdr -lt 0) {
  Write-Host "DEBUG: could not find header. First 60 lines:" -ForegroundColor Yellow
  $n = [Math]::Min(60, $list.Count)
  for ($k=0; $k -lt $n; $k++) { Write-Host ("{0,3}: {1}" -f ($k+1), $list[$k]) }
  throw "Header not found: '## Aktueller Stand ...' in $fp"
}

# Insert block under header (after blank lines)
$insertAt = $hdr + 1
while ($insertAt -lt $list.Count -and (TrimNorm $list[$insertAt]) -eq "") { $insertAt++ }

if ($insertAt -lt $list.Count -and (TrimNorm $list[$insertAt]) -match '^\s*✅\s*PR\s*#65\b') {
  Write-Host "OK: PR#65 already under Aktueller Stand."
} else {
  $list.InsertRange($insertAt, [string[]]($block + ""))
  Write-Host "OK: inserted PR#65 block under Aktueller Stand."
}

$out = ($list.ToArray() -join "`n")
if (-not $out.EndsWith("`n")) { $out += "`n" }

# Write UTF-8 no BOM + LF
$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($fp, $out, $enc)
Write-Host "Wrote: $fp"
