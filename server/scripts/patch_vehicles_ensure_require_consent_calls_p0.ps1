# server/scripts/patch_vehicles_ensure_require_consent_calls_p0.ps1
# RUN (Repo-Root):
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\patch_vehicles_ensure_require_consent_calls_p0.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function _AsText { param([AllowNull()][object]$v) if($null -eq $v){""} else {[string]$v} }

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$path = "server/app/routers/vehicles.py"
if (!(Test-Path $path)) { throw "FEHLT: $path" }

$txt = (_AsText (Get-Content $path -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")

if ($txt -notmatch "(?m)^\s*def\s+require_consent\s*\(") {
  throw "require_consent() fehlt in vehicles.py (erst patch_vehicles_add_require_consent_p0.ps1 laufen lassen)."
}

function Ensure-ConsentCall([string]$FuncName) {
  $re = "(?ms)(^def\s+$FuncName\b.*?:\n)(.*?)(?=\n@router\.|\n^def\s+|\Z)"
  $m = [regex]::Match($txt, $re)
  if (-not $m.Success) { throw "Function block nicht gefunden: $FuncName" }

  $block = $m.Value
  if ($block -match "(?m)^\s*require_consent\(db,\s*actor\)\s*$") { return }

  $block2 = [regex]::Replace(
    $block,
    "(?m)^(\s*)role\s*=\s*_enforce_role\(actor\)\s*$",
    "`$1role = _enforce_role(actor)`n`$1require_consent(db, actor)",
    1
  )
  if ($block2 -eq $block) { throw "Insert-Point nicht gefunden in $FuncName (role=_enforce_role(actor) fehlt?)" }

  $script:txt = $txt.Replace($block, $block2)
}

Ensure-ConsentCall "create_vehicle"
Ensure-ConsentCall "list_vehicles"
Ensure-ConsentCall "get_vehicle"

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $txt, $utf8NoBom)

Write-Host "OK: ensured require_consent(db, actor) in create/list/get."