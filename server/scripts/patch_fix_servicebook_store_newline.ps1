Set-StrictMode -Off
$ErrorActionPreference = "Stop"

$root = (git rev-parse --show-toplevel).Trim()
Set-Location $root

$f = Join-Path $root "server\app\services\servicebook_store.py"
if (-not (Test-Path $f)) { throw "Missing: $f" }

$txt = Get-Content -LiteralPath $f -Raw -Encoding UTF8

# Fix: fehlender Zeilenumbruch zwischen "...uuid4())" und "def _json_dump"
$pat = 'uuid\.uuid4\(\)\)\s*def _json_dump'
$rep = "uuid.uuid4())`r`n`r`ndef _json_dump"

$txt2 = [regex]::Replace($txt, $pat, $rep, 1)

if ($txt2 -eq $txt) { throw "Pattern not found; file may differ. Expected '$pat'." }

Set-Content -LiteralPath $f -Value $txt2 -Encoding UTF8 -NoNewline
Write-Host "OK: newline between uuid4()) and def _json_dump fixed in $f"