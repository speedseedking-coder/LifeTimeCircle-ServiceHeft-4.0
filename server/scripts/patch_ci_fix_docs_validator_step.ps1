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

$repo = Resolve-RepoRoot
$wf = Join-Path $repo ".github/workflows/ci.yml"
$raw = Read-Text $wf
$nl = ($raw -match "`r`n") ? "`r`n" : "`n"
$lines = $raw -split "\r?\n", -1

# Step finden
$idx = -1
$stepIndent = ""
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^(\s*)-\s+name:\s*LTC docs unified validator\s*$') {
    $idx = $i
    $stepIndent = $Matches[1]
    break
  }
}
if ($idx -lt 0) { throw "Step not found: 'LTC docs unified validator' in $wf" }

$keyIndent = $stepIndent + "  "

# Ende des Steps (nächster Step gleicher Indent)
$end = $lines.Count - 1
for ($j=$idx+1; $j -lt $lines.Count; $j++) {
  if ($lines[$j] -match ("^" + [regex]::Escape($stepIndent) + "-\s+")) { $end = $j - 1; break }
}

# Canonical lines (single-quoted, damit PowerShell ${{ }} nicht parst)
$wdLine  = $keyIndent + 'working-directory: ${{ github.workspace }}'
$runLine = $keyIndent + 'run: pwsh -NoProfile -ExecutionPolicy Bypass -File server/scripts/patch_docs_unified_final_refresh.ps1'

$changed = $false

# working-directory: setzen/ersetzen/insert
$wdIdx = -1
for ($k=$idx+1; $k -le $end; $k++) {
  if ($lines[$k] -match '^\s*working-directory\s*:') { $wdIdx = $k; break }
}
if ($wdIdx -ge 0) {
  if ($lines[$wdIdx] -ne $wdLine) { $lines[$wdIdx] = $wdLine; $changed = $true }
} else {
  $lines = @($lines[0..$idx] + @($wdLine) + $lines[($idx+1)..($lines.Count-1)])
  $changed = $true
  $end += 1
}

# Step-Ende neu berechnen (nach möglichem Insert)
$end = $lines.Count - 1
for ($j=$idx+1; $j -lt $lines.Count; $j++) {
  if ($lines[$j] -match ("^" + [regex]::Escape($stepIndent) + "-\s+")) { $end = $j - 1; break }
}

# run: setzen/ersetzen/insert
$runIdx = -1
for ($k=$idx+1; $k -le $end; $k++) {
  if ($lines[$k] -match '^\s*run\s*:') { $runIdx = $k; break }
}
if ($runIdx -ge 0) {
  if ($lines[$runIdx] -ne $runLine) { $lines[$runIdx] = $runLine; $changed = $true }
} else {
  $insertAt = $idx + 1
  if ($lines[$insertAt] -ne $wdLine) { $insertAt = $idx }
  $lines = @($lines[0..$insertAt] + @($runLine) + $lines[($insertAt+1)..($lines.Count-1)])
  $changed = $true
}

$newRaw = ($lines -join $nl)
if (-not $changed -or $newRaw -eq $raw) {
  Write-Host "OK: no changes needed."
  exit 0
}

Write-Text $wf $newRaw
Write-Host "OK: patched CI docs validator step (workdir=root + correct run)."
Write-Host "File: $wf"
