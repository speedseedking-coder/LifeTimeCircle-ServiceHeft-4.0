# server/scripts/patch_ci_fix_docs_validator_step.ps1
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

function Write-Text([string]$path, [string]$text) {
  $nl = ($text -match "`r`n") ? "`r`n" : "`n"
  if (-not $text.EndsWith($nl)) { $text += $nl }
  Set-Content -LiteralPath $path -Value $text -Encoding UTF8
}

function Normalize-Line([string]$s) {
  if ($null -eq $s) { return "" }
  # remove Unicode format chars (BOM/zero-width), normalize NBSP to space
  $s = ($s -replace '\p{Cf}', '')
  $s = ($s -replace [char]0x00A0, ' ')
  return $s
}

function Find-StepMatches([string[]]$lines) {
  $hits = @()
  for ($i=0; $i -lt $lines.Count; $i++) {
    $n = (Normalize-Line $lines[$i]).ToLowerInvariant()
    if ($n -like '*- name:*' -and $n -like '*ltc docs unified validator*') {
      $hits += $i
    }
  }
  return $hits
}

function Get-Indent([string]$line) {
  $n = Normalize-Line $line
  if ($n -match '^(\s*)-\s*name\s*:') { return $Matches[1] }
  # fallback: take everything before first '-'
  if ($n -match '^(\s*)-') { return $Matches[1] }
  return "      "
}

function Find-StepEnd([string[]]$lines, [int]$startIdx, [string]$stepIndent) {
  $end = $lines.Count - 1
  $re = "^" + [regex]::Escape($stepIndent) + "-\s+"
  for ($j=$startIdx+1; $j -lt $lines.Count; $j++) {
    $n = Normalize-Line $lines[$j]
    if ($n -match $re) { return ($j - 1) }
  }
  return $end
}

$repo = Resolve-RepoRoot
$wf = Join-Path $repo ".github/workflows/ci.yml"
$raw = Read-Text $wf
$nl = ($raw -match "`r`n") ? "`r`n" : "`n"
$lines = $raw -split "\r?\n", -1

$hits = Find-StepMatches $lines
if ($hits.Count -eq 0) { throw "Step not found: LTC docs unified validator in $wf" }

# 1) Dedupe: keep first, remove any later duplicates (remove from bottom to top)
$keep = [int]$hits[0]
if ($hits.Count -gt 1) {
  for ($h = $hits.Count - 1; $h -ge 1; $h--) {
    $idx = [int]$hits[$h]
    $indent = Get-Indent $lines[$idx]
    $end = Find-StepEnd $lines $idx $indent
    $before = @()
    if ($idx -gt 0) { $before = @($lines[0..($idx-1)]) }
    $after = @()
    if ($end + 1 -le $lines.Count - 1) { $after = @($lines[($end+1)..($lines.Count-1)]) }
    $lines = @($before + $after)
  }
  # recompute keep index after deletions
  $hits2 = Find-StepMatches $lines
  $keep = [int]$hits2[0]
}

# 2) Patch kept step
$stepIndent = Get-Indent $lines[$keep]
$keyIndent  = $stepIndent + "  "
$end = Find-StepEnd $lines $keep $stepIndent

$wdWanted  = $keyIndent + 'working-directory: ${{ github.workspace }}'
$runWanted = $keyIndent + 'run: pwsh -NoProfile -ExecutionPolicy Bypass -File "${{ github.workspace }}/server/scripts/patch_docs_unified_final_refresh.ps1"'

$changed = $false

# ensure working-directory
$wdIdx = -1
for ($i=$keep+1; $i -le $end; $i++) {
  $n = Normalize-Line $lines[$i]
  if ($n -match '^\s*working-directory\s*:') { $wdIdx = $i; break }
}
if ($wdIdx -ge 0) {
  if ($lines[$wdIdx] -ne $wdWanted) { $lines[$wdIdx] = $wdWanted; $changed = $true }
} else {
  # insert directly after name line
  $lines = @($lines[0..$keep] + @($wdWanted) + $lines[($keep+1)..($lines.Count-1)])
  $changed = $true
  $end += 1
}

# recompute end after possible insert
$end = Find-StepEnd $lines $keep $stepIndent

# ensure run (replace pipe-block if needed)
$runIdx = -1
for ($i=$keep+1; $i -le $end; $i++) {
  $n = Normalize-Line $lines[$i]
  if ($n -match '^\s*run\s*:') { $runIdx = $i; break }
}
if ($runIdx -ge 0) {
  $n0 = Normalize-Line $lines[$runIdx]
  $isPipe = ($n0 -match '^\s*run\s*:\s*\|\s*$')
  if ($lines[$runIdx] -ne $runWanted) { $lines[$runIdx] = $runWanted; $changed = $true }

  if ($isPipe) {
    # remove block lines more indented than keyIndent
    $rmFrom = $runIdx + 1
    $rmTo = $rmFrom - 1
    for ($t=$rmFrom; $t -le $end; $t++) {
      if ($lines[$t].StartsWith($keyIndent + "  ")) { $rmTo = $t; continue }
      break
    }
    if ($rmTo -ge $rmFrom) {
      $before = @($lines[0..($rmFrom-1)])
      $after = @()
      if ($rmTo + 1 -le $lines.Count - 1) { $after = @($lines[($rmTo+1)..($lines.Count-1)]) }
      $lines = @($before + $after)
      $changed = $true
    }
  }
} else {
  # insert run after working-directory if present, else after name
  $insertAt = $keep + 1
  if ($lines[$insertAt] -eq $wdWanted) { $insertAt = $insertAt } else { $insertAt = $keep }
  $lines = @($lines[0..$insertAt] + @($runWanted) + $lines[($insertAt+1)..($lines.Count-1)])
  $changed = $true
}

$newRaw = ($lines -join $nl)
if (-not $changed -or $newRaw -eq $raw) {
  Write-Host "OK: no changes needed."
  exit 0
}

Write-Text $wf $newRaw
Write-Host "OK: patched CI docs validator step (deduped + workdir=root + correct -File)."
Write-Host "File: $wf"
