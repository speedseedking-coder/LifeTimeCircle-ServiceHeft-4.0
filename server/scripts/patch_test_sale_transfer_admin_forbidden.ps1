param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$target   = Join-Path $repoRoot "server\tests\test_sale_transfer_api.py"

if (-not (Test-Path $target)) {
  throw "Target file not found: $target"
}

$raw = Get-Content -Raw -Path $target

$updated = $raw

# 1) Testname anpassen
$updated = $updated -replace 'def\s+test_sale_transfer_status_admin_can_read\s*\(', 'def test_sale_transfer_status_admin_forbidden('

# 2) Erwartung 200 -> 403
$updated = $updated -replace 'assert\s+rs\.status_code\s*==\s*200\s*,\s*rs\.text', 'assert rs.status_code == 403, rs.text'

if ($updated -eq $raw) {
  throw "No changes applied; expected patterns not found."
}

if ($updated -match 'test_sale_transfer_status_admin_can_read') {
  throw "Replacement incomplete: old test name still present."
}

Set-Content -Path $target -Value $updated -NoNewline

Write-Host "OK: sale_transfer status test updated (admin -> 403)."