# server/scripts/patch_normalize_sale_transfer_tests.ps1
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$target   = Join-Path $repoRoot "server\tests\test_sale_transfer_api.py"

if (-not (Test-Path $target)) { throw "Target file not found: $target" }

$raw = Get-Content -Raw -Path $target
$updated = $raw

# --- 1) Rename admin test (optional, if still old name exists)
$updated = $updated -replace 'def\s+test_sale_transfer_status_admin_can_read\s*\(', 'def test_sale_transfer_status_admin_forbidden('

# --- 2) Happy path: VIP initiator (tok_a) must see status -> 200 (indent-safe)
$patHappy = '(?m)^(?<i>[ \t]*)rs\s*=\s*client\.get\(\s*f"/sale/transfer/status/\{tid\}"\s*,\s*headers=\{"Authorization":\s*f"Bearer\s*\{tok_a\}"\}\s*\)\s*\r?\n[ \t]*assert\s+rs\.status_code\s*==\s*\d+\s*,\s*rs\.text\s*$'
$repHappy = '${i}rs = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_a}"})' + "`r`n" +
            '${i}assert rs.status_code == 200, rs.text'

$matchesHappy = ([regex]::Matches($updated, $patHappy)).Count
if ($matchesHappy -lt 1) { throw "Happy path tok_a status block not found." }
$updated = [regex]::Replace($updated, $patHappy, $repHappy)

# --- 3) Admin forbidden test: force tok_adm + 403 (only inside that function)
$funcPat = '(?ms)^def\s+test_sale_transfer_status_admin_forbidden\s*\(.*?\):\s*\r?\n(?<body>.*?)(?=^\s*def\s+|\z)'
$m = [regex]::Match($updated, $funcPat)
if (-not $m.Success) { throw "Function not found: test_sale_transfer_status_admin_forbidden" }

$funcText = $m.Value
$body     = $m.Groups["body"].Value

# ensure token example/fixture is tok_adm (if some script left tok_a behind)
$body2 = $body -replace '\{tok_a\}', '{tok_adm}'

# enforce rs/assert block (indent-safe) -> 403
$patAdm = '(?m)^(?<i>[ \t]*)rs\s*=\s*client\.get\(\s*f"/sale/transfer/status/\{tid\}"\s*,\s*headers=\{"Authorization":\s*f"Bearer\s*\{tok_adm\}"\}\s*\)\s*\r?\n[ \t]*assert\s+rs\.status_code\s*==\s*\d+\s*,\s*rs\.text\s*$'
$repAdm = '${i}rs = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_adm}"})' + "`r`n" +
          '${i}assert rs.status_code == 403, rs.text'

$matchesAdm = ([regex]::Matches($body2, $patAdm)).Count
if ($matchesAdm -lt 1) { throw "Admin forbidden rs/assert block not found inside function." }

$body2 = [regex]::Replace($body2, $patAdm, $repAdm)

$funcText2 = $funcText.Replace($body, $body2)
$updated = $updated.Substring(0, $m.Index) + $funcText2 + $updated.Substring($m.Index + $m.Length)

if ($updated -eq $raw) { throw "No changes applied (unexpected)." }

Set-Content -Path $target -Value $updated -NoNewline -Encoding utf8
Write-Host "OK: sale_transfer tests normalized (vip=200, admin=403, indent-safe)."