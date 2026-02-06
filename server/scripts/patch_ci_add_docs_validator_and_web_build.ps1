# server/scripts/patch_ci_add_docs_validator_and_web_build.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $start = $PSScriptRoot
  if ([string]::IsNullOrWhiteSpace($start)) { $start = (Get-Location).Path }

  $current = (Resolve-Path -LiteralPath $start).Path

  while ($true) {
    $gitDir = Join-Path $current ".git"
    $mc = Join-Path $current "docs/99_MASTER_CHECKPOINT.md"

    if ((Test-Path -LiteralPath $gitDir) -or (Test-Path -LiteralPath $mc)) {
      return $current
    }

    $parent = [System.IO.Directory]::GetParent($current)
    if ($null -eq $parent) { break }
    $current = $parent.FullName
  }

  throw "Repo root not found (expected .git or docs/99_MASTER_CHECKPOINT.md). Start=$start"
}

function Read-TextFile([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
  return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

function Write-TextFile([string]$Path, [string]$Text) {
  $nl = ($Text -match "`r`n") ? "`r`n" : "`n"
  if (-not $Text.EndsWith($nl)) { $Text += $nl }
  Set-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}

function Find-WorkflowFile([string]$RepoRoot) {
  $wfDir = Join-Path $RepoRoot ".github/workflows"
  if (-not (Test-Path -LiteralPath $wfDir)) { throw "Missing workflows dir: $wfDir" }

  $candidates = @()
  $candidates += Get-ChildItem -LiteralPath $wfDir -File -Filter "*.yml" -ErrorAction SilentlyContinue
  $candidates += Get-ChildItem -LiteralPath $wfDir -File -Filter "*.yaml" -ErrorAction SilentlyContinue
  if ($candidates.Count -eq 0) { throw "No workflow files found in $wfDir" }

  foreach ($f in $candidates) {
    $raw = Read-TextFile $f.FullName
    if ($raw -match "poetry\s+run\s+pytest|pytest\s+-q") { return $f.FullName }
  }

  $ciYml = Join-Path $wfDir "ci.yml"
  if (Test-Path -LiteralPath $ciYml) { return $ciYml }

  throw "No workflow matched (expected poetry run pytest / pytest -q)."
}

function Split-Lines([string]$Raw) { return ($Raw -split "\r?\n", -1) }
function Join-Lines([string[]]$Lines, [string]$Nl) { return ($Lines -join $Nl) }
function Detect-Newline([string]$Raw) { return ($Raw -match "`r`n") ? "`r`n" : "`n" }

function Detect-StepIndent([string[]]$Lines) {
  foreach ($l in $Lines) {
    if ($l -match "^(\s*)-\s+name:") { return $Matches[1] }
    if ($l -match "^(\s*)-\s+uses:") { return $Matches[1] }
  }
  return "      "
}

function IndexOf-FirstMatch([string[]]$Lines, [string]$Regex) {
  for ($i=0; $i -lt $Lines.Count; $i++) { if ($Lines[$i] -match $Regex) { return $i } }
  return -1
}

function Find-Checkout-StepBounds([string[]]$Lines, [string]$StepIndent) {
  $idx = IndexOf-FirstMatch $Lines "actions/checkout@"
  if ($idx -lt 0) { return $null }

  $start = $idx
  for ($i=$idx; $i -ge 0; $i--) {
    if ($Lines[$i] -match ("^" + [regex]::Escape($StepIndent) + "-\s+")) { $start = $i; break }
  }

  $end = $Lines.Count - 1
  for ($j=$start + 1; $j -lt $Lines.Count; $j++) {
    if ($Lines[$j] -match ("^" + [regex]::Escape($StepIndent) + "-\s+")) { $end = $j - 1; break }
  }

  return @{ Start = $start; End = $end }
}

function Insert-LinesAfter([string[]]$Lines, [int]$AfterIndex, [string[]]$Insert) {
  $before = @()
  if ($AfterIndex -ge 0) { $before = $Lines[0..$AfterIndex] }
  $after = @()
  if ($AfterIndex + 1 -le $Lines.Count - 1) { $after = $Lines[($AfterIndex+1)..($Lines.Count-1)] }
  return @($before + $Insert + $after)
}

function Ensure-GlobalEnvSecret([string[]]$Lines, [string]$Nl) {
  $raw = ($Lines -join $Nl)
  if ($raw -match "LTC_SECRET_KEY\s*:") { return @{ Lines=$Lines; Changed=$false } }

  $idxName = IndexOf-FirstMatch $Lines "^\s*name\s*:"
  $envBlock = @(
    "env:",
    "  LTC_SECRET_KEY: `${{ secrets.LTC_SECRET_KEY }}"
  )

  if ($idxName -ge 0) {
    $newLines = @($Lines[0..$idxName] + $envBlock + $Lines[($idxName+1)..($Lines.Count-1)])
    return @{ Lines=$newLines; Changed=$true }
  } else {
    $newLines = @($envBlock + $Lines)
    return @{ Lines=$newLines; Changed=$true }
  }
}

function Ensure-CiSteps([string[]]$Lines, [string]$Nl) {
  $changed = $false
  $raw = ($Lines -join $Nl)

  $stepIndent = Detect-StepIndent $Lines
  $k = $stepIndent + "  "

  $bounds = Find-Checkout-StepBounds $Lines $stepIndent
  $anchor = -1
  if ($null -ne $bounds) {
    $anchor = [int]$bounds.End
  } else {
    $idxSteps = IndexOf-FirstMatch $Lines "^\s*steps\s*:"
    if ($idxSteps -ge 0) { $anchor = $idxSteps }
  }
  if ($anchor -lt 0) { throw "Could not find insertion point (no checkout step, no steps:)" }

  # 1) Docs validator
  if ($raw -notmatch "patch_docs_unified_final_refresh\.ps1") {
    $docsStep = @(
      ($stepIndent + "- name: LTC docs unified validator"),
      ($k + "run: pwsh -NoProfile -ExecutionPolicy Bypass -File ./server/scripts/patch_docs_unified_final_refresh.ps1")
    )
    $Lines = Insert-LinesAfter $Lines $anchor $docsStep
    $changed = $true
    $anchor += $docsStep.Count
    $raw = ($Lines -join $Nl)
  }

  # 2) Node setup
  if ($raw -notmatch "actions/setup-node@") {
    $nodeStep = @(
      ($stepIndent + "- name: Setup Node (web)"),
      ($k + "uses: actions/setup-node@v4"),
      ($k + "with:"),
      ($k + "  node-version: '20'"),
      ($k + "  cache: 'npm'"),
      ($k + "  cache-dependency-path: packages/web/package-lock.json")
    )
    $Lines = Insert-LinesAfter $Lines $anchor $nodeStep
    $changed = $true
    $anchor += $nodeStep.Count
    $raw = ($Lines -join $Nl)
  }

  # 3) Web build
  if ($raw -notmatch "working-directory:\s*packages/web" -and $raw -notmatch "npm run build") {
    $webStep = @(
      ($stepIndent + "- name: Web build (packages/web)"),
      ($k + "working-directory: packages/web"),
      ($k + "run: |"),
      ($k + "  npm ci"),
      ($k + "  npm run build")
    )
    $Lines = Insert-LinesAfter $Lines $anchor $webStep
    $changed = $true
    $anchor += $webStep.Count
  }

  return @{ Lines=$Lines; Changed=$changed }
}

$repo = Resolve-RepoRoot
$wf = Find-WorkflowFile $repo

$raw = Read-TextFile $wf
$nl = Detect-Newline $raw
$lines = Split-Lines $raw

$globalEnvRes = Ensure-GlobalEnvSecret $lines $nl
$lines = $globalEnvRes.Lines
$changed = [bool]$globalEnvRes.Changed

$stepsRes = Ensure-CiSteps $lines $nl
$lines = $stepsRes.Lines
$changed = $changed -or [bool]$stepsRes.Changed

if (-not $changed) {
  Write-Host "OK: no changes needed."
  exit 0
}

$newRaw = Join-Lines $lines $nl
Write-TextFile $wf $newRaw
Write-Host "OK: patched CI workflow: docs validator + web build (idempotent)."
Write-Host "File: $wf"
