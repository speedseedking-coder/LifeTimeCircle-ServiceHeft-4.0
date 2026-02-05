# server/scripts/patch_test_sale_transfer_status_initiator_allowed.ps1
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$target   = Join-Path $repoRoot "server\tests\test_sale_transfer_api.py"

if (-not (Test-Path $target)) { throw "Target file not found: $target" }

$raw = Get-Content -Raw -Path $target

# Fix: VIP initiator (tok_a) darf status lesen -> 200, und Indent = Indent der rs-Zeile
$pattern = '(?m)^(?<i>[ \t]*)rs\s*=\s*client\.get\([^\r\n]*?/sale/transfer/status/\{tid\}[^\r\n]*tok_a[^\r\n]*\)\s*\r?\n[ \t]*assert\s+rs\.status_code\s*==\s*\d+\s*,\s*rs\.text\s*$'

$replacement = '${i}rs = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_a}"})' + "`r`n" +
               '${i}assert rs.status_code == 200, rs.text'

$updated = [regex]::Replace($raw, $pattern, $replacement)

if ($updated -eq $raw) {
  throw "No changes applied; pattern not found (expected tok_a status check block)."
}

Set-Content -Path $target -Value $updated -NoNewline -Encoding utf8
Write-Host "OK: happy path status for VIP initiator set to 200 (indent-safe)."