# server/scripts/patch_fix_test_sale_transfer_admin_token.ps1
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$target   = Join-Path $repoRoot "server\tests\test_sale_transfer_api.py"

if (-not (Test-Path $target)) { throw "Target file not found: $target" }

$raw = Get-Content -Raw -Path $target

# Nur innerhalb der Funktion test_sale_transfer_status_admin_forbidden tok_a -> tok_adm ersetzen
$patternFunc = '(?ms)^def\s+test_sale_transfer_status_admin_forbidden\s*\(.*?\):\s*\r?\n(?<body>.*?)(?=^\s*def\s+|\z)'
$m = [regex]::Match($raw, $patternFunc)
if (-not $m.Success) { throw "Function not found: test_sale_transfer_status_admin_forbidden" }

$body = $m.Groups["body"].Value
$body2 = $body -replace '\{tok_a\}', '{tok_adm}'

if ($body2 -eq $body) {
  throw "No change applied (did not find {tok_a} inside admin_forbidden test)."
}

$updated = $raw.Substring(0, $m.Index) + $m.Value -replace [regex]::Escape($body), [regex]::Escape($body2)
# Obiges -replace arbeitet escaped; einfacher und sicherer: direkt zusammensetzen
$updated = $raw.Substring(0, $m.Index) + $m.Value.Replace($body, $body2) + $raw.Substring($m.Index + $m.Length)

Set-Content -Path $target -Value $updated -NoNewline -Encoding utf8
Write-Host "OK: admin_forbidden test uses tok_adm (fixed tok_a NameError)."