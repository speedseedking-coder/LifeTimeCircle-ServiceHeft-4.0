# tools/ist_check.ps1
# LifeTimeCircle – ServiceHeft 4.0
# Zweck: schneller IST-Check inkl. BOM-Gate (fail-fast)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (git rev-parse --show-toplevel).Trim()
Set-Location $root
[Environment]::CurrentDirectory = $root

Write-Host "==> BOM gate (repo): python ./tools/bom_scan.py --root ."

if (Get-Command python -ErrorAction SilentlyContinue) {
  & python ".\tools\bom_scan.py" --root "." | Out-Host
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 ".\tools\bom_scan.py" --root "." | Out-Host
} else {
  throw "Weder 'python' noch 'py' gefunden fuer BOM-Gate."
}

$rc = $LASTEXITCODE
if ($rc -ne 0) {
  throw "BOM gate failed (exit=$rc)"
}

Write-Host "==> IST-Zustand Voll-Check"
& (Join-Path $root "server\scripts\ltc_verify_ist_zustand.ps1")
if ($LASTEXITCODE -ne 0) {
  throw "ltc_verify_ist_zustand failed (exit=$LASTEXITCODE)"
}

Write-Host "OK: IST-Check inkl. BOM-Gate erfolgreich."