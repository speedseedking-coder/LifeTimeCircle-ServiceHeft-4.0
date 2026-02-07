# server/scripts/patch_master_checkpoint_pr65_order_fix_2026_02_07.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $start = $PSScriptRoot
  if ([string]::IsNullOrWhiteSpace($start)) { $start = (Get-Location).Path }
  $current = (Resolve-Path -LiteralPath $start).Path
  while ($true) {
    if (Test-Path -LiteralPath (Join-Path $current ".git")) { return $current }
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

function Clean([string]$s) {
  if ($null -eq $s) { return "" }
  $s = ($s -replace '\p{Cf}', '')       # BOM/zero-width
  $s = ($s -replace [char]0x00A0, ' ')  # NBSP
  return $s
}

$repo = Resolve-RepoRoot
$fp   = Join-Path $repo "docs/99_MASTER_CHECKPOINT.md"

$raw  = Read-Text $fp
$nl   = ($raw -match "`r`n") ? "`r`n" : "`n"
$lines = $raw -split "\r?\n", -1

$block = @(
  '✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`',
  '✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf',
  '✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)',
  '✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)'
)

# Wenn Block schon direkt unter "Aktueller Stand" steht -> OK
function Find-AktuellerStandHeaderIndex([string[]]$arr) {
  for ($i=0; $i -lt $arr.Count; $i++) {
    $c = (Clean $arr[$i]).TrimStart()
    if ($c.StartsWith("##") -and ($c -like "##*Aktueller*Stand*")) { return $i }
  }
  return -1
}

$hdr = Find-AktuellerStandHeaderIndex $lines
if ($hdr -lt 0) { throw "Header not found: '## ... Aktueller ... Stand ...' in $fp" }

$firstAfter = $hdr + 1
while ($firstAfter -lt $lines.Count -and ((Clean $lines[$firstAfter]).Trim() -eq "")) { $firstAfter++ }

$alreadyOk = $false
if ($firstAfter -lt $lines.Count) {
  $l0 = (Clean $lines[$firstAfter]).ToLowerInvariant()
  if ($l0.Contains("pr #65 gemerged")) {
    # grob prüfen: die nächsten Zeilen enthalten die restlichen Marker
    $window = ($lines[$firstAfter..([Math]::Min($lines.Count-1, $firstAfter+6))] | ForEach-Object { (Clean $_).ToLowerInvariant() }) -join "`n"
    if ($window.Contains("ltc docs unified validator") -and $window.Contains("patch_ci_fix_docs_validator_step.ps1") -and $window.Contains("ci grün auf")) {
      $alreadyOk = $true
    }
  }
}

if ($alreadyOk) {
  Write-Host "OK: PR#65 block already under 'Aktueller Stand'."
  exit 0
}

# 1) Block überall entfernen (nur ✅-Zeilen, damit wir nix anderes kaputtmachen)
$keys = @(
  "pr #65 gemerged",
  "ltc docs unified validator",
  "patch_ci_fix_docs_validator_step.ps1",
  "ci grün auf"
)

$list = New-Object System.Collections.Generic.List[string]
$removed = 0
foreach ($l in $lines) {
  $c = (Clean $l)
  $t = $c.TrimStart()
  $lc = $c.ToLowerInvariant()
  $isEntry = $t.StartsWith("✅")
  $hit = $false
  foreach ($k in $keys) { if ($lc.Contains($k)) { $hit = $true; break } }

  if ($isEntry -and $hit) { $removed++; continue }
  $list.Add($l)
}

# 2) Header im bereinigten Text neu finden
$hdr2 = Find-AktuellerStandHeaderIndex ($list.ToArray())
if ($hdr2 -lt 0) { throw "Header not found after cleanup: '## ... Aktueller ... Stand ...' in $fp" }

# 3) Insert direkt nach Header (nach evtl. Leerzeilen)
$insertAt = $hdr2 + 1
while ($insertAt -lt $list.Count -and ((Clean $list[$insertAt]).Trim() -eq "")) { $insertAt++ }

# InsertRange braucht IEnumerable[string]
$toInsert = [string[]]($block + "")
$list.InsertRange($insertAt, $toInsert)

$out = ($list.ToArray() -join $nl)
if ($out -eq $raw) { Write-Host "OK: no changes needed."; exit 0 }

Write-Text $fp $out $nl
Write-Host "OK: moved PR#65 block under 'Aktueller Stand'. RemovedLines=$removed"
Write-Host "File: $fp"
