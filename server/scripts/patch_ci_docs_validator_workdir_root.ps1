# server/scripts/patch_ci_docs_validator_workdir_root.ps1
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

$repo = Resolve-RepoRoot
$wf = Join-Path $repo ".github/workflows/ci.yml"
if (-not (Test-Path -LiteralPath $wf)) { throw "Missing workflow: $wf" }

$raw = Get-Content -LiteralPath $wf -Raw -Encoding UTF8
$nl = ($raw -match "`r`n") ? "`r`n" : "`n"
$lines = $raw -split "\r?\n", -1

$idx = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^(\s*)-\s+name:\s*LTC docs unified validator\s*$') { $idx = $i; break }
}
if ($idx -lt 0) { throw "Step not found: 'LTC docs unified validator' in $wf" }

$stepIndent = ($lines[$idx] -replace '^(\s*).*$','$1')
$keyIndent = $stepIndent + "  "

# Step-Block Ende finden (nächster Step gleicher Indent)
$end = $lines.Count - 1
for ($j=$idx+1; $j -lt $lines.Count; $j++) {
  if ($lines[$j] -match ("^" + [regex]::Escape($stepIndent) + "-\s+")) { $end = $j - 1; break }
}

# schon vorhanden?
for ($k=$idx; $k -le $end; $k++) {
  if ($lines[$k] -match '^\s*working-directory:\s*\$\{\{\s*github\.workspace\s*\}\}\s*$') {
    Write-Host "OK: no changes needed."
    exit 0
  }
}

# einfügen direkt nach name:
$insert = ($keyIndent + "working-directory: `${{ github.workspace }}")
$new = @()
$new += $lines[0..$idx]
$new += $insert
if ($idx + 1 -le $lines.Count - 1) { $new += $lines[($idx+1)..($lines.Count-1)] }

$out = ($new -join $nl)
if (-not $out.EndsWith($nl)) { $out += $nl }
Set-Content -LiteralPath $wf -Value $out -Encoding UTF8

Write-Host "OK: patched docs validator step to run from repo root."
Write-Host "File: $wf"
