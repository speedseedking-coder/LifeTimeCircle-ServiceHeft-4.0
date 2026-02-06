# server/scripts/patch_enforce_test_sale_transfer_admin_forbidden.ps1
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$target   = Join-Path $repoRoot "server\tests\test_sale_transfer_api.py"

if (-not (Test-Path $target)) { throw "Target file not found: $target" }

$raw = Get-Content -Raw -Path $target

$patternFunc = '(?ms)^def\s+test_sale_transfer_status_admin_forbidden\s*\(.*?\):\s*\r?\n(?<body>.*?)(?=^\s*def\s+|\z)'
$m = [regex]::Match($raw, $patternFunc)
if (-not $m.Success) { throw "Function not found: test_sale_transfer_status_admin_forbidden" }

$body  = $m.Groups["body"].Value
$body2 = $body

# 1) falsche Token-Var absichern
$body2 = $body2 -replace '\{tok_a\}', '{tok_adm}'

# 2) rs-Assertion korrekt setzen (nur die rs-Line!)
$body2 = $body2 -replace '(?m)^\s*assert\s+rs\.status_code\s*==\s*200\s*,\s*rs\.text\s*$', '        assert rs.status_code == 403, rs.text'
$body2 = $body2 -replace '(?m)^\s*assert\s+rs\.status_code\s*==\s*403\s*,\s*rs\.text\s*$', '        assert rs.status_code == 403, rs.text'

if ($body2 -eq $body) {
  throw "No changes applied (admin_forbidden body already matches or patterns not found)."
}

$updated = $raw.Substring(0, $m.Index) + $m.Value.Replace($body, $body2) + $raw.Substring($m.Index + $m.Length)

Set-Content -Path $target -Value $updated -NoNewline -Encoding utf8
Write-Host "OK: admin_forbidden test enforced (tok_adm + 403)."