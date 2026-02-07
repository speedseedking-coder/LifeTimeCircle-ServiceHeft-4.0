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
  $s = ($s -replace '\p{Cf}', '')        # zero-width/BOM
  $s = ($s -replace '\p{Zs}', ' ')       # alle Space-Separators -> Space
  $s = ($s -replace [char]0x00A0, ' ')   # NBSP
  $s = ($s -replace '\s+', ' ')          # collapse
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

# Header finden (ohne regex, ohne rg): "##" + enthält "aktueller stand"
$hdr = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  $t = (Norm $lines[$i]).ToLowerInvariant()
  if ($t.Contains("aktueller stand") -and (Norm $lines[$i]).TrimStart().StartsWith("##")) { $hdr = $i; break }
}
if ($hdr -lt 0) { throw "Header not found: '## ... Aktueller Stand ...' in $fp" }

# Block-Lineset (exakt) + keyed removal (✅ + keywords)
$blockSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($b in $block) { [void]$blockSet.Add((Norm $b)) }

$keys = @("pr #65 gemerged","ltc docs unified validator","patch_ci_fix_docs_validator_step.ps1","ci grün auf")
$list = New-Object 'System.Collections.Generic.List[string]'
$removed = 0

foreach ($l in $lines) {
  $n  = Norm $l
  $lc = $n.ToLowerInvariant()
  $isExact = $blockSet.Contains($n)
  $isKeyed = ($n.StartsWith("✅") -and ($keys | Where-Object { $lc.Contains($_) } | Select-Object -First 1))
  if ($isExact -or $isKeyed) { $removed++; continue }
  $list.Add($l)
}

# Header in bereinigtem Text neu finden
$hdr2 = -1
for ($i=0; $i -lt $list.Count; $i++) {
  $t = (Norm $list[$i]).ToLowerInvariant()
  if ($t.Contains("aktueller stand") -and (Norm $list[$i]).TrimStart().StartsWith("##")) { $hdr2 = $i; break }
}
if ($hdr2 -lt 0) { throw "Header not found after cleanup in $fp" }

# already ok?
$next = $hdr2 + 1
while ($next -lt $list.Count -and (Norm $list[$next]) -eq "") { $next++ }
if ($next -lt $list.Count -and (Norm $list[$next]).ToLowerInvariant().Contains("pr #65 gemerged")) {
  Write-Host "OK: PR#65 already under 'Aktueller Stand'. RemovedLines=$removed"
  exit 0
}

# Insert direkt nach Header (nach Leerzeilen)
$insertAt = $hdr2 + 1
while ($insertAt -lt $list.Count -and (Norm $list[$insertAt]) -eq "") { $insertAt++ }

$list.InsertRange($insertAt, [string[]]($block + ""))

$out = ($list.ToArray() -join $nl)
if (-not $out.EndsWith($nl)) { $out += $nl }

if ($out -eq $raw) { Write-Host "OK: no changes needed. RemovedLines=$removed"; exit 0 }

Set-Content -LiteralPath $fp -Value $out -Encoding UTF8
Write-Host "OK: moved PR#65 under 'Aktueller Stand'. RemovedLines=$removed"
Write-Host "File: $fp"
