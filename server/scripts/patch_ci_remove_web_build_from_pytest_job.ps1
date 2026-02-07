# server/scripts/patch_ci_remove_web_build_from_pytest_job.ps1
# Removes duplicate web build steps from the pytest job in .github/workflows/ci.yml (idempotent)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot
if (-not $scriptRoot -or $scriptRoot.Trim() -eq "") { $scriptRoot = Split-Path -Parent $PSCommandPath }
if (-not $scriptRoot -or $scriptRoot.Trim() -eq "") { $scriptRoot = (Get-Location).Path }

$repoRoot = Resolve-Path (Join-Path $scriptRoot "..\..")
$ciPath   = Join-Path $repoRoot ".github\workflows\ci.yml"

if (-not (Test-Path -LiteralPath $ciPath)) { throw "CI workflow not found: $ciPath" }

$raw = Get-Content -LiteralPath $ciPath -Raw

# If not present -> nothing to do
if ($raw -notmatch '(?m)^\s{6}- name:\s*Setup Node \(web\)\s*$') {
  Write-Host "OK: pytest job does not contain duplicate web build steps." -ForegroundColor Green
  exit 0
}

# Remove the whole duplicate block: Setup Node (web) ... Web build ... npm run build
$pattern = '(?ms)^\s{6}- name:\s*Setup Node \(web\)\s*\r?\n.*?^\s{8}npm run build\s*\r?\n(?:\r?\n)*'
$new = [regex]::Replace($raw, $pattern, '', 1)

if ($new -eq $raw) {
  throw "Pattern did not match as expected. Abort to avoid accidental edits."
}

Set-Content -LiteralPath $ciPath -Value ($new.TrimEnd() + "`n") -Encoding utf8NoBOM
Write-Host "OK: removed duplicate web build steps from pytest job in $ciPath" -ForegroundColor Green
