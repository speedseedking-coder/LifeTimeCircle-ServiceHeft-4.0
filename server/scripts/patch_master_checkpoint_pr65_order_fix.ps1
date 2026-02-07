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
  $s = ($s -replace '\s+', ' ')
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

# Header-LineNumber via ripgrep (1-based)
$rgLine = rg -n '^\s*##\s+Aktueller\s+Stand\b' $fp | Select-Object -First 1
if (-not $rgLine) { throw "Header not found by rg: '## Aktueller Stand...' in $fp" }

# parse "25:## Aktueller Stand (main)"
$colon = $rgLine.IndexOf(':')
if ($colon -lt 1) { throw "Unexpected rg output: $rgLine" }
$hdrLineNo = [int]($rgLine.Substring(0, $colon))   # 1-based
$hdrIdx0   = $hdrLineNo - 1                        # 0-based in original $lines

# Build block set
$blockSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($b in $block) { [void]$blockSet.Add((Norm $b)) }

# Count how many block-lines occur BEFORE the header (so we can adjust index after removal)
$removedBefore = 0
for ($i=0; $i -lt $hdrIdx0; $i++) {
  if ($blockSet.Contains((Norm $lines[$i]))) { $removedBefore++ }
}

# Remove block lines anywhere (exact via Norm)
$list = New-Object 'System.Collections.Generic.List[string]'
$removedTotal = 0
foreach ($l in $lines) {
  if ($blockSet.Contains((Norm $l))) { $removedTotal++; continue }
  $list.Add($l)
}

# New header index after removal
$hdrIdx = $hdrIdx0 - $removedBefore
if ($hdrIdx -lt 0 -or $hdrIdx -ge $list.Count) { throw "Computed header index out of range after cleanup." }

# sanity check: header line should still mention "Aktueller Stand"
if (-not ((Norm $list[$hdrIdx]).ToLowerInvariant().Contains("aktueller stand"))) {
  # fallback: find it by substring
  $hdrIdx = -1
  for ($i=0; $i -lt $list.Count; $i++) {
    if ((Norm $list[$i]).ToLowerInvariant().Contains("aktueller stand")) { $hdrIdx = $i; break }
  }
  if ($hdrIdx -lt 0) { throw "Header not found in cleaned content." }
}

# If already directly under header -> ok
$next = $hdrIdx + 1
while ($next -lt $list.Count -and (Norm $list[$next]) -eq "") { $next++ }
if ($next -lt $list.Count -and (Norm $list[$next]).ToLowerInvariant().Contains("pr #65 gemerged")) {
  Write-Host "OK: PR#65 already under 'Aktueller Stand'."
  exit 0
}

# Insert directly under header (skip blanks)
$insertAt = $hdrIdx + 1
while ($insertAt -lt $list.Count -and (Norm $list[$insertAt]) -eq "") { $insertAt++ }

$toInsert = [string[]]($block + "")
$list.InsertRange($insertAt, $toInsert)

$out = ($list.ToArray() -join $nl)
if (-not $out.EndsWith($nl)) { $out += $nl }

if ($out -eq $raw) { Write-Host "OK: no changes needed. RemovedTotal=$removedTotal"; exit 0 }

Set-Content -LiteralPath $fp -Value $out -Encoding UTF8
Write-Host "OK: moved PR#65 under 'Aktueller Stand'. RemovedTotal=$removedTotal RemovedBeforeHeader=$removedBefore"
Write-Host "File: $fp"
