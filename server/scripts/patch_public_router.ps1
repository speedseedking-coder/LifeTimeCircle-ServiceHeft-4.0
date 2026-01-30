# C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server\scripts\patch_public_router.ps1
# Mountet den Public-QR Router in app/main.py (idempotent).

$ErrorActionPreference = "Stop"

$serverRoot = Split-Path -Parent $PSScriptRoot
$mainPath = Join-Path $serverRoot "app\main.py"

if (-not (Test-Path $mainPath)) {
  throw "main.py nicht gefunden: $mainPath"
}

# sicherstellen, dass public module existiert
$publicDir = Join-Path $serverRoot "app\public"
if (-not (Test-Path $publicDir)) {
  throw "Public-Ordner nicht gefunden: $publicDir (bitte app/public anlegen)"
}

$routesPath = Join-Path $publicDir "routes.py"
if (-not (Test-Path $routesPath)) {
  throw "Public routes.py nicht gefunden: $routesPath"
}

$importLine = "from app.public.routes import router as public_router"
$includeRegex = 'include_router\s*\(\s*public_router\b'

$mainText = Get-Content -LiteralPath $mainPath -Raw
$changed = $false

# 1) Import einfügen (vor def create_app), falls fehlt
if ($mainText -notmatch [regex]::Escape($importLine)) {
  if ($mainText -match '(?m)^\s*def\s+create_app\s*\(') {
    $mainText = [regex]::Replace(
      $mainText,
      '(?m)^\s*def\s+create_app\s*\(',
      "$importLine`r`n`r`ndef create_app(",
      1
    )
    $changed = $true
  } else {
    throw "Konnte def create_app(...) in main.py nicht finden."
  }
}

# 2) include_router einfügen (vor return app), falls fehlt
if ($mainText -notmatch $includeRegex) {
  if ($mainText -match '(?m)^\s*return\s+app\s*$') {
    $mainText = [regex]::Replace(
      $mainText,
      '(?m)^\s*return\s+app\s*$',
      "    app.include_router(public_router)`r`n    return app",
      1
    )
    $changed = $true
  } else {
    throw "Konnte 'return app' in create_app() nicht finden."
  }
}

if ($changed) {
  Set-Content -LiteralPath $mainPath -Value $mainText -Encoding UTF8
  Write-Host "OK: Public-Router gemountet in $mainPath"
} else {
  Write-Host "OK: Keine Änderungen nötig (Public-Router scheint bereits gemountet)."
}
