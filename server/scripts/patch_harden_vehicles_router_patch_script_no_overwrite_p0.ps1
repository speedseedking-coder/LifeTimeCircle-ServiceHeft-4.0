# server/scripts/patch_harden_vehicles_router_patch_script_no_overwrite_p0.ps1
# RUN (Repo-Root):
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\patch_harden_vehicles_router_patch_script_no_overwrite_p0.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function _AsText {
  param([AllowNull()][object]$Value)
  if ($null -eq $Value) { return "" }
  return [string]$Value
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$target = "server/scripts/patch_vehicles_router_mvp_p0.ps1"
if (!(Test-Path $target)) { throw "FEHLT: $target" }

$txt = (_AsText (Get-Content $target -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")

$oldLine = 'Update-FileIfChanged -Path "server/app/routers/vehicles.py" -NewContent $vehiclesPy'

if ($txt -notmatch [regex]::Escape($oldLine)) {
  throw "Konnte Zielzeile nicht finden: $oldLine"
}

$replacement = @'
# --- do NOT overwrite vehicles.py if it already exists with a /vehicles router (prevents clobbering consent gate etc.) ---
$vehPath = "server/app/routers/vehicles.py"
$vehExisting = ""
if (Test-Path $vehPath) {
  $vehExisting = (_AsText (Get-Content $vehPath -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")
}
if ($vehExisting -match 'APIRouter\s*\(\s*prefix\s*=\s*"/vehicles"' -or $vehExisting -match 'prefix="/vehicles"' -or $vehExisting -match 'prefix\s*=\s*"/vehicles"') {
  Write-Host "OK: skip overwrite $vehPath (already has /vehicles router)"
} else {
  Update-FileIfChanged -Path "server/app/routers/vehicles.py" -NewContent $vehiclesPy
}
'@

$txt2 = $txt.Replace($oldLine, $replacement)

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($target, $txt2, $utf8NoBom)

Write-Host "OK: hardened $target (no overwrite vehicles.py if already present)"