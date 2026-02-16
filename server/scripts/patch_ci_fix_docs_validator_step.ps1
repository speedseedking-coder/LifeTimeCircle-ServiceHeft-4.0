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
  $s = ($s -replace '\p{Cf}', '')       # BOM/zero-width
  $s = ($s -replace [char]0x00A0, ' ')  # NBSP -> space
  return $s
}

function Find-FirstStepIndex([System.Collections.Generic.List[string]]$lines) {
  for ($i=0; $i -lt $lines.Count; $i++) {
    $n = (Normalize-Line $lines[$i]).ToLowerInvariant()
    if ($n -like '*- name:*' -and $n -like '*ltc docs unified validator*') { return $i }
  }
  return -1
}

function Get-StepIndent([System.Collections.Generic.List[string]]$lines, [int]$idx) {
  $n = Normalize-Line $lines[$idx]
  if ($n -match '^(\s*)-\s*name\s*:') { return $Matches[1] }
  if ($n -match '^(\s*)-') { return $Matches[1] }
  return "      "
}

function Get-StepEnd([System.Collections.Generic.List[string]]$lines, [int]$startIdx, [string]$indent) {
  $re = "^" + [regex]::Escape($indent) + "-\s+"
  for ($i=$startIdx+1; $i -lt $lines.Count; $i++) {
    $n = Normalize-Line $lines[$i]
    if ($n -match $re) { return ($i - 1) }
  }
  return ($lines.Count - 1)
}

$repo = Resolve-RepoRoot
$wf = Join-Path $repo ".github/workflows/ci.yml"
$raw = Read-Text $wf
$nl = ($raw -match "`r`n") ? "`r`n" : "`n"

# split -> List
$parts = $raw -split "\r?\n", -1
$list = [System.Collections.Generic.List[string]]::new()
$list.AddRange($parts)

$idx = Find-FirstStepIndex $list
if ($idx -lt 0) { throw "Step not found: LTC docs unified validator in $wf" }

$indent = Get-StepIndent $list $idx
$keyIndent = $indent + "  "

$wdWanted  = $keyIndent + 'working-directory: ${{ github.workspace }}'
$runWanted = $keyIndent + 'run: pwsh -NoProfile -ExecutionPolicy Bypass -File "$GITHUB_WORKSPACE/server/scripts/patch_docs_unified_final_refresh.ps1"'

$changed = $false

# Step-End (vor Änderungen)
$end = Get-StepEnd $list $idx $indent

# ensure working-directory (insert directly after name)
$wdIdx = -1
for ($i=$idx+1; $i -le $end; $i++) {
  if ((Normalize-Line $list[$i]) -match '^\s*working-directory\s*:') { $wdIdx = $i; break }
}
if ($wdIdx -ge 0) {
  if ($list[$wdIdx] -ne $wdWanted) { $list[$wdIdx] = $wdWanted; $changed = $true }
} else {
  $list.Insert($idx + 1, $wdWanted)
  $changed = $true
}

# Step-End neu (nach Insert)
$end = Get-StepEnd $list $idx $indent

# ensure run (replace pipe-block if needed)
$runIdx = -1
for ($i=$idx+1; $i -le $end; $i++) {
  if ((Normalize-Line $list[$i]) -match '^\s*run\s*:') { $runIdx = $i; break }
}

if ($runIdx -ge 0) {
  $n0 = Normalize-Line $list[$runIdx]
  $isPipe = ($n0 -match '^\s*run\s*:\s*\|\s*$')
  if ($list[$runIdx] -ne $runWanted) { $list[$runIdx] = $runWanted; $changed = $true }

  if ($isPipe) {
    # remove YAML block lines that are more indented than keyIndent
    $rmFrom = $runIdx + 1
    $rmTo = $rmFrom - 1
    for ($t=$rmFrom; $t -le $end -and $t -lt $list.Count; $t++) {
      if ($list[$t].StartsWith($keyIndent + "  ")) { $rmTo = $t; continue }
      break
    }
    if ($rmTo -ge $rmFrom) {
      for ($t=$rmTo; $t -ge $rmFrom; $t--) { $list.RemoveAt($t) }
      $changed = $true
    }
  }
} else {
  # insert run after working-directory if it sits right after name, else after name
  $insertAt = $idx + 1
  if ($insertAt -lt $list.Count -and $list[$insertAt] -eq $wdWanted) { $insertAt = $insertAt + 1 }
  $list.Insert($insertAt, $runWanted)
  $changed = $true
}

$newRaw = ($list.ToArray() -join $nl)
if (-not $changed -or $newRaw -eq $raw) {
  Write-Host "OK: no changes needed."
  exit 0
}

Write-Text $wf $newRaw
Write-Host "OK: patched CI docs validator step (workdir=root + correct -File)."
Write-Host "File: $wf"
