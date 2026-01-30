# patch_admin_router.ps1
# Mountet den Admin-Router in app/main.py (idempotent).
# - erkennt admin router file (routes.py/router.py/api.py)
# - prüft, ob APIRouter bereits prefix="/admin" hat
# - fügt Import + include_router vor return app ein

$ErrorActionPreference = "Stop"

$serverRoot = Split-Path -Parent $PSScriptRoot
$mainPath = Join-Path $serverRoot "app\main.py"

if (-not (Test-Path $mainPath)) {
  throw "main.py nicht gefunden: $mainPath"
}

# Kandidaten für Admin-Router
$adminDir = Join-Path $serverRoot "app\admin"
if (-not (Test-Path $adminDir)) {
  throw "Admin-Ordner nicht gefunden: $adminDir"
}

$candidates = @(
  @{ File = Join-Path $adminDir "routes.py"; Module = "app.admin.routes" },
  @{ File = Join-Path $adminDir "router.py"; Module = "app.admin.router" },
  @{ File = Join-Path $adminDir "api.py";    Module = "app.admin.api" }
)

$chosen = $null
foreach ($c in $candidates) {
  if (Test-Path $c.File) { $chosen = $c; break }
}

if ($null -eq $chosen) {
  $found = Get-ChildItem -Path $adminDir -Filter "*.py" -Recurse | Select-Object -ExpandProperty FullName
  $hint = if ($found) { ($found -join "`n - ") } else { "(keine .py Dateien gefunden)" }
  throw "Kein Admin-Router gefunden. Erwartet routes.py/router.py/api.py in $adminDir. Gefunden:`n - $hint"
}

$routerFileText = Get-Content -LiteralPath $chosen.File -Raw

# Prüfen ob Router in der Datei bereits prefix="/admin" gesetzt hat
$hasPrefixInRouterFile =
  [regex]::IsMatch(
    $routerFileText,
    'APIRouter\s*\(\s*[^)]*prefix\s*=\s*["' + "'" + ']/admin["' + "'" + ']',
    [System.Text.RegularExpressions.RegexOptions]::Singleline
  )

$importLine = "from $($chosen.Module) import router as admin_router"
$includeLine = if ($hasPrefixInRouterFile) {
  "    app.include_router(admin_router)"
} else {
  "    app.include_router(admin_router, prefix=""/admin"", tags=[""admin""])"
}

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
if ($mainText -notmatch 'include_router\s*\(\s*admin_router') {
  if ($mainText -match '(?m)^\s*return\s+app\s*$') {
    $mainText = [regex]::Replace(
      $mainText,
      '(?m)^\s*return\s+app\s*$',
      "$includeLine`r`n    return app",
      1
    )
    $changed = $true
  } else {
    throw "Konnte 'return app' in create_app() nicht finden."
  }
}

if ($changed) {
  Set-Content -LiteralPath $mainPath -Value $mainText -Encoding UTF8
  Write-Host "OK: Admin-Router gemountet in $mainPath"
  Write-Host " - Router-Modul: $($chosen.Module)"
  Write-Host " - Router hat prefix in Datei: $hasPrefixInRouterFile"
} else {
  Write-Host "OK: Keine Änderungen nötig (Admin-Router scheint bereits gemountet)."
}
