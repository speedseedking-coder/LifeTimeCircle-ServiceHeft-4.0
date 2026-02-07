# server/scripts/patch_master_checkpoint_pr65_order_fix.ps1
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

function Norm([string]$s) {
  if ($null -eq $s) { return "" }
  $s = ($s -replace '\p{Cf}', '')       # BOM/zero-width
  $s = ($s -replace [char]0x00A0, ' ')  # NBSP
  $s = ($s -replace '\s+', ' ')         # collapse whitespace
  return $s.Trim()
}

$repo = Resolve-RepoRoot
$fp   = Join-Path $repo "docs/99_MASTER_CHECKPOINT.md"
if (-not (Test-Path -LiteralPath $fp)) { throw "Missing file: $fp" }

$raw   = Get-Content -LiteralPath $fp -Raw -Encoding UTF8
$nl    = ($raw -match "`r`n") ? "`r`n" : "`n"
$lines = $raw -split "\r?\n", -1

$block = @(
  '✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`',
  '✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf',
  '✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)',
  '✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)'
)

# 0) already ok?
function FindHeader([string[]]$arr) {
  for ($i=0; $i -lt $arr.Count; $i++) {
    $n = (Norm $arr[$i]).ToLowerInvariant()
    if ($n -like "##*aktueller*stand*") { return $i }
  }
  return -1
}

$hdr0 = FindHeader $lines
if ($hdr0 -lt 0) { throw "Header not found: '## ... Aktueller ... Stand ...' in $fp" }

$after0 = $hdr0 + 1
while ($after0 -lt $lines.Count -and (Norm $lines[$after0]) -eq "") { $after0++ }

if ($after0 -lt $lines.Count) {
  $n0 = (Norm $lines[$after0]).ToLowerInvariant()
  if ($n0 -like "*pr #65 gemerged*") {
    Write-Host "OK: PR#65 block already under 'Aktueller Stand'."
    exit 0
  }
}

# 1) remove block lines anywhere (exact or keyed ✅-lines)
$blockSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($b in $block) { [void]$blockSet.Add((Norm $b)) }

$keys = @("pr #65 gemerged", "ltc docs unified validator", "patch_ci_fix_docs_validator_step.ps1", "docs unified validator", "ci grün auf")

$list = New-Object 'System.Collections.Generic.List[string]'
$removed = 0
foreach ($l in $lines) {
  $n  = (Norm $l)
  $lc = $n.ToLowerInvariant()

  $isExact = $blockSet.Contains($n)
  $isKeyed = ($n.StartsWith("✅") -and ($keys | ForEach-Object { $lc.Contains($_) } | Where-Object { $_ } | Select-Object -First 1))

  if ($isExact -or $isKeyed) { $removed++; continue }
  $list.Add($l)
}

# 2) find header after cleanup
$hdr = FindHeader ($list.ToArray())
if ($hdr -lt 0) { throw "Header not found after cleanup: '## ... Aktueller ... Stand ...' in $fp" }

# 3) insert under header (after blank lines)
$insertAt = $hdr + 1
while ($insertAt -lt $list.Count -and (Norm $list[$insertAt]) -eq "") { $insertAt++ }

$toInsert = [string[]]($block + "")
$list.InsertRange($insertAt, $toInsert)

$out = ($list.ToArray() -join $nl)
if (-not $out.EndsWith($nl)) { $out += $nl }

if ($out -eq $raw) { Write-Host "OK: no changes needed. RemovedLines=$removed"; exit 0 }

Set-Content -LiteralPath $fp -Value $out -Encoding UTF8
Write-Host "OK: moved PR#65 block under 'Aktueller Stand'. RemovedLines=$removed"
Write-Host "File: $fp"
