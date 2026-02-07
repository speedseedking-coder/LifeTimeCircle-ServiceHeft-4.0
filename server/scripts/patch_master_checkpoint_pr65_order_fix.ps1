# server/scripts/patch_master_checkpoint_pr65_order_fix.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$fp = Join-Path (Get-Location) "docs/99_MASTER_CHECKPOINT.md"
if (-not (Test-Path -LiteralPath $fp)) { throw "Missing file: $fp" }

$raw = Get-Content -LiteralPath $fp -Raw -Encoding UTF8
$nl  = ($raw -match "`r`n") ? "`r`n" : "`n"
$lines = $raw -split "\r?\n", -1

function Norm([string]$s) {
  if ($null -eq $s) { return "" }
  $s = ($s -replace '\p{Cf}', '')       # BOM/zero-width
  $s = ($s -replace [char]0x00A0, ' ')  # NBSP
  return $s.TrimEnd()
}

$block = @(
  '✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`',
  '✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf',
  '✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)',
  '✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)'
)

# 1) Block überall entfernen (norm-robust)
$set = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($b in $block) { [void]$set.Add((Norm $b)) }

$list = New-Object 'System.Collections.Generic.List[string]'
foreach ($l in $lines) {
  if ($set.Contains((Norm $l))) { continue }
  $list.Add($l)
}

# 2) Header finden: "## Aktueller Stand..." (egal ob (main) etc.)
$hdr = -1
for ($i=0; $i -lt $list.Count; $i++) {
  if ((Norm $list[$i]) -match '^\s*##\s+Aktueller\s+Stand\b') { $hdr = $i; break }
}
if ($hdr -lt 0) { throw "Header not found: '## Aktueller Stand...' in $fp" }

# 3) Insert direkt nach Header (nach evtl. Leerzeilen)
$insertAt = $hdr + 1
while ($insertAt -lt $list.Count -and (Norm $list[$insertAt]) -eq '') { $insertAt++ }

# InsertRange braucht IEnumerable[string]
$toInsert = [string[]]($block + '')
$list.InsertRange($insertAt, $toInsert)

$out = ($list.ToArray() -join $nl)
if (-not $out.EndsWith($nl)) { $out += $nl }

if ($out -eq $raw) { Write-Host "OK: no changes needed."; exit 0 }

Set-Content -LiteralPath $fp -Value $out -Encoding UTF8
Write-Host "OK: moved PR#65 block under 'Aktueller Stand'."
Write-Host "File: $fp"
