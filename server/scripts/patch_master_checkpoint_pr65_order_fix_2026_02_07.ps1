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

function Norm([string]$s) {
  if ($null -eq $s) { return "" }
  $s = ($s -replace '\p{Cf}', '')       # BOM/zero-width
  $s = ($s -replace [char]0x00A0, ' ')  # NBSP
  return $s.TrimEnd()
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

# Block als norm-set
$blockSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($b in $block) { [void]$blockSet.Add((Norm $b)) }

# 1) Block überall entfernen (norm-robust)
$list = New-Object System.Collections.Generic.List[string]
foreach ($l in $lines) {
  if ($blockSet.Contains((Norm $l))) { continue }
  $list.Add($l)
}

# 2) Header finden
$hdr = -1
for ($i=0; $i -lt $list.Count; $i++) {
  if ((Norm $list[$i]) -match '^\s*##\s+Aktueller\s+Stand\b') { $hdr = $i; break }
}
if ($hdr -lt 0) { throw "Header not found: '## Aktueller Stand ...' in $fp" }

# 3) Block direkt nach Header einfügen (nach evtl. Leerzeilen)
$insertAt = $hdr + 1
while ($insertAt -lt $list.Count -and (Norm $list[$insertAt]) -eq '') { $insertAt++ }

$list.InsertRange($insertAt, @($block + @('')))

$out = ($list.ToArray() -join $nl)
if ($out -eq $raw) { Write-Host "OK: no changes needed."; exit 0 }

Write-Text $fp $out $nl
Write-Host "OK: moved PR#65 block under 'Aktueller Stand'."
Write-Host "File: $fp"
