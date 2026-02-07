# server/scripts/patch_ci_cleanup_pytest_orphan_web_lines.ps1
# Cleans up orphaned web-build lines accidentally left inside the pytest job in .github/workflows/ci.yml (idempotent)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot
if (-not $scriptRoot -or $scriptRoot.Trim() -eq "") { $scriptRoot = Split-Path -Parent $PSCommandPath }
if (-not $scriptRoot -or $scriptRoot.Trim() -eq "") { $scriptRoot = (Get-Location).Path }

$repoRoot = Resolve-Path (Join-Path $scriptRoot "..\..")
$ciPath   = Join-Path $repoRoot ".github\workflows\ci.yml"

if (-not (Test-Path -LiteralPath $ciPath)) { throw "CI workflow not found: $ciPath" }

$raw = Get-Content -LiteralPath $ciPath -Raw
$lines = $raw -split "`r?`n"

$currentJob = ""
$skippingStep = $false

$kept = New-Object System.Collections.Generic.List[string]

for ($i = 0; $i -lt $lines.Length; $i++) {
  $line = $lines[$i]

  if ($line -match '^\s{2}([A-Za-z0-9_]+):\s*$') {
    $currentJob = $matches[1]
    $skippingStep = $false
    $kept.Add($line)
    continue
  }

  if ($currentJob -ne "pytest") {
    $kept.Add($line)
    continue
  }

  if ($line -match '^\s{6}- name:\s*Setup Node \(web\)\s*$' -or
      $line -match '^\s{6}- name:\s*Web build \(packages/web\)\s*$') {
    $skippingStep = $true
    continue
  }

  if ($skippingStep) {
    if ($line -match '^\s{6}-\s' -or $line -match '^\s{2}[A-Za-z0-9_]+:\s*$') {
      $skippingStep = $false
      $i--
      continue
    }
    continue
  }

  if ($line -match '^\s{10}(node-version|cache|cache-dependency-path):\s*') { continue }
  if ($line -match '^\s{10}npm\s+ci\s*$') { continue }
  if ($line -match '^\s{10}npm\s+run\s+build\s*$') { continue }
  if ($line -match '^\s*\|\s*$') { continue }

  $kept.Add($line)
}

$out = New-Object System.Collections.Generic.List[string]
$prevBlank = $false
foreach ($ln in $kept) {
  $isBlank = ($ln.Trim() -eq "")
  if ($isBlank -and $prevBlank) { continue }
  $out.Add($ln)
  $prevBlank = $isBlank
}

$new = ($out -join "`n").TrimEnd() + "`n"

if ($new -eq $raw) {
  Write-Host "OK: no orphaned pytest web lines found (nothing to change)." -ForegroundColor Green
  exit 0
}

Set-Content -LiteralPath $ciPath -Value $new -Encoding utf8NoBOM
Write-Host "OK: cleaned orphaned pytest web lines in $ciPath" -ForegroundColor Green
