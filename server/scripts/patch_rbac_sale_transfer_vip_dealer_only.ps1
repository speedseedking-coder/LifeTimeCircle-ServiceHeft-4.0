# server/scripts/patch_rbac_sale_transfer_vip_dealer_only.ps1
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$target   = Join-Path $repoRoot "server\app\routers\sale_transfer.py"

if (-not (Test-Path $target)) {
  throw "Target file not found: $target"
}

$raw = Get-Content -Raw -Path $target

$before = $raw
$raw = $raw -replace 'require_roles\("vip",\s*"dealer",\s*"admin",\s*"superadmin"\)', 'require_roles("vip", "dealer")'

if ($raw -eq $before) {
  Write-Host "No changes applied (pattern not found)."
  exit 0
}

# Safety: ensure no remaining widened role-set exists
if ($raw -match 'require_roles\("vip",\s*"dealer",\s*"admin",\s*"superadmin"\)') {
  throw "Replacement incomplete: pattern still present."
}

Set-Content -Path $target -Value $raw -NoNewline

Write-Host "OK: sale_transfer roles tightened to vip+dealer only."